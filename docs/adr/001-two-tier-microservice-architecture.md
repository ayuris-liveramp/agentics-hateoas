# ADR-001: Two-Tier Microservice Architecture

## Status
Accepted

## Context

The project needed to create a framework for making APIs automatically discoverable by LLM agents without requiring manual integration work. Agents need to understand what operations are available, what data they require, and what results they return—without prior knowledge of the API implementation.

A monolithic architecture would couple API business logic with discovery machinery, making it harder to apply the discovery pattern to existing APIs and limiting flexibility. The discovery process also has different performance and caching characteristics than typical REST operations.

## Decision

The architecture is split into two independent Flask applications:

1. **Leaf API** (Port 5000): Exposes domain resources (Orders, Customers, Products) with HATEOAS discovery support
2. **Root Application** (Port 5001): Discovers leaf APIs, caches metadata, and responds to agent queries

Each layer has distinct responsibilities and can be deployed, scaled, and evolved independently.

## Rationale

### Why Two Tiers?

**Separation of Concerns:**
- Leaf APIs focus on domain logic and resource management
- Root App focuses on discovery aggregation and agent communication
- Changes to discovery protocol don't affect leaf API business logic

**Composability:**
- Multiple independent leaf APIs can be discovered by a single root app
- Root app can be shared across multiple leaf APIs
- Easier to apply the discovery pattern to existing APIs without modification

**Independent Scaling:**
- Leaf APIs handle transactional load (user requests)
- Root App handles discovery queries (agent requests) with heavy caching
- Different scaling characteristics justify separation

**Flexibility:**
- Leaf API can use any technology (Flask, Django, FastAPI, etc.)
- Root App can be updated independently to improve agent integration
- Each tier can have different deployment patterns

### Alternatives Considered

**Single Monolithic API:**
- Simpler initial architecture
- Harder to apply pattern to existing APIs
- Discovery machinery bloats leaf API code
- Difficult to optimize caching separately from business logic

**Event-Driven Discovery (third tier):**
- Leaf APIs emit events when schema changes
- Separate event processor aggregates discoveries
- Overly complex for current requirements
- Added operational burden

## Consequences

### Positive
- ✅ Leaf APIs remain clean and focused on domain logic
- ✅ Discovery can be optimized independently (caching, performance)
- ✅ Pattern can be applied to multiple existing APIs
- ✅ Clear network boundary for auth/security (root app validates JWT to leaf)
- ✅ Easier to test each tier independently

### Negative
- ❌ Increased operational complexity: two services to deploy, monitor, manage
- ❌ Network latency between root and leaf during crawling
- ❌ Consistency: root app cache may lag behind leaf API changes
- ❌ Additional failure modes: root app failure isolates all agents from APIs
- ❌ Requires coordinated deployment for schema changes

## Implementation Details

**Leaf API (Port 5000):**
- Flask application with PostgreSQL database
- REST endpoints for Orders, Customers, Products (GET)
- Discovery endpoints that return schemas (HEAD)
- JWT authentication with role-based filtering
- ETag generation for cache validation

**Root Application (Port 5001):**
- Flask application with no database
- `APICrawler` recursively discovers child API surfaces
- `APIGraph` maintains in-memory discovery cache
- `SkillBuilder` converts graph to agent-friendly markdown
- Routes for agent queries via HEAD requests

**Communication:**
- Root app → Leaf API: HEAD requests with JWT bearer token
- Agent → Root app: HEAD requests with Accept-Intention headers
- All communication via standard HTTP

## Alternatives Considered

| Approach | Pros | Cons | Why Not |
|----------|------|------|---------|
| **Two-Tier (Chosen)** | Clean separation, composable | Operational complexity | Selected |
| Monolithic | Simpler deployment | Harder to extend, optimizations limited | Complexity increase not worth simplicity |
| Three-Tier (events) | Full decoupling | Over-engineered for needs | Premature complexity |
| Embedded discovery | No separate service | Can't be applied to existing APIs | Limits applicability |

## References

- **Commits**: ef569e4 (Leaf API foundation), 7b06d3a (Root App crawler)
- **Architecture**: [ARCHITECTURE.md](../ARCHITECTURE.md#system-overview)
- **Related ADRs**: 
  - [ADR-002](002-hateoas-head-request-protocol.md) — Protocol that enables discovery
  - [ADR-004](004-etag-based-caching.md) — Caching strategy for root app
- **Code Files**:
  - `leaf_api/` — Domain logic and resource endpoints
  - `root_app/` — Discovery aggregation and agent interface
  - `docker-compose.yml` — Deployment configuration

## Decision History

- **Proposed**: Phase 1 (Leaf API foundation)
- **Confirmed**: Phase 3 (Root App crawler implementation)
- **Status**: Stable, no changes since implementation
