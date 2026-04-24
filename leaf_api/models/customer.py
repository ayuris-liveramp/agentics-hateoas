from leaf_api.models import db
from leaf_api.models.base import BaseModel


class Customer(BaseModel):
    """Customer model"""
    __tablename__ = "customers"

    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    phone = db.Column(db.String(20))
    status = db.Column(db.String(50), default="active")  # active, inactive, suspended

    # Relationships
    orders = db.relationship("Order", backref="customer", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self, include_orders=False):
        """Convert to dictionary"""
        data = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_orders:
            data["orders"] = [o.to_dict() for o in self.orders]
        return data

    def __repr__(self):
        return f"<Customer {self.id}: {self.name}>"
