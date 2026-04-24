# Agentics-HATEOAS System Design

## Context

This project defines a standard for crafting LLM-discoverable APIs by leveraging content negotiation when a user agent identifies itself as `LLM/*`. The system uses HEAD requests at the API root to trigger discovery, returning response bodies (non-standard) with resource descriptions, JSON schemas, and HATEOAS links. Conformance is advertised via `.well-known/agentics-robots.txt`.

The two-part architecture includes:
1. **Leaf API** (Flask-based Orders API) - serves resources with HEAD request support, role-based schema filtering via JWT, ETag caching, and API surface discovery
2. **Root Application** - recursively crawls child APIs, caches representations using ETags, responds to agent HEAD requests with skill content (markdown), maintains fresh API surface map

## Implementation Architecture

### Directory Structure

```
agentics-hateoas/
├── README.md
├── requirements.txt
├── docker-compose.yml
│
├── leaf-api/                          # Example Orders API (Flask)
│   ├── __init__.py
│   ├── app.py                         # Flask application entry point
│   ├── config.py                      # Configuration (JWT secrets, DB URL)
│   ├── wsgi.py                        # WSGI entry point for production
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── jwt_handler.py             # JWT validation & decoding
│   │   ├── roles.py                   # Role definitions & permissions
│   │   └── keypair.pem               # Demo RSA private key
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py                # SQLAlchemy setup, session management
│   │   ├── order.py                   # Order model
│   │   ├── customer.py                # Customer model
│   │   └── product.py                 # Product model
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── base_schema.py             # Base JSON schema builder
│   │   ├── order_schema.py            # Order resource schema
│   │   ├── customer_schema.py         # Customer resource schema
│   │   └── product_schema.py          # Product resource schema
│   │
│   ├── resources/
│   │   ├── __init__.py
│   │   ├── orders.py                  # Orders resource endpoints
│   │   ├── customers.py               # Customers resource endpoints
│   │   ├── products.py                # Products resource endpoints
│   │   └── root.py                    # Root endpoint & discovery
│   │
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── discovery.py               # HEAD request handler & discovery logic
│   │   ├── cache.py                   # ETag & cache header management
│   │   └── jwt_middleware.py          # JWT extraction & validation middleware
│   │
│   ├── migrations/
│   │   └── (alembic migration files)
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_jwt_auth.py
│       ├── test_head_requests.py
│       └── test_schema_generation.py
│
├── root-app/                          # Root Application (Crawler & Skill Server)
│   ├── __init__.py
│   ├── app.py                         # Root application entry point
│   ├── config.py                      # Configuration (child API URLs, cache dirs)
│   ├── wsgi.py                        # WSGI entry point
│   │
│   ├── crawler/
│   │   ├── __init__.py
│   │   ├── api_crawler.py             # Recursive API discovery engine
│   │   ├── cache_manager.py           # ETag-based caching strategy
│   │   ├── graph_builder.py           # Builds API surface graph
│   │   └── client.py                  # HTTP client for HEAD requests
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── skill_builder.py           # Converts API graph to skill markdown
│   │   ├── intention_parser.py        # Parses Accept-Intention headers
│   │   └── response_formatter.py      # Formats response bodies for HEAD
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── graph_store.py             # Stores API surface graph
│   │   └── cache_store.py             # Persistent cache for ETags
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── discovery.py               # HEAD request handlers
│   │   └── health.py                  # Health check endpoints
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_crawler.py
│       └── test_skill_generation.py
│
├── shared/                            # Shared utilities
│   ├── __init__.py
│   ├── well_known.py                  # .well-known/agentics-robots.txt generation
│   ├── constants.py                   # Shared constants
│   └── utils.py                       # Utility functions
│
└── docs/
    ├── ARCHITECTURE.md                # Architecture documentation
    ├── API_PROTOCOL.md                # HEAD request protocol spec
    └── IMPLEMENTATION_GUIDE.md        # Step-by-step implementation
```

## Key Components

### Leaf API (Flask Orders API)

**JWT & Authentication** (`leaf-api/auth/jwt_handler.py`)
- Validates RS256 JWT signatures
- Extracts user role from claims
- Provides user context (role, permissions)

**Models** (`leaf-api/models/`)
- Order, Customer, Product SQLAlchemy models
- Database session management via SQLAlchemy

**Schema Generation** (`leaf-api/schemas/`)
- JSONSchemaBuilder: base class for schema construction
- Role-based field filtering (admin sees cost/margin, user sees limited fields, public sees minimal)
- Query parameter processing (e.g., `?positive_only=true` constrains numeric fields)

**Discovery Handler** (`leaf-api/middleware/discovery.py`)
- HEAD request handler returning resource descriptions + JSON schemas + children list
- Response includes `_links` with HATEOAS children references
- Response includes `_meta` with user role and permissions

**Cache Management** (`leaf-api/middleware/cache.py`)
- ETag generation (MD5 hash of content)
- Cache-Control header setting
- If-None-Match conditional request support

**Endpoints** (`leaf-api/resources/`)
- HEAD handlers for collections and individual resources
- GET handlers for resource retrieval
- `.well-known/agentics-robots.txt` endpoint advertising conformance

### Root Application (Crawler & Agent Interface)

**API Crawler** (`root-app/crawler/api_crawler.py`)
- Recursive depth-first traversal with cycle detection
- Issues HEAD requests to discover API surface
- Extracts children from `_links.children` in HEAD responses
- Uses JWT token for authenticated discovery

**Cache Manager** (`root-app/crawler/cache_manager.py`)
- Persistent ETag storage
- Conditional request support (If-None-Match)
- Cache expiry based on Cache-Control headers
- Delta updates when ETags change

**API Graph** (`root-app/crawler/graph_builder.py`)
- In-memory representation of API surface
- Nodes: path → resource metadata (description, schema, etag)
- Edges: parent → [children]
- Graph queries for traversal

**Skill Builder** (`root-app/agent/skill_builder.py`)
- Converts API graph to markdown format for LLM agents
- Includes endpoint descriptions, parameters, return types
- Optional intention-based filtering

**Intention Parser** (`root-app/agent/intention_parser.py`)
- Parses Accept-Intention headers (action, resource, details level)
- Filters graph by intention to return relevant resources only

**Agent Routes** (`root-app/routes/discovery.py`)
- Universal HEAD handler for `/<path:path>`
- Checks cache, issues fresh HEAD if needed
- Returns skill markdown in response body with ETag

## Request/Response Flows

### Discovery Flow (Agent → Root App → Leaf API)

```
Agent: HEAD /orders
       User-Agent: LLM/claude
       Accept-Intention: action=list, resource=order

Root App checks cache. If stale:
  → HEAD leaf-api:/orders
     Authorization: Bearer <jwt>
     If-None-Match: <cached_etag>

Leaf API returns:
  Status: 200
  ETag: "abc123"
  Cache-Control: max-age=3600
  Body:
    {
      "description": "Orders collection",
      "schema": {...},
      "_links": {
        "children": ["/orders/1", "/orders/2"]
      },
      "_meta": {
        "role": "user",
        "permissions": ["read"]
      }
    }

Root App extracts skill markdown, caches response, returns to agent
```

### Role-Based Schema Modification

```
GET /orders with JWT (role: admin)
→ Schema includes: id, customer_id, quantity, status, total_price, cost, margin

GET /orders with JWT (role: user)
→ Schema includes: id, customer_id, quantity, status, total_price

GET /orders (no JWT)
→ Schema includes: id, status (public only)
```

### Query Parameter Schema Transformation

```
HEAD /orders?positive_only=true
→ quantity: { "type": "integer", "minimum": 1 }
→ total_price: { "type": "number", "minimum": 0 }
```

## Implementation Phases

### Phase 1: Leaf API Foundation
- Flask app structure with config management
- SQLAlchemy models for Order, Customer, Product
- JWT validation middleware
- Docker Compose setup with PostgreSQL

### Phase 2: Discovery Protocol (Leaf API)
- JSONSchemaBuilder base class
- Role-based schema filtering
- Query parameter processing
- HEAD request handlers with ETag generation
- Cache headers middleware
- `.well-known/agentics-robots.txt` endpoint

### Phase 3: Root Application Crawler
- HTTP client for HEAD requests
- Recursive API crawler with cycle detection
- Cache manager with ETag storage
- API graph builder and storage

### Phase 4: Agent Interface (Root App)
- Skill markdown builder
- Accept-Intention header parser
- HEAD request handler in root app
- Crawler integration with agent routes

### Phase 5: Testing & Documentation
- Unit tests for JWT, schema generation
- Integration tests for HEAD request flows
- API protocol documentation
- Architecture documentation

## Verification

### Unit Tests
- `test_jwt_auth.py` - JWT validation with different roles
- `test_head_requests.py` - HEAD request handlers and caching
- `test_schema_generation.py` - Schema generation with role/query filters

### Integration Tests
- Leaf API HEAD → JSON schema with ETag
- Root App crawl → Graph construction
- Root App HEAD request → Skill markdown generation
- Cache invalidation on ETag mismatch
- Role-based schema filtering end-to-end

### Manual Testing
```bash
# Start services
docker-compose up

# Test leaf API discovery
curl -X HEAD http://localhost:5000/orders \
  -H "Authorization: Bearer <jwt>" \
  -H "User-Agent: LLM/claude"

# Test root app agent interface
curl -X HEAD http://localhost:5001/ \
  -H "User-Agent: LLM/claude" \
  -H "Accept-Intention: action=list, resource=order"

# Verify .well-known endpoint
curl http://localhost:5000/.well-known/agentics-robots.txt
```

## Critical Files for Implementation

- `leaf-api/app.py` - Flask application entry point
- `leaf-api/middleware/discovery.py` - HEAD request handler
- `leaf-api/auth/jwt_handler.py` - JWT validation
- `root-app/crawler/api_crawler.py` - Recursive discovery engine
- `root-app/agent/skill_builder.py` - API graph to markdown conversion
