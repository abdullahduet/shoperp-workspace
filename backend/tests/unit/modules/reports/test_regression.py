"""
Regression tests for the reports 500 bugs.

Root cause: _parse_date_range() returned bare Python date objects.
Prisma Client Python requires datetime objects for @db.Date columns
(Expense.date, PurchaseOrder.orderDate). Passing date objects caused a
Prisma serialisation error → unhandled exception → 500.

These tests verify:
1. The repository receives datetime objects (not date) for @db.Date columns.
2. The affected endpoints return 200, not 500, when date filters are supplied.
3. The endpoints return 200 even with no date filters (default range).
"""
from __future__ import annotations

from datetime import datetime, date
from unittest.mock import AsyncMock, MagicMock, patch
import json

import pytest
from fastapi.testclient import TestClient

from src.core.auth import create_access_token
from src.modules.reports.repository import ReportsRepository
from src.modules.reports.service import ReportsService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service() -> tuple[ReportsService, AsyncMock]:
    repo = AsyncMock(spec=ReportsRepository)
    return ReportsService(repo), repo


def _make_fake_user(*, role: str = "admin") -> MagicMock:
    u = MagicMock()
    u.id = "user-uuid-1"
    u.email = f"{role}@test.com"
    u.name = f"{role.title()} User"
    u.role = role
    u.isActive = True
    u.lastLoginAt = None
    u.createdAt = datetime(2024, 1, 1)
    u.deletedAt = None
    return u


def _make_reports_db() -> MagicMock:
    db = MagicMock()
    db.sale = MagicMock()
    db.sale.find_many = AsyncMock(return_value=[])
    db.expense = MagicMock()
    db.expense.find_many = AsyncMock(return_value=[])
    db.purchaseorder = MagicMock()
    db.purchaseorder.find_many = AsyncMock(return_value=[])
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
# Bug 1 — profit-loss: find_expenses_in_range must receive datetime, not date
# ---------------------------------------------------------------------------

class TestProfitLossDateTypeRegression:
    @pytest.mark.asyncio
    async def test_find_expenses_in_range_receives_datetime_not_date(self):
        """get_profit_loss must pass datetime objects to find_expenses_in_range."""
        service, repo = _make_service()
        repo.find_sales_with_items_in_range.return_value = []
        repo.find_expenses_in_range.return_value = []

        await service.get_profit_loss("2026-04-01", "2026-04-30")

        assert repo.find_expenses_in_range.called
        start_arg, end_arg = repo.find_expenses_in_range.call_args.args
        assert isinstance(start_arg, datetime), (
            f"Expected datetime, got {type(start_arg).__name__}. "
            "Passing bare date to Prisma @db.Date causes a 500."
        )
        assert isinstance(end_arg, datetime), (
            f"Expected datetime, got {type(end_arg).__name__}."
        )
        assert start_arg.tzinfo is not None, "datetime must be timezone-aware"
        assert end_arg.tzinfo is not None, "datetime must be timezone-aware"

    @pytest.mark.asyncio
    async def test_find_expenses_receives_datetime_with_no_date_params(self):
        """Default (no date params) must also pass datetime, not date."""
        service, repo = _make_service()
        repo.find_sales_with_items_in_range.return_value = []
        repo.find_expenses_in_range.return_value = []

        await service.get_profit_loss(None, None)

        start_arg, end_arg = repo.find_expenses_in_range.call_args.args
        assert isinstance(start_arg, datetime)
        assert isinstance(end_arg, datetime)

    def test_profit_loss_endpoint_returns_200_with_date_params(self):
        """Integration: /profit-loss must not 500 when date params are supplied."""
        user = _make_fake_user(role="admin")
        token = create_access_token({"sub": user.id, "role": "admin"})
        db = _make_reports_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get(
                "/api/reports/profit-loss?start_date=2026-04-01&end_date=2026-04-30",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}. "
            "Likely cause: bare date passed to Prisma @db.Date column."
        )
        b = body(resp)
        assert b["success"] is True
        assert "revenue" in b["data"]
        assert "net_profit" in b["data"]

    def test_profit_loss_endpoint_returns_200_without_date_params(self):
        """Integration: /profit-loss must not 500 when no date params are given."""
        user = _make_fake_user(role="admin")
        token = create_access_token({"sub": user.id, "role": "admin"})
        db = _make_reports_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get(
                "/api/reports/profit-loss",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        assert body(resp)["success"] is True


# ---------------------------------------------------------------------------
# Bug 2 — expenses report: find_expenses_in_range must receive datetime
# ---------------------------------------------------------------------------

class TestExpensesReportDateTypeRegression:
    @pytest.mark.asyncio
    async def test_find_expenses_in_range_receives_datetime_not_date(self):
        """get_expenses_report must pass datetime objects to find_expenses_in_range."""
        service, repo = _make_service()
        repo.find_expenses_in_range.return_value = []

        await service.get_expenses_report("2026-04-01", "2026-04-30")

        start_arg, end_arg = repo.find_expenses_in_range.call_args.args
        assert isinstance(start_arg, datetime), (
            f"Expected datetime, got {type(start_arg).__name__}."
        )
        assert isinstance(end_arg, datetime)
        assert start_arg.tzinfo is not None
        assert end_arg.tzinfo is not None

    def test_expenses_endpoint_returns_200_with_date_params(self):
        user = _make_fake_user(role="admin")
        token = create_access_token({"sub": user.id, "role": "admin"})
        db = _make_reports_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get(
                "/api/reports/expenses?start_date=2026-04-01&end_date=2026-04-30",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}."
        )
        assert body(resp)["success"] is True


# ---------------------------------------------------------------------------
# Bug 3 — purchases report: find_pos_in_range must receive datetime
# ---------------------------------------------------------------------------

class TestPurchasesReportDateTypeRegression:
    @pytest.mark.asyncio
    async def test_find_pos_in_range_receives_datetime_not_date(self):
        """get_purchases_report must pass datetime objects to find_pos_in_range."""
        service, repo = _make_service()
        repo.find_pos_in_range.return_value = []

        await service.get_purchases_report("2026-04-01", "2026-04-30")

        start_arg, end_arg = repo.find_pos_in_range.call_args.args
        assert isinstance(start_arg, datetime), (
            f"Expected datetime, got {type(start_arg).__name__}. "
            "PurchaseOrder.orderDate is @db.Date — bare date causes a 500."
        )
        assert isinstance(end_arg, datetime)
        assert start_arg.tzinfo is not None
        assert end_arg.tzinfo is not None

    def test_purchases_endpoint_returns_200_with_date_params(self):
        user = _make_fake_user(role="admin")
        token = create_access_token({"sub": user.id, "role": "admin"})
        db = _make_reports_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get(
                "/api/reports/purchases?start_date=2026-04-01&end_date=2026-04-30",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200, (
            f"Expected 200, got {resp.status_code}."
        )
        assert body(resp)["success"] is True

    def test_purchases_endpoint_returns_200_without_date_params(self):
        user = _make_fake_user(role="admin")
        token = create_access_token({"sub": user.id, "role": "admin"})
        db = _make_reports_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get(
                "/api/reports/purchases",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        assert body(resp)["success"] is True


# ---------------------------------------------------------------------------
# Verify _parse_date_range returns datetime, not date
# ---------------------------------------------------------------------------

class TestParseDateRangeReturnType:
    def test_returns_datetime_with_explicit_dates(self):
        service = ReportsService(MagicMock())
        start, end = service._parse_date_range("2026-04-01", "2026-04-30")
        assert isinstance(start, datetime), f"Expected datetime, got {type(start).__name__}"
        assert isinstance(end, datetime), f"Expected datetime, got {type(end).__name__}"
        assert start.tzinfo is not None
        assert end.tzinfo is not None

    def test_returns_datetime_with_no_params(self):
        service = ReportsService(MagicMock())
        start, end = service._parse_date_range(None, None)
        assert isinstance(start, datetime)
        assert isinstance(end, datetime)

    def test_never_returns_bare_date(self):
        service = ReportsService(MagicMock())
        for start_str, end_str in [
            ("2026-01-01", "2026-12-31"),
            (None, "2026-06-30"),
            ("2026-03-01", None),
            (None, None),
        ]:
            start, end = service._parse_date_range(start_str, end_str)
            assert not isinstance(start, date) or isinstance(start, datetime), (
                "date is a superclass of datetime — must be datetime specifically"
            )
            # More explicit: datetime is a subclass of date, so check type exactly
            assert type(start) is datetime, f"Got {type(start).__name__}, expected datetime"
            assert type(end) is datetime, f"Got {type(end).__name__}, expected datetime"
