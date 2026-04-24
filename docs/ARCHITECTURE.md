# Agentics-HATEOAS Architecture

## System Overview

Agentics-HATEOAS is a two-tier system for building LLM-discoverable APIs using hypermedia and content negotiation.

```
┌─────────────────────────────────────────────────────────┐
│              LLM Agent (Claude, GPT-4, etc)              │
└─────────────────────────────────────────────────────────┘
                           │
                      HEAD Request
                   (Accept-Intention header)
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│              Root Application (Port 5001)                │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Discovery Routes (HEAD /<path>)                    │  │
│  │ - Parse Accept-Intention header                    │  │
│  │ - Query cached API graph                           │  │
│  │ - Return skill markdown with ETag                  │  │
│  │ - Support 304 Not Modified responses               │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │ API Crawler                                        │  │
│  │ - Recursive discovery with cycle detection         │  │
│  │ - HEAD requests to leaf APIs                       │  │
│  │ - ETag-based cache management                      │  │
│  │ - API surface graph building & persistence         │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                           │
         HEAD Requests (discover schemas)
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│            Leaf API (Port 5000)                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Discovery Handlers (HEAD /orders, /customers, etc) │  │
│  │ - Return JSON schema                               │  │
│  │ - Include HATEOAS links (_links.children)          │  │
│  │ - Apply role-based filtering                       │  │
│  │ - Generate ETags                                   │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Resource Endpoints (GET /orders, /customers, etc)  │  │
│  │ - Serve actual resource data                       │  │
│  │ - JWT authentication & role extraction             │  │
│  │ - Query parameter processing                       │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Models & Database (PostgreSQL)                     │  │
│  │ - Orders, Customers, Products                      │  │
│  │ - Relationships & timestamps                       │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Leaf API (Flask)

**Purpose:** Expose resources with HATEOAS discovery support

**Key Components:**

- **Models** (`models/`): SQLAlchemy ORM models for Order, Customer, Product
- **Schemas** (`schemas/`): JSONSchemaBuilder and resource-specific generators
- **Resources** (`resources/`): REST endpoints with GET for data, HEAD for discovery
- **Authentication** (`auth/`): JWT RS256 validation with role-based context
- **Middleware** (`middleware/`): Discovery handlers, cache managers, JWT extraction

**Discovery Protocol:**
```
HEAD /orders
├── Returns: JSON schema, description, HATEOAS links
├── Headers: ETag, Cache-Control, Content-Type
├── Body: {"description": "...", "schema": {...}, "_links": {"children": [...]}}
└── Supports: If-None-Match for 304 responses
```

### 2. Root Application (Flask)

**Purpose:** Discover APIs and respond to agent queries

**Key Components:**

- **Crawler** (`crawler/`): 
  - APIClient: HTTP HEAD requests with LLM user agent
  - APICrawler: Recursive discovery with cycle detection
  - CacheManager: ETag-based persistent caching
  - APIGraph: In-memory API surface representation

- **Agent Interface** (`agent/`):
  - IntentionParser: Parse Accept-Intention headers for filtering
  - SkillBuilder: Convert API graphs to markdown descriptions
  - ResponseFormatter: Format responses for agents

- **Routes** (`routes/`):
  - Discovery routes: HEAD handler for agent queries
  - Health check: Service status endpoint

- **Storage** (`storage/`):
  - GraphStore: Persist and restore API graphs

**Discovery Flow:**

```
1. Agent: HEAD / with User-Agent: LLM/* and Accept-Intention: action=read,resource=order
2. Root App:
   a. Check cache for "/" resource
   b. If stale: issue HEAD / to leaf API
   c. Parse response, extract schema and children
   d. Store in graph, cache with ETag
3. Return: Markdown skill description in response body with ETag header
4. Agent: Follows HATEOAS links for related resources
5. Root App: Caches all discovered resources using ETags
```

## Data Flow

### User Agent → Root App → Leaf API

```
┌─────────────┐
│  LLM Agent  │
└──────┬──────┘
       │ HEAD /orders
       │ User-Agent: LLM/claude
       │ Accept-Intention: action=list, resource=order
       ▼
┌────────────────────────────────────────┐
│       Root App Discovery Routes        │
│                                        │
│ 1. Parse Accept-Intention header       │
│ 2. Query API graph from cache          │
│ 3. Generate skill markdown             │
│ 4. Return with ETag header             │
└────┬─────────────────────────────────┘
     │ (if cache stale)
     │ HEAD /orders
     │ Authorization: Bearer <jwt>
     │ If-None-Match: <cached_etag>
     ▼
┌────────────────────────────────────────┐
│      Leaf API Discovery Handler        │
│                                        │
│ 1. Validate JWT, extract role          │
│ 2. Generate schema (role-filtered)     │
│ 3. Get children: [/orders/1, .../2]   │
│ 4. Build discovery response            │
│ 5. Generate ETag                       │
│ 6. Return with Cache-Control           │
└────────────────────────────────────────┘
     │ Response:
     │ {
     │   "description": "Orders collection",
     │   "schema": {...},
     │   "_links": {"children": [...]},
     │   "_meta": {"role": "user", ...}
     │ }
     ▼
```

### Role-Based Schema Filtering

**Admin** sees all fields:
```json
{
  "properties": {
    "id", "customer_id", "quantity", "status", 
    "total_price", "cost", "created_at", "updated_at"
  }
}
```

**User** sees business data:
```json
{
  "properties": {
    "id", "customer_id", "quantity", "status", 
    "total_price", "created_at"
  }
}
```

**Public** sees minimal info:
```json
{
  "properties": {
    "id", "status"
  }
}
```

### Query Parameter Processing

**Positive Only**: `HEAD /orders?positive_only=true`
- Constrains numeric fields: `"minimum": 0`

**Detailed**: `HEAD /orders?detailed=true`
- Adds timestamp fields if missing
- Includes extended properties

**Summary**: `HEAD /orders?summary=true`
- Returns only required fields
- Minimal schema representation

## Caching Strategy

### ETag-Based Invalidation

**Leaf API (Producer):**
1. Generate ETag for every HEAD response (MD5 hash of JSON)
2. Set Cache-Control headers
3. Support If-None-Match conditional requests

**Root App (Consumer):**
1. Cache HEAD responses with ETag
2. Check If-None-Match on re-crawl
3. Use cached content if ETag unchanged
4. Re-parse and store if ETag changed
5. Return 304 Not Modified to agents if content unchanged

**TTL Management:**
- Default TTL: 3600 seconds
- Configurable per API
- Metadata stored with timestamp

## Graph Data Structure

```
APIGraph {
  nodes: {
    "/": {
      path: "/",
      description: "Root API endpoint",
      schema: {...},
      etag: "root-etag-123",
      children_count: 2
    },
    "/orders": {
      path: "/orders",
      description: "Orders collection",
      schema: {...},
      etag: "orders-etag-456",
      children_count: 50
    },
    ...
  },
  edges: {
    "/": ["/orders", "/customers", "/products"],
    "/orders": ["/orders/1", "/orders/2", ...],
    ...
  },
  root_apis: [
    {
      url: "http://localhost:5000",
      title: "Orders API",
      version: "1.0.0"
    }
  ]
}
```

## Security

### JWT Authentication

- **Algorithm:** RS256 (RSA asymmetric)
- **Claims:** `sub` (user ID), `role` (permission level), `iat`, `exp`
- **Key Management:** Demo uses local keypair in `leaf_api/auth/`
- **Role-Based Access:** Schema filtering based on JWT role claim

### Authorization

- **Leaf API:** Validates JWT, extracts role for schema filtering
- **Root App:** Passes JWT to leaf API when crawling private APIs
- **Public Access:** No JWT required, defaults to "public" role

## Deployment

### Docker Compose

```yaml
services:
  postgres: PostgreSQL database
  leaf-api: Flask orders API (port 5000)
  root-app: Flask root application (port 5001)
```

### Environment Variables

```
DATABASE_URL=postgresql://user:pass@postgres:5432/db
JWT_SECRET_KEY=<demo-secret-key>
CHILD_API_URLS=http://leaf-api:5000
CACHE_DIR=/app/cache
```

## Testing

### Unit Tests (35+ passing)
- Leaf API: JWT validation, schema generation, endpoints
- Root App: Cache manager, graph operations, crawler logic
- Agent Interface: Intention parsing, skill building, formatting

### Integration Points
- Leaf API HEAD endpoints return discovery responses
- Root App crawler discovers and caches API surface
- Agent interface converts graphs to skill markdown
- ETag-based caching ensures efficiency

## Future Enhancements

1. **Multi-API Orchestration:** Coordinate across multiple leaf APIs
2. **Dynamic Schema Evolution:** Track schema changes over time
3. **Agent Context Preservation:** Pass context across requests
4. **Recursive Skill Composition:** Combine skills from multiple APIs
5. **Real-time Notifications:** Invalidate cache on API changes
6. **Analytics & Monitoring:** Track agent queries and patterns
