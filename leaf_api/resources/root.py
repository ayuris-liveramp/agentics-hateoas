"""Root endpoint and API discovery"""

import json
from typing import cast
from flask import Blueprint, jsonify, request, Response
from leaf_api.auth.jwt_handler import JWTHandler
from leaf_api.middleware.cache import CacheManager
from leaf_api.middleware.discovery import DiscoveryHandler

bp = Blueprint("root", __name__)


@bp.route("/", methods=["GET"])
def root():
    """Root endpoint - lists available resources (GET)"""
    data = {
        "title": "Agentics Orders API",
        "version": "1.0.0",
        "description": "Example Orders API demonstrating Agentics-HATEOAS",
        "_links": {
            "resources": [
                {"rel": "orders", "href": "/orders"},
                {"rel": "customers", "href": "/customers"},
                {"rel": "products", "href": "/products"},
            ],
            "self": {"href": "/"},
            "conformance": {"href": "/.well-known/agentics-robots.txt"},
        },
    }
    return jsonify(data)


@bp.route("/", methods=["HEAD"])
def head_root():
    """Root endpoint (HEAD) - for discovery"""
    from flask import current_app

    handler = cast(JWTHandler, current_app.extensions["jwt_handler"])
    token = handler.extract_jwt_from_header(request.headers)
    user_context = handler.get_user_context(token)

    # Build discovery response for root
    discovery_data = DiscoveryHandler.build_discovery_response(
        resource_type="API",
        description="Agentics Orders API - Root resource listing available endpoints",
        schema={
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "title": "API Root",
            "properties": {
                "title": {"type": "string"},
                "version": {"type": "string"},
                "description": {"type": "string"},
            },
        },
        children=["/orders", "/customers", "/products"],
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


@bp.route("/.well-known/agentics-robots.txt", methods=["GET"])
def agentics_conformance():
    """Advertises Agentics-HATEOAS conformance"""
    data = {
        "conformsTo": "https://agentics.dev/hateoas/v1",
        "crawlDelay": 3600,
        "childApis": [],
        "description": "This API conforms to Agentics-HATEOAS specification for LLM discovery",
    }
    return jsonify(data)
