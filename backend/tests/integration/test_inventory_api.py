"""
Integration tests for inventory endpoints:
  GET  /api/inventory/movements
  POST /api/inventory/adjust
  GET  /api/inventory/valuation

Tests run against the FastAPI TestClient with the Prisma DB layer mocked.
No live database is required.
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from src.core.auth import create_access_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def body(response) -> dict:
    return json.loads(response.content)


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


def _make_inventory_db(movements=None, product=None, movement_count=0):
    db = MagicMock()
    db.stockmovement = MagicMock()
    db.stockmovement.find_many = AsyncMock(return_value=movements or [])
    db.stockmovement.count = AsyncMock(return_value=movement_count)
    db.product = MagicMock()
    db.product.find_first = AsyncMock(return_value=product)
    db.product.find_many = AsyncMock(return_value=[product] if product else [])
    db.user.find_first = AsyncMock(return_value=None)  # overridden per-test for auth

    # Mock the transaction context manager
    mock_tx = MagicMock()
    fake_movement = movements[0] if movements else _make_fake_movement()
    mock_tx.stockmovement = MagicMock()
    mock_tx.stockmovement.create = AsyncMock(return_value=fake_movement)
    mock_tx.product = MagicMock()
    mock_tx.product.update = AsyncMock(return_value=None)

    @asynccontextmanager
    async def fake_tx():
        yield mock_tx

    db.tx = fake_tx
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
# GET /api/inventory/movements
# ---------------------------------------------------------------------------

class TestListMovements:
    def test_list_returns_200_paginated(self):
        fake_movement = _make_fake_movement()
        token, user = _admin_token()
        db = _make_inventory_db(movements=[fake_movement], movement_count=1)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/inventory/movements", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert "pagination" in b
        assert isinstance(b["data"], list)
        assert len(b["data"]) == 1

    def test_list_requires_auth(self):
        db = _make_inventory_db()
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/inventory/movements")

        assert resp.status_code == 401

    def test_list_with_staff_returns_200(self):
        fake_movement = _make_fake_movement()
        token, user = _staff_token()
        db = _make_inventory_db(movements=[fake_movement], movement_count=1)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/inventory/movements", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True


# ---------------------------------------------------------------------------
# POST /api/inventory/adjust
# ---------------------------------------------------------------------------

class TestAdjust:
    def test_adjust_with_manager_returns_201(self):
        product = _make_fake_product(stock_quantity=100)
        fake_movement = _make_fake_movement(product=product)
        token, user = _manager_token()
        db = _make_inventory_db(movements=[fake_movement], product=product)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/inventory/adjust",
                json={"product_id": "prod-uuid", "quantity": 10, "notes": "Restock"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 201
        b = body(resp)
        assert b["success"] is True

    def test_adjust_with_staff_returns_403(self):
        token, user = _staff_token()
        db = _make_inventory_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/inventory/adjust",
                json={"product_id": "prod-uuid", "quantity": 10},
                cookies={"access_token": token},
            )

        assert resp.status_code == 403

    def test_adjust_quantity_zero_returns_422(self):
        token, user = _admin_token()
        db = _make_inventory_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/inventory/adjust",
                json={"product_id": "prod-uuid", "quantity": 0},
                cookies={"access_token": token},
            )

        assert resp.status_code == 422

    def test_adjust_negative_stock_returns_422(self):
        product = _make_fake_product(stock_quantity=5)
        token, user = _admin_token()
        db = _make_inventory_db(product=product)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/inventory/adjust",
                json={"product_id": "prod-uuid", "quantity": -20},
                cookies={"access_token": token},
            )

        assert resp.status_code == 422

    def test_adjust_product_not_found_returns_404(self):
        token, user = _admin_token()
        db = _make_inventory_db(product=None)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/inventory/adjust",
                json={"product_id": "nonexistent-id", "quantity": 10},
                cookies={"access_token": token},
            )

        assert resp.status_code == 404
        assert body(resp)["code"] == "NOT_FOUND"

    def test_adjust_inactive_product_returns_422(self):
        product = _make_fake_product(is_active=False)
        token, user = _admin_token()
        db = _make_inventory_db(product=product)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/inventory/adjust",
                json={"product_id": "prod-uuid", "quantity": 10},
                cookies={"access_token": token},
            )

        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/inventory/valuation
# ---------------------------------------------------------------------------

class TestValuation:
    def test_valuation_with_admin_returns_200(self):
        product = _make_fake_product(stock_quantity=10, cost_price=5000)
        token, user = _admin_token()
        db = _make_inventory_db(product=product)
        db.product.find_many = AsyncMock(return_value=[product])
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/inventory/valuation", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert "total_value" in b["data"]
        assert "product_count" in b["data"]
        assert "currency" in b["data"]
        assert b["data"]["currency"] == "BDT"

    def test_valuation_with_staff_returns_403(self):
        token, user = _staff_token()
        db = _make_inventory_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/inventory/valuation", cookies={"access_token": token})

        assert resp.status_code == 403
