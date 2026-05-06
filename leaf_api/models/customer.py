from typing import ClassVar, List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from leaf_api.models.base import BaseModel

if TYPE_CHECKING:
    from leaf_api.models.order import Order


class Customer(BaseModel, table=True):
    """Customer model"""
    __tablename__: ClassVar[str] = "customers"  # type: ignore[assignment]

    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., max_length=255, index=True, unique=True)
    phone: Optional[str] = Field(None, max_length=20)
    status: str = Field(default="active", max_length=50)

    # Relationships
    orders: List["Order"] = Relationship(back_populates="customer", cascade_delete=True)

    def __repr__(self) -> str:
        return f"<Customer {self.id}: {self.name}>"
