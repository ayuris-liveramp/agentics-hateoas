# NOTICE

Until this header is removed, no human has verified the contents of this repository. I generated it using Haiku on low effort while waiting at the airport, and haven't reveiwed it yet.

---

# Agentics-HATEOAS

**Version: v0.0.1** (Pre-release)

A standard for crafting LLM-discoverable APIs by leveraging content negotiation and HEAD requests. APIs expose their surface through hypermedia (HATEOAS) while supporting LLM agents as first-class clients.

## Quick Start

```bash
make          # start all services via Docker Compose
make test     # run functional tests
make leaf_api/auth/token.b64  # generate a JWT token
```

The leaf API runs on `http://localhost:5000` and the root app on `http://localhost:5001`. Use `Authorization: Bearer <token>` for authenticated requests.

## Architecture

The **Leaf API** is a Flask/PostgreSQL REST API where HEAD requests return JSON schemas and HATEOAS links filtered by JWT role (admin, user, public). The **Root Application** crawls leaf APIs, caches their surface maps using ETags, and serves aggregated skill descriptions to LLM agents via `HEAD /*` with optional `Accept-Intention` headers for intent-based filtering.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API Protocol](docs/API_PROTOCOL.md)
- [Implementation Guide](docs/IMPLEMENTATION_GUIDE.md)

## References

- [Agentics.org](https://agentics.org/) — Agentics specification
- [HATEOAS](https://en.wikipedia.org/wiki/HATEOAS) — Hypermedia As The Engine Of Application State

## License

MIT — see LICENSE.md
