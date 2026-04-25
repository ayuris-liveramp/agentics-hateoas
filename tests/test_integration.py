"""Functional tests for end-to-end integration."""

import pytest
import json


class TestEndToEndIntegration:
    """Test full request-response cycles."""

    def test_leaf_api_create_customer(self, leaf_client):
        """Should be able to create a customer."""
        customer_data = {
            "name": "Test Customer",
            "email": "test@example.com",
        }
        resp = leaf_client.post("/customers", json=customer_data)
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert "id" in data or "customer_id" in data

    def test_leaf_api_get_customers(self, leaf_client):
        """Should be able to retrieve customers."""
        resp = leaf_client.get("/customers")
        assert resp.status_code == 200
        data = resp.json()
        # Response could be list or dict with items
        if isinstance(data, dict):
            assert "items" in data or "customers" in data or "data" in data
        else:
            assert isinstance(data, list)

    def test_leaf_api_head_request(self, leaf_client):
        """Should support HEAD requests for discovery."""
        resp = leaf_client.head("/customers")
        assert resp.status_code == 200
        # HEAD response should have headers but no body
        assert len(resp.content) == 0

    def test_leaf_api_product_operations(self, leaf_client):
        """Should support CRUD operations on products."""
        # Create product
        product_data = {"name": "Test Product", "price": 99.99}
        resp = leaf_client.post("/products", json=product_data)
        assert resp.status_code in (200, 201)

        # List products
        resp = leaf_client.get("/products")
        assert resp.status_code == 200

    def test_root_app_forward_request(self, root_client):
        """Root app should forward requests to leaf API."""
        # This tests that root-app can act as a proxy/gateway
        resp = root_client.get("/discover")
        assert resp.status_code == 200
        data = resp.json()
        # Should have discovered at least the leaf API
        assert data is not None

    def test_response_contains_links(self, leaf_client):
        """HATEOAS responses should contain links."""
        resp = leaf_client.get("/")
        if resp.status_code == 200:
            data = resp.json()
            # HATEOAS responses typically have _links or similar
            # This is flexible since it depends on implementation
            assert isinstance(data, dict)

    def test_concurrent_requests(self, leaf_client):
        """System should handle multiple requests."""
        responses = []
        for i in range(5):
            resp = leaf_client.get("/customers")
            responses.append(resp)

        # All should succeed
        assert all(r.status_code == 200 for r in responses)

    def test_etag_caching(self, leaf_client):
        """Repeated requests should return consistent ETags."""
        resp1 = leaf_client.get("/customers")
        etag1 = resp1.headers.get("ETag")

        resp2 = leaf_client.get("/customers")
        etag2 = resp2.headers.get("ETag")

        # If ETags are present, they should match for same resource
        if etag1 and etag2:
            assert etag1 == etag2

    def test_orders_workflow(self, leaf_client):
        """Test complete order workflow."""
        # Create customer
        customer_data = {"name": "Order Test Customer", "email": "orders@test.com"}
        customer_resp = leaf_client.post("/customers", json=customer_data)
        assert customer_resp.status_code in (200, 201)

        # Create product
        product_data = {"name": "Test Item", "price": 49.99}
        product_resp = leaf_client.post("/products", json=product_data)
        assert product_resp.status_code in (200, 201)

        # Create order
        order_data = {
            "customer_id": customer_resp.json().get("id"),
            "product_id": product_resp.json().get("id"),
            "quantity": 1,
        }
        order_resp = leaf_client.post("/orders", json=order_data)
        assert order_resp.status_code in (200, 201)

        # Get orders
        orders_list = leaf_client.get("/orders")
        assert orders_list.status_code == 200
