"""Discovery helper functions for agent queries"""

from root_app.crawler.api_crawler import APICrawler
from root_app.crawler.cache_manager import CacheManager
from root_app.storage.graph_store import GraphStore
from root_app.agent.intention_parser import IntentionParser
from root_app.agent.skill_builder import SkillBuilder
from root_app.agent.response_formatter import ResponseFormatter
from shared.utils import generate_etag


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
