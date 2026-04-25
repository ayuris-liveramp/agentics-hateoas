from decimal import Decimal
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from leaf_api.models.base import BaseModel


class Product(BaseModel, table=True):
    """Product model"""
    __tablename__ = "products"

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    cost: Optional[Decimal] = Field(None, gt=0)
    stock_quantity: int = Field(default=0, ge=0)
    status: str = Field(default="active", max_length=50)

    # Relationships
    orders: List["Order"] = Relationship(back_populates="product", cascade_delete=True)

    def __repr__(self) -> str:
        return f"<Product {self.id}: {self.name}>"
