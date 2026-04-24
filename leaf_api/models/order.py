from leaf_api.models import db
from leaf_api.models.base import BaseModel


class Order(BaseModel):
    """Order model"""
    __tablename__ = "orders"

    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    cost = db.Column(db.Numeric(10, 2))
    status = db.Column(
        db.String(50),
        default="pending",
    )  # pending, confirmed, shipped, delivered, cancelled

    def to_dict(self, include_customer=False, include_product=False):
        """Convert to dictionary"""
        data = {
            "id": self.id,
            "customer_id": self.customer_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "total_price": float(self.total_price),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_customer and self.customer:
            data["customer"] = self.customer.to_dict()
        if include_product and self.product:
            data["product"] = self.product.to_dict()
        return data

    def __repr__(self):
        return f"<Order {self.id}: customer={self.customer_id}, product={self.product_id}>"
