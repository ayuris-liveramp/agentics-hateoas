"""Root endpoint and API discovery"""

from flask import Blueprint, jsonify

bp = Blueprint("root", __name__)


@bp.route("/", methods=["GET", "HEAD"])
def root():
    """Root endpoint - lists available resources"""
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
        },
    }
    return jsonify(data)


@bp.route("/.well-known/agentics-robots.txt", methods=["GET"])
def agentics_conformance():
    """Advertises Agentics-HATEOAS conformance"""
    data = {
        "conformsTo": "https://agentics.dev/hateoas/v1",
        "crawlDelay": 3600,
        "childApis": [],
    }
    return jsonify(data)
