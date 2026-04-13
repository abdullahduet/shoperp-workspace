"""
Unit tests for src/modules/sales/service.py

All repository and promotion_service calls are mocked. Tests verify business logic only.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.sales.repository import SalesRepository
from src.modules.sales.schemas import (
    DailySummaryResponse,
    SaleCreate,
    SaleItemCreate,
    SaleResponse,
)
from src.modules.sales.service import SalesService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_product(
    *,
    product_id: str = "prod-uuid-1",
    stock_quantity: int = 100,
    tax_rate: Decimal = Decimal("10"),
    is_active: bool = True,
    deleted_at=None,
) -> MagicMock:
    product = MagicMock()
    product.id = product_id
    product.stockQuantity = stock_quantity
    product.taxRate = tax_rate
    product.isActive = is_active
    product.deletedAt = deleted_at
    return product


def _make_fake_sale(
    *,
    sale_id: str = "sale-uuid-1",
    sale_number: str = "SALE-20260411-001",
    subtotal: int = 100000,
    discount_amount: int = 0,
    tax_amount: int = 10000,
    total_amount: int = 110000,
    payment_method: str = "cash",
    promotion_id: str | None = None,
    customer_name: str | None = None,
    notes: str | None = None,
    recorded_by: str | None = "user-uuid-1",
    sale_items: list | None = None,
) -> MagicMock:
    sale = MagicMock()
    sale.id = sale_id
    sale.saleNumber = sale_number
    sale.saleDate = datetime(2026, 4, 11, tzinfo=timezone.utc)
    sale.customerName = customer_name
    sale.subtotal = subtotal
    sale.discountAmount = discount_amount
    sale.taxAmount = tax_amount
    sale.totalAmount = total_amount
    sale.paymentMethod = payment_method
    sale.promotionId = promotion_id
    sale.notes = notes
    sale.recordedBy = recorded_by
    sale.saleItems = sale_items or []
    sale.createdAt = datetime(2026, 4, 11, tzinfo=timezone.utc)
    return sale


def _make_fake_sale_item(
    *,
    item_id: str = "item-uuid-1",
    product_id: str = "prod-uuid-1",
    product_name: str = "Test Product",
    product_sku: str = "SKU-001",
    quantity: int = 2,
    unit_price: int = 50000,
    discount: int = 0,
    total_price: int = 100000,
) -> MagicMock:
    item = MagicMock()
    item.id = item_id
    item.productId = product_id
    item.quantity = quantity
    item.unitPrice = unit_price
    item.discount = discount
    item.totalPrice = total_price
    item.createdAt = datetime(2026, 4, 11, tzinfo=timezone.utc)
    product = MagicMock()
    product.name = product_name
    product.sku = product_sku
    item.product = product
    return item


def _make_fake_account(account_id: str = "account-uuid-1") -> MagicMock:
    account = MagicMock()
    account.id = account_id
    return account


def _make_service() -> tuple[SalesService, AsyncMock, MagicMock]:
    repo = AsyncMock(spec=SalesRepository)
    promotion_service = MagicMock()
    promotion_service.get_best_discount = AsyncMock(return_value=(None, 0))
    service = SalesService(repo, promotion_service)
    return service, repo, promotion_service


def _make_sale_input(
    *,
    product_id: str = "prod-uuid-1",
    quantity: int = 2,
    unit_price: int = 50000,
    payment_method: str = "cash",
) -> SaleCreate:
    return SaleCreate(
        items=[SaleItemCreate(product_id=product_id, quantity=quantity, unit_price=unit_price)],
        payment_method=payment_method,
    )


# ---------------------------------------------------------------------------
# TestRecordSale
# ---------------------------------------------------------------------------

class TestRecordSale:
    @pytest.mark.asyncio
    async def test_raises_not_found_if_product_missing(self):
        service, repo, _promo = _make_service()
        repo.find_product_by_id.return_value = None

        with pytest.raises(ValidationError, match="Product not found"):
            await service.record_sale(_make_sale_input(), recorded_by="user-1")

    @pytest.mark.asyncio
    async def test_raises_validation_error_if_product_inactive(self):
        service, repo, _promo = _make_service()
        repo.find_product_by_id.return_value = _make_fake_product(is_active=False)

        with pytest.raises(ValidationError, match="Product is inactive"):
            await service.record_sale(_make_sale_input(), recorded_by="user-1")

    @pytest.mark.asyncio
    async def test_raises_validation_error_if_insufficient_stock(self):
        service, repo, _promo = _make_service()
        repo.find_product_by_id.return_value = _make_fake_product(stock_quantity=1)

        with pytest.raises(ValidationError, match="Insufficient stock"):
            await service.record_sale(_make_sale_input(quantity=5), recorded_by="user-1")

    @pytest.mark.asyncio
    async def test_computes_subtotal_correctly(self):
        service, repo, _promo = _make_service()
        product = _make_fake_product(stock_quantity=100, tax_rate=Decimal("0"))
        repo.find_product_by_id.return_value = product
        repo.count_today_sales.return_value = 0
        repo.count_today_journal_entries.return_value = 0
        repo.find_account_by_code.return_value = _make_fake_account()
        sale_item = _make_fake_sale_item(quantity=3, unit_price=10000, total_price=30000)
        fake_sale = _make_fake_sale(subtotal=30000, tax_amount=0, total_amount=30000, sale_items=[sale_item])
        repo.create_sale_atomic.return_value = fake_sale

        await service.record_sale(
            SaleCreate(items=[SaleItemCreate(product_id="prod-uuid-1", quantity=3, unit_price=10000)]),
            recorded_by="user-1",
        )

        call_args = repo.create_sale_atomic.call_args
        sale_data = call_args.args[0]
        assert sale_data["subtotal"] == 30000

    @pytest.mark.asyncio
    async def test_applies_best_promotion_discount(self):
        service, repo, promo_service = _make_service()
        promo_service.get_best_discount.return_value = ("promo-uuid-1", 5000)
        product = _make_fake_product(stock_quantity=100, tax_rate=Decimal("0"))
        repo.find_product_by_id.return_value = product
        repo.count_today_sales.return_value = 0
        repo.count_today_journal_entries.return_value = 0
        repo.find_account_by_code.return_value = _make_fake_account()
        fake_sale = _make_fake_sale(
            subtotal=100000, discount_amount=5000, tax_amount=0, total_amount=95000,
            promotion_id="promo-uuid-1", sale_items=[]
        )
        repo.create_sale_atomic.return_value = fake_sale

        await service.record_sale(_make_sale_input(quantity=2, unit_price=50000), recorded_by="user-1")

        call_args = repo.create_sale_atomic.call_args
        sale_data = call_args.args[0]
        assert sale_data["discountAmount"] == 5000
        assert sale_data["promotionId"] == "promo-uuid-1"

    @pytest.mark.asyncio
    async def test_tax_computed_from_product_tax_rate(self):
        service, repo, _promo = _make_service()
        # 10% tax on 100000 subtotal = 10000
        product = _make_fake_product(stock_quantity=100, tax_rate=Decimal("10"))
        repo.find_product_by_id.return_value = product
        repo.count_today_sales.return_value = 0
        repo.count_today_journal_entries.return_value = 0
        repo.find_account_by_code.return_value = _make_fake_account()
        sale_item = _make_fake_sale_item(quantity=2, unit_price=50000)
        fake_sale = _make_fake_sale(subtotal=100000, tax_amount=10000, total_amount=110000, sale_items=[sale_item])
        repo.create_sale_atomic.return_value = fake_sale

        await service.record_sale(_make_sale_input(quantity=2, unit_price=50000), recorded_by="user-1")

        call_args = repo.create_sale_atomic.call_args
        sale_data = call_args.args[0]
        # 2 * 50000 * 10 / 100 = 10000
        assert sale_data["taxAmount"] == 10000

    @pytest.mark.asyncio
    async def test_total_amount_is_subtotal_minus_discount_plus_tax(self):
        service, repo, promo_service = _make_service()
        promo_service.get_best_discount.return_value = ("promo-1", 20000)
        # 10% tax
        product = _make_fake_product(stock_quantity=100, tax_rate=Decimal("10"))
        repo.find_product_by_id.return_value = product
        repo.count_today_sales.return_value = 0
        repo.count_today_journal_entries.return_value = 0
        repo.find_account_by_code.return_value = _make_fake_account()
        fake_sale = _make_fake_sale(
            subtotal=100000, discount_amount=20000, tax_amount=10000, total_amount=90000,
            sale_items=[]
        )
        repo.create_sale_atomic.return_value = fake_sale

        await service.record_sale(_make_sale_input(quantity=2, unit_price=50000), recorded_by="user-1")

        call_args = repo.create_sale_atomic.call_args
        sale_data = call_args.args[0]
        # 100000 - 20000 + 10000 = 90000
        assert sale_data["totalAmount"] == 90000

    @pytest.mark.asyncio
    async def test_records_sale_with_no_promotion_when_none_active(self):
        service, repo, promo_service = _make_service()
        promo_service.get_best_discount.return_value = (None, 0)
        product = _make_fake_product(stock_quantity=100, tax_rate=Decimal("0"))
        repo.find_product_by_id.return_value = product
        repo.count_today_sales.return_value = 0
        repo.count_today_journal_entries.return_value = 0
        repo.find_account_by_code.return_value = _make_fake_account()
        fake_sale = _make_fake_sale(subtotal=100000, sale_items=[])
        repo.create_sale_atomic.return_value = fake_sale

        await service.record_sale(_make_sale_input(quantity=2, unit_price=50000), recorded_by="user-1")

        call_args = repo.create_sale_atomic.call_args
        sale_data = call_args.args[0]
        assert "promotionId" not in sale_data


# ---------------------------------------------------------------------------
# TestGetById
# ---------------------------------------------------------------------------

class TestGetById:
    @pytest.mark.asyncio
    async def test_returns_sale_response(self):
        service, repo, _promo = _make_service()
        sale_item = _make_fake_sale_item()
        fake_sale = _make_fake_sale(sale_items=[sale_item])
        repo.find_by_id.return_value = fake_sale

        result = await service.get_by_id("sale-uuid-1")

        assert isinstance(result, SaleResponse)
        assert result.id == "sale-uuid-1"
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_raises_not_found_if_missing(self):
        service, repo, _promo = _make_service()
        repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.get_by_id("nonexistent-id")


# ---------------------------------------------------------------------------
# TestList
# ---------------------------------------------------------------------------

class TestList:
    @pytest.mark.asyncio
    async def test_returns_paginated_sales(self):
        service, repo, _promo = _make_service()
        fake_sale = _make_fake_sale(sale_items=[])
        repo.find_paginated.return_value = ([fake_sale], 1)

        result = await service.list(page=1, limit=20, start_date=None, end_date=None, payment_method=None)

        assert result.total == 1
        assert len(result.items) == 1
        assert isinstance(result.items[0], SaleResponse)

    @pytest.mark.asyncio
    async def test_applies_date_filters(self):
        service, repo, _promo = _make_service()
        repo.find_paginated.return_value = ([], 0)

        await service.list(
            page=1, limit=20,
            start_date="2026-04-01",
            end_date="2026-04-30",
            payment_method=None,
        )

        call_args = repo.find_paginated.call_args
        where = call_args.args[2]
        assert "saleDate" in where
        assert "gte" in where["saleDate"]
        assert "lte" in where["saleDate"]

    @pytest.mark.asyncio
    async def test_applies_payment_method_filter(self):
        service, repo, _promo = _make_service()
        repo.find_paginated.return_value = ([], 0)

        await service.list(page=1, limit=20, start_date=None, end_date=None, payment_method="card")

        call_args = repo.find_paginated.call_args
        where = call_args.args[2]
        assert where.get("paymentMethod") == "card"


# ---------------------------------------------------------------------------
# TestGetDailySummary
# ---------------------------------------------------------------------------

class TestGetDailySummary:
    def _make_sale_with_total(self, total: int, method: str) -> MagicMock:
        s = MagicMock()
        s.totalAmount = total
        s.paymentMethod = method
        return s

    @pytest.mark.asyncio
    async def test_returns_correct_totals(self):
        service, repo, _promo = _make_service()
        repo.find_today_sales.return_value = [
            self._make_sale_with_total(50000, "cash"),
            self._make_sale_with_total(30000, "card"),
        ]

        result = await service.get_daily_summary()

        assert isinstance(result, DailySummaryResponse)
        assert result.total_sales == 80000
        assert result.transaction_count == 2

    @pytest.mark.asyncio
    async def test_payment_breakdown_correct(self):
        service, repo, _promo = _make_service()
        repo.find_today_sales.return_value = [
            self._make_sale_with_total(50000, "cash"),
            self._make_sale_with_total(30000, "card"),
            self._make_sale_with_total(20000, "mobile"),
        ]

        result = await service.get_daily_summary()

        assert result.payment_breakdown["cash"] == 50000
        assert result.payment_breakdown["card"] == 30000
        assert result.payment_breakdown["mobile"] == 20000
        assert result.payment_breakdown["credit"] == 0

    @pytest.mark.asyncio
    async def test_returns_zeros_when_no_sales_today(self):
        service, repo, _promo = _make_service()
        repo.find_today_sales.return_value = []

        result = await service.get_daily_summary()

        assert result.total_sales == 0
        assert result.transaction_count == 0
        assert result.payment_breakdown == {"cash": 0, "card": 0, "mobile": 0, "credit": 0}
