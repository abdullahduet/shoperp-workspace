"""
Unit tests for src/modules/promotions/service.py

All repository calls are mocked. Tests verify business logic only.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.promotions.repository import PromotionRepository
from src.modules.promotions.schemas import (
    PromotionCreate,
    PromotionResponse,
    PromotionUpdate,
)
from src.modules.promotions.service import PromotionService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_pp(product_id: str = "prod-uuid-1") -> MagicMock:
    """Create a MagicMock that mimics a Prisma PromotionProduct model."""
    pp = MagicMock()
    pp.productId = product_id
    return pp


def _make_fake_promotion(
    *,
    promotion_id: str = "promo-uuid-1",
    name: str = "Summer Sale",
    promo_type: str = "percentage",
    value: int = 20,
    applies_to: str = "all",
    is_active: bool = True,
    min_purchase_amount: int = 0,
    product_ids: list[str] | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> MagicMock:
    """Create a MagicMock that mimics a Prisma Promotion model with relations."""
    promotion = MagicMock()
    promotion.id = promotion_id
    promotion.name = name
    promotion.type = promo_type
    promotion.value = value
    promotion.appliesTo = applies_to
    promotion.isActive = is_active
    promotion.minPurchaseAmount = min_purchase_amount
    promotion.startDate = start_date or datetime(2026, 6, 1, tzinfo=timezone.utc)
    promotion.endDate = end_date or datetime(2026, 6, 30, tzinfo=timezone.utc)
    promotion.createdAt = datetime(2026, 4, 11, tzinfo=timezone.utc)
    promotion.deletedAt = None
    if product_ids is not None:
        promotion.promotionProducts = [_make_fake_pp(pid) for pid in product_ids]
    else:
        promotion.promotionProducts = []
    return promotion


def _make_service() -> tuple[PromotionService, AsyncMock]:
    repo = AsyncMock(spec=PromotionRepository)
    service = PromotionService(repo)
    return service, repo


# ---------------------------------------------------------------------------
# TestCreate
# ---------------------------------------------------------------------------

class TestCreate:
    @pytest.mark.asyncio
    async def test_raises_validation_error_if_end_date_before_start_date(self):
        service, _repo = _make_service()

        with pytest.raises(ValidationError, match="end_date must be after start_date"):
            await service.create(
                PromotionCreate(
                    name="Bad Promo",
                    type="percentage",
                    value=10,
                    start_date="2026-06-30T00:00:00+00:00",
                    end_date="2026-06-01T00:00:00+00:00",
                )
            )

    @pytest.mark.asyncio
    async def test_raises_validation_error_if_specific_applies_to_has_no_product_ids(self):
        service, _repo = _make_service()

        with pytest.raises(ValidationError, match="product_ids must not be empty"):
            await service.create(
                PromotionCreate(
                    name="Specific Promo",
                    type="fixed",
                    value=500,
                    start_date="2026-06-01T00:00:00+00:00",
                    end_date="2026-06-30T00:00:00+00:00",
                    applies_to="specific",
                    product_ids=[],
                )
            )

    @pytest.mark.asyncio
    async def test_creates_promotion_with_products(self):
        service, repo = _make_service()
        fake_promo = _make_fake_promotion(product_ids=["prod-1", "prod-2"])
        repo.create_with_products.return_value = fake_promo

        result = await service.create(
            PromotionCreate(
                name="Summer Sale",
                type="percentage",
                value=20,
                start_date="2026-06-01T00:00:00+00:00",
                end_date="2026-06-30T00:00:00+00:00",
                applies_to="specific",
                product_ids=["prod-1", "prod-2"],
            )
        )

        repo.create_with_products.assert_awaited_once()
        call_args = repo.create_with_products.call_args
        promo_data = call_args.args[0]
        product_ids_arg = call_args.args[1]
        assert promo_data["name"] == "Summer Sale"
        assert promo_data["type"] == "percentage"
        assert isinstance(promo_data["startDate"], datetime)
        assert isinstance(promo_data["endDate"], datetime)
        assert product_ids_arg == ["prod-1", "prod-2"]
        assert isinstance(result, PromotionResponse)

    @pytest.mark.asyncio
    async def test_creates_promotion_without_products(self):
        service, repo = _make_service()
        fake_promo = _make_fake_promotion(product_ids=[])
        repo.create_with_products.return_value = fake_promo

        result = await service.create(
            PromotionCreate(
                name="All Products Sale",
                type="fixed",
                value=1000,
                start_date="2026-06-01T00:00:00+00:00",
                end_date="2026-06-30T00:00:00+00:00",
                applies_to="all",
                product_ids=[],
            )
        )

        call_args = repo.create_with_products.call_args
        assert call_args.args[1] == []
        assert isinstance(result, PromotionResponse)


# ---------------------------------------------------------------------------
# TestUpdate
# ---------------------------------------------------------------------------

class TestUpdate:
    @pytest.mark.asyncio
    async def test_raises_not_found_if_missing(self):
        service, repo = _make_service()
        repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.update("nonexistent-id", PromotionUpdate(name="New Name"))

    @pytest.mark.asyncio
    async def test_updates_fields_and_passes_product_ids_to_repo(self):
        service, repo = _make_service()
        fake_promo = _make_fake_promotion(product_ids=["prod-1"])
        updated_promo = _make_fake_promotion(name="Updated", product_ids=["prod-2"])
        repo.find_by_id.return_value = fake_promo
        repo.update_with_products.return_value = updated_promo

        result = await service.update(
            "promo-uuid-1",
            PromotionUpdate(name="Updated", product_ids=["prod-2"]),
        )

        call_args = repo.update_with_products.call_args
        promo_data = call_args.args[1]
        product_ids_arg = call_args.args[2]
        assert promo_data["name"] == "Updated"
        assert product_ids_arg == ["prod-2"]
        assert isinstance(result, PromotionResponse)

    @pytest.mark.asyncio
    async def test_passes_none_product_ids_when_not_provided(self):
        service, repo = _make_service()
        fake_promo = _make_fake_promotion(product_ids=[])
        repo.find_by_id.return_value = fake_promo
        repo.update_with_products.return_value = fake_promo

        await service.update("promo-uuid-1", PromotionUpdate(name="Renamed"))

        call_args = repo.update_with_products.call_args
        product_ids_arg = call_args.args[2]
        assert product_ids_arg is None


# ---------------------------------------------------------------------------
# TestList
# ---------------------------------------------------------------------------

class TestList:
    @pytest.mark.asyncio
    async def test_returns_paginated_promotions(self):
        service, repo = _make_service()
        fake_promos = [_make_fake_promotion()]
        repo.find_paginated.return_value = (fake_promos, 1)

        result = await service.list(page=1, limit=20, is_active=None, type=None)

        assert result.total == 1
        assert len(result.items) == 1
        assert isinstance(result.items[0], PromotionResponse)

    @pytest.mark.asyncio
    async def test_applies_is_active_filter(self):
        service, repo = _make_service()
        repo.find_paginated.return_value = ([], 0)

        await service.list(page=1, limit=20, is_active=True, type=None)

        call_args = repo.find_paginated.call_args
        where = call_args.args[2]
        assert where.get("isActive") is True

    @pytest.mark.asyncio
    async def test_applies_type_filter(self):
        service, repo = _make_service()
        repo.find_paginated.return_value = ([], 0)

        await service.list(page=1, limit=20, is_active=None, type="bogo")

        call_args = repo.find_paginated.call_args
        where = call_args.args[2]
        assert where.get("type") == "bogo"


# ---------------------------------------------------------------------------
# TestGetById
# ---------------------------------------------------------------------------

class TestGetById:
    @pytest.mark.asyncio
    async def test_returns_promotion_response(self):
        service, repo = _make_service()
        fake_promo = _make_fake_promotion()
        repo.find_by_id.return_value = fake_promo

        result = await service.get_by_id("promo-uuid-1")

        assert isinstance(result, PromotionResponse)
        assert result.id == "promo-uuid-1"

    @pytest.mark.asyncio
    async def test_raises_not_found_if_missing(self):
        service, repo = _make_service()
        repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.get_by_id("nonexistent-id")


# ---------------------------------------------------------------------------
# TestGetActive
# ---------------------------------------------------------------------------

class TestGetActive:
    @pytest.mark.asyncio
    async def test_returns_list_of_promotion_responses(self):
        service, repo = _make_service()
        fake_promos = [_make_fake_promotion(), _make_fake_promotion(promotion_id="promo-uuid-2")]
        repo.find_active.return_value = fake_promos

        result = await service.get_active()

        assert len(result) == 2
        assert all(isinstance(p, PromotionResponse) for p in result)

    @pytest.mark.asyncio
    async def test_passes_utc_datetime_to_repo(self):
        service, repo = _make_service()
        repo.find_active.return_value = []

        await service.get_active()

        call_args = repo.find_active.call_args
        now_arg = call_args.args[0]
        assert isinstance(now_arg, datetime)
        assert now_arg.tzinfo is not None


# ---------------------------------------------------------------------------
# TestDelete
# ---------------------------------------------------------------------------

class TestDelete:
    @pytest.mark.asyncio
    async def test_soft_deletes_promotion(self):
        service, repo = _make_service()
        fake_promo = _make_fake_promotion()
        repo.find_by_id.return_value = fake_promo

        await service.delete("promo-uuid-1")

        repo.soft_delete.assert_awaited_once_with("promo-uuid-1")

    @pytest.mark.asyncio
    async def test_raises_not_found_if_missing(self):
        service, repo = _make_service()
        repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.delete("nonexistent-id")


# ---------------------------------------------------------------------------
# TestCalculateDiscount
# ---------------------------------------------------------------------------

class TestCalculateDiscount:
    def _make_promotion(
        self,
        *,
        promo_type: str = "percentage",
        value: int = 20,
        min_purchase_amount: int = 0,
        applies_to: str = "all",
        product_ids: list[str] | None = None,
    ) -> MagicMock:
        promo = MagicMock()
        promo.type = promo_type
        promo.value = value
        promo.minPurchaseAmount = min_purchase_amount
        promo.appliesTo = applies_to
        if product_ids is not None:
            promo.promotionProducts = [_make_fake_pp(pid) for pid in product_ids]
        else:
            promo.promotionProducts = []
        return promo

    def test_percentage_discount_correct(self):
        service, _ = _make_service()
        promo = self._make_promotion(promo_type="percentage", value=20)
        items = [{"product_id": "p1", "quantity": 2, "unit_price": 500}]
        # subtotal = 1000, discount = 1000 * 20 / 100 = 200
        assert service.calculate_discount(promo, 1000, items) == 200

    def test_fixed_discount_correct(self):
        service, _ = _make_service()
        promo = self._make_promotion(promo_type="fixed", value=300)
        items = [{"product_id": "p1", "quantity": 1, "unit_price": 1000}]
        # subtotal = 1000, discount = min(300, 1000) = 300
        assert service.calculate_discount(promo, 1000, items) == 300

    def test_fixed_discount_capped_at_subtotal(self):
        service, _ = _make_service()
        promo = self._make_promotion(promo_type="fixed", value=5000)
        items = [{"product_id": "p1", "quantity": 1, "unit_price": 500}]
        # subtotal = 500, discount = min(5000, 500) = 500
        assert service.calculate_discount(promo, 500, items) == 500

    def test_bogo_all_products(self):
        service, _ = _make_service()
        promo = self._make_promotion(promo_type="bogo", value=0, applies_to="all")
        items = [
            {"product_id": "p1", "quantity": 4, "unit_price": 100},
            {"product_id": "p2", "quantity": 3, "unit_price": 200},
        ]
        # p1: free_count = 4//2 = 2, discount = 2*100 = 200
        # p2: free_count = 3//2 = 1, discount = 1*200 = 200
        # total = 400
        assert service.calculate_discount(promo, 1000, items) == 400

    def test_bogo_specific_products_only(self):
        service, _ = _make_service()
        promo = self._make_promotion(
            promo_type="bogo",
            value=0,
            applies_to="specific",
            product_ids=["p1"],
        )
        items = [
            {"product_id": "p1", "quantity": 4, "unit_price": 100},
            {"product_id": "p2", "quantity": 4, "unit_price": 200},
        ]
        # only p1 qualifies: free_count = 4//2 = 2, discount = 2*100 = 200
        # p2 is excluded
        assert service.calculate_discount(promo, 1200, items) == 200

    def test_returns_zero_if_min_purchase_not_met(self):
        service, _ = _make_service()
        promo = self._make_promotion(promo_type="percentage", value=20, min_purchase_amount=5000)
        items = [{"product_id": "p1", "quantity": 1, "unit_price": 1000}]
        # subtotal = 1000 < min_purchase_amount = 5000 → 0
        assert service.calculate_discount(promo, 1000, items) == 0

    def test_bogo_odd_quantity_floors_correctly(self):
        service, _ = _make_service()
        promo = self._make_promotion(promo_type="bogo", value=0, applies_to="all")
        items = [{"product_id": "p1", "quantity": 3, "unit_price": 150}]
        # free_count = 3//2 = 1, discount = 1*150 = 150
        assert service.calculate_discount(promo, 450, items) == 150


# ---------------------------------------------------------------------------
# TestGetBestDiscount
# ---------------------------------------------------------------------------

class TestGetBestDiscount:
    @pytest.mark.asyncio
    async def test_returns_none_zero_when_no_active_promotions(self):
        service, repo = _make_service()
        repo.find_active_auto_apply.return_value = []
        items = [{"product_id": "p1", "quantity": 2, "unit_price": 50000}]

        promotion_id, discount = await service.get_best_discount(100000, items)

        assert promotion_id is None
        assert discount == 0

    @pytest.mark.asyncio
    async def test_returns_promotion_with_highest_discount(self):
        service, repo = _make_service()
        # Promo A: 10% of 100000 = 10000
        promo_a = _make_fake_promotion(
            promotion_id="promo-a",
            promo_type="percentage",
            value=10,
            min_purchase_amount=0,
        )
        # Promo B: fixed 20000
        promo_b = _make_fake_promotion(
            promotion_id="promo-b",
            promo_type="fixed",
            value=20000,
            min_purchase_amount=0,
        )
        repo.find_active_auto_apply.return_value = [promo_a, promo_b]
        items = [{"product_id": "p1", "quantity": 2, "unit_price": 50000}]

        promotion_id, discount = await service.get_best_discount(100000, items)

        # Promo B gives 20000, promo A gives 10000 → B wins
        assert promotion_id == "promo-b"
        assert discount == 20000
