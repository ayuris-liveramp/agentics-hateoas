from decimal import Decimal
from typing import ClassVar, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from leaf_api.models.base import BaseModel

if TYPE_CHECKING:
    from leaf_api.models.customer import Customer
    from leaf_api.models.product import Product


class Order(BaseModel, table=True):
    """Order model"""
    __tablename__: ClassVar[str] = "orders"  # type: ignore[assignment]

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
