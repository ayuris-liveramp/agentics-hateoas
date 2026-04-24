"""Tests for JWT authentication"""

import pytest
from leaf_api.auth.jwt_handler import JWTHandler


def test_jwt_handler_initialization():
    """Test JWT handler initialization"""
    handler = JWTHandler()
    assert handler is not None


def test_extract_jwt_from_header():
    """Test extracting JWT from Authorization header"""
    handler = JWTHandler()
    headers = {"Authorization": "Bearer test-token-value"}
    token = handler.extract_jwt_from_header(headers)
    assert token == "test-token-value"


def test_extract_jwt_missing_header():
    """Test extracting JWT when header is missing"""
    handler = JWTHandler()
    headers = {}
    token = handler.extract_jwt_from_header(headers)
    assert token is None


def test_extract_jwt_invalid_format():
    """Test extracting JWT with invalid format"""
    handler = JWTHandler()
    headers = {"Authorization": "Basic test-token-value"}
    token = handler.extract_jwt_from_header(headers)
    assert token is None


def test_get_user_context_unauthenticated():
    """Test getting user context without token"""
    handler = JWTHandler()
    context = handler.get_user_context(None)
    assert context["authenticated"] is False
    assert context["role"] == "public"
    assert context["user_id"] is None
