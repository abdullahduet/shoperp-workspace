"""
Unit tests for src/modules/reports/service.py

All repository calls are mocked. Tests verify business logic only.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.reports.repository import ReportsRepository
from src.modules.reports.service import ReportsService
from src.modules.reports.schemas import SalesReport, ProfitLossReport, TopProductsReport, LowStockItem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service() -> tuple[ReportsService, AsyncMock]:
    repo = AsyncMock(spec=ReportsRepository)
    service = ReportsService(repo)
    return service, repo


def _make_fake_sale(
    *,
    sale_id: str = "sale-uuid-1",
    total_amount: int = 10000,
    payment_method: str = "cash",
    sale_date: datetime | None = None,
    sale_items: list | None = None,
) -> MagicMock:
    sale = MagicMock()
    sale.id = sale_id
    sale.totalAmount = total_amount
    sale.paymentMethod = payment_method
    sale.saleDate = sale_date or datetime(2026, 4, 1, 10, 0, 0, tzinfo=timezone.utc)
    sale.saleItems = sale_items or []
    return sale


def _make_fake_product(
    *,
    product_id: str = "product-uuid-1",
    name: str = "Widget",
    sku: str = "WGT-001",
    cost_price: int = 500,
    stock_quantity: int = 10,
    min_stock_level: int = 5,
) -> MagicMock:
    p = MagicMock()
    p.id = product_id
    p.name = name
    p.sku = sku
    p.costPrice = cost_price
    p.stockQuantity = stock_quantity
    p.minStockLevel = min_stock_level
    return p


def _make_fake_sale_item(
    *,
    product_id: str = "product-uuid-1",
    quantity: int = 2,
    total_price: int = 2000,
    product: MagicMock | None = None,
) -> MagicMock:
    item = MagicMock()
    item.productId = product_id
    item.quantity = quantity
    item.totalPrice = total_price
    item.product = product or _make_fake_product()
    return item


def _make_fake_expense(
    *,
    amount: int = 5000,
    category: str = "Rent",
) -> MagicMock:
    e = MagicMock()
    e.amount = amount
    e.category = category
    return e


def _make_fake_po(
    *,
    total_amount: int = 20000,
    order_date: datetime | None = None,
) -> MagicMock:
    po = MagicMock()
    po.totalAmount = total_amount
    po.orderDate = order_date or datetime(2026, 4, 5, 0, 0, 0, tzinfo=timezone.utc)
    return po


# ---------------------------------------------------------------------------
# TestGetSalesReport
# ---------------------------------------------------------------------------

class TestGetSalesReport:
    @pytest.mark.asyncio
    async def test_returns_sales_grouped_by_date(self):
        service, repo = _make_service()
        sale1 = _make_fake_sale(total_amount=10000, payment_method="cash",
                                 sale_date=datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc))
        sale2 = _make_fake_sale(sale_id="sale-uuid-2", total_amount=5000, payment_method="card",
                                 sale_date=datetime(2026, 4, 2, 11, 0, tzinfo=timezone.utc))
        repo.find_sales_in_range.return_value = [sale1, sale2]

        report = await service.get_sales_report("2026-04-01", "2026-04-30")

        assert isinstance(report, SalesReport)
        assert len(report.items) == 2
        assert report.items[0].date == "2026-04-01"
        assert report.items[1].date == "2026-04-02"

    @pytest.mark.asyncio
    async def test_payment_breakdown_correct(self):
        service, repo = _make_service()
        sale1 = _make_fake_sale(total_amount=10000, payment_method="cash",
                                 sale_date=datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc))
        sale2 = _make_fake_sale(sale_id="sale-uuid-2", total_amount=5000, payment_method="card",
                                 sale_date=datetime(2026, 4, 1, 11, 0, tzinfo=timezone.utc))
        repo.find_sales_in_range.return_value = [sale1, sale2]

        report = await service.get_sales_report("2026-04-01", "2026-04-01")

        assert len(report.items) == 1
        day = report.items[0]
        assert day.payment_breakdown["cash"] == 10000
        assert day.payment_breakdown["card"] == 5000
        assert day.payment_breakdown["mobile"] == 0
        assert day.payment_breakdown["credit"] == 0

    @pytest.mark.asyncio
    async def test_totals_correct(self):
        service, repo = _make_service()
        sale1 = _make_fake_sale(total_amount=10000,
                                 sale_date=datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc))
        sale2 = _make_fake_sale(sale_id="sale-uuid-2", total_amount=5000,
                                 sale_date=datetime(2026, 4, 2, 11, 0, tzinfo=timezone.utc))
        repo.find_sales_in_range.return_value = [sale1, sale2]

        report = await service.get_sales_report("2026-04-01", "2026-04-30")

        assert report.totals["total_amount"] == 15000
        assert report.totals["transaction_count"] == 2


# ---------------------------------------------------------------------------
# TestGetProfitLoss
# ---------------------------------------------------------------------------

class TestGetProfitLoss:
    @pytest.mark.asyncio
    async def test_revenue_is_sum_of_sale_totals(self):
        service, repo = _make_service()
        sale1 = _make_fake_sale(total_amount=10000, sale_items=[])
        sale2 = _make_fake_sale(sale_id="sale-uuid-2", total_amount=8000, sale_items=[])
        repo.find_sales_with_items_in_range.return_value = [sale1, sale2]
        repo.find_expenses_in_range.return_value = []

        report = await service.get_profit_loss("2026-04-01", "2026-04-30")

        assert isinstance(report, ProfitLossReport)
        assert report.revenue == 18000

    @pytest.mark.asyncio
    async def test_cogs_uses_product_cost_price(self):
        service, repo = _make_service()
        product = _make_fake_product(cost_price=200)
        item = _make_fake_sale_item(quantity=3, product=product)
        sale = _make_fake_sale(total_amount=1200, sale_items=[item])
        repo.find_sales_with_items_in_range.return_value = [sale]
        repo.find_expenses_in_range.return_value = []

        report = await service.get_profit_loss("2026-04-01", "2026-04-30")

        assert report.cogs == 600  # 3 * 200

    @pytest.mark.asyncio
    async def test_net_profit_equals_gross_minus_expenses(self):
        service, repo = _make_service()
        product = _make_fake_product(cost_price=100)
        item = _make_fake_sale_item(quantity=2, product=product)
        sale = _make_fake_sale(total_amount=5000, sale_items=[item])
        expense = _make_fake_expense(amount=1000)
        repo.find_sales_with_items_in_range.return_value = [sale]
        repo.find_expenses_in_range.return_value = [expense]

        report = await service.get_profit_loss("2026-04-01", "2026-04-30")

        # cogs = 2 * 100 = 200, gross_profit = 5000 - 200 = 4800, net = 4800 - 1000 = 3800
        assert report.gross_profit == 4800
        assert report.net_profit == 3800


# ---------------------------------------------------------------------------
# TestGetTopProducts
# ---------------------------------------------------------------------------

class TestGetTopProducts:
    @pytest.mark.asyncio
    async def test_returns_sorted_by_quantity_descending(self):
        service, repo = _make_service()
        product_a = _make_fake_product(product_id="prod-a", name="A", sku="A-001")
        product_b = _make_fake_product(product_id="prod-b", name="B", sku="B-001")
        item_a = _make_fake_sale_item(product_id="prod-a", quantity=5, product=product_a)
        item_b = _make_fake_sale_item(product_id="prod-b", quantity=10, product=product_b)
        sale = _make_fake_sale(sale_items=[item_a, item_b])
        repo.find_sales_with_items_in_range.return_value = [sale]

        report = await service.get_top_products("2026-04-01", "2026-04-30")

        assert isinstance(report, TopProductsReport)
        assert report.items[0].product_id == "prod-b"
        assert report.items[1].product_id == "prod-a"

    @pytest.mark.asyncio
    async def test_limited_to_limit_param(self):
        service, repo = _make_service()
        items = []
        for i in range(5):
            prod = _make_fake_product(product_id=f"prod-{i}", name=f"Product {i}", sku=f"P-{i:03d}")
            si = _make_fake_sale_item(product_id=f"prod-{i}", quantity=i + 1, product=prod)
            items.append(si)
        sale = _make_fake_sale(sale_items=items)
        repo.find_sales_with_items_in_range.return_value = [sale]

        report = await service.get_top_products("2026-04-01", "2026-04-30", limit=3)

        assert len(report.items) == 3

    @pytest.mark.asyncio
    async def test_aggregates_multiple_sales_correctly(self):
        service, repo = _make_service()
        product = _make_fake_product(product_id="prod-x", name="X", sku="X-001")
        item1 = _make_fake_sale_item(product_id="prod-x", quantity=3, total_price=3000, product=product)
        item2 = _make_fake_sale_item(product_id="prod-x", quantity=4, total_price=4000, product=product)
        sale1 = _make_fake_sale(sale_items=[item1])
        sale2 = _make_fake_sale(sale_id="sale-uuid-2", sale_items=[item2])
        repo.find_sales_with_items_in_range.return_value = [sale1, sale2]

        report = await service.get_top_products("2026-04-01", "2026-04-30")

        assert len(report.items) == 1
        assert report.items[0].total_quantity == 7
        assert report.items[0].total_revenue == 7000


# ---------------------------------------------------------------------------
# TestGetLowStock
# ---------------------------------------------------------------------------

class TestGetLowStock:
    @pytest.mark.asyncio
    async def test_returns_only_products_below_min_level(self):
        service, repo = _make_service()
        low_product = _make_fake_product(product_id="prod-low", name="Low", sku="LOW-001",
                                          stock_quantity=2, min_stock_level=5)
        repo.find_low_stock_products.return_value = [low_product]

        result = await service.get_low_stock()

        assert len(result) == 1
        assert isinstance(result[0], LowStockItem)
        assert result[0].id == "prod-low"
        assert result[0].stock_quantity == 2
        assert result[0].min_stock_level == 5

    @pytest.mark.asyncio
    async def test_returns_empty_when_all_stocked(self):
        service, repo = _make_service()
        repo.find_low_stock_products.return_value = []

        result = await service.get_low_stock()

        assert result == []


# ---------------------------------------------------------------------------
# TestGetPurchasesReport
# ---------------------------------------------------------------------------

class TestGetPurchasesReport:
    @pytest.mark.asyncio
    async def test_groups_by_order_date(self):
        service, repo = _make_service()
        po1 = _make_fake_po(total_amount=10000,
                             order_date=datetime(2026, 4, 5, 0, 0, tzinfo=timezone.utc))
        po2 = _make_fake_po(total_amount=8000,
                             order_date=datetime(2026, 4, 6, 0, 0, tzinfo=timezone.utc))
        repo.find_pos_in_range.return_value = [po1, po2]

        report = await service.get_purchases_report("2026-04-01", "2026-04-30")

        assert len(report.items) == 2
        assert report.items[0].date == "2026-04-05"
        assert report.items[1].date == "2026-04-06"

    @pytest.mark.asyncio
    async def test_excludes_cancelled_pos(self):
        """Repo handles exclusion; verify service works with empty result."""
        service, repo = _make_service()
        repo.find_pos_in_range.return_value = []

        report = await service.get_purchases_report("2026-04-01", "2026-04-30")

        assert report.items == []
        assert report.totals["total_amount"] == 0
        assert report.totals["order_count"] == 0


# ---------------------------------------------------------------------------
# TestGetExpensesReport
# ---------------------------------------------------------------------------

class TestGetExpensesReport:
    @pytest.mark.asyncio
    async def test_groups_by_category(self):
        service, repo = _make_service()
        e1 = _make_fake_expense(amount=5000, category="Rent")
        e2 = _make_fake_expense(amount=2000, category="Utilities")
        e3 = _make_fake_expense(amount=3000, category="Rent")
        repo.find_expenses_in_range.return_value = [e1, e2, e3]

        report = await service.get_expenses_report("2026-04-01", "2026-04-30")

        assert len(report.items) == 2
        rent_item = next(i for i in report.items if i.category == "Rent")
        assert rent_item.total_amount == 8000
        assert rent_item.count == 2

    @pytest.mark.asyncio
    async def test_sorted_by_total_amount_descending(self):
        service, repo = _make_service()
        e1 = _make_fake_expense(amount=1000, category="Misc")
        e2 = _make_fake_expense(amount=8000, category="Rent")
        e3 = _make_fake_expense(amount=3000, category="Utilities")
        repo.find_expenses_in_range.return_value = [e1, e2, e3]

        report = await service.get_expenses_report("2026-04-01", "2026-04-30")

        amounts = [i.total_amount for i in report.items]
        assert amounts == sorted(amounts, reverse=True)


# ---------------------------------------------------------------------------
# TestGetInventoryValuation
# ---------------------------------------------------------------------------

class TestGetInventoryValuation:
    @pytest.mark.asyncio
    async def test_value_is_stock_times_cost_price(self):
        service, repo = _make_service()
        product = _make_fake_product(stock_quantity=10, cost_price=500)
        repo.find_active_products_with_stock.return_value = [product]

        report = await service.get_inventory_valuation()

        assert report.items[0].value == 5000  # 10 * 500

    @pytest.mark.asyncio
    async def test_total_value_is_sum_of_item_values(self):
        service, repo = _make_service()
        p1 = _make_fake_product(product_id="p1", stock_quantity=10, cost_price=500)
        p2 = _make_fake_product(product_id="p2", stock_quantity=5, cost_price=1000)
        repo.find_active_products_with_stock.return_value = [p1, p2]

        report = await service.get_inventory_valuation()

        # p1: 10 * 500 = 5000, p2: 5 * 1000 = 5000
        assert report.total_value == 10000
        assert report.product_count == 2
        assert report.currency == "BDT"
