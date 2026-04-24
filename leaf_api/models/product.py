from leaf_api.models import db
from leaf_api.models.base import BaseModel


class Product(BaseModel):
    """Product model"""
    __tablename__ = "products"

    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    cost = db.Column(db.Numeric(10, 2))
    stock_quantity = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default="active")  # active, discontinued, draft

    # Relationships
    orders = db.relationship("Order", backref="product", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self, include_orders=False):
        """Convert to dictionary"""
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "stock_quantity": self.stock_quantity,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_orders:
            data["orders"] = [o.to_dict() for o in self.orders]
        return data

    def __repr__(self):
        return f"<Product {self.id}: {self.name}>"
