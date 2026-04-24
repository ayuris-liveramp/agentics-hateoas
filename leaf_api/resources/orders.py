"""Orders resource endpoints"""

from flask import Blueprint, jsonify, request
from leaf_api.models import db
from leaf_api.models.order import Order
from leaf_api.auth.jwt_handler import JWTHandler

bp = Blueprint("orders", __name__, url_prefix="/orders")


@bp.route("", methods=["GET", "HEAD"])
def list_orders():
    """List all orders"""
    from flask import current_app

    handler = current_app.jwt_handler
    token = handler.extract_jwt_from_header(request.headers)
    user_context = handler.get_user_context(token)

    orders = Order.query.all()
    data = {
        "items": [o.to_dict() for o in orders],
        "_meta": {"role": user_context["role"]},
    }
    return jsonify(data)


@bp.route("/<int:order_id>", methods=["GET", "HEAD"])
def get_order(order_id: int):
    """Get a specific order"""
    from flask import current_app

    handler = current_app.jwt_handler
    token = handler.extract_jwt_from_header(request.headers)
    user_context = handler.get_user_context(token)

    order = Order.query.get_or_404(order_id)
    data = {
        **order.to_dict(),
        "_meta": {"role": user_context["role"]},
    }
    return jsonify(data)
