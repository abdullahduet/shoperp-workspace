"""
Regression tests for the dashboard 500 bugs.

Each test class targets one specific root cause that previously caused
GET /api/dashboard/summary to return 500.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import json

import pytest
from fastapi.testclient import TestClient

from src.core.auth import create_access_token
from src.modules.dashboard.repository import DashboardRepository
from src.modules.dashboard.service import DashboardService, _twelve_months_ago
from src.modules.dashboard.schemas import DashboardSummary


# ---------------------------------------------------------------------------
# Helpers shared across test classes
# ---------------------------------------------------------------------------

def _make_service() -> tuple[DashboardService, AsyncMock]:
    repo = AsyncMock(spec=DashboardRepository)
    return DashboardService(repo), repo


def _make_fake_sale(*, total_amount: int = 10000,
                    sale_date: datetime | None = None) -> MagicMock:
    s = MagicMock()
    s.totalAmount = total_amount
    s.saleDate = sale_date or datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)
    return s


def _make_fake_expense(*, amount: int = 5000) -> MagicMock:
    e = MagicMock()
    e.amount = amount
    return e


def _make_fake_user(*, role: str = "admin") -> MagicMock:
    u = MagicMock()
    u.id = "user-uuid-1"
    u.email = f"{role}@test.com"
    u.name = f"{role.title()} User"
    u.role = role
    u.isActive = True
    u.lastLoginAt = None
    u.createdAt = datetime(2024, 1, 1, tzinfo=timezone.utc)
    u.deletedAt = None
    return u


def _make_dashboard_db() -> MagicMock:
    db = MagicMock()
    db.sale = MagicMock()
    db.sale.find_many = AsyncMock(return_value=[])
    db.expense = MagicMock()
    db.expense.find_many = AsyncMock(return_value=[])
    db.product = MagicMock()
    db.product.find_many = AsyncMock(return_value=[])
    db.user = MagicMock()
    db.user.find_first = AsyncMock(return_value=None)
    return db


def _make_client(mock_db: MagicMock) -> TestClient:
    with patch("src.database._db", mock_db), \
         patch("src.database.connect", new_callable=AsyncMock), \
         patch("src.database.disconnect", new_callable=AsyncMock):
        import src.main as main_module
        return TestClient(main_module.app, raise_server_exceptions=False)


def body(response) -> dict:
    return json.loads(response.content)


# ---------------------------------------------------------------------------
# Bug 1 — find_expenses_in_range must receive datetime, not date
#
# Previously: service passed bare date objects → Prisma serialisation error
# → unhandled exception → 500.
# Fix: service now passes datetime objects for the @db.Date column.
# ---------------------------------------------------------------------------

class TestExpenseDateTypeRegression:
    @pytest.mark.asyncio
    async def test_find_expenses_in_range_receives_datetime_objects(self):
        """Service must pass datetime objects to find_expenses_in_range, not date."""
        service, repo = _make_service()
        repo.find_sales_in_range.return_value = []
        repo.find_expenses_in_range.return_value = []
        repo.count_low_stock_products.return_value = 0

        await service.get_summary()

        assert repo.find_expenses_in_range.called
        call_args = repo.find_expenses_in_range.call_args
        start_arg, end_arg = call_args.args[0], call_args.args[1]

        # Both arguments must be datetime instances, not bare date instances
        assert isinstance(start_arg, datetime), (
            f"Expected datetime, got {type(start_arg).__name__}. "
            "Passing a bare date to Prisma @db.Date causes a 500."
        )
        assert isinstance(end_arg, datetime), (
            f"Expected datetime, got {type(end_arg).__name__}. "
            "Passing a bare date to Prisma @db.Date causes a 500."
        )

    @pytest.mark.asyncio
    async def test_expense_datetime_args_are_timezone_aware(self):
        """Datetime args must be timezone-aware to avoid naive datetime errors."""
        service, repo = _make_service()
        repo.find_sales_in_range.return_value = []
        repo.find_expenses_in_range.return_value = []
        repo.count_low_stock_products.return_value = 0

        await service.get_summary()

        start_arg, end_arg = repo.find_expenses_in_range.call_args.args
        assert start_arg.tzinfo is not None, "start datetime must be timezone-aware"
        assert end_arg.tzinfo is not None, "end datetime must be timezone-aware"

    @pytest.mark.asyncio
    async def test_expense_range_covers_full_current_month(self):
        """The expense range must start on the 1st of the current month."""
        service, repo = _make_service()
        repo.find_sales_in_range.return_value = []
        repo.find_expenses_in_range.return_value = []
        repo.count_low_stock_products.return_value = 0

        await service.get_summary()

        start_arg = repo.find_expenses_in_range.call_args.args[0]
        assert start_arg.day == 1, "Expense range must start on the 1st of the month"


# ---------------------------------------------------------------------------
# Bug 2 — Repository exception must not propagate as unhandled 500
#
# Previously: any Prisma error escaped the controller as a raw exception,
# bypassing the AppError handler and returning 500 with no structured body.
# Fix: service catches non-AppError exceptions, logs them, and returns a
# zeroed DashboardSummary so the page always renders.
# ---------------------------------------------------------------------------

class TestRepositoryExceptionHandling:
    @pytest.mark.asyncio
    async def test_get_summary_returns_zeros_on_db_error(self):
        """A repository failure must return a zeroed summary, not raise."""
        service, repo = _make_service()
        repo.find_sales_in_range.side_effect = RuntimeError("DB connection lost")

        result = await service.get_summary()

        assert isinstance(result, DashboardSummary)
        assert result.today_sales == 0
        assert result.today_transactions == 0
        assert result.month_revenue == 0
        assert result.month_profit == 0
        assert result.low_stock_count == 0

    @pytest.mark.asyncio
    async def test_get_trends_returns_empty_list_on_db_error(self):
        """A repository failure in get_trends must return [], not raise."""
        service, repo = _make_service()
        repo.find_sales_last_12_months.side_effect = RuntimeError("timeout")

        result = await service.get_trends()

        assert result == []

    def test_summary_endpoint_returns_200_even_when_db_raises(self):
        """Integration: endpoint must return 200 with zeroed data, not 500."""
        user = _make_fake_user(role="admin")
        token = create_access_token({"sub": user.id, "role": "admin"})

        db = _make_dashboard_db()
        db.user.find_first = AsyncMock(return_value=user)
        # Simulate a Prisma serialisation error on the sale query
        db.sale.find_many = AsyncMock(side_effect=RuntimeError("Prisma error"))

        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/dashboard/summary",
                              cookies={"access_token": token})

        assert resp.status_code == 200, (
            f"Expected 200 (degraded response), got {resp.status_code}. "
            "A DB error must not propagate as 500."
        )
        b = body(resp)
        assert b["success"] is True
        assert b["data"]["today_sales"] == 0

    def test_trends_endpoint_returns_200_even_when_db_raises(self):
        """Integration: /trends must return 200 with empty list, not 500."""
        user = _make_fake_user(role="admin")
        token = create_access_token({"sub": user.id, "role": "admin"})

        db = _make_dashboard_db()
        db.user.find_first = AsyncMock(return_value=user)
        db.sale.find_many = AsyncMock(side_effect=RuntimeError("Prisma error"))

        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/dashboard/trends",
                              cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert b["data"] == []


# ---------------------------------------------------------------------------
# Bug 3 — 12-month window must use calendar arithmetic, not timedelta(days=365)
#
# Previously: timedelta(days=365) could land in the wrong month on leap years.
# Fix: _twelve_months_ago() subtracts 12 from the month with year rollover.
# ---------------------------------------------------------------------------

class TestTwelveMonthsAgoCalculation:
    def test_non_january_month(self):
        """April 2026 → April 2025."""
        now = datetime(2026, 4, 15, 10, 0, tzinfo=timezone.utc)
        result = _twelve_months_ago(now)
        assert result.year == 2025
        assert result.month == 4
        assert result.day == 1

    def test_january_rolls_back_to_previous_year(self):
        """January 2026 → January 2025."""
        now = datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc)
        result = _twelve_months_ago(now)
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 1

    def test_leap_year_march_2024(self):
        """March 2024 (leap year) → March 2023. timedelta(days=365) would give March 2023 too,
        but February 2024 → February 2023 is where timedelta(days=365) fails
        (it would land on Feb 1 2023 correctly, but March 1 2024 - 365 = March 2 2023)."""
        now = datetime(2024, 3, 1, 0, 0, tzinfo=timezone.utc)
        result = _twelve_months_ago(now)
        assert result.year == 2023
        assert result.month == 3
        assert result.day == 1

    def test_result_is_always_first_of_month(self):
        """The result must always be the 1st of the target month."""
        for month in range(1, 13):
            now = datetime(2026, month, 15, 10, 0, tzinfo=timezone.utc)
            result = _twelve_months_ago(now)
            assert result.day == 1, f"Expected day=1 for month={month}, got {result.day}"

    def test_result_is_timezone_aware(self):
        now = datetime(2026, 6, 1, tzinfo=timezone.utc)
        result = _twelve_months_ago(now)
        assert result.tzinfo is not None


# ---------------------------------------------------------------------------
# Bug 4 — count_low_stock_products must not fetch unbounded rows
# ---------------------------------------------------------------------------

class TestBoundedProductFetch:
    @pytest.mark.asyncio
    async def test_product_fetch_has_take_limit(self):
        """find_many for low-stock count must include a take= limit."""
        from src.modules.dashboard.repository import DashboardRepository

        mock_prisma = MagicMock()
        mock_prisma.product.find_many = AsyncMock(return_value=[])
        repo = DashboardRepository(mock_prisma)

        await repo.count_low_stock_products()

        call_kwargs = mock_prisma.product.find_many.call_args.kwargs
        assert "take" in call_kwargs, (
            "count_low_stock_products must pass take= to prevent unbounded fetches"
        )
        assert call_kwargs["take"] > 0
