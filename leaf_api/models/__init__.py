from flask_sqlalchemy import SQLAlchemy
from sqlmodel import SQLModel

# Create the base db instance
db = SQLAlchemy()

# Make SQLModel use SQLAlchemy's metadata
SQLModel.metadata = db.metadata

# Import models so they register with SQLAlchemy
from leaf_api.models.customer import Customer
from leaf_api.models.product import Product
from leaf_api.models.order import Order

__all__ = ["db", "Customer", "Product", "Order"]
