"""Recursive API crawler for discovering Agentics-HATEOAS APIs"""

import json
import asyncio
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin
from root_app.crawler.client import APIClient
from root_app.crawler.cache_manager import CacheManager
from root_app.crawler.graph_builder import APIGraph
from shared.constants import MAX_CRAWL_DEPTH, CRAWL_BATCH_SIZE


class APICrawler:
    """Crawls APIs to discover their surface using HEAD requests"""

    def __init__(
        self,
        api_urls: List[str],
        cache_manager: CacheManager,
        jwt_token: Optional[str] = None,
    ):
        self.api_urls = api_urls
        self.cache = cache_manager
        self.jwt_token = jwt_token
        self.graph = APIGraph()
        self.client = APIClient(
            headers={"Authorization": f"Bearer {jwt_token}"} if jwt_token else {}
        )

    def crawl(self) -> APIGraph:
        """
        Crawl all configured APIs and build graph

        Returns:
            APIGraph with discovered resources
        """
        visited = set()

        for api_url in self.api_urls:
            self._crawl_recursive(
                api_url,
                max_depth=MAX_CRAWL_DEPTH,
                current_depth=0,
                visited=visited,
            )

        return self.graph

    def _crawl_recursive(
        self,
        url: str,
        max_depth: int = 5,
        current_depth: int = 0,
        visited: Optional[Set[str]] = None,
    ) -> Optional[Dict]:
        """
        Recursively crawl API with cycle detection

        Returns:
            Resource metadata or None if crawl fails
        """
        if visited is None:
            visited = set()

        if url in visited or current_depth > max_depth:
            return None

        visited.add(url)

        # Make HEAD request
        response = self.client.head_request(url)
        if not response or response["status_code"] != 200:
            return None

        # Check cache for existing data
        cache_key = url
        cached_etag = self.cache.get_etag(cache_key)
        etag = response.get("etag")

        # If ETag matches, use cached data
        if cached_etag and etag and cached_etag == etag:
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        # Parse response body
        resource_data = self._parse_head_response(response, url)
        if not resource_data:
            return None

        # Add to graph
        self.graph.add_resource(url, resource_data)

        # Cache the result
        if etag:
            self.cache.set(cache_key, resource_data, etag=etag)

        # Crawl children
        children = resource_data.get("children", [])
        for child_path in children:
            child_url = urljoin(url.rstrip("/") + "/", child_path.lstrip("/"))
            self._crawl_recursive(
                child_url,
                max_depth=max_depth,
                current_depth=current_depth + 1,
                visited=visited,
            )
            self.graph.add_edge(url, child_url)

        return resource_data

    def _parse_head_response(self, response: Dict, url: str) -> Optional[Dict]:
        """
        Parse HEAD response body to extract resource metadata

        Returns:
            Dictionary with resource info or None if parsing fails
        """
        try:
            if not response.get("body"):
                return None

            body = json.loads(response["body"])

            return {
                "url": url,
                "description": body.get("description", ""),
                "schema": body.get("schema"),
                "etag": response.get("etag"),
                "children": body.get("_links", {}).get("children", []),
                "resource_type": body.get("_meta", {}).get("role"),
                "permissions": body.get("_meta", {}).get("permissions", []),
            }
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def refresh_stale(self) -> Dict:
        """
        Re-crawl APIs where ETag has changed

        Returns:
            Dictionary of changed resources
        """
        changed = {}

        for path in self.graph.get_all_paths():
            cached_etag = self.cache.get_etag(path)
            if not cached_etag:
                continue

            response = self.client.head_request(path)
            if not response:
                continue

            current_etag = response.get("etag")
            if current_etag and current_etag != cached_etag:
                # Resource has changed, re-crawl
                resource = self._parse_head_response(response, path)
                if resource:
                    changed[path] = resource
                    self.cache.set(path, resource, etag=current_etag)

        return changed

    def get_graph(self) -> APIGraph:
        """Get the discovered API graph"""
        return self.graph

    def close(self):
        """Close HTTP session"""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
