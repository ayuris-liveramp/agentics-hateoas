"""Customers resource endpoints"""

import json
from flask import Blueprint, jsonify, request, Response
from leaf_api.models import db
from leaf_api.models.customer import Customer
from leaf_api.auth.jwt_handler import JWTHandler
from leaf_api.schemas.customer_schema import CustomerSchemaGenerator
from leaf_api.middleware.discovery import DiscoveryHandler
from leaf_api.middleware.cache import CacheManager

bp = Blueprint("customers", __name__, url_prefix="/customers")


@bp.route("", methods=["GET"])
def list_customers():
    """List all customers (GET)"""
    from flask import current_app

    handler = current_app.jwt_handler
    token = handler.extract_jwt_from_header(request.headers)
    user_context = handler.get_user_context(token)

    customers = Customer.query.all()
    data = {
        "items": [c.model_dump() for c in customers],
        "_meta": {"role": user_context["role"]},
    }
    return jsonify(data)


@bp.route("", methods=["HEAD"])
def head_customers():
    """List all customers (HEAD) - for discovery"""
    from flask import current_app

    handler = current_app.jwt_handler
    token = handler.extract_jwt_from_header(request.headers)
    user_context = handler.get_user_context(token)

    # Generate schema
    schema = CustomerSchemaGenerator.get_collection_schema(
        user_context["role"],
        request.args.to_dict(),
    )

    # Get child customer IDs
    customers = Customer.query.all()
    children = [f"/customers/{c.id}" for c in customers]

    # Build discovery response
    discovery_data = DiscoveryHandler.build_discovery_response(
        resource_type="Customer",
        description="Collection of customers",
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


@bp.route("/<int:customer_id>", methods=["GET"])
def get_customer(customer_id: int):
    """Get a specific customer (GET)"""
    from flask import current_app

    handler = current_app.jwt_handler
    token = handler.extract_jwt_from_header(request.headers)
    user_context = handler.get_user_context(token)

    customer = Customer.query.get_or_404(customer_id)
    data = {
        **customer.model_dump(),
        "_meta": {"role": user_context["role"]},
    }
    return jsonify(data)


@bp.route("/<int:customer_id>", methods=["HEAD"])
def head_customer(customer_id: int):
    """Get a specific customer (HEAD) - for discovery"""
    from flask import current_app

    handler = current_app.jwt_handler
    token = handler.extract_jwt_from_header(request.headers)
    user_context = handler.get_user_context(token)

    customer = Customer.query.get_or_404(customer_id)

    # Generate schema
    schema = CustomerSchemaGenerator.get_detail_schema(
        user_context["role"],
        request.args.to_dict(),
    )

    # Build discovery response
    discovery_data = DiscoveryHandler.build_discovery_response(
        resource_type="Customer",
        description=f"Customer #{customer_id} details",
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
