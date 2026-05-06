"""Orders resource endpoints"""

from typing import cast
from flask import Blueprint, jsonify, request, Response
from leaf_api.models import db
from leaf_api.models.order import Order
from leaf_api.auth.jwt_handler import JWTHandler
from leaf_api.schemas.order_schema import OrderSchemaGenerator
from leaf_api.middleware.discovery import DiscoveryHandler
from leaf_api.middleware.cache import CacheManager

bp = Blueprint("orders", __name__, url_prefix="/orders")


@bp.route("", methods=["GET", "POST"])
def list_orders():
    """List all orders (GET) or create a new order (POST)"""
    from flask import current_app

    handler = cast(JWTHandler, current_app.extensions["jwt_handler"])
    token = handler.extract_jwt_from_header(request.headers)
    user_context = handler.get_user_context(token)

    if request.method == "POST":
        # Create a new order
        data = request.get_json()
        order = Order(
            customer_id=data.get("customer_id"),
            product_id=data.get("product_id"),
            quantity=data.get("quantity", 1),
        )
        db.session.add(order)
        db.session.commit()
        return jsonify(order.model_dump()), 201

    # GET request - list all orders
    orders = db.session.query(Order).all()
    data = {
        "items": [o.model_dump() for o in orders],
        "_meta": {"role": user_context["role"]},
    }
    return jsonify(data)


@bp.route("", methods=["HEAD"])
def head_orders():
    """List all orders (HEAD) - for discovery"""
    from flask import current_app

    handler = cast(JWTHandler, current_app.extensions["jwt_handler"])
    token = handler.extract_jwt_from_header(request.headers)
    user_context = handler.get_user_context(token)

    # Generate schema
    schema = OrderSchemaGenerator.get_collection_schema(
        user_context["role"],
        request.args.to_dict(),
    )

    # Get child order IDs
    orders = db.session.query(Order).all()
    children = [f"/orders/{o.id}" for o in orders]

    # Build discovery response
    discovery_data = DiscoveryHandler.build_discovery_response(
        resource_type="Order",
        description="Collection of customer orders",
        schema=schema,
        children=children,
        user_role=user_context["role"],
        permissions=user_context["permissions"],
    )

    # Check if client has matching ETag
    etag = CacheManager.generate_etag(discovery_data)
    if DiscoveryHandler.should_return_304(request.headers, etag):
        response = Response(status=304)
        response.headers["ETag"] = f'"{etag}"'
        return response

    # Return with cache headers - manually create response to include body in HEAD
    import json
    response = Response(
        json.dumps(discovery_data),
        mimetype="application/json",
        status=200,
    )
    DiscoveryHandler.apply_cache_headers(response, discovery_data)
    return response


@bp.route("/<int:order_id>", methods=["GET"])
def get_order(order_id: int):
    """Get a specific order (GET)"""
    from flask import current_app

    handler = cast(JWTHandler, current_app.extensions["jwt_handler"])
    token = handler.extract_jwt_from_header(request.headers)
    user_context = handler.get_user_context(token)

    order = db.get_or_404(Order, order_id)
    data = {
        **order.model_dump(),
        "_meta": {"role": user_context["role"]},
    }
    return jsonify(data)


@bp.route("/<int:order_id>", methods=["HEAD"])
def head_order(order_id: int):
    """Get a specific order (HEAD) - for discovery"""
    from flask import current_app
    import json

    handler = cast(JWTHandler, current_app.extensions["jwt_handler"])
    token = handler.extract_jwt_from_header(request.headers)
    user_context = handler.get_user_context(token)

    order = db.get_or_404(Order, order_id)

    # Generate schema
    schema = OrderSchemaGenerator.get_detail_schema(
        user_context["role"],
        request.args.to_dict(),
    )

    # Build discovery response
    discovery_data = DiscoveryHandler.build_discovery_response(
        resource_type="Order",
        description=f"Order #{order_id} details",
        schema=schema,
        user_role=user_context["role"],
        permissions=user_context["permissions"],
    )

    # Check if client has matching ETag
    etag = CacheManager.generate_etag(discovery_data)
    if DiscoveryHandler.should_return_304(request.headers, etag):
        response = Response(status=304)
        response.headers["ETag"] = f'"{etag}"'
        return response

    # Return with cache headers - manually create response to include body in HEAD
    response = Response(
        json.dumps(discovery_data),
        mimetype="application/json",
        status=200,
    )
    DiscoveryHandler.apply_cache_headers(response, discovery_data)
    return response
