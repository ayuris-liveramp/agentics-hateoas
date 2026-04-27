"""Root application factory"""

import os
from flask import Flask, jsonify, current_app, request, Response
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
        IntentionParser,
        ResponseFormatter,
        generate_etag,
    )

    # Register specific routes directly on app (before blueprint) for routing priority
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

    @app.route("/refresh", methods=["POST"])
    def refresh_discovery():
        """Manually trigger API discovery refresh"""
        from root_app.crawler.api_crawler import APICrawler
        from root_app.storage.graph_store import GraphStore
        from root_app.crawler.cache_manager import CacheManager

        child_api_urls = current_app.config.get("CHILD_API_URLS", [])
        cache_dir = current_app.config.get("CACHE_DIR", "cache")

        cache_manager = CacheManager(cache_dir)
        crawler = APICrawler(child_api_urls, cache_manager)
        graph = crawler.crawl()
        crawler.close()

        # Save refreshed graph
        graph_store = GraphStore(cache_dir)
        graph_store.save_graph(graph)

        return jsonify({
            "status": "success",
            "message": "API discovery refreshed",
            "summary": graph.get_graph_summary(),
        })

    @app.route("/<path:path>", methods=["HEAD"])
    def discover_path(path):
        """
        Universal HEAD handler for agent discovery

        Supports:
        - Accept-Intention header for intent-based filtering
        - If-None-Match for conditional requests (304 responses)
        """
        # Get or initialize crawler and graph
        graph, graph_store, cache_manager = get_crawler_and_graph(current_app.config)

        # Parse intention header if present
        intention_header = request.headers.get("Accept-Intention", "")
        intention = IntentionParser.parse_header(intention_header)

        # Build skill markdown
        if intention_header:
            skill_markdown = SkillBuilder.build_intention_specific_skill(graph, intention)
        else:
            skill_markdown = SkillBuilder.build_skill_markdown(graph)

        # Format response
        graph_summary = graph.get_graph_summary()
        response_data = ResponseFormatter.format_discovery_response(
            skill_markdown=skill_markdown,
            intention=intention,
            graph_summary=graph_summary,
        )

        # Generate ETag
        etag = generate_etag(response_data)

        # Check If-None-Match header
        if_none_match = request.headers.get("If-None-Match", "").strip('"')
        if if_none_match and if_none_match == etag:
            # Return 304 Not Modified
            response = Response(status=304)
            response.headers["ETag"] = f'"{etag}"'
            return response

        # Return response with skill content
        response_body = ResponseFormatter.to_markdown(response_data)

        response = Response(
            response_body,
            mimetype="text/markdown; charset=utf-8",
            status=200,
        )
        response.headers["ETag"] = f'"{etag}"'
        response.headers["Cache-Control"] = "public, max-age=3600"
        response.headers["Content-Type"] = "text/markdown; charset=utf-8"

        return response

    # Register blueprints
    from root_app.routes import health

    with app.app_context():
        app.register_blueprint(health.bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(port=5001, debug=True)
