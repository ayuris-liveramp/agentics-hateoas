from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from leaf_api.models.base import BaseModel


class Customer(BaseModel, table=True):
    """Customer model"""
    __tablename__ = "customers"

    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., max_length=255, index=True, unique=True)
    phone: Optional[str] = Field(None, max_length=20)
    status: str = Field(default="active", max_length=50)

    # Relationships
    orders: List["Order"] = Relationship(back_populates="customer", cascade_delete=True)

    def __repr__(self) -> str:
        return f"<Customer {self.id}: {self.name}>"
