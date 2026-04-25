# NOTICE

Until this header is removed, no human has verified the contents of this repository. I generated it using Haiku on low effort while waiting at the airport, and haven't reveiwed it yet.

---

# Agentics-HATEOAS

**Version: v0.0.1** (Pre-release)

A standard for crafting LLM-discoverable APIs by leveraging content negotiation and HEAD requests. This project demonstrates how to build APIs that expose their surface through hypermedia (HATEOAS) while supporting LLM agents as first-class clients.

## Overview

This repository contains a two-part architecture:

1. **Leaf API** - Example Orders API demonstrating Agentics-HATEOAS
   - Flask-based REST API with PostgreSQL backend
   - JWT-authenticated HEAD requests for API discovery
   - Role-based schema filtering (admin, user, public)
   - ETag caching for efficient crawling
   - Returns JSON schemas and HATEOAS links in HEAD responses

2. **Root Application** - API Crawler & Agent Interface
   - Recursively discovers and indexes child APIs
   - Maintains cached API surface map using ETags
   - Responds to agent HEAD requests with skill descriptions
   - Parses `Accept-Intention` headers for intent-based filtering

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)

### Running with Docker Compose

```bash
# Start all services
make

# In another terminal, test the leaf API
curl http://localhost:5000/
curl http://localhost:5000/.well-known/agentics-robots.txt

# Test the root app
curl http://localhost:5001/health
```

### Local Development Setup

```bash
# Create virtual environment
make .venv
source venv/bin/activate

# Start leaf API
FLASK_APP=leaf_api.app:create_app flask run

# In another terminal, start root app
FLASK_APP=root_app.app:create_app flask run --port 5001
```

## Architecture

### Leaf API

**Endpoints:**
- `GET /` - Root endpoint listing available resources
- `GET /.well-known/agentics-robots.txt` - Conformance declaration
- `HEAD /orders`, `GET /orders` - Order collection
- `HEAD /orders/{id}`, `GET /orders/{id}` - Order detail
- `HEAD /customers`, `GET /customers` - Customer collection
- `HEAD /customers/{id}`, `GET /customers/{id}` - Customer detail
- `HEAD /products`, `GET /products` - Product collection
- `HEAD /products/{id}`, `GET /products/{id}` - Product detail

**JWT Authentication:**
- RS256 RSA key pair at `leaf_api/auth/keypair.pem` and `public_key.pem`
- Token claims: `sub` (user ID), `role` (admin/user/public), `iat`, `exp`
- Role-based field visibility for schemas

**Example JWT Token:**
```sh
make leaf_api/auth/token.b64

# this is equivalent to the above command
make leaf_api/auth/token.admin.b64

# you can make other roles too
make leaf_api/auth/token.user.b64
make leaf_api/auth/token.public.b64
```

**Use in request**
```sh
curl -H "Authorization: Bearer <(leaf_api/auth/token.b64)" http://localhost:5000/orders
```

### Root Application

**Endpoints:**
- `GET /health` - Health check
- `HEAD /*` - Universal discovery endpoint for agents
- `HEAD /.well-known/agentics-robots.txt` - Conformance declaration

**Headers:**
- `User-Agent: LLM/*` - Identifies LLM agent
- `Accept-Intention: action=list, resource=order` - Intent-based filtering
- `If-None-Match: "<etag>"` - Conditional requests for caching

## API Discovery Flow

```
LLM Agent
  ↓
HEAD /orders (User-Agent: LLM/claude)
  ↓
Root App (checks cache)
  ↓ (if stale)
HEAD leaf-api:/orders (with JWT)
  ↓
Leaf API returns:
{
  "description": "Orders collection",
  "schema": { JSON Schema },
  "_links": {
    "children": ["/orders/1", "/orders/2"]
  },
  "_meta": {
    "role": "user",
    "permissions": ["read"]
  }
}
  ↓
Root App caches + extracts skill markdown
  ↓
Agent receives skill description in HEAD response body
```

## Testing

### Functional Tests (v0.0.0 - v0.x.x)

Run the complete functional test suite:

```bash
# Start services, then run tests in isolated container
make test
```

Functional tests validate end-to-end behavior and the top-level interface. Until v1.0.0, the project focuses exclusively on functional testing to ensure API correctness without over-specifying implementation details.

### Unit Tests (individual modules)

```bash
# Run leaf API tests
pytest leaf_api/tests/

# Run root app tests
pytest root_app/tests/

# Run all tests with coverage
pytest --cov=leaf_api --cov=root_app
```

**Note:** Until v1.0.0, unit tests are limited to simple objects and transformations. Pass-through logic is excluded. At v1.0.0, the API will be locked and exhaustive unit testing will begin for backwards-compatibility assurance.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Detailed system design
- [API Protocol](docs/API_PROTOCOL.md) - HEAD request protocol specification
- [Implementation Guide](docs/IMPLEMENTATION_GUIDE.md) - Step-by-step development guide

## References

- [Agentics.org](https://agentics.org/) - Agentics specification
- [HATEOAS](https://en.wikipedia.org/wiki/HATEOAS) - Hypermedia As The Engine Of Application State
- [JSON Schema](https://json-schema.org/) - JSON Schema specification
- [JWT](https://jwt.io/) - JSON Web Tokens

## License

MIT License - See LICENSE.md
