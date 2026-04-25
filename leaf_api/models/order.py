from decimal import Decimal
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from leaf_api.models.base import BaseModel


class Order(BaseModel, table=True):
    """Order model"""
    __tablename__ = "orders"

    customer_id: int = Field(foreign_key="customers.id")
    product_id: int = Field(foreign_key="products.id")
    quantity: int = Field(..., gt=0)
    total_price: Decimal = Field(..., ge=0)
    cost: Optional[Decimal] = Field(None, ge=0)
    status: str = Field(default="pending", max_length=50)

    # Relationships
    customer: Optional["Customer"] = Relationship(back_populates="orders")
    product: Optional["Product"] = Relationship(back_populates="orders")

    def __repr__(self) -> str:
        return f"<Order {self.id}: customer={self.customer_id}, product={self.product_id}>"
