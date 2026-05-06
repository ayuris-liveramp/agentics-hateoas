"""Root application factory"""

import base64
import os
from typing import Optional
import anthropic
from anthropic.types import TextBlock
from flask import Flask, jsonify, request, current_app
from root_app.config import config


def create_app(config_name: Optional[str] = None) -> Flask:
    """Application factory"""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config.get(config_name, config["default"]))

    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500

    # Import here to avoid circular imports
    from root_app.routes.discovery import (
        get_crawler_and_graph,
        SkillBuilder,
    )

    # Register GET endpoints for discovery
    @app.route("/discover", methods=["GET"])
    def discover():
        """Get API graph discovery data as JSON"""
        graph, graph_store, cache_manager = get_crawler_and_graph(current_app.config)
        graph_summary = graph.get_graph_summary()
        return jsonify(graph_summary)

    @app.route("/skills", methods=["GET"])
    def get_skills():
        """Get agent skills as JSON list"""
        graph, graph_store, cache_manager = get_crawler_and_graph(current_app.config)
        skill_markdown = SkillBuilder.build_skill_markdown(graph)
        return jsonify([skill_markdown])

    @app.route("/", methods=["HEAD"])
    def head_root():
        """Return Anthropic-generated skill payload for Accept-Intention HEAD requests."""
        intention = request.headers.get("Accept-Intention", "create a new product and order it")
        client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY", "test-key"),
            base_url=os.environ.get("ANTHROPIC_BASE_URL"),
        )
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": intention}],
        )
        first = message.content[0] if message.content else None
        skill_payload = first.text if isinstance(first, TextBlock) else ""
        resp = current_app.make_response(skill_payload)
        resp.content_type = "text/markdown"
        resp.headers["X-Anthropic-Message-Id"] = message.id
        resp.headers["X-Anthropic-Model"] = message.model
        resp.headers["X-Anthropic-Stop-Reason"] = message.stop_reason or "end_turn"
        resp.headers["X-Intention-Received"] = intention
        resp.headers["X-Skill-Payload"] = base64.b64encode(skill_payload.encode()).decode()
        return resp

    # Register blueprints
    from root_app.routes import health

    with app.app_context():
        app.register_blueprint(health.bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(port=5001, debug=True)
