"""Pytest configuration for root app tests"""

import pytest
import tempfile
import json
from pathlib import Path
from root_app.app import create_app
from root_app.crawler.cache_manager import CacheManager
from root_app.crawler.graph_builder import APIGraph


@pytest.fixture
def app():
    """Create and configure root app for testing"""
    app = create_app("testing")
    yield app


@pytest.fixture
def client(app):
    """A test client for the root app"""
    return app.test_client()


@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def cache_manager(temp_cache_dir):
    """Create a cache manager for testing"""
    return CacheManager(temp_cache_dir)


@pytest.fixture
def sample_api_graph():
    """Create a sample API graph"""
    graph = APIGraph()

    # Add root API
    graph.add_api("http://localhost:5000", {
        "title": "Test API",
        "version": "1.0.0",
        "description": "Test API for discovery",
    })

    # Add resources
    graph.add_resource("/", {
        "description": "Root resource",
        "schema": {"type": "object"},
        "etag": "root-etag",
        "children": ["/orders", "/customers"],
    })

    graph.add_resource("/orders", {
        "description": "Orders collection",
        "schema": {"type": "object"},
        "etag": "orders-etag",
        "children": [],
    })

    graph.add_resource("/customers", {
        "description": "Customers collection",
        "schema": {"type": "object"},
        "etag": "customers-etag",
        "children": [],
    })

    # Add edges
    graph.add_edge("/", "/orders")
    graph.add_edge("/", "/customers")

    return graph
