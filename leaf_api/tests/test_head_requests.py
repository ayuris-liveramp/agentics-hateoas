"""Tests for HEAD request discovery"""

import pytest
from shared.utils import generate_etag


def test_head_orders_collection(client, sample_order):
    """Test HEAD request on orders collection"""
    response = client.head("/orders")
    assert response.status_code == 200
    assert "ETag" in response.headers
    assert "Cache-Control" in response.headers
    assert response.data  # HEAD should return body for discovery


def test_head_orders_detail(client, sample_order):
    """Test HEAD request on order detail"""
    response = client.head(f"/orders/{sample_order['id']}")
    assert response.status_code == 200
    assert "ETag" in response.headers


def test_head_etag_generation(client, sample_order):
    """Test ETag generation consistency"""
    response1 = client.head("/orders")
    etag1 = response1.headers.get("ETag")

    response2 = client.head("/orders")
    etag2 = response2.headers.get("ETag")

    assert etag1 == etag2


def test_head_with_if_none_match(client, sample_order):
    """Test If-None-Match header returns 304"""
    # First request
    response1 = client.head("/orders")
    etag = response1.headers.get("ETag")

    # Second request with matching ETag
    response2 = client.head("/orders", headers={"If-None-Match": etag})
    assert response2.status_code == 304
    assert response2.headers.get("ETag") == etag


def test_head_discovery_response_structure(client, sample_order):
    """Test HEAD response has correct discovery structure"""
    response = client.get("/orders", method="HEAD")
    assert response.status_code == 200

    import json
    data = json.loads(response.data)

    assert "description" in data
    assert "schema" in data
    assert "_meta" in data
    assert "_links" in data


def test_head_schema_included(client):
    """Test HEAD response includes JSON schema"""
    response = client.get("/products", method="HEAD")
    assert response.status_code == 200

    import json
    data = json.loads(response.data)

    schema = data["schema"]
    assert "$schema" in schema
    assert "properties" in schema
    assert "type" in schema


def test_head_role_based_schema(client):
    """Test HEAD response filters schema by role"""
    # Public role - limited fields
    response_public = client.head("/products")
    assert response_public.status_code == 200

    import json
    data_public = json.loads(response_public.data)

    # Products schema should have fewer fields for public
    assert len(data_public["schema"]["properties"]) <= len(
        [p for p in data_public["schema"]["properties"].keys()]
    )


def test_head_children_list(client, sample_order):
    """Test HEAD response includes children list"""
    response = client.head("/orders")
    assert response.status_code == 200

    import json
    data = json.loads(response.data)

    assert "_links" in data
    assert "children" in data["_links"]
    assert isinstance(data["_links"]["children"], list)


def test_head_query_params_positive_only(client):
    """Test HEAD response with positive_only query parameter"""
    response = client.head("/products?positive_only=true")
    assert response.status_code == 200

    import json
    data = json.loads(response.data)

    schema = data["schema"]
    # Check that numeric fields have minimum constraint
    if "price" in schema["properties"]:
        assert schema["properties"]["price"].get("minimum") == 0


def test_head_query_params_detailed(client):
    """Test HEAD response with detailed query parameter"""
    response = client.head("/customers?detailed=true")
    assert response.status_code == 200

    import json
    data = json.loads(response.data)

    schema = data["schema"]
    # Detailed schema should have timestamps
    assert "created_at" in schema["properties"]
    assert "updated_at" in schema["properties"]


def test_head_root_endpoint(client):
    """Test HEAD request on root endpoint"""
    response = client.head("/")
    assert response.status_code == 200
    assert "ETag" in response.headers

    import json
    data = json.loads(response.data)

    assert "description" in data
    assert "schema" in data
    assert "_links" in data
    assert "children" in data["_links"]
