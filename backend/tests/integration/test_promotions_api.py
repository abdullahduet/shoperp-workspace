"""
Integration tests for promotions endpoints:
  GET    /api/promotions
  GET    /api/promotions/active
  GET    /api/promotions/:id
  POST   /api/promotions
  PUT    /api/promotions/:id
  DELETE /api/promotions/:id

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


def _make_fake_pp(product_id: str = "prod-uuid-1") -> MagicMock:
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
) -> MagicMock:
    """Create a MagicMock that mimics a Prisma Promotion model."""
    promo = MagicMock()
    promo.id = promotion_id
    promo.name = name
    promo.type = promo_type
    promo.value = value
    promo.appliesTo = applies_to
    promo.isActive = is_active
    promo.minPurchaseAmount = min_purchase_amount
    promo.startDate = datetime(2026, 6, 1, tzinfo=timezone.utc)
    promo.endDate = datetime(2026, 6, 30, tzinfo=timezone.utc)
    promo.createdAt = datetime(2026, 4, 11, tzinfo=timezone.utc)
    promo.deletedAt = None
    promo.promotionProducts = (
        [_make_fake_pp(pid) for pid in product_ids] if product_ids else []
    )
    return promo


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


def _make_promotion_db(
    find_many_return=None,
    find_first_return=None,
    create_return=None,
    update_return=None,
    count_return: int = 0,
) -> MagicMock:
    """Build a mock Prisma client with promotion method stubs."""
    db = MagicMock()

    # promotion
    db.promotion = MagicMock()
    db.promotion.find_many = AsyncMock(return_value=find_many_return or [])
    db.promotion.find_first = AsyncMock(return_value=find_first_return)
    db.promotion.create = AsyncMock(return_value=create_return)
    db.promotion.update = AsyncMock(return_value=update_return)
    db.promotion.count = AsyncMock(return_value=count_return)

    # promotionproduct
    db.promotionproduct = MagicMock()
    db.promotionproduct.create = AsyncMock(return_value=None)
    db.promotionproduct.delete_many = AsyncMock(return_value=None)

    # user
    db.user = MagicMock()
    db.user.find_first = AsyncMock(return_value=None)

    # Transaction mock
    mock_tx = MagicMock()
    mock_tx.promotion = MagicMock()
    mock_tx.promotion.create = AsyncMock(return_value=create_return or _make_fake_promotion())
    mock_tx.promotion.update = AsyncMock(return_value=update_return)
    mock_tx.promotionproduct = MagicMock()
    mock_tx.promotionproduct.create = AsyncMock(return_value=None)
    mock_tx.promotionproduct.delete_many = AsyncMock(return_value=None)

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
# GET /api/promotions
# ---------------------------------------------------------------------------

class TestListPromotions:
    def test_admin_gets_paginated_promotions_returns_200(self):
        fake_promo = _make_fake_promotion()
        token, user = _admin_token()
        db = _make_promotion_db(find_many_return=[fake_promo], count_return=1)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get(
                "/api/promotions",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert "pagination" in b
        assert b["pagination"]["total"] == 1
        assert len(b["data"]) == 1
        assert b["data"][0]["name"] == "Summer Sale"

    def test_unauthenticated_returns_401(self):
        db = _make_promotion_db()
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/promotions")

        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/promotions/active
# ---------------------------------------------------------------------------

class TestGetActivePromotions:
    def test_staff_gets_active_promotions_returns_200(self):
        fake_promo = _make_fake_promotion()
        token, user = _staff_token()
        db = _make_promotion_db(find_many_return=[fake_promo])
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get(
                "/api/promotions/active",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert isinstance(b["data"], list)

    def test_active_route_not_shadowed_by_id_route(self):
        """Verify /active is not treated as a promotion_id."""
        token, user = _admin_token()
        db = _make_promotion_db(find_many_return=[])
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get(
                "/api/promotions/active",
                cookies={"access_token": token},
            )

        # Should NOT be a 404 (which would happen if /active was treated as /{id})
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/promotions/:id
# ---------------------------------------------------------------------------

class TestGetPromotion:
    def test_returns_promotion_by_id(self):
        fake_promo = _make_fake_promotion(product_ids=["prod-1"])
        token, user = _admin_token()
        db = _make_promotion_db(find_first_return=fake_promo)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get(
                "/api/promotions/promo-uuid-1",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert b["data"]["id"] == "promo-uuid-1"
        assert b["data"]["product_ids"] == ["prod-1"]

    def test_returns_404_for_missing_promotion(self):
        token, user = _admin_token()
        db = _make_promotion_db(find_first_return=None)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get(
                "/api/promotions/nonexistent-id",
                cookies={"access_token": token},
            )

        assert resp.status_code == 404
        assert body(resp)["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# POST /api/promotions
# ---------------------------------------------------------------------------

class TestCreatePromotion:
    def test_manager_creates_promotion_returns_201(self):
        fake_promo = _make_fake_promotion()
        token, user = _manager_token()
        db = _make_promotion_db(find_first_return=fake_promo)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/promotions",
                json={
                    "name": "Summer Sale",
                    "type": "percentage",
                    "value": 20,
                    "start_date": "2026-06-01T00:00:00+00:00",
                    "end_date": "2026-06-30T00:00:00+00:00",
                },
                cookies={"access_token": token},
            )

        assert resp.status_code == 201
        b = body(resp)
        assert b["success"] is True

    def test_staff_cannot_create_promotion_returns_403(self):
        token, user = _staff_token()
        db = _make_promotion_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/promotions",
                json={
                    "name": "Unauthorized",
                    "type": "fixed",
                    "value": 100,
                    "start_date": "2026-06-01T00:00:00+00:00",
                    "end_date": "2026-06-30T00:00:00+00:00",
                },
                cookies={"access_token": token},
            )

        assert resp.status_code == 403

    def test_missing_required_fields_returns_422(self):
        token, user = _admin_token()
        db = _make_promotion_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/promotions",
                json={"name": "Incomplete"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PUT /api/promotions/:id
# ---------------------------------------------------------------------------

class TestUpdatePromotion:
    def test_manager_updates_promotion_returns_200(self):
        fake_promo = _make_fake_promotion()
        updated_promo = _make_fake_promotion(name="Updated Sale")
        token, user = _manager_token()
        db = _make_promotion_db(find_first_return=fake_promo)
        db.promotion.find_first = AsyncMock(side_effect=[fake_promo, updated_promo])
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.put(
                "/api/promotions/promo-uuid-1",
                json={"name": "Updated Sale"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True

    def test_returns_404_for_missing_promotion(self):
        token, user = _admin_token()
        db = _make_promotion_db(find_first_return=None)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.put(
                "/api/promotions/nonexistent-id",
                json={"name": "Ghost"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/promotions/:id
# ---------------------------------------------------------------------------

class TestDeletePromotion:
    def test_admin_deletes_promotion_returns_200(self):
        fake_promo = _make_fake_promotion()
        token, user = _admin_token()
        db = _make_promotion_db(find_first_return=fake_promo, update_return=fake_promo)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.delete(
                "/api/promotions/promo-uuid-1",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True

    def test_manager_cannot_delete_promotion_returns_403(self):
        token, user = _manager_token()
        db = _make_promotion_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.delete(
                "/api/promotions/promo-uuid-1",
                cookies={"access_token": token},
            )

        assert resp.status_code == 403

    def test_returns_404_for_missing_promotion(self):
        token, user = _admin_token()
        db = _make_promotion_db(find_first_return=None)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.delete(
                "/api/promotions/nonexistent-id",
                cookies={"access_token": token},
            )

        assert resp.status_code == 404
