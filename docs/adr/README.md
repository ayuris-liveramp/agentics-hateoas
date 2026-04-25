# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) for the Agentics-HATEOAS project. ADRs document significant architectural decisions, the context that led to them, their rationale, and the consequences of each decision.

## What is an ADR?

An Architecture Decision Record is a short text document describing a single architectural decision made in the context of the project. Each ADR should be self-contained and explain:

- **Context**: The problem or situation that prompted the decision
- **Decision**: What was decided and why
- **Rationale**: Why this approach was chosen over alternatives
- **Consequences**: The positive and negative implications of the decision

ADRs are not meant to replace the technical architecture documentation (see [ARCHITECTURE.md](../ARCHITECTURE.md) for details). Instead, they focus on the "why" behind each major decision.

## Decision Log

| ADR | Title | Status | Commit |
|-----|-------|--------|--------|
| [001](001-two-tier-microservice-architecture.md) | Two-Tier Microservice Architecture | Accepted | ef569e4, 7b06d3a |
| [002](002-hateoas-head-request-protocol.md) | HATEOAS + HEAD Request Protocol for API Discovery | Accepted | 0f3e83e, e70a00f |
| [003](003-sqlmodel-migration.md) | SQLModel Migration from Flask-SQLAlchemy | Accepted | 575fcbe, d8db178, 5b1ceec, 50f2056 |
| [004](004-etag-based-caching.md) | ETag-Based Caching for Efficient API Crawling | Accepted | 0f3e83e, 7b06d3a |
| [005](005-role-based-schema-filtering.md) | Role-Based Schema Filtering via JWT Claims | Accepted | ef569e4, 0f3e83e |
| [006](006-ed25519-jwt-authentication.md) | Ed25519 Over RS256 for JWT Authentication | Accepted | ef569e4, c108130 |
| [007](007-dual-get-head-endpoints.md) | Dual GET/HEAD Endpoints for Optimization | Accepted | 0f3e83e |
| [008](008-accept-intention-header.md) | Accept-Intention Header for Agent Intent Specification | Accepted | e70a00f |

## Quick Links

- **[ARCHITECTURE.md](../ARCHITECTURE.md)** — Technical architecture documentation with diagrams and component details
- **[Project README](../../README.md)** — Project overview and getting started guide
- **[Source Code](../../)** — The actual implementation

## How to Use These ADRs

1. **Understanding the project**: Start with this README and the decision log above
2. **Learning specific decisions**: Read the relevant ADR for context on why something was implemented a certain way
3. **Making new decisions**: Follow the same template and process when adding new ADRs
4. **Referencing decisions**: Link to specific ADRs in code comments or documentation when decisions are relevant

## Adding New ADRs

When making a new significant architectural decision:

1. Create a new file: `docs/adr/NNN-decision-title.md` (incrementing the number)
2. Use the template below
3. Include references to commits, files, and related decisions
4. Update this README's decision log
5. Commit with a message referencing the ADR

### ADR Template

```markdown
# ADR-NNN: [Decision Title]

## Status
Accepted | Proposed | Deprecated

## Context
Describe the situation or problem that led to this decision. What constraints or requirements drove it?

## Decision
State what was decided, concisely.

## Rationale
Explain why this decision was made. What alternatives were considered? Why was this chosen?

## Consequences
What are the positive outcomes and potential downsides of this decision?

## Alternatives Considered
- **Option A**: Why it wasn't chosen
- **Option B**: Why it wasn't chosen

## Implementation Notes
How was this implemented? Link to relevant commits or files.

## References
- Related ADRs: [ADR-NNN](NNN-related.md)
- Code: `path/to/relevant/files`
- Commits: `abc1234`, `def5678`
- Documentation: [Link to docs]
```

## Status Legend

- **Accepted**: Decision has been made and implemented
- **Proposed**: Decision under consideration
- **Deprecated**: Decision was made but later superseded by another

## Related Documentation

- [ARCHITECTURE.md](../ARCHITECTURE.md) — System design, components, data flows
- [CLAUDE.md](../../CLAUDE.md) — Development guidelines and conventions
- [Docker Compose](../../docker-compose.yml) — Deployment configuration

---

Last updated: April 2026
