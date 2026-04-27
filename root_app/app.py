"""Root application factory"""

import os
from flask import Flask, jsonify, current_app
from root_app.config import config


def create_app(config_name: str = None) -> Flask:
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

    # Register blueprints
    from root_app.routes import health

    with app.app_context():
        app.register_blueprint(health.bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(port=5001, debug=True)
