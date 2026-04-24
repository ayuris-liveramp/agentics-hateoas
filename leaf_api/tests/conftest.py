"""Pytest configuration and fixtures"""

import pytest
from leaf_api.app import create_app
from leaf_api.models import db as database
from leaf_api.models.customer import Customer
from leaf_api.models.product import Product
from leaf_api.models.order import Order


@pytest.fixture
def app():
    """Create and configure app for testing"""
    app = create_app("testing")

    with app.app_context():
        database.create_all()
        yield app
        database.session.remove()
        database.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's CLI"""
    return app.test_cli_runner()


@pytest.fixture
def sample_customer(app):
    """Create a sample customer"""
    with app.app_context():
        customer = Customer(name="John Doe", email="john@example.com", phone="555-1234")
        database.session.add(customer)
        database.session.commit()
        # Refresh to get the ID
        customer_id = customer.id
        database.session.expunge_all()
    return {"id": customer_id, "name": "John Doe", "email": "john@example.com"}


@pytest.fixture
def sample_product(app):
    """Create a sample product"""
    with app.app_context():
        product = Product(
            name="Test Product",
            description="A test product",
            price=99.99,
            cost=50.00,
            stock_quantity=100,
        )
        database.session.add(product)
        database.session.commit()
        product_id = product.id
        database.session.expunge_all()
    return {"id": product_id, "name": "Test Product"}


@pytest.fixture
def sample_order(app, sample_customer, sample_product):
    """Create a sample order"""
    with app.app_context():
        order = Order(
            customer_id=sample_customer["id"],
            product_id=sample_product["id"],
            quantity=5,
            total_price=499.95,
            cost=250.00,
        )
        database.session.add(order)
        database.session.commit()
        order_id = order.id
        database.session.expunge_all()
    return {"id": order_id}
