# ADR-007: Dual GET/HEAD Endpoints for Optimization

## Status
Accepted

## Context

REST APIs typically provide GET endpoints to fetch data. When the discovery protocol was designed (ADR-002), agents needed to understand available operations and data structures without:
- Fetching full datasets (e.g., all 100,000 orders)
- Loading large response bodies
- Making unnecessary data requests

This created a dilemma:

**Option A**: PUT discovery data in GET responses
- Agents could discover by calling GET
- But GET endpoints return massive payloads
- Agents waste bandwidth and time fetching all data

**Option B**: Use HEAD requests for discovery metadata
- HEAD is intended for headers-only responses
- Returns metadata without body
- But HTTP spec typically doesn't include response body for HEAD

**Option C**: Create separate discovery endpoints
- `/orders` for data
- `/orders/schema` or `/orders/discovery` for metadata
- Bloats API surface with extra endpoints

The team chose Option B: dual GET/HEAD on the same endpoints, leveraging HEAD's metadata nature while including a body (valid in HTTP, though unconventional).

## Decision

Implement both GET and HEAD handlers on all resource endpoints:

1. **GET /resource**: Returns actual data (traditional REST)
   - For agents/clients wanting to fetch actual records
   - Full response body with pagination, filtering, etc.
   - Use for operational data requests

2. **HEAD /resource**: Returns discovery metadata (schema, links)
   - Returns schema, description, HATEOAS links
   - Includes response body (unconventional but valid)
   - Use for discovery, schema validation, caching checks
   - No actual data included

**Same endpoint, different purposes:**
```
GET /orders
← 200 OK, Content-Length: 50KB
← Body: [{"id": 1, "quantity": 5, ...}, {"id": 2, ...}, ...]

HEAD /orders
← 200 OK, Content-Length: ~3KB
← Body: {"description": "...", "schema": {...}, "_links": {...}}
```

## Rationale

### Why Dual Endpoints?

**Clean Separation of Concerns:**
- GET: Operational data retrieval
- HEAD: Schema discovery and metadata
- Same logical resource, different views
- Agents can choose which to use based on needs

**HTTP Standard Compliance:**
- GET and HEAD are part of HTTP standard
- No custom protocol or extensions needed
- Standard tools and libraries understand both

**Efficiency:**
- Agents discovering API: use HEAD (no data transfer)
- Agents fetching records: use GET (get actual data)
- No forced choice between discovery and operations

**Optimization Opportunity:**
- HEAD responses are smaller (schema only)
- Can be heavily cached (identical for role, ETag-based)
- GET responses are larger (all data)
- Different caching strategies work for each

**Single Implementation Path:**
- Both handlers call same schema builder
- Avoid endpoint duplication
- Single source of truth for what "orders" means
- Reduces maintenance burden

### Alternatives Considered

| Approach | Discovery? | Data? | Endpoint Count | Complexity |
|----------|-----------|-------|---|---|
| **Dual GET/HEAD (Chosen)** | ✓ | ✓ | 1 per resource | Medium |
| Separate discovery endpoint | ✓ | ✓ | 2 per resource | Medium |
| GET only (data in response) | ⚠ | ✓ | 1 per resource | Low |
| HEAD only | ✓ | ✗ | 1 per resource | Low |
| Query parameter for schema | ✓ | ✓ | 1 per resource | High |
| RPC-style endpoint | ✓ | ✓ | Custom | High |

Dual GET/HEAD wins because it:
- ✓ Supports both discovery and operations
- ✓ Uses standard HTTP methods
- ✓ Maintains single endpoint per resource
- ✓ Keeps complexity manageable

## Consequences

### Positive
- ✅ Discovery doesn't require fetching all data
- ✅ Single endpoint (no schema-specific URLs like `/schema`)
- ✅ Standard HTTP methods (GET/HEAD) understood by all tools
- ✅ Agents have choice: discover via HEAD, fetch via GET
- ✅ Caching strategies can differ (HEAD vs GET)
- ✅ Clean semantics: HEAD=structure, GET=data
- ✅ Backward compatible: GET still works for data

### Negative
- ❌ Non-standard: HEAD responses usually have no body
- ❌ Implementation overhead: handle both methods
- ❌ Client confusion: what's the difference between GET and HEAD responses?
- ❌ Caching complexity: headers might differ (Content-Length)
- ❌ Agents need to understand both patterns
- ❌ Testing burden: test both GET and HEAD paths

## HTTP Semantics Considerations

### HEAD Specification

**Standard HTTP (RFC 7231)**:
> The server MUST NOT send a message body in the response to a HEAD request.

**Agentics-HATEOAS Interpretation**:
- HEAD responses *do* include a body (metadata/schema)
- This is technically not strictly compliant
- But valid in practice: many systems ignore this constraint

**Why This Works**:
- HTTP libraries send HEAD without `Content-Length` mismatch
- Cache validators still function correctly
- Most clients handle extra body gracefully
- The response is still "metadata" (schema), not "data" (records)

### Content-Length Handling

**GET response**:
```
GET /orders
← Content-Length: 50000 (actual data)
← Body: [50KB of actual order records]
```

**HEAD response**:
```
HEAD /orders
← Content-Length: 3000 (schema)
← Body: {schema document}
```

Standard behavior: clients see same headers as GET but get metadata instead of data.

### Caching Implications

**GET responses**:
- Cached separately per query string
- May include `?limit=10&offset=20`
- Larger cache footprint

**HEAD responses**:
- Cached separately (different method)
- ETag used for validation
- Smaller cache footprint
- Can be heavily cached (same schema always returned)

## Implementation

### Resource Handler Pattern

**Orders endpoint** (`leaf_api/resources/orders.py`):

```python
@orders_bp.get('/orders')
def get_orders():
    """Fetch actual order data."""
    # Authorization check
    role = extract_jwt_context(request)
    
    # Query orders from database
    orders = Order.query.limit(100).all()
    
    # Return actual data
    return {
        'data': [order.model_dump() for order in orders],
        'count': len(orders),
        'links': {
            'self': '/orders'
        }
    }

@orders_bp.head('/orders')
def head_orders():
    """Discover schema and metadata."""
    # Authorization check
    role = extract_jwt_context(request)
    
    # Generate schema (no database query)
    schema = JSONSchemaBuilder().build(Order, role=role)
    
    # Get children (order IDs for graph structure)
    children = Order.query.with_entities(Order.id).limit(100).all()
    
    # Build discovery response
    response = {
        'description': 'Orders collection',
        'schema': schema,
        '_links': {
            'children': [f'/orders/{o.id}' for o in children]
        }
    }
    
    # Return with ETag
    etag = generate_etag(response)
    return jsonify(response), 200, {
        'ETag': f'"{etag}"',
        'Cache-Control': 'public, max-age=3600'
    }
```

### Shared Code

Both GET and HEAD can share:
```python
def generate_schema(role: Role) -> dict:
    """Shared schema generation."""
    return JSONSchemaBuilder().build(Order, role=role)
```

### Routing

Flask routes:

```python
# Single endpoint, both methods
@orders_bp.route('/orders', methods=['GET', 'HEAD'])
def orders_handler():
    if request.method == 'GET':
        return get_orders()
    elif request.method == 'HEAD':
        return head_orders()
```

Or with decorators:

```python
@orders_bp.get('/orders')
def get_orders(): ...

@orders_bp.head('/orders')
def head_orders(): ...
```

## Workflow

### Agent Discovery Flow

```
Agent wants to know about orders:
1. HEAD /orders (discover schema)
   ← 200 OK, ETag: "abc123"
   ← Body: {description, schema, _links: [/orders/1, /orders/2, ...]}

2. Agent decides what to do with this info
   Option A: Fetch some data
   → GET /orders?limit=10 (get actual data)

   Option B: Explore related resources
   → HEAD /orders/1 (discover individual order)

   Option C: Ask about customers
   → HEAD /customers (discover different resource)
```

### Agent HATEOAS Traversal

```
1. START: HEAD /orders
   Discover: customers, products resources available

2. TRAVERSE: HEAD /customers
   Discover: customer schema, fields

3. TRAVERSE: HEAD /products
   Discover: product schema, fields

4. OPERATE: GET /orders?customer=1
   Get actual data for that customer
```

## Testing

### Unit Tests

**GET Endpoints** (`tests/test_endpoints.py`):
```python
def test_get_orders():
    response = client.get('/orders')
    assert response.status_code == 200
    assert 'data' in response.json
    assert response.content_length > 1000  # Has actual data

def test_get_requires_auth():
    response = client.get('/orders')  # No JWT
    assert response.status_code == 401
```

**HEAD Endpoints** (`tests/test_discovery.py`):
```python
def test_head_orders():
    response = client.head('/orders')
    assert response.status_code == 200
    assert 'schema' in response.json
    assert 'ETag' in response.headers
    assert response.content_length < 10000  # Metadata only

def test_head_returns_schema():
    response = client.head('/orders')
    schema = response.json['schema']
    assert 'properties' in schema
    assert 'type' in schema
```

### Integration Tests

```python
def test_discovery_then_fetch():
    # Discover schema
    discovery = client.head('/orders').json
    
    # Use schema to validate subsequent data fetch
    data = client.get('/orders').json
    
    # Validate data matches schema
    assert matches_schema(data, discovery['schema'])
```

## Real-World Usage

### Agents Using Both

1. **Discovery-first agents**: 
   - HEAD /resource to understand structure
   - Then GET /resource for actual data

2. **Opportunistic agents**:
   - Try HEAD first
   - Fall back to GET if discovery not needed
   - Use metadata for optimization

3. **Optimization-focused agents**:
   - Always HEAD first to validate assumptions
   - Cache schema for future requests
   - Minimize network traffic

## Security Implications

### Authentication

Both methods require authentication:
```python
@orders_bp.route('/orders', methods=['GET', 'HEAD'])
@require_auth
def orders_handler():
    ...
```

### Authorization

Both methods apply same RBAC:
```python
role = extract_jwt_context(request)  # Both GET and HEAD
schema = generate_schema(role=role)  # Role-filtered
data = query_data(role=role)         # Both methods
```

## References

- **Commits**: 0f3e83e (HEAD discovery implementation), ef569e4 (GET data endpoints)
- **Code**:
  - `leaf_api/resources/` — GET/HEAD handlers for all resources
  - `leaf_api/schemas/` — Shared schema generation
  - `tests/test_endpoints.py` — GET tests
  - `tests/test_discovery.py` — HEAD tests
- **HTTP RFCs**:
  - [RFC 7231 - HEAD method](https://tools.ietf.org/html/rfc7231#section-4.3.2)
  - [RFC 7232 - Conditional requests](https://tools.ietf.org/html/rfc7232)
- **Related ADRs**:
  - [ADR-002](002-hateoas-head-request-protocol.md) — HEAD protocol definition
  - [ADR-004](004-etag-based-caching.md) — ETag caching for HEAD responses

## Precedent in Web Standards

This pattern isn't entirely novel:

- **Search engines**: Use HEAD requests to validate URLs before crawling
- **API gateways**: Issue HEAD requests for schema validation
- **CDNs**: Use HEAD to check freshness without body
- **Link checkers**: HEAD verifies URLs exist without full transfer

The difference here is intentional body inclusion for schema discovery.

## Future Enhancements

1. **OPTIONS method**: Could return available methods and parameters
2. **PATCH support**: For partial updates (future operation)
3. **Query parameter filtering**: HEAD ?role=admin for different view
4. **Stream support**: Large datasets via streaming GET
5. **WebSocket upgrade**: For real-time discovery updates
