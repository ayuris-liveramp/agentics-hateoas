"""Customers resource endpoints"""

from flask import Blueprint, jsonify, request
from leaf_api.models import db
from leaf_api.models.customer import Customer
from leaf_api.auth.jwt_handler import JWTHandler

bp = Blueprint("customers", __name__, url_prefix="/customers")


@bp.route("", methods=["GET", "HEAD"])
def list_customers():
    """List all customers"""
    from flask import current_app

    handler = current_app.jwt_handler
    token = handler.extract_jwt_from_header(request.headers)
    user_context = handler.get_user_context(token)

    customers = Customer.query.all()
    data = {
        "items": [c.to_dict() for c in customers],
        "_meta": {"role": user_context["role"]},
    }
    return jsonify(data)


@bp.route("/<int:customer_id>", methods=["GET", "HEAD"])
def get_customer(customer_id: int):
    """Get a specific customer"""
    from flask import current_app

    handler = current_app.jwt_handler
    token = handler.extract_jwt_from_header(request.headers)
    user_context = handler.get_user_context(token)

    customer = Customer.query.get_or_404(customer_id)
    data = {
        **customer.to_dict(),
        "_meta": {"role": user_context["role"]},
    }
    return jsonify(data)
