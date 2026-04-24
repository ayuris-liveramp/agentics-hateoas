"""Tests for schema generation"""

import pytest
from leaf_api.schemas.order_schema import OrderSchemaGenerator
from leaf_api.schemas.customer_schema import CustomerSchemaGenerator
from leaf_api.schemas.product_schema import ProductSchemaGenerator


class TestOrderSchema:
    def test_order_schema_public_role(self):
        """Test order schema for public role"""
        schema = OrderSchemaGenerator.get_collection_schema("public")
        assert schema["title"] == "Order"
        assert "id" in schema["properties"]
        assert "status" in schema["properties"]
        # Admin-only fields should not be present
        assert "cost" not in schema["properties"]

    def test_order_schema_admin_role(self):
        """Test order schema for admin role"""
        schema = OrderSchemaGenerator.get_collection_schema("admin")
        assert schema["title"] == "Order"
        assert "id" in schema["properties"]
        assert "cost" in schema["properties"]
        assert schema["properties"]["cost"]["type"] == "number"

    def test_order_schema_positive_only(self):
        """Test order schema with positive_only constraint"""
        schema = OrderSchemaGenerator.get_collection_schema(
            "user",  # user role has quantity and total_price
            {"positive_only": "true"},
        )
        assert schema["properties"]["quantity"]["minimum"] == 0
        assert schema["properties"]["total_price"]["minimum"] == 0

    def test_order_schema_detailed(self):
        """Test order schema with detailed query parameter"""
        schema = OrderSchemaGenerator.get_collection_schema(
            "public",
            {"detailed": "true"},
        )
        assert "created_at" in schema["properties"]
        assert "updated_at" in schema["properties"]

    def test_order_schema_summary(self):
        """Test order schema with summary query parameter"""
        schema = OrderSchemaGenerator.get_collection_schema(
            "public",
            {"summary": "true"},
        )
        # Summary should only include required fields
        for prop in schema["properties"].keys():
            assert prop in schema["required"]


class TestCustomerSchema:
    def test_customer_schema_public_role(self):
        """Test customer schema for public role"""
        schema = CustomerSchemaGenerator.get_collection_schema("public")
        assert schema["title"] == "Customer"
        assert "id" in schema["properties"]
        assert "name" in schema["properties"]
        # Public role only sees id and name

    def test_customer_schema_user_role(self):
        """Test customer schema for user role"""
        schema = CustomerSchemaGenerator.get_collection_schema("user")
        assert "id" in schema["properties"]
        assert "email" in schema["properties"]
        assert schema["properties"]["email"]["format"] == "email"

    def test_customer_schema_name_min_length(self):
        """Test customer schema has name constraints"""
        schema = CustomerSchemaGenerator.get_collection_schema("public")
        assert schema["properties"]["name"]["minLength"] == 1


class TestProductSchema:
    def test_product_schema_public_role(self):
        """Test product schema for public role"""
        schema = ProductSchemaGenerator.get_collection_schema("public")
        assert schema["title"] == "Product"
        assert "id" in schema["properties"]
        assert "price" in schema["properties"]
        # Admin-only fields should not be present
        assert "cost" not in schema["properties"]

    def test_product_schema_admin_role(self):
        """Test product schema for admin role"""
        schema = ProductSchemaGenerator.get_collection_schema("admin")
        assert "cost" in schema["properties"]

    def test_product_schema_price_minimum(self):
        """Test product schema has price constraints"""
        schema = ProductSchemaGenerator.get_collection_schema("public")
        assert schema["properties"]["price"]["minimum"] == 0
        # Public role only sees id, name, price

    def test_product_schema_user_role_stock(self):
        """Test product schema for user role includes stock"""
        schema = ProductSchemaGenerator.get_collection_schema("user")
        assert "stock_quantity" in schema["properties"]
        assert schema["properties"]["stock_quantity"]["minimum"] == 0
