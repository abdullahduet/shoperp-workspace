"""
Unit tests for src/modules/products/service.py

All repository calls are mocked. Tests verify business logic only.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.exceptions import ConflictError, NotFoundError
from src.modules.products.repository import ProductRepository
from src.modules.products.schemas import ProductCreate, ProductResponse, ProductUpdate
from src.modules.products.service import PaginatedProducts, ProductService


def _make_fake_product(
    *,
    product_id: str = "product-uuid-1",
    name: str = "Test Product",
    sku: str = "SKU-001",
    barcode: str | None = None,
    category_id: str | None = None,
    description: str | None = None,
    unit_price: int = 1000,
    cost_price: int = 800,
    tax_rate: Decimal = Decimal("0.00"),
    stock_quantity: int = 10,
    min_stock_level: int = 5,
    unit_of_measure: str = "pcs",
    image_url: str | None = None,
    is_active: bool = True,
    created_at: datetime | None = None,
    deleted_at: datetime | None = None,
) -> MagicMock:
    """Create a MagicMock that mimics a Prisma Product model."""
    product = MagicMock()
    product.id = product_id
    product.name = name
    product.sku = sku
    product.barcode = barcode
    product.categoryId = category_id
    product.description = description
    product.unitPrice = unit_price
    product.costPrice = cost_price
    product.taxRate = tax_rate
    product.stockQuantity = stock_quantity
    product.minStockLevel = min_stock_level
    product.unitOfMeasure = unit_of_measure
    product.imageUrl = image_url
    product.isActive = is_active
    product.createdAt = created_at or datetime(2024, 1, 1, tzinfo=timezone.utc)
    product.deletedAt = deleted_at
    return product


def _make_service() -> tuple[ProductService, AsyncMock]:
    repo = AsyncMock(spec=ProductRepository)
    service = ProductService(repo)
    return service, repo


# ---------------------------------------------------------------------------
# list_products
# ---------------------------------------------------------------------------

class TestListProducts:
    @pytest.mark.asyncio
    async def test_returns_paginated_products(self):
        service, repo = _make_service()
        fake_product = _make_fake_product()
        repo.find_paginated.return_value = ([fake_product], 1)

        result = await service.list_products(
            page=1, limit=20, search=None, category_id=None,
            is_active=None, sort="name", order="asc",
        )

        assert isinstance(result, PaginatedProducts)
        assert result.total == 1
        assert len(result.items) == 1
        assert isinstance(result.items[0], ProductResponse)

    @pytest.mark.asyncio
    async def test_calls_repo_with_correct_skip_and_take(self):
        service, repo = _make_service()
        repo.find_paginated.return_value = ([], 0)

        await service.list_products(
            page=3, limit=10, search=None, category_id=None,
            is_active=None, sort="name", order="asc",
        )

        call_kwargs = repo.find_paginated.call_args.kwargs
        assert call_kwargs["skip"] == 20  # (3-1)*10
        assert call_kwargs["take"] == 10

    @pytest.mark.asyncio
    async def test_passes_search_filter_when_provided(self):
        service, repo = _make_service()
        repo.find_paginated.return_value = ([], 0)

        await service.list_products(
            page=1, limit=20, search="widget", category_id=None,
            is_active=None, sort="name", order="asc",
        )

        call_kwargs = repo.find_paginated.call_args.kwargs
        where = call_kwargs["where"]
        assert "OR" in where

    @pytest.mark.asyncio
    async def test_does_not_pass_none_filters_to_where(self):
        service, repo = _make_service()
        repo.find_paginated.return_value = ([], 0)

        await service.list_products(
            page=1, limit=20, search=None, category_id=None,
            is_active=None, sort="name", order="asc",
        )

        call_kwargs = repo.find_paginated.call_args.kwargs
        where = call_kwargs["where"]
        assert "OR" not in where
        assert "categoryId" not in where
        assert "isActive" not in where


# ---------------------------------------------------------------------------
# get_low_stock
# ---------------------------------------------------------------------------

class TestGetLowStock:
    @pytest.mark.asyncio
    async def test_returns_products_below_min_stock(self):
        service, repo = _make_service()
        low_product = _make_fake_product(stock_quantity=2, min_stock_level=5)
        repo.find_low_stock.return_value = [low_product]

        result = await service.get_low_stock()

        assert len(result) == 1
        assert isinstance(result[0], ProductResponse)

    @pytest.mark.asyncio
    async def test_returns_empty_when_all_stock_adequate(self):
        service, repo = _make_service()
        repo.find_low_stock.return_value = []

        result = await service.get_low_stock()

        assert result == []


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------

class TestGetById:
    @pytest.mark.asyncio
    async def test_returns_product_response_when_found(self):
        service, repo = _make_service()
        fake_product = _make_fake_product()
        repo.find_by_id.return_value = fake_product

        result = await service.get_by_id("product-uuid-1")

        assert isinstance(result, ProductResponse)
        assert result.sku == fake_product.sku

    @pytest.mark.asyncio
    async def test_raises_not_found_when_product_missing(self):
        service, repo = _make_service()
        repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.get_by_id("nonexistent-id")


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

class TestCreate:
    @pytest.mark.asyncio
    async def test_creates_and_returns_product_response(self):
        service, repo = _make_service()
        fake_product = _make_fake_product()
        repo.find_by_sku.return_value = None
        repo.create.return_value = fake_product

        result = await service.create(
            ProductCreate(name="Test Product", sku="SKU-001")
        )

        assert isinstance(result, ProductResponse)
        repo.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_conflict_on_duplicate_sku(self):
        service, repo = _make_service()
        existing = _make_fake_product()
        repo.find_by_sku.return_value = existing

        with pytest.raises(ConflictError):
            await service.create(
                ProductCreate(name="Another Product", sku="SKU-001")
            )

    @pytest.mark.asyncio
    async def test_raises_conflict_on_duplicate_barcode(self):
        service, repo = _make_service()
        repo.find_by_sku.return_value = None
        existing = _make_fake_product(barcode="BAR-001")
        repo.find_by_barcode.return_value = existing

        with pytest.raises(ConflictError):
            await service.create(
                ProductCreate(name="New Product", sku="SKU-NEW", barcode="BAR-001")
            )

    @pytest.mark.asyncio
    async def test_does_not_check_barcode_when_none(self):
        service, repo = _make_service()
        repo.find_by_sku.return_value = None
        repo.create.return_value = _make_fake_product()

        await service.create(ProductCreate(name="Product", sku="NEW-SKU"))

        repo.find_by_barcode.assert_not_awaited()


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

class TestUpdate:
    @pytest.mark.asyncio
    async def test_updates_and_returns_product_response(self):
        service, repo = _make_service()
        existing = _make_fake_product(product_id="pid")
        updated = _make_fake_product(product_id="pid", name="Updated Name")
        repo.find_by_id.return_value = existing
        repo.find_by_sku.return_value = None
        repo.update.return_value = updated

        result = await service.update("pid", ProductUpdate(name="Updated Name"))

        assert isinstance(result, ProductResponse)
        repo.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_not_found_when_product_missing(self):
        service, repo = _make_service()
        repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.update("nonexistent-id", ProductUpdate(name="X"))

    @pytest.mark.asyncio
    async def test_raises_conflict_when_sku_taken_by_other_product(self):
        service, repo = _make_service()
        existing = _make_fake_product(product_id="pid-1", sku="SKU-1")
        other = _make_fake_product(product_id="pid-2", sku="SKU-2")
        repo.find_by_id.return_value = existing
        repo.find_by_sku.return_value = other  # different product owns this SKU

        with pytest.raises(ConflictError):
            await service.update("pid-1", ProductUpdate(sku="SKU-2"))


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

class TestDelete:
    @pytest.mark.asyncio
    async def test_soft_deletes_product(self):
        service, repo = _make_service()
        existing = _make_fake_product()
        repo.find_by_id.return_value = existing
        repo.soft_delete.return_value = existing

        await service.delete("product-uuid-1")

        repo.soft_delete.assert_awaited_once_with("product-uuid-1")

    @pytest.mark.asyncio
    async def test_raises_not_found_when_product_missing(self):
        service, repo = _make_service()
        repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.delete("nonexistent-id")


# ---------------------------------------------------------------------------
# import_from_csv
# ---------------------------------------------------------------------------

class TestImportFromCSV:
    @pytest.mark.asyncio
    async def test_imports_two_valid_rows(self):
        service, repo = _make_service()
        repo.find_by_sku.return_value = None
        repo.create.return_value = _make_fake_product()

        csv_content = b"name,sku\nProduct A,SKU-A\nProduct B,SKU-B\n"
        result = await service.import_from_csv(csv_content)

        assert result["created"] == 2
        assert result["skipped"] == 0
        assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_skips_row_with_duplicate_sku(self):
        service, repo = _make_service()
        existing = _make_fake_product(sku="SKU-DUP")
        repo.find_by_sku.return_value = existing  # always returns existing

        csv_content = b"name,sku\nDuplicate Product,SKU-DUP\n"
        result = await service.import_from_csv(csv_content)

        assert result["created"] == 0
        assert result["skipped"] == 1
        assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_records_error_for_missing_name(self):
        service, repo = _make_service()
        repo.find_by_sku.return_value = None

        csv_content = b"name,sku\n,SKU-001\n"
        result = await service.import_from_csv(csv_content)

        assert result["created"] == 0
        assert result["skipped"] == 0
        assert len(result["errors"]) == 1
        assert result["errors"][0]["row"] == 2

    @pytest.mark.asyncio
    async def test_records_error_for_missing_sku(self):
        service, repo = _make_service()
        repo.find_by_sku.return_value = None

        csv_content = b"name,sku\nProduct Without SKU,\n"
        result = await service.import_from_csv(csv_content)

        assert result["created"] == 0
        assert len(result["errors"]) == 1
