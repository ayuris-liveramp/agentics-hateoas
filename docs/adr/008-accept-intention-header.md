# ADR-008: Accept-Intention Header for Agent Intent Specification

## Status
Accepted

## Context

In Phase 4 development (commit e70a00f), the Root App needed a way for agents to express what they were looking for when making HEAD requests. The problem:

**Scenario 1**: Agent asks Root App "what can I do with orders?"
**Scenario 2**: Agent asks Root App "show me only public products"
**Scenario 3**: Agent asks Root App "what customer-related resources exist?"

Without a way to express intent, the Root App would always return the same discovery response: a full graph of all available resources. This isn't ideal because:

1. **Verbose**: Full API surface may have hundreds of resources
2. **Irrelevant**: Agent might only care about specific resource types
3. **Inefficient**: Sending full schema when subset is needed
4. **Confusing**: Agent gets more information than useful

The team needed a header-based mechanism to let agents specify what they're interested in, enabling the Root App to filter responses intelligently.

## Decision

Introduce a custom HTTP header `Accept-Intention` for agents to express their intent. Root App parses this header and filters discovery responses accordingly.

**Format**:
```
Accept-Intention: action=read, resource=order, details=full
```

**Components**:
- `action`: What the agent wants to do (read, write, list, search)
- `resource`: What entity type (order, customer, product, or `*` for all)
- `details`: Level of detail (full, summary, minimal)

**Example Usage**:
```bash
# Agent wants to read order data
HEAD /orders HTTP/1.1
Accept-Intention: action=read, resource=order, details=full

# Agent wants list of all resources
HEAD / HTTP/1.1
Accept-Intention: action=list, resource=*, details=summary

# Agent wants minimal public info
HEAD /customers HTTP/1.1
Accept-Intention: action=read, resource=customer, details=minimal
```

## Rationale

### Why Custom Header?

**Standard HTTP Semantics:**
- Headers are designed for metadata about the request
- Intent is metadata, not part of request body
- Leverages HTTP infrastructure (logging, routing)
- Works with existing proxies and caches

**Why Not Query Parameters?**
- Query parameters typically filter data, not intent
- Intent is about the response format/filtering, not data filtering
- Headers are cleaner for metadata
- Doesn't pollute the cache key (same resource, different intent)

**Why Not Accept Header?**
- `Accept` typically specifies content type (application/json vs application/xml)
- Intent is different from content type
- Using `Accept` would conflate two concerns
- Custom header is clearer

**Why Not POST/Payload?**
- HEAD requests typically have no body
- Keeping HEAD bodyless (with intent in header) is cleaner
- No need to parse body for simple intent

### Intent Components

**action** (what to do):
- `read` — Retrieve information (GET-like)
- `write` — Create or modify (POST/PUT-like)
- `list` — Enumerate available resources
- `search` — Query with filters
- `*` — Any action

**resource** (what entity):
- `order`, `customer`, `product` — Specific type
- `*` — All types
- Filters discovery to only relevant resources

**details** (how much info):
- `full` — Complete schema, examples, all fields
- `summary` — Basic schema, required fields
- `minimal` — Just names and IDs
- Reduces response verbosity

## Consequences

### Positive
- ✅ Agents can express what they need
- ✅ Root App can filter responses intelligently
- ✅ Reduces response size (only relevant resources)
- ✅ Improves discoverability (less noise)
- ✅ Enables efficient agent planning (agents know what's available upfront)
- ✅ Standard HTTP header mechanism
- ✅ Extensible: new intent parameters can be added
- ✅ Optional: defaults work if header absent

### Negative
- ❌ Custom header not part of HTTP standard
- ❌ Agents need to understand intent format
- ❌ Filtering logic adds complexity to Root App
- ❌ Intent filtering needs testing/validation
- ❌ Potential for mismatched expectations (agent vs server)
- ❌ Additional parsing and validation overhead

## Implementation

### Header Parsing

**IntentionParser** (`root_app/agent/intention_parser.py`):

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Intention:
    action: str  # read, write, list, search, or *
    resource: str  # order, customer, product, or *
    details: str  # full, summary, minimal

class IntentionParser:
    @staticmethod
    def parse(header_value: Optional[str]) -> Intention:
        """
        Parse Accept-Intention header.
        
        Format: action=read, resource=order, details=full
        
        Defaults: action=read, resource=*, details=summary
        """
        if not header_value:
            return Intention(action='read', resource='*', details='summary')
        
        # Parse comma-separated key=value pairs
        parts = {}
        for pair in header_value.split(','):
            key, value = pair.strip().split('=', 1)
            parts[key.strip()] = value.strip()
        
        return Intention(
            action=parts.get('action', 'read'),
            resource=parts.get('resource', '*'),
            details=parts.get('details', 'summary')
        )

    @staticmethod
    def validate(intention: Intention) -> bool:
        """Validate intention values."""
        valid_actions = {'read', 'write', 'list', 'search', '*'}
        valid_details = {'full', 'summary', 'minimal'}
        
        if intention.action not in valid_actions:
            return False
        if intention.details not in valid_details:
            return False
        if intention.resource and not intention.resource.isidentifier() and intention.resource != '*':
            return False
        
        return True
```

### Response Filtering

**SkillBuilder with Intent Filtering** (`root_app/agent/skill_builder.py`):

```python
class SkillBuilder:
    def build_skills(
        self, 
        graph: APIGraph, 
        intention: Intention
    ) -> str:
        """
        Convert API graph to markdown skills, filtered by intention.
        """
        # Filter resources by action and resource type
        filtered_resources = self._filter_by_intention(graph, intention)
        
        # Generate markdown
        markdown = "# Available Skills\n\n"
        
        for resource in filtered_resources:
            # Include different detail levels
            if intention.details == 'minimal':
                markdown += self._minimal_skill(resource)
            elif intention.details == 'summary':
                markdown += self._summary_skill(resource)
            else:  # full
                markdown += self._full_skill(resource)
        
        return markdown
    
    def _filter_by_intention(
        self, 
        graph: APIGraph, 
        intention: Intention
    ) -> List[APIResource]:
        """Filter graph by action and resource type."""
        filtered = []
        
        for resource in graph.nodes.values():
            # Filter by resource type
            if intention.resource != '*':
                if not resource.path.endswith(intention.resource):
                    continue
            
            # Filter by action
            if intention.action != '*':
                if intention.action not in self._get_resource_actions(resource):
                    continue
            
            filtered.append(resource)
        
        return filtered
    
    def _get_resource_actions(self, resource: APIResource) -> List[str]:
        """Determine what actions are available for a resource."""
        # Based on HTTP methods supported
        actions = []
        if resource.supports_get:
            actions.append('read')
        if resource.supports_post:
            actions.append('write')
        if resource.has_children:
            actions.append('list')
        # etc.
        return actions
    
    def _minimal_skill(self, resource: APIResource) -> str:
        """Generate minimal skill description (just names)."""
        return f"- {resource.path}\n"
    
    def _summary_skill(self, resource: APIResource) -> str:
        """Generate summary skill description."""
        return f"""## {resource.name}
{resource.description}

Path: {resource.path}

"""
    
    def _full_skill(self, resource: APIResource) -> str:
        """Generate full skill description with schema."""
        schema_str = json.dumps(resource.schema, indent=2)
        return f"""## {resource.name}
{resource.description}

**Endpoint**: {resource.path}

**Schema**:
```json
{schema_str}
```

**Available Actions**: {', '.join(self._get_resource_actions(resource))}

"""
```

### Discovery Route Handler

**Root App HEAD Handler** (`root_app/routes/discovery.py`):

```python
@app.head('/<path:path>')
def head_discovery(path=''):
    """
    Respond to agent discovery requests.
    
    Parses Accept-Intention header and returns filtered skills.
    """
    # Parse intention
    intention_header = request.headers.get('Accept-Intention')
    intention = IntentionParser.parse(intention_header)
    
    # Validate
    if not IntentionParser.validate(intention):
        return {'error': 'Invalid intention'}, 400
    
    # Build skills from graph
    skills = SkillBuilder().build_skills(api_graph, intention)
    
    # Generate ETag
    etag = generate_etag(skills)
    
    # Return response
    response = Response(skills)
    response.headers['ETag'] = f'"{etag}"'
    response.headers['Content-Type'] = 'text/markdown'
    
    # Handle conditional requests
    if_none_match = request.headers.get('If-None-Match')
    if if_none_match == f'"{etag}"':
        return '', 304
    
    return response
```

### Example Agent Usage

**Python agent using agentics-hateoas**:

```python
import requests

# What can I do with orders?
response = requests.head(
    'http://localhost:5001/orders',
    headers={
        'Accept-Intention': 'action=read, resource=order, details=full'
    }
)

skills = response.text  # Markdown skill description
print(skills)
# Output:
# # Available Skills
# ## Orders
# Fetch order information...
# **Endpoint**: /orders
# **Schema**: {...}
```

## Intent Matching Examples

### Example 1: List All Available Resources

**Request**:
```
HEAD / HTTP/1.1
Accept-Intention: action=list, resource=*, details=summary
```

**Response**: Markdown with all available resources and their purposes

### Example 2: Just Customer Resources

**Request**:
```
HEAD / HTTP/1.1
Accept-Intention: action=*, resource=customer, details=full
```

**Response**: Complete schema for all customer-related endpoints

### Example 3: What Can I Write?

**Request**:
```
HEAD / HTTP/1.1
Accept-Intention: action=write, resource=*, details=summary
```

**Response**: Only endpoints that support POST/PUT operations

## Default Behavior

If `Accept-Intention` header is absent:

```python
# Defaults
action = 'read'     # Assume reading data
resource = '*'      # Show all resources
details = 'summary' # Show moderate detail
```

This ensures backward compatibility with agents that don't use the header.

## Testing

**Unit Tests** (`tests/test_intention.py`):

```python
def test_parse_full_intention():
    header = 'action=read, resource=order, details=full'
    intention = IntentionParser.parse(header)
    assert intention.action == 'read'
    assert intention.resource == 'order'
    assert intention.details == 'full'

def test_parse_defaults():
    intention = IntentionParser.parse(None)
    assert intention.action == 'read'
    assert intention.resource == '*'
    assert intention.details == 'summary'

def test_validate_intention():
    good = Intention(action='read', resource='order', details='full')
    assert IntentionParser.validate(good)
    
    bad = Intention(action='invalid', resource='order', details='full')
    assert not IntentionParser.validate(bad)
```

**Integration Tests** (`tests/test_discovery_filtering.py`):

```python
def test_filter_by_resource_type():
    # Request only customer resources
    response = client.head(
        '/',
        headers={'Accept-Intention': 'resource=customer'}
    )
    
    skills = response.text
    assert 'Orders' not in skills  # Filtered out
    assert 'Customers' in skills

def test_detail_levels():
    # Full detail
    full = client.head(
        '/',
        headers={'Accept-Intention': 'details=full'}
    ).text
    
    # Minimal detail
    minimal = client.head(
        '/',
        headers={'Accept-Intention': 'details=minimal'}
    ).text
    
    assert len(full) > len(minimal)
```

## Extensibility

The header format allows for future parameters:

```
Accept-Intention: action=read, resource=order, details=full, 
                  scope=my_org, version=2, cached=true
```

New parameters can be added without breaking existing agents.

## Related Commits

- **e70a00f**: IntentionParser and SkillBuilder implementation

## Limitations & Future Work

**Current Limitations**:
- No complex boolean logic (can't ask for "orders OR customers")
- No field-level filtering ("just id and status")
- No pagination hints

**Future Enhancements**:
1. **Advanced filtering**: Support field selectors
2. **Pagination intent**: Specify expected result size
3. **Versioning intent**: Request specific API version
4. **Performance hints**: Request cached vs fresh data
5. **Relationship intent**: Include/exclude related resources

## References

- **Commits**: e70a00f (IntentionParser and SkillBuilder)
- **Code**:
  - `root_app/agent/intention_parser.py` — Header parsing
  - `root_app/agent/skill_builder.py` — Intent-based filtering
  - `root_app/routes/discovery.py` — Handler using intent
  - `tests/test_intention.py` — Parser tests
  - `tests/test_discovery_filtering.py` — Filtering tests
- **Related ADRs**:
  - [ADR-002](002-hateoas-head-request-protocol.md) — HEAD protocol
  - [ADR-007](007-dual-get-head-endpoints.md) — Dual endpoint design
  - [ADR-001](001-two-tier-microservice-architecture.md) — Root app architecture

## Design Philosophy

This ADR reflects a principle: **make the protocol intelligent enough to support agent needs while keeping it simple enough to understand and implement.**

The `Accept-Intention` header bridges that gap:
- Simple enough for agents to construct
- Powerful enough for Root App to make decisions
- Extensible for future needs
- Based on HTTP standards (headers for metadata)

## Prior Art

Similar intent-specification mechanisms exist:
- **HTTP Accept header**: Specifies content type preference
- **GraphQL query fields**: Specify which fields to return
- **REST query parameters**: Filter results by attributes
- **RPC method parameters**: Specify operation parameters

The `Accept-Intention` header combines lessons from these approaches for API discovery specifically.
