"""Products resource endpoints"""

from flask import Blueprint, jsonify, request
from leaf_api.models import db
from leaf_api.models.product import Product
from leaf_api.auth.jwt_handler import JWTHandler

bp = Blueprint("products", __name__, url_prefix="/products")


@bp.route("", methods=["GET", "HEAD"])
def list_products():
    """List all products"""
    from flask import current_app

    handler = current_app.jwt_handler
    token = handler.extract_jwt_from_header(request.headers)
    user_context = handler.get_user_context(token)

    products = Product.query.all()
    data = {
        "items": [p.to_dict() for p in products],
        "_meta": {"role": user_context["role"]},
    }
    return jsonify(data)


@bp.route("/<int:product_id>", methods=["GET", "HEAD"])
def get_product(product_id: int):
    """Get a specific product"""
    from flask import current_app

    handler = current_app.jwt_handler
    token = handler.extract_jwt_from_header(request.headers)
    user_context = handler.get_user_context(token)

    product = Product.query.get_or_404(product_id)
    data = {
        **product.to_dict(),
        "_meta": {"role": user_context["role"]},
    }
    return jsonify(data)
