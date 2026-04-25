# ADR-005: Role-Based Schema Filtering via JWT Claims

## Status
Accepted

## Context

The Leaf API exposes resources (Orders, Customers, Products) that contain fields with different sensitivity levels:

- **Internal/Cost data**: `cost`, `profit_margin` — visible only to admin/staff
- **Business data**: `total_price`, `customer_id`, `quantity` — visible to authorized users
- **Public data**: `id`, `status` — visible to all

Without access control, any agent seeing the API would discover all fields, potentially accessing sensitive information. However, simply blocking endpoints is too coarse—we need **field-level visibility** based on user permissions.

Traditional approaches require checking permissions at query time for each record. However, in the discovery protocol, schemas are static structures (not individual records). We can apply permissions at the schema level instead.

## Decision

Apply Role-Based Access Control (RBAC) at the schema generation level using JWT role claims:

1. **Extract role** from JWT token (`role` claim)
2. **Generate role-specific schema** with only visible fields
3. **Return filtered schema** in HEAD response
4. **Agent sees only what it's authorized for**

Three predefined roles:

| Role | Fields Visible | Use Case |
|------|---|---|
| **admin** | All (id, customer_id, quantity, status, total_price, cost, created_at, updated_at) | Internal operations, cost analysis |
| **user** | Business data (id, customer_id, quantity, status, total_price, created_at) | Standard API users, applications |
| **public** | Minimal (id, status) | Anonymous access, search results |

## Rationale

### Why Schema-Level RBAC?

**Efficiency:**
- Schema is static (not per-record) → permission check happens once per HEAD request
- No database queries needed to determine visibility
- Caching applies across all similar requests

**Simplicity:**
- Single schema generator with role parameter
- Declarative field visibility (which fields in which roles)
- No complex query-time filtering

**Scalability:**
- Scales to any number of agents/users
- No per-record overhead
- Leverages HTTP caching (304 responses identical for same role)

**Security by Design:**
- Can't accidentally expose fields if they're not in schema
- Schema acts as contract: "these are the only fields available"
- Agents can't request unknown fields (validation fails)

### Alternatives Considered

| Approach | Efficiency | Complexity | Per-Record? |
|----------|-----------|-----------|---------|
| **Schema-level RBAC (Chosen)** | High | Low | No |
| Query-level filtering | Medium | High | Yes |
| Endpoint-level access | Low | Low | No |
| Separate role-specific endpoints | Low | Medium | No |
| No access control | N/A | N/A | N/A |

Schema-level RBAC balances all concerns: it's efficient (single schema generation), simple to implement (declarative rules), and effective (prevents visibility of unauthorized fields).

## Consequences

### Positive
- ✅ Field-level visibility without per-record overhead
- ✅ Schema acts as contract: guarantees what's available
- ✅ Cacheable: same role always gets same schema
- ✅ Simple to implement: declarative field lists
- ✅ Composable: role can be extracted from any JWT claim
- ✅ Transparent to agents: discovered schema is the actual available data
- ✅ Audit trail: role claim is logged (who requested what)

### Negative
- ❌ Coarse-grained: can't hide individual records (field-level only)
- ❌ Static: can't dynamically change visibility per request
- ❌ JWT required: public access needs "public" role token
- ❌ Schema duplication: three versions of each schema (admin/user/public)
- ❌ Role proliferation: adding new roles requires schema variants

## Implementation

### Role Definitions

**Enum** (`shared/constants.py`):
```python
class Role(str, Enum):
    ADMIN = "admin"      # Cost data, timestamps, all fields
    USER = "user"        # Business data, application-visible
    PUBLIC = "public"    # Minimal, anonymous access
```

### Field Visibility

**Declarative** (`leaf_api/schemas/field_visibility.py`):
```python
FIELD_VISIBILITY = {
    "Order": {
        "admin": ["id", "customer_id", "quantity", "status", "total_price", "cost", "created_at", "updated_at"],
        "user": ["id", "customer_id", "quantity", "status", "total_price", "created_at"],
        "public": ["id", "status"]
    },
    "Customer": {
        "admin": ["id", "name", "email", "phone", "status", "created_at", "updated_at"],
        "user": ["id", "name", "status", "created_at"],
        "public": ["id", "status"]
    }
    # ... more models
}
```

### Schema Generation

**With Role Parameter** (`leaf_api/schemas/schema_builder.py`):
```python
class JSONSchemaBuilder:
    def build(self, model: type, role: Role = Role.PUBLIC) -> dict:
        schema = model.model_json_schema()
        visible_fields = FIELD_VISIBILITY.get(model.__name__, {}).get(role.value, [])
        
        # Filter properties to visible fields only
        filtered_schema = {
            **schema,
            "properties": {
                k: v for k, v in schema.get("properties", {}).items()
                if k in visible_fields
            },
            "required": [f for f in schema.get("required", []) if f in visible_fields]
        }
        return filtered_schema
```

### JWT Role Extraction

**Middleware** (`leaf_api/middleware/jwt_handler.py`):
```python
def extract_jwt_context(request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return Role.PUBLIC  # Default to public
    
    token = auth_header[7:]  # Remove 'Bearer '
    try:
        payload = jwt.decode(token, key, algorithms=['EdDSA'])
        role = payload.get('role', 'public')
        return Role(role)
    except jwt.InvalidSignatureError:
        return Role.PUBLIC  # Invalid token, default to public
```

### HEAD Response with Role Filtering

**Resource Handler** (`leaf_api/resources/orders.py`):
```python
@orders_bp.head('/orders')
def head_orders():
    # Extract role from JWT (or default to public)
    role = extract_jwt_context(request)
    
    # Generate schema for this role
    schema = JSONSchemaBuilder().build(Order, role=role)
    
    # Generate ETag from role-specific schema
    etag = generate_etag(schema)
    
    return jsonify(schema), 200, {'ETag': f'"{etag}"'}
```

### Example: Admin vs Public View

**Admin request** (with valid JWT claiming `role: admin`):
```json
{
  "properties": {
    "id": {"type": "integer"},
    "customer_id": {"type": "integer"},
    "quantity": {"type": "integer", "minimum": 0},
    "status": {"type": "string"},
    "total_price": {"type": "number"},
    "cost": {"type": "number"},           // ← Visible to admin only
    "created_at": {"type": "string"},     // ← Visible to admin only
    "updated_at": {"type": "string"}      // ← Visible to admin only
  }
}
```

**Public request** (no JWT, or JWT with `role: public`):
```json
{
  "properties": {
    "id": {"type": "integer"},
    "status": {"type": "string"}
  }
}
```

## Caching Implications

**ETag differs per role:**
```
HEAD /orders (JWT role=admin)
← ETag: "admin-abc123"
← 200 OK with full schema

HEAD /orders (JWT role=public)
← ETag: "public-def456"
← 200 OK with minimal schema
```

**Root App caching** (`root_app/crawler/`):
- Caches separately per role
- `cache["admin:/orders"]` stores admin view
- `cache["public:/orders"]` stores public view
- 304 responses cached per role

## Security Properties

### What This Provides
- ✅ Field-level visibility based on role
- ✅ Schema prevents unauthorized field requests
- ✅ JWT validation required for privileged roles

### What This Doesn't Provide
- ❌ Record-level filtering (can't hide specific orders, only field types)
- ❌ Query parameter filtering (can't request `?status=shipped` without schema field)
- ❌ Endpoint-level access control (doesn't prevent GET if JWT invalid)

### Security Best Practices

1. **Always validate JWT** before returning filtered schema
2. **Use HTTPS** to prevent JWT interception
3. **Rotate keys** regularly for token signing
4. **Log role claims** for audit trails
5. **Test schema filtering** to ensure no leaks

## Role Extension Strategy

To add a new role (e.g., `accountant`):

1. Add to `Role` enum
2. Add field visibility mapping in `FIELD_VISIBILITY`
3. Update JWT token generator
4. No code changes needed (schema builder is generic)

## References

- **Commits**: ef569e4 (JWT auth), 0f3e83e (Role-based schemas)
- **Code**:
  - `leaf_api/schemas/field_visibility.py` — Visibility rules
  - `leaf_api/schemas/schema_builder.py` — Schema generation
  - `leaf_api/middleware/jwt_handler.py` — Role extraction
  - `leaf_api/resources/` — HEAD handlers applying roles
  - `shared/constants.py` — Role definitions
- **Related ADRs**:
  - [ADR-006](006-ed25519-jwt-authentication.md) — JWT implementation details
  - [ADR-002](002-hateoas-head-request-protocol.md) — HEAD protocol carrying filtered schemas
  - [ADR-004](004-etag-based-caching.md) — Per-role ETag caching

## Testing Strategy

**Unit Tests** (`tests/test_schema_visibility.py`):
- Admin role sees all fields
- User role sees business data
- Public role sees minimal fields
- Invalid JWT defaults to public

**Integration Tests** (`tests/test_discovery.py`):
- HEAD requests with different JWT tokens return different schemas
- ETag differs per role
- 304 responses cached correctly per role

## Future Enhancements

1. **Fine-grained roles**: Expand from 3 roles to domain-specific roles
2. **Attribute-based access control**: ABAC with more complex rules
3. **Per-request role overrides**: Query parameter to request different view
4. **Audit logging**: Track who requested which schemas
5. **Role inheritance**: User role inherits from public, admin from user
