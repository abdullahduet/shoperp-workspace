"""
Unit tests for src/modules/dashboard/service.py

All repository calls are mocked. Tests verify business logic only.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.dashboard.repository import DashboardRepository
from src.modules.dashboard.service import DashboardService
from src.modules.dashboard.schemas import DashboardSummary, TrendItem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service() -> tuple[DashboardService, AsyncMock]:
    repo = AsyncMock(spec=DashboardRepository)
    service = DashboardService(repo)
    return service, repo


def _make_fake_sale(
    *,
    sale_id: str = "sale-uuid-1",
    total_amount: int = 10000,
    sale_date: datetime | None = None,
) -> MagicMock:
    sale = MagicMock()
    sale.id = sale_id
    sale.totalAmount = total_amount
    sale.saleDate = sale_date or datetime(2026, 4, 12, 10, 0, 0, tzinfo=timezone.utc)
    return sale


def _make_fake_expense(*, amount: int = 3000) -> MagicMock:
    e = MagicMock()
    e.amount = amount
    return e


# ---------------------------------------------------------------------------
# TestGetSummary
# ---------------------------------------------------------------------------

class TestGetSummary:
    @pytest.mark.asyncio
    async def test_today_sales_and_count_correct(self):
        service, repo = _make_service()
        sale1 = _make_fake_sale(total_amount=10000)
        sale2 = _make_fake_sale(sale_id="sale-uuid-2", total_amount=5000)
        repo.find_sales_in_range.side_effect = [[sale1, sale2], []]  # today, month
        repo.find_expenses_in_range.return_value = []
        repo.count_low_stock_products.return_value = 0

        summary = await service.get_summary()

        assert isinstance(summary, DashboardSummary)
        assert summary.today_sales == 15000
        assert summary.today_transactions == 2

    @pytest.mark.asyncio
    async def test_month_profit_is_revenue_minus_expenses(self):
        service, repo = _make_service()
        month_sale = _make_fake_sale(total_amount=50000)
        expense = _make_fake_expense(amount=12000)
        repo.find_sales_in_range.side_effect = [[], [month_sale]]  # today, month
        repo.find_expenses_in_range.return_value = [expense]
        repo.count_low_stock_products.return_value = 0

        summary = await service.get_summary()

        assert summary.month_revenue == 50000
        assert summary.month_profit == 38000  # 50000 - 12000

    @pytest.mark.asyncio
    async def test_low_stock_count_from_repo(self):
        service, repo = _make_service()
        repo.find_sales_in_range.side_effect = [[], []]
        repo.find_expenses_in_range.return_value = []
        repo.count_low_stock_products.return_value = 7

        summary = await service.get_summary()

        assert summary.low_stock_count == 7


# ---------------------------------------------------------------------------
# TestGetTrends
# ---------------------------------------------------------------------------

class TestGetTrends:
    @pytest.mark.asyncio
    async def test_returns_items_sorted_descending_by_month(self):
        service, repo = _make_service()
        sale_jan = _make_fake_sale(total_amount=10000,
                                    sale_date=datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc))
        sale_mar = _make_fake_sale(sale_id="sale-mar", total_amount=20000,
                                    sale_date=datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc))
        sale_feb = _make_fake_sale(sale_id="sale-feb", total_amount=15000,
                                    sale_date=datetime(2026, 2, 5, 10, 0, tzinfo=timezone.utc))
        repo.find_sales_last_12_months.return_value = [sale_jan, sale_mar, sale_feb]

        trends = await service.get_trends()

        assert all(isinstance(t, TrendItem) for t in trends)
        months = [t.month for t in trends]
        assert months == sorted(months, reverse=True)
        assert months[0] == "2026-03"

    @pytest.mark.asyncio
    async def test_groups_correctly_by_month(self):
        service, repo = _make_service()
        sale1 = _make_fake_sale(total_amount=10000,
                                 sale_date=datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc))
        sale2 = _make_fake_sale(sale_id="sale-uuid-2", total_amount=8000,
                                 sale_date=datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc))
        sale3 = _make_fake_sale(sale_id="sale-uuid-3", total_amount=5000,
                                 sale_date=datetime(2026, 3, 20, 9, 0, tzinfo=timezone.utc))
        repo.find_sales_last_12_months.return_value = [sale1, sale2, sale3]

        trends = await service.get_trends()

        apr_trend = next((t for t in trends if t.month == "2026-04"), None)
        assert apr_trend is not None
        assert apr_trend.revenue == 18000
        assert apr_trend.transaction_count == 2

        mar_trend = next((t for t in trends if t.month == "2026-03"), None)
        assert mar_trend is not None
        assert mar_trend.revenue == 5000
        assert mar_trend.transaction_count == 1
