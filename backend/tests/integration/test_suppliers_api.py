"""
Integration tests for suppliers endpoints:
  GET    /api/suppliers
  GET    /api/suppliers/:id
  GET    /api/suppliers/:id/purchases
  POST   /api/suppliers
  PUT    /api/suppliers/:id
  DELETE /api/suppliers/:id

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


def _make_fake_supplier(
    *,
    supplier_id: str = "supplier-uuid-1",
    name: str = "Test Supplier",
    is_active: bool = True,
) -> MagicMock:
    """Create a MagicMock that mimics a Prisma Supplier model."""
    supplier = MagicMock()
    supplier.id = supplier_id
    supplier.name = name
    supplier.contactPerson = "Jane Doe"
    supplier.phone = "01711000000"
    supplier.email = "test@supplier.com"
    supplier.address = "123 Main St"
    supplier.city = "Dhaka"
    supplier.country = "Bangladesh"
    supplier.paymentTerms = "Net 30"
    supplier.isActive = is_active
    supplier.notes = None
    supplier.createdAt = datetime(2024, 1, 1, tzinfo=timezone.utc)
    supplier.deletedAt = None
    return supplier


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


def _make_supplier_db(
    find_many_return=None,
    find_first_return=None,
    create_return=None,
    update_return=None,
    count_return: int = 0,
) -> MagicMock:
    """Build a mock Prisma client with supplier method stubs."""
    db = MagicMock()
    db.supplier = MagicMock()
    db.supplier.find_many = AsyncMock(return_value=find_many_return or [])
    db.supplier.find_first = AsyncMock(return_value=find_first_return)
    db.supplier.create = AsyncMock(return_value=create_return)
    db.supplier.update = AsyncMock(return_value=update_return)
    db.supplier.count = AsyncMock(return_value=count_return)
    # purchase order stubs for /purchases endpoint
    db.purchaseorder = MagicMock()
    db.purchaseorder.find_many = AsyncMock(return_value=[])
    db.purchaseorder.count = AsyncMock(return_value=0)
    # user.find_first needed for auth checks
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
# GET /api/suppliers
# ---------------------------------------------------------------------------

class TestListSuppliers:
    def test_returns_200_paginated_list(self):
        fake_supplier = _make_fake_supplier()
        token, user = _admin_token()
        db = _make_supplier_db(find_many_return=[fake_supplier], count_return=1)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/suppliers", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert "pagination" in b
        assert isinstance(b["data"], list)

    def test_returns_401_without_auth(self):
        db = _make_supplier_db()
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/suppliers")

        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/suppliers
# ---------------------------------------------------------------------------

class TestCreateSupplier:
    def test_manager_can_create_supplier_returns_201(self):
        fake_supplier = _make_fake_supplier()
        token, user = _manager_token()
        db = _make_supplier_db(create_return=fake_supplier)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/suppliers",
                json={"name": "Test Supplier"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 201
        b = body(resp)
        assert b["success"] is True

    def test_staff_cannot_create_supplier_returns_403(self):
        token, user = _staff_token()
        db = _make_supplier_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/suppliers",
                json={"name": "Test Supplier"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 403

    def test_missing_name_returns_422(self):
        token, user = _admin_token()
        db = _make_supplier_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/suppliers",
                json={"contact_person": "John"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PUT /api/suppliers/:id
# ---------------------------------------------------------------------------

class TestUpdateSupplier:
    def test_manager_can_update_supplier_returns_200(self):
        fake_supplier = _make_fake_supplier()
        updated_supplier = _make_fake_supplier(name="Updated Supplier")
        token, user = _manager_token()
        db = _make_supplier_db(find_first_return=fake_supplier, update_return=updated_supplier)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.put(
                "/api/suppliers/supplier-uuid-1",
                json={"name": "Updated Supplier"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True

    def test_nonexistent_supplier_returns_404(self):
        token, user = _admin_token()
        db = _make_supplier_db(find_first_return=None)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.put(
                "/api/suppliers/nonexistent-id",
                json={"name": "X"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 404
        assert body(resp)["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# DELETE /api/suppliers/:id
# ---------------------------------------------------------------------------

class TestDeleteSupplier:
    def test_admin_can_delete_supplier_returns_200(self):
        fake_supplier = _make_fake_supplier()
        token, user = _admin_token()
        db = _make_supplier_db(find_first_return=fake_supplier, update_return=fake_supplier)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.delete(
                "/api/suppliers/supplier-uuid-1",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True

    def test_manager_cannot_delete_supplier_returns_403(self):
        token, user = _manager_token()
        db = _make_supplier_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.delete(
                "/api/suppliers/some-id",
                cookies={"access_token": token},
            )

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/suppliers/:id/purchases
# ---------------------------------------------------------------------------

class TestGetSupplierPurchases:
    def test_admin_can_get_supplier_purchases_returns_200(self):
        fake_supplier = _make_fake_supplier()
        token, user = _admin_token()
        db = _make_supplier_db(find_first_return=fake_supplier, count_return=0)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get(
                "/api/suppliers/supplier-uuid-1/purchases",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert "pagination" in b
