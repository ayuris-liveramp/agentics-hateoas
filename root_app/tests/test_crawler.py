"""Tests for API crawler components"""

import pytest
from root_app.crawler.cache_manager import CacheManager
from root_app.crawler.graph_builder import APIGraph


class TestCacheManager:
    def test_cache_manager_set_and_get(self, cache_manager):
        """Test cache set and get operations"""
        key = "test_key"
        value = {"data": "test_value"}

        cache_manager.set(key, value, etag="test-etag")
        cached = cache_manager.get(key)

        assert cached == value

    def test_cache_manager_etag_tracking(self, cache_manager):
        """Test ETag tracking"""
        key = "test_key"
        value = {"data": "test"}
        etag = "etag-123"

        cache_manager.set(key, value, etag=etag)
        retrieved_etag = cache_manager.get_etag(key)

        assert retrieved_etag == etag

    def test_cache_manager_invalidation(self, cache_manager):
        """Test cache invalidation"""
        key = "test_key"
        cache_manager.set(key, {"data": "test"})

        assert cache_manager.get(key) is not None

        cache_manager.invalidate(key)

        assert cache_manager.get(key) is None

    def test_cache_manager_is_stale(self, cache_manager):
        """Test staleness detection"""
        key = "test_key"
        cache_manager.set(key, {"data": "test"}, etag="old-etag")

        # Same ETag - not stale
        assert not cache_manager.is_stale(key, "old-etag")

        # Different ETag - stale
        assert cache_manager.is_stale(key, "new-etag")

        # No cached - stale
        assert cache_manager.is_stale("nonexistent", "any-etag")


class TestAPIGraph:
    def test_graph_add_resource(self, sample_api_graph):
        """Test adding resources to graph"""
        graph = APIGraph()
        graph.add_resource("/test", {"description": "Test"})

        assert graph.get_resource("/test") is not None

    def test_graph_add_edge(self, sample_api_graph):
        """Test adding parent-child relationships"""
        graph = APIGraph()
        graph.add_resource("/parent", {})
        graph.add_resource("/parent/child", {})

        graph.add_edge("/parent", "/parent/child")

        children = graph.get_children("/parent")
        assert "/parent/child" in children

    def test_graph_traversal_bfs(self, sample_api_graph):
        """Test breadth-first traversal"""
        paths = list(sample_api_graph.traverse_breadth_first("/"))
        assert "/" in paths
        assert "/orders" in paths
        assert "/customers" in paths

    def test_graph_traversal_dfs(self, sample_api_graph):
        """Test depth-first traversal"""
        paths = list(sample_api_graph.traverse_depth_first("/"))
        assert "/" in paths
        assert "/orders" in paths or "/customers" in paths

    def test_graph_summary(self, sample_api_graph):
        """Test graph summary generation"""
        summary = sample_api_graph.get_graph_summary()

        assert summary["total_nodes"] >= 3
        assert summary["total_apis"] == 1

    def test_graph_to_dict(self, sample_api_graph):
        """Test graph serialization"""
        graph_dict = sample_api_graph.to_dict()

        assert "apis" in graph_dict
        assert "resources" in graph_dict
        assert "structure" in graph_dict
        assert len(graph_dict["resources"]) >= 3
