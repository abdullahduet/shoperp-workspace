"""
Integration tests for dashboard endpoints:
  GET /api/dashboard/summary
  GET /api/dashboard/trends

Tests run against the FastAPI TestClient with the Prisma DB layer mocked.
No live database is required.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from src.core.auth import create_access_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def body(response) -> dict:
    return json.loads(response.content)


def _make_fake_user(*, user_id: str = "user-uuid-1", role: str = "admin") -> MagicMock:
    user = MagicMock()
    user.id = user_id
    user.email = f"{role}@test.com"
    user.name = f"{role.title()} User"
    user.role = role
    user.isActive = True
    user.lastLoginAt = None
    user.createdAt = datetime(2024, 1, 1, tzinfo=timezone.utc)
    user.deletedAt = None
    return user


def _make_dashboard_db() -> MagicMock:
    """Build a mock Prisma client for dashboard tests."""
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
    """Return a FastAPI TestClient with the given mock DB injected."""
    with patch("src.database._db", mock_db), \
         patch("src.database.connect", new_callable=AsyncMock), \
         patch("src.database.disconnect", new_callable=AsyncMock):
        import src.main as main_module
        return TestClient(main_module.app, raise_server_exceptions=False)


def _admin_token() -> tuple[str, MagicMock]:
    user = _make_fake_user(role="admin")
    token = create_access_token({"sub": user.id, "role": "admin"})
    return token, user


def _manager_token() -> tuple[str, MagicMock]:
    user = _make_fake_user(user_id="manager-uuid", role="manager")
    token = create_access_token({"sub": user.id, "role": "manager"})
    return token, user


def _staff_token() -> tuple[str, MagicMock]:
    user = _make_fake_user(user_id="staff-uuid", role="staff")
    token = create_access_token({"sub": user.id, "role": "staff"})
    return token, user


# ---------------------------------------------------------------------------
# GET /api/dashboard/summary
# ---------------------------------------------------------------------------

class TestGetSummary:
    def test_admin_200(self):
        token, user = _admin_token()
        db = _make_dashboard_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/dashboard/summary", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert "today_sales" in b["data"]
        assert "month_revenue" in b["data"]
        assert "low_stock_count" in b["data"]

    def test_staff_403(self):
        token, user = _staff_token()
        db = _make_dashboard_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/dashboard/summary", cookies={"access_token": token})

        assert resp.status_code == 403

    def test_unauthenticated_401(self):
        db = _make_dashboard_db()
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/dashboard/summary")

        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/dashboard/trends
# ---------------------------------------------------------------------------

class TestGetTrends:
    def test_admin_200(self):
        token, user = _admin_token()
        db = _make_dashboard_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/dashboard/trends", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert isinstance(b["data"], list)

    def test_staff_403(self):
        token, user = _staff_token()
        db = _make_dashboard_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/dashboard/trends", cookies={"access_token": token})

        assert resp.status_code == 403
