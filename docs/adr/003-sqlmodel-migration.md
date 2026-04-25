# ADR-003: SQLModel Migration from Flask-SQLAlchemy

## Status
Accepted

## Context

In the initial implementation, models were defined using Flask-SQLAlchemy (traditional ORM approach) while JSON schemas were generated separately using a custom JSONSchemaBuilder class. This created a maintenance burden:

- **Duplication**: Model definitions in SQLAlchemy and schema definitions existed separately
- **Drift risk**: If one was updated, the other could become out of sync
- **Two sources of truth**: Changes in DB schema required updating both ORM and schema generator
- **Serialization complexity**: Manual `to_dict()` methods needed for API responses

During Phase 4 (around commit 575fcbe), the team decided to migrate to SQLModel, which unifies ORM and data validation in a single definition.

## Decision

Migrate from Flask-SQLAlchemy + custom schemas to SQLModel:

```python
# Before (Flask-SQLAlchemy + manual schema)
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    quantity = db.Column(db.Integer)
    # JSON schema generated separately

# After (SQLModel)
class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id")
    quantity: int = Field(gt=0)
    # JSON schema auto-generated from type annotations
```

SQLModel combines:
- **SQLAlchemy 2.0** for database ORM
- **Pydantic v2** for validation and JSON schema generation
- Single unified model definition

## Rationale

### Why SQLModel?

**Eliminates Duplication:**
- One definition for DB structure AND validation
- No separate JSONSchemaBuilder needed
- Changes to model automatically propagate to schema

**Type Annotations:**
- Python types are executable documentation
- Type hints enable better IDE support and static analysis
- Constraints (`gt=0`, `max_length=255`) are code, not strings

**Automatic Schema Generation:**
- Pydantic `model_json_schema()` generates JSON schema automatically
- Validation rules become DB constraints via SQLAlchemy
- No custom builder class needed

**Built-in Serialization:**
- `model_dump()` and `model_dump_json()` replace manual `to_dict()`
- Cleaner API response formatting
- Consistent serialization across endpoints

**Modern Python Stack:**
- Aligns with modern Python web patterns
- Compatible with FastAPI (if future migration needed)
- Better type safety throughout codebase

### Phased Migration Approach

Rather than big-bang migration, the team used a phased approach (commits 575fcbe → 50f2056):

1. **575fcbe**: Introduce SQLModel alongside Flask-SQLAlchemy
2. **d8db178**: Update response handlers to use `model.model_dump()`
3. **5b1ceec**: Fix SQLModel integration with Flask-SQLAlchemy
4. **50f2056**: Final cleanup, remove unused legacy code

This reduced risk of breakage and allowed testing at each phase.

## Consequences

### Positive
- ✅ Single source of truth: one model definition per entity
- ✅ Automatic schema generation: less maintenance code
- ✅ Better type safety: full Python type annotation support
- ✅ Cleaner response handlers: use `model_dump()` directly
- ✅ Constraint enforcement: type hints become DB constraints
- ✅ Future-proof: aligns with modern Python web frameworks
- ✅ Easier composition: Pydantic relationships work better

### Negative
- ❌ Learning curve: SQLModel API differs from Flask-SQLAlchemy
- ❌ Migration effort: incremental changes throughout codebase
- ❌ Less familiar to some: Flask-SQLAlchemy is more widely used
- ❌ Pydantic v2 migration: Had to update validators and methods
- ❌ Relationship complexity: SQLModel relationships have different syntax

## Migration Path Taken

### Phase 1: Parallel Definitions (575fcbe)
- Introduced SQLModel models alongside legacy SQLAlchemy models
- Both defined, neither required yet
- Tests verify both work

### Phase 2: Response Updates (d8db178)
- Updated response handlers to use SQLModel's `model_dump()`
- Removed manual `to_dict()` calls where possible
- Tested response serialization

### Phase 3: Integration Fixes (5b1ceec)
- Fixed Flask-SQLAlchemy integration (session management)
- Verified foreign key relationships work correctly
- Tested cascade delete behavior

### Phase 4: Cleanup (50f2056)
- Removed legacy Flask-SQLAlchemy only code
- Deleted unused base_schema.py
- Removed `.#claude` marker files

## Alternatives Considered

| Approach | Single Source? | Auto Schema? | Type Safe? | Effort |
|----------|---|---|---|---|
| **SQLModel (Chosen)** | ✓ | ✓ | ✓ | Medium |
| Status quo | ✗ | ✗ | ⚠ | Low |
| Pydantic only | ⚠ | ✓ | ✓ | High |
| Pure SQLAlchemy 2.0 | ✗ | ✗ | ⚠ | Medium |

## Technical Details

### Model Example

```python
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

class Customer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(unique=True)
    orders: List["Order"] = Relationship(back_populates="customer")

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id")
    quantity: int = Field(gt=0)
    customer: Optional[Customer] = Relationship(back_populates="orders")
```

### Key Benefits in Code

**Serialization** (before/after):
```python
# Before
def to_dict(self):
    return {"id": self.id, "name": self.name, ...}

# After
order.model_dump()  # Automatic, complete
```

**Validation** (before/after):
```python
# Before: No type validation at model level
# After: Automatic via Pydantic validators
```

**Schema Generation** (before/after):
```python
# Before
schema = JSONSchemaBuilder(Order).build()

# After
schema = Order.model_json_schema()
```

## Version Requirements

- **SQLAlchemy**: ≥2.0.30 (for Python 3.14 compatibility)
- **SQLModel**: Latest stable
- **Pydantic**: v2.8.0+

## References

- **Commits**: 575fcbe (start), d8db178 (responses), 5b1ceec (integration), 50f2056 (cleanup)
- **Code**:
  - `leaf_api/models/` — SQLModel unified models
  - `leaf_api/schemas/` — Now minimal, mostly uses SQLModel's built-in generation
  - `leaf_api/resources/` — Updated to use `model_dump()`
- **Documentation**:
  - [SQLModel docs](https://sqlmodel.tiangolo.com/)
  - [Pydantic v2 migration guide](https://docs.pydantic.dev/v2/migration/)
- **Related ADRs**:
  - [ADR-001](001-two-tier-microservice-architecture.md) — Overall architecture
  - [ADR-005](005-role-based-schema-filtering.md) — Uses SQLModel schemas for RBAC

## Lessons Learned

1. **Phased migration beats big-bang**: Smaller steps reduced risk and made debugging easier
2. **Type annotations are powerful**: They enable both validation and documentation
3. **Framework alignment matters**: Using SQLModel aligns better with modern Python conventions
4. **Maintenance burden matters**: Single source of truth reduced long-term maintenance

## Future Considerations

- Could migrate to **FastAPI** in future (SQLModel native support)
- **Pydantic validators** can replace some custom validation logic
- **Relationship eager loading** can optimize query performance
- **SQLModel 1.0** API stability as it approaches production release
