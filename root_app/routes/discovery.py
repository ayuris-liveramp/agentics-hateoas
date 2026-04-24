"""Discovery routes for agent queries"""

import json
from flask import Blueprint, Response, request
from root_app.crawler.api_crawler import APICrawler
from root_app.crawler.cache_manager import CacheManager
from root_app.storage.graph_store import GraphStore
from root_app.agent.intention_parser import IntentionParser
from root_app.agent.skill_builder import SkillBuilder
from root_app.agent.response_formatter import ResponseFormatter
from shared.utils import generate_etag

bp = Blueprint("discovery", __name__)


def get_crawler_and_graph(app_config):
    """Get or initialize crawler and API graph"""
    cache_dir = app_config.get("CACHE_DIR", "cache")
    cache_manager = CacheManager(cache_dir)
    graph_store = GraphStore(cache_dir)

    # Try to load existing graph
    graph = graph_store.load_graph()

    # If no existing graph or if graph is empty, crawl APIs
    if not graph or len(graph.get_all_paths()) == 0:
        child_api_urls = app_config.get("CHILD_API_URLS", [])
        crawler = APICrawler(child_api_urls, cache_manager)
        graph = crawler.crawl()
        crawler.close()

        # Save graph
        graph_store.save_graph(graph)

    return graph, graph_store, cache_manager


@bp.route("/<path:path>", methods=["HEAD"])
def discover_path(path):
    """
    Universal HEAD handler for agent discovery

    Supports:
    - Accept-Intention header for intent-based filtering
    - If-None-Match for conditional requests (304 responses)
    """
    from flask import current_app

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


@bp.route("/refresh", methods=["POST"])
def refresh_discovery():
    """Manually trigger API discovery refresh"""
    from flask import current_app, jsonify

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
