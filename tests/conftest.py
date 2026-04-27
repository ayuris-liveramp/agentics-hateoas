"""Pytest configuration and fixtures for functional tests."""

import os
import time
import pytest
import requests
from typing import Generator


@pytest.fixture(scope="session")
def root_app_url() -> str:
    """Get root app URL from environment."""
    return os.environ.get("ROOT_APP_URL", "http://localhost:5001")


@pytest.fixture(scope="session")
def leaf_api_url() -> str:
    """Get leaf API URL from environment."""
    return os.environ.get("LEAF_API_URL", "http://localhost:5000")


@pytest.fixture(scope="session")
def wait_for_services(root_app_url: str, leaf_api_url: str) -> None:
    """Wait for services to be ready."""
    services = [
        ("Root App", root_app_url),
        ("Leaf API", leaf_api_url),
    ]

    for name, url in services:
        for attempt in range(30):
            try:
                resp = requests.get(f"{url}/health", timeout=2)
                if resp.status_code == 200:
                    print(f"✓ {name} is ready")
                    break
            except requests.RequestException:
                if attempt < 29:
                    time.sleep(1)
                else:
                    raise RuntimeError(f"{name} ({url}) failed to start")

    # Debug: check registered routes in root app
    try:
        routes_resp = requests.get(f"{root_app_url}/_routes", timeout=2)
        if routes_resp.status_code == 200:
            routes = routes_resp.json()
            print(f"\n=== Root App Routes ===")
            for route in routes:
                print(f"  {route['rule']} {route['methods']}")
            print("=======================\n")
    except Exception as e:
        print(f"Warning: Could not fetch route list: {e}")


@pytest.fixture(scope="session")
def root_client(root_app_url: str, wait_for_services: None):
    """HTTP client for root app."""
    class RootAppClient:
        def __init__(self, base_url: str):
            self.base_url = base_url

        def get(self, path: str, **kwargs):
            url = f"{self.base_url}{path}"
            return requests.get(url, **kwargs)

        def post(self, path: str, **kwargs):
            url = f"{self.base_url}{path}"
            return requests.post(url, **kwargs)

        def head(self, path: str, **kwargs):
            url = f"{self.base_url}{path}"
            return requests.head(url, **kwargs)

    return RootAppClient(root_app_url)


@pytest.fixture(scope="session")
def leaf_client(leaf_api_url: str, wait_for_services: None):
    """HTTP client for leaf API."""
    class LeafApiClient:
        def __init__(self, base_url: str):
            self.base_url = base_url

        def get(self, path: str, **kwargs):
            url = f"{self.base_url}{path}"
            return requests.get(url, **kwargs)

        def post(self, path: str, data=None, json=None, **kwargs):
            url = f"{self.base_url}{path}"
            return requests.post(url, data=data, json=json, **kwargs)

        def head(self, path: str, **kwargs):
            url = f"{self.base_url}{path}"
            return requests.head(url, **kwargs)

    return LeafApiClient(leaf_api_url)
