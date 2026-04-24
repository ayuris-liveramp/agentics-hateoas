"""Orders resource endpoints"""

from flask import Blueprint, jsonify, request, Response
from leaf_api.models import db
from leaf_api.models.order import Order
from leaf_api.auth.jwt_handler import JWTHandler
from leaf_api.schemas.order_schema import OrderSchemaGenerator
from leaf_api.middleware.discovery import DiscoveryHandler
from leaf_api.middleware.cache import CacheManager

bp = Blueprint("orders", __name__, url_prefix="/orders")


@bp.route("", methods=["GET"])
def list_orders():
    """List all orders (GET)"""
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


@bp.route("", methods=["HEAD"])
def head_orders():
    """List all orders (HEAD) - for discovery"""
    from flask import current_app

    handler = current_app.jwt_handler
    token = handler.extract_jwt_from_header(request.headers)
    user_context = handler.get_user_context(token)

    # Generate schema
    schema = OrderSchemaGenerator.get_collection_schema(
        user_context["role"],
        request.args.to_dict(),
    )

    # Get child order IDs
    orders = Order.query.all()
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

    handler = current_app.jwt_handler
    token = handler.extract_jwt_from_header(request.headers)
    user_context = handler.get_user_context(token)

    order = Order.query.get_or_404(order_id)
    data = {
        **order.to_dict(),
        "_meta": {"role": user_context["role"]},
    }
    return jsonify(data)


@bp.route("/<int:order_id>", methods=["HEAD"])
def head_order(order_id: int):
    """Get a specific order (HEAD) - for discovery"""
    from flask import current_app
    import json

    handler = current_app.jwt_handler
    token = handler.extract_jwt_from_header(request.headers)
    user_context = handler.get_user_context(token)

    order = Order.query.get_or_404(order_id)

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
