# NOTICE

Until this header is removed, no human has verified the contents of this repository. I generated it using Haiku on low effort while waiting at the airport, and haven't reveiwed it yet.

---

# Agentics-HATEOAS

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
docker-compose up

# In another terminal, test the leaf API
curl http://localhost:5000/
curl http://localhost:5000/.well-known/agentics-robots.txt

# Test the root app
curl http://localhost:5001/health
```

### Local Development Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env

# Run migrations (if using Alembic)
# flask db upgrade

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
```python
from leaf_api.auth.jwt_handler import JWTHandler

handler = JWTHandler(
    public_key_path="leaf_api/auth/public_key.pem",
    private_key_path="leaf_api/auth/keypair.pem"
)

# Create a token
token = handler.create_token(user_id="user123", role="admin", exp=3600)

# Use in request
curl -H "Authorization: Bearer $token" http://localhost:5000/orders
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

## Implementation Phases

### Phase 1: ✅ Leaf API Foundation
- Flask app structure with config management
- SQLAlchemy models (Order, Customer, Product)
- JWT validation middleware with RS256
- Docker Compose setup with PostgreSQL

### Phase 2: Discovery Protocol (Leaf API)
- JSONSchemaBuilder for schema generation
- Role-based schema filtering
- Query parameter processing (e.g., `?positive_only=true`)
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

## Testing

```bash
# Run leaf API tests
pytest leaf_api/tests/

# Run root app tests
pytest root_app/tests/

# Run all tests with coverage
pytest --cov=leaf_api --cov=root_app
```

## Project Structure

```
agentics-hateoas/
├── leaf_api/                  # Example Orders API
│   ├── app.py                 # Flask application factory
│   ├── config.py              # Configuration
│   ├── models/                # SQLAlchemy models
│   ├── auth/                  # JWT handling
│   ├── schemas/               # JSON schema generation
│   ├── resources/             # API endpoints
│   ├── middleware/            # Discovery & caching
│   └── tests/                 # Test suite
├── root_app/                  # Root Application
│   ├── app.py                 # Flask application factory
│   ├── config.py              # Configuration
│   ├── crawler/               # API discovery
│   ├── agent/                 # Agent interface
│   ├── routes/                # API endpoints
│   └── tests/                 # Test suite
├── shared/                    # Shared utilities
├── docker-compose.yml         # Service orchestration
└── requirements.txt           # Python dependencies
```

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
