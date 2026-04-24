"""Pytest configuration for root app"""

import pytest
from root_app.app import create_app


@pytest.fixture
def app():
    """Create and configure root app for testing"""
    app = create_app("testing")
    yield app


@pytest.fixture
def client(app):
    """A test client for the root app"""
    return app.test_client()
