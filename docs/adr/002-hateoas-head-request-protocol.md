# ADR-002: HATEOAS + HEAD Request Protocol for API Discovery

## Status
Accepted

## Context

LLM agents need to discover what operations are available in an API without:
- Pre-built documentation or API specs
- Hardcoded knowledge of endpoints
- Making actual data requests to understand structure
- Requiring authentication secrets upfront

Traditional approaches (OpenAPI specs, GraphQL introspection, custom endpoints) require manual configuration or pre-setup. The project needed a self-describing protocol where agents could explore APIs dynamically.

HTTP already has HEAD requests (like GET but without response body), which could carry metadata. HATEOAS (Hypermedia As The Engine Of Application State) provides a pattern for hypermedia links that enable graph traversal.

## Decision

Use HTTP HEAD requests with HATEOAS links for API discovery:

1. **HEAD requests** return schemas and metadata without resource data
2. **Response body** includes JSON schema for validation and OpenAPI-like structure
3. **HATEOAS links** (`_links.children`) point to related resources for graph traversal
4. **ETag headers** enable efficient cache validation for recrawling

Example:
```
HEAD /orders
← 200 OK
← ETag: "abc123"
← Content-Type: application/json
{
  "description": "Orders collection",
  "schema": {
    "type": "object",
    "properties": {...}
  },
  "_links": {
    "children": ["/orders/1", "/orders/2", ...]
  }
}
```

## Rationale

### Why HEAD + HATEOAS?

**Standard HTTP:**
- HEAD method is part of HTTP spec; agents/crawlers naturally understand it
- No custom protocol; uses existing HTTP infrastructure
- Works with any HTTP library or tool

**Schema Discovery:**
- JSON schema returned in response body describes data structure
- Agents can validate inputs and understand outputs without trial-and-error
- Different roles can receive filtered schemas (RBAC)

**Graph Traversal:**
- HATEOAS links enable automatic discovery without hardcoding paths
- `_links.children` provides entry points for traversal
- API evolution doesn't break agent discovery (new endpoints auto-discover)

**Efficiency:**
- HEAD requests don't require data transfer (no payload)
- Agents can discover structure without loading thousands of records
- Combined with ETags, enables intelligent caching

**Universality:**
- Same pattern works for any REST API (not tied to specific tech stack)
- Agents can apply the same discovery logic to multiple APIs
- No API-specific integration code needed

### Why Not Alternatives?

**OpenAPI/Swagger:**
- ✗ Requires manual specification (not self-describing)
- ✗ Separate from API (can drift out of sync)
- ✗ Agents need to fetch, parse, understand spec format

**GraphQL:**
- ✗ Requires API to be built with GraphQL
- ✗ Can't be applied to existing REST APIs
- ✗ More complex introspection protocol
- ✗ Not all agents understand GraphQL

**Custom Discovery Endpoint:**
- ✗ Each API decides format (no standardization)
- ✗ Requires documentation of custom format
- ✗ Not part of HTTP standard

**GET with schema query parameter:**
- ✗ Pollutes GET semantics (GET should return data)
- ✗ Doesn't leverage HTTP method semantics
- ✗ Caching becomes ambiguous

## Consequences

### Positive
- ✅ Self-describing protocol: agents can discover any compliant API
- ✅ Standard HTTP: no custom protocol needed
- ✅ Efficient: HEAD doesn't require data transfer
- ✅ Extensible: response body can grow without breaking clients
- ✅ Backward compatible: coexists with normal GET endpoints
- ✅ Traversable: HATEOAS links enable automatic exploration

### Negative
- ❌ Non-standard usage: HEAD typically returns no body; agents need to handle this
- ❌ Semantic oddity: response body on HEAD request violates some strict interpretations
- ❌ Discovery overhead: discovering full API requires multiple requests
- ❌ Coupling: agents must follow schema conventions
- ❌ Caching complexity: standard caches may not understand HEAD bodies

## Alternatives Considered

| Approach | Discovery? | Standard? | Manual Config? | API Agnostic? |
|----------|-----------|-----------|-----------------|---------------|
| **HEAD + HATEOAS (Chosen)** | ✓ | ✓ HTTP | ✗ | ✓ |
| OpenAPI | ✓ | ✓ Spec | ✓ | ✓ |
| GraphQL | ✓ | ✗ Custom | ✓ | ✗ |
| Custom endpoint | ✓ | ✗ Custom | ✓ | ✗ |
| Documentation only | ✗ | N/A | ✓ | N/A |

## Implementation Notes

**Leaf API HEAD Handlers** (`leaf_api/resources/`):
- Each resource (Orders, Customers, Products) implements HEAD handler
- Generates JSON schema based on SQLModel definitions
- Returns HATEOAS links to child resources and related endpoints
- Applies role-based filtering based on JWT claims
- Generates ETag from response content

**Root App Discovery Routes** (`root_app/routes/discovery.py`):
- Universal HEAD handler `head_handler()`
- Parses Accept-Intention header for filtering
- Queries cached API graph
- Returns skill markdown to agents
- Sets ETag header for conditional requests

**Crawler Logic** (`root_app/crawler/`):
- APICrawler makes HEAD requests to discover API surface
- Recursive traversal follows `_links.children` links
- Cycle detection prevents infinite loops
- Stores discovered structure in APIGraph

**Related commits**:
- 0f3e83e: Initial discovery protocol with HEAD endpoints
- e70a00f: Agent interface with skill building

## Query Parameter Extensions

The protocol supports optional query parameters to modify schema:

- `?positive_only=true` — Constrain numeric fields to non-negative
- `?detailed=true` — Include extended properties and timestamps
- `?summary=true` — Return only required fields
- `?include_examples=true` — Add example values to schema

These are applied at schema generation time, enabling flexible discovery.

## References

- **Commits**: 0f3e83e (Discovery protocol), e70a00f (Agent interface)
- **Architecture**: [Data Flow section](../ARCHITECTURE.md#data-flow)
- **Related ADRs**:
  - [ADR-001](001-two-tier-microservice-architecture.md) — Two-tier design that makes this pattern necessary
  - [ADR-004](004-etag-based-caching.md) — Caching built on HEAD responses
  - [ADR-008](008-accept-intention-header.md) — Agent intent specification
- **Code**:
  - `leaf_api/resources/` — HEAD endpoint implementations
  - `root_app/crawler/api_crawler.py` — Discovery crawling
  - `root_app/routes/discovery.py` — Agent discovery routes

## Design Principles

This decision embodies several key principles:

1. **Use existing standards** — HTTP HEAD is part of the HTTP spec, not a custom protocol
2. **Discoverability over documentation** — API describes itself via protocol, not separate docs
3. **Composability** — Pattern applies to multiple APIs without modification
4. **Efficiency** — Metadata delivery is optimized (no data transfer)
5. **Autonomy** — Agents can explore without pre-configuration

## Open Questions & Future Work

- **Real-time updates**: Currently root app caches discoveries; could we invalidate on API changes?
- **Cross-API relationships**: How do links work across multiple leaf APIs?
- **Partial discovery**: What's the minimum subset to discover for an agent to be useful?
- **Schema versioning**: How do we handle schema evolution while maintaining backward compatibility?
