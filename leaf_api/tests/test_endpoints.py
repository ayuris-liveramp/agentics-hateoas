"""Tests for API endpoints"""

import pytest


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.get_json()
    assert "title" in data
    assert "_links" in data


def test_agentics_robots_endpoint(client):
    """Test .well-known/agentics-robots.txt endpoint"""
    response = client.get("/.well-known/agentics-robots.txt")
    assert response.status_code == 200
    data = response.get_json()
    assert "conformsTo" in data
    assert "crawlDelay" in data


def test_list_orders(client, sample_order):
    """Test listing orders"""
    response = client.get("/orders")
    assert response.status_code == 200
    data = response.get_json()
    assert "items" in data
    assert "_meta" in data


def test_get_order(client, sample_order):
    """Test getting a specific order"""
    response = client.get(f"/orders/{sample_order['id']}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == sample_order["id"]


def test_list_customers(client, sample_customer):
    """Test listing customers"""
    response = client.get("/customers")
    assert response.status_code == 200
    data = response.get_json()
    assert "items" in data


def test_get_customer(client, sample_customer):
    """Test getting a specific customer"""
    response = client.get(f"/customers/{sample_customer['id']}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == sample_customer["name"]


def test_list_products(client, sample_product):
    """Test listing products"""
    response = client.get("/products")
    assert response.status_code == 200
    data = response.get_json()
    assert "items" in data


def test_get_product(client, sample_product):
    """Test getting a specific product"""
    response = client.get(f"/products/{sample_product['id']}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == sample_product["name"]
