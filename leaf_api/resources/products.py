"""Products resource endpoints"""

import json
from flask import Blueprint, jsonify, request, Response
from leaf_api.models import db
from leaf_api.models.product import Product
from leaf_api.auth.jwt_handler import JWTHandler
from leaf_api.schemas.product_schema import ProductSchemaGenerator
from leaf_api.middleware.discovery import DiscoveryHandler
from leaf_api.middleware.cache import CacheManager

bp = Blueprint("products", __name__, url_prefix="/products")


@bp.route("", methods=["GET"])
def list_products():
    """List all products (GET)"""
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


@bp.route("", methods=["HEAD"])
def head_products():
    """List all products (HEAD) - for discovery"""
    from flask import current_app

    handler = current_app.jwt_handler
    token = handler.extract_jwt_from_header(request.headers)
    user_context = handler.get_user_context(token)

    # Generate schema
    schema = ProductSchemaGenerator.get_collection_schema(
        user_context["role"],
        request.args.to_dict(),
    )

    # Get child product IDs
    products = Product.query.all()
    children = [f"/products/{p.id}" for p in products]

    # Build discovery response
    discovery_data = DiscoveryHandler.build_discovery_response(
        resource_type="Product",
        description="Collection of products available for ordering",
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
    response = Response(
        json.dumps(discovery_data),
        mimetype="application/json",
        status=200,
    )
    DiscoveryHandler.apply_cache_headers(response, discovery_data)
    return response


@bp.route("/<int:product_id>", methods=["GET"])
def get_product(product_id: int):
    """Get a specific product (GET)"""
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


@bp.route("/<int:product_id>", methods=["HEAD"])
def head_product(product_id: int):
    """Get a specific product (HEAD) - for discovery"""
    from flask import current_app

    handler = current_app.jwt_handler
    token = handler.extract_jwt_from_header(request.headers)
    user_context = handler.get_user_context(token)

    product = Product.query.get_or_404(product_id)

    # Generate schema
    schema = ProductSchemaGenerator.get_detail_schema(
        user_context["role"],
        request.args.to_dict(),
    )

    # Build discovery response
    discovery_data = DiscoveryHandler.build_discovery_response(
        resource_type="Product",
        description=f"Product #{product_id} details",
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
