"""
Unit tests for src/modules/inventory/service.py

All repository calls are mocked. Tests verify business logic only.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.inventory.repository import InventoryRepository
from src.modules.inventory.schemas import StockMovementResponse, ValuationResponse
from src.modules.inventory.service import InventoryService, PaginatedMovements


def _make_fake_product(stock_quantity=100, cost_price=5000, is_active=True):
    p = MagicMock()
    p.id = "prod-uuid"
    p.name = "Test Product"
    p.sku = "SKU-001"
    p.stockQuantity = stock_quantity
    p.costPrice = cost_price
    p.isActive = is_active
    p.deletedAt = None
    return p


def _make_fake_movement(product=None):
    m = MagicMock()
    m.id = "mov-uuid"
    m.productId = "prod-uuid"
    m.product = product or _make_fake_product()
    m.movementType = "adjustment"
    m.quantity = 10
    m.stockBefore = 100
    m.stockAfter = 110
    m.referenceType = "manual_adjustment"
    m.referenceId = None
    m.notes = "Test"
    m.performedBy = "user-uuid"
    m.createdAt = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return m


def _make_service() -> tuple[InventoryService, AsyncMock]:
    repo = AsyncMock(spec=InventoryRepository)
    service = InventoryService(repo)
    return service, repo


# ---------------------------------------------------------------------------
# list_movements
# ---------------------------------------------------------------------------

class TestListMovements:
    @pytest.mark.asyncio
    async def test_returns_paginated_movements(self):
        service, repo = _make_service()
        fake_movement = _make_fake_movement()
        repo.find_movements.return_value = ([fake_movement], 1)

        result = await service.list_movements(
            page=1, limit=20, product_id=None, movement_type=None,
            start_date=None, end_date=None,
        )

        assert isinstance(result, PaginatedMovements)
        assert result.total == 1
        assert len(result.items) == 1
        assert isinstance(result.items[0], StockMovementResponse)

    @pytest.mark.asyncio
    async def test_calls_repo_with_correct_skip_and_take(self):
        service, repo = _make_service()
        repo.find_movements.return_value = ([], 0)

        await service.list_movements(
            page=3, limit=10, product_id=None, movement_type=None,
            start_date=None, end_date=None,
        )

        call_kwargs = repo.find_movements.call_args.kwargs
        assert call_kwargs["skip"] == 20  # (3-1)*10
        assert call_kwargs["take"] == 10

    @pytest.mark.asyncio
    async def test_filters_by_product_id_when_provided(self):
        service, repo = _make_service()
        repo.find_movements.return_value = ([], 0)

        await service.list_movements(
            page=1, limit=20, product_id="prod-uuid", movement_type=None,
            start_date=None, end_date=None,
        )

        call_kwargs = repo.find_movements.call_args.kwargs
        assert call_kwargs["where"]["productId"] == "prod-uuid"

    @pytest.mark.asyncio
    async def test_filters_by_movement_type_when_provided(self):
        service, repo = _make_service()
        repo.find_movements.return_value = ([], 0)

        await service.list_movements(
            page=1, limit=20, product_id=None, movement_type="adjustment",
            start_date=None, end_date=None,
        )

        call_kwargs = repo.find_movements.call_args.kwargs
        assert call_kwargs["where"]["movementType"] == "adjustment"

    @pytest.mark.asyncio
    async def test_applies_date_range_filter_when_provided(self):
        service, repo = _make_service()
        repo.find_movements.return_value = ([], 0)

        await service.list_movements(
            page=1, limit=20, product_id=None, movement_type=None,
            start_date="2026-01-01", end_date="2026-01-31",
        )

        call_kwargs = repo.find_movements.call_args.kwargs
        where = call_kwargs["where"]
        assert "createdAt" in where
        assert "gte" in where["createdAt"]
        assert "lt" in where["createdAt"]


# ---------------------------------------------------------------------------
# adjust
# ---------------------------------------------------------------------------

class TestAdjust:
    @pytest.mark.asyncio
    async def test_positive_adjustment_succeeds(self):
        service, repo = _make_service()
        product = _make_fake_product(stock_quantity=100)
        movement = _make_fake_movement(product=product)
        repo.find_product_by_id.return_value = product
        repo.create_adjustment.return_value = movement

        result = await service.adjust(
            product_id="prod-uuid",
            quantity=10,
            notes="Restock",
            performed_by="user-uuid",
        )

        assert isinstance(result, StockMovementResponse)
        repo.create_adjustment.assert_awaited_once_with(
            product_id="prod-uuid",
            quantity=10,
            stock_before=100,
            stock_after=110,
            notes="Restock",
            performed_by="user-uuid",
        )

    @pytest.mark.asyncio
    async def test_negative_adjustment_succeeds(self):
        service, repo = _make_service()
        product = _make_fake_product(stock_quantity=100)
        movement = _make_fake_movement(product=product)
        movement.quantity = -10
        movement.stockBefore = 100
        movement.stockAfter = 90
        repo.find_product_by_id.return_value = product
        repo.create_adjustment.return_value = movement

        result = await service.adjust(
            product_id="prod-uuid",
            quantity=-10,
            notes="Sale correction",
            performed_by="user-uuid",
        )

        assert isinstance(result, StockMovementResponse)
        repo.create_adjustment.assert_awaited_once_with(
            product_id="prod-uuid",
            quantity=-10,
            stock_before=100,
            stock_after=90,
            notes="Sale correction",
            performed_by="user-uuid",
        )

    @pytest.mark.asyncio
    async def test_rejected_when_would_go_negative(self):
        service, repo = _make_service()
        product = _make_fake_product(stock_quantity=5)
        repo.find_product_by_id.return_value = product

        with pytest.raises(ValidationError):
            await service.adjust(
                product_id="prod-uuid",
                quantity=-10,
                notes=None,
                performed_by="user-uuid",
            )

        repo.create_adjustment.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_raises_not_found_for_missing_product(self):
        service, repo = _make_service()
        repo.find_product_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.adjust(
                product_id="nonexistent-id",
                quantity=10,
                notes=None,
                performed_by="user-uuid",
            )

    @pytest.mark.asyncio
    async def test_raises_validation_for_inactive_product(self):
        service, repo = _make_service()
        product = _make_fake_product(is_active=False)
        repo.find_product_by_id.return_value = product

        with pytest.raises(ValidationError):
            await service.adjust(
                product_id="prod-uuid",
                quantity=10,
                notes=None,
                performed_by="user-uuid",
            )


# ---------------------------------------------------------------------------
# get_valuation
# ---------------------------------------------------------------------------

class TestGetValuation:
    @pytest.mark.asyncio
    async def test_valuation_sums_correctly(self):
        service, repo = _make_service()
        p1 = MagicMock(); p1.stockQuantity = 10; p1.costPrice = 5000
        p2 = MagicMock(); p2.stockQuantity = 5; p2.costPrice = 3000
        repo.get_active_products_for_valuation.return_value = [p1, p2]

        result = await service.get_valuation()

        assert result.total_value == 10 * 5000 + 5 * 3000  # 65000
        assert result.product_count == 2
        assert result.currency == "BDT"

    @pytest.mark.asyncio
    async def test_valuation_zero_when_no_active_products(self):
        service, repo = _make_service()
        repo.get_active_products_for_valuation.return_value = []

        result = await service.get_valuation()

        assert result.total_value == 0
        assert result.product_count == 0
