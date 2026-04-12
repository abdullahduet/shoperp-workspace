"""
Unit tests for src/modules/products/schemas.py

Verifies Pydantic validation rules on ProductCreate.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.modules.products.schemas import ProductCreate


class TestProductCreate:
    def test_valid_product_create_succeeds(self):
        product = ProductCreate(name="Widget", sku="WGT-001")
        assert product.name == "Widget"
        assert product.sku == "WGT-001"

    def test_missing_name_raises_validation_error(self):
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(sku="WGT-001")  # type: ignore[call-arg]
        errors = exc_info.value.errors()
        fields = [e["loc"][0] for e in errors]
        assert "name" in fields

    def test_missing_sku_raises_validation_error(self):
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(name="Widget")  # type: ignore[call-arg]
        errors = exc_info.value.errors()
        fields = [e["loc"][0] for e in errors]
        assert "sku" in fields

    def test_negative_unit_price_raises_validation_error(self):
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(name="Widget", sku="WGT-001", unit_price=-1)
        errors = exc_info.value.errors()
        fields = [e["loc"][0] for e in errors]
        assert "unit_price" in fields

    def test_negative_cost_price_raises_validation_error(self):
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(name="Widget", sku="WGT-001", cost_price=-100)
        errors = exc_info.value.errors()
        fields = [e["loc"][0] for e in errors]
        assert "cost_price" in fields

    def test_zero_prices_are_valid(self):
        product = ProductCreate(name="Widget", sku="WGT-001", unit_price=0, cost_price=0)
        assert product.unit_price == 0
        assert product.cost_price == 0

    def test_defaults_are_applied(self):
        product = ProductCreate(name="Widget", sku="WGT-001")
        assert product.unit_price == 0
        assert product.cost_price == 0
        assert product.tax_rate == 0.0
        assert product.stock_quantity == 0
        assert product.min_stock_level == 0
        assert product.unit_of_measure == "pcs"
        assert product.is_active is True

    def test_tax_rate_above_100_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ProductCreate(name="Widget", sku="WGT-001", tax_rate=101.0)

    def test_negative_tax_rate_raises_validation_error(self):
        with pytest.raises(ValidationError):
            ProductCreate(name="Widget", sku="WGT-001", tax_rate=-1.0)
