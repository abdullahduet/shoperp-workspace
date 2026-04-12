"""
Integration tests for products endpoints:
  GET    /api/products
  GET    /api/products/low-stock
  GET    /api/products/:id
  POST   /api/products
  PUT    /api/products/:id
  DELETE /api/products/:id
  POST   /api/products/import

Tests run against the FastAPI TestClient with the Prisma DB layer mocked.
No live database is required.
"""
from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from src.core.auth import create_access_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def body(response) -> dict:
    return json.loads(response.content)


def _make_fake_product(
    *,
    product_id: str = "product-uuid-1",
    name: str = "Test Product",
    sku: str = "SKU-001",
    barcode: str | None = None,
    category_id: str | None = None,
    unit_price: int = 1000,
    cost_price: int = 800,
    tax_rate: Decimal = Decimal("0.00"),
    stock_quantity: int = 10,
    min_stock_level: int = 5,
    unit_of_measure: str = "pcs",
    is_active: bool = True,
) -> MagicMock:
    """Create a MagicMock that mimics a Prisma Product model."""
    product = MagicMock()
    product.id = product_id
    product.name = name
    product.sku = sku
    product.barcode = barcode
    product.categoryId = category_id
    product.description = None
    product.unitPrice = unit_price
    product.costPrice = cost_price
    product.taxRate = tax_rate
    product.stockQuantity = stock_quantity
    product.minStockLevel = min_stock_level
    product.unitOfMeasure = unit_of_measure
    product.imageUrl = None
    product.isActive = is_active
    product.createdAt = datetime(2024, 1, 1, tzinfo=timezone.utc)
    product.deletedAt = None
    return product


def _make_fake_user(
    *,
    user_id: str = "user-uuid-1",
    role: str = "admin",
) -> MagicMock:
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


def _make_product_db(
    find_many_return=None,
    find_first_return=None,
    create_return=None,
    update_return=None,
    count_return: int = 0,
) -> MagicMock:
    """Build a mock Prisma client with product method stubs."""
    db = MagicMock()
    db.product.find_many = AsyncMock(return_value=find_many_return or [])
    db.product.find_first = AsyncMock(return_value=find_first_return)
    db.product.create = AsyncMock(return_value=create_return)
    db.product.update = AsyncMock(return_value=update_return)
    db.product.count = AsyncMock(return_value=count_return)
    # category stubs to avoid attribute errors
    db.category.find_many = AsyncMock(return_value=[])
    db.category.find_first = AsyncMock(return_value=None)
    # user.find_first is needed for auth checks
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
# GET /api/products
# ---------------------------------------------------------------------------

class TestListProducts:
    def test_returns_200_paginated_list(self):
        fake_product = _make_fake_product()
        token, user = _admin_token()
        db = _make_product_db(find_many_return=[fake_product], count_return=1)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/products", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert "pagination" in b
        assert isinstance(b["data"], list)

    def test_returns_401_without_auth(self):
        db = _make_product_db()
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/products")

        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/products/low-stock
# ---------------------------------------------------------------------------

class TestLowStock:
    def test_returns_200_with_low_stock_list(self):
        low_product = _make_fake_product(stock_quantity=2, min_stock_level=5)
        token, user = _admin_token()
        db = _make_product_db(find_many_return=[low_product])
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/products/low-stock", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert isinstance(b["data"], list)


# ---------------------------------------------------------------------------
# GET /api/products/:id
# ---------------------------------------------------------------------------

class TestGetProduct:
    def test_returns_200_with_product_detail(self):
        fake_product = _make_fake_product()
        token, user = _admin_token()
        db = _make_product_db(find_first_return=fake_product)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get(
                "/api/products/product-uuid-1",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert b["data"]["sku"] == fake_product.sku

    def test_returns_404_for_missing_product(self):
        token, user = _admin_token()
        db = _make_product_db(find_first_return=None)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get(
                "/api/products/nonexistent-id",
                cookies={"access_token": token},
            )

        assert resp.status_code == 404
        assert body(resp)["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# POST /api/products
# ---------------------------------------------------------------------------

class TestCreateProduct:
    def test_manager_can_create_product_returns_201(self):
        fake_product = _make_fake_product()
        token, user = _manager_token()
        db = _make_product_db(create_return=fake_product)
        db.product.find_first = AsyncMock(return_value=None)  # no dup SKU/barcode
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/products",
                json={"name": "Test Product", "sku": "SKU-001"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 201
        b = body(resp)
        assert b["success"] is True

    def test_admin_can_create_product_returns_201(self):
        fake_product = _make_fake_product()
        token, user = _admin_token()
        db = _make_product_db(create_return=fake_product)
        db.product.find_first = AsyncMock(return_value=None)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/products",
                json={"name": "Test Product", "sku": "SKU-001"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 201

    def test_staff_cannot_create_product_returns_403(self):
        token, user = _staff_token()
        db = _make_product_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/products",
                json={"name": "Test Product", "sku": "SKU-001"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 403

    def test_missing_name_returns_422(self):
        token, user = _admin_token()
        db = _make_product_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/products",
                json={"sku": "SKU-001"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 422

    def test_duplicate_sku_returns_409(self):
        existing = _make_fake_product(sku="SKU-DUP")
        token, user = _admin_token()
        db = _make_product_db()
        # find_by_sku returns an existing product → SKU conflict fires
        db.product.find_first = AsyncMock(return_value=existing)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/products",
                json={"name": "Duplicate SKU Product", "sku": "SKU-DUP"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 409

    def test_duplicate_barcode_returns_409(self):
        existing = _make_fake_product(barcode="BAR-DUP")
        token, user = _admin_token()
        db = _make_product_db()
        # First call (find_by_sku) returns None so SKU check passes,
        # second call (find_by_barcode) returns existing product so barcode check fires
        db.product.find_first = AsyncMock(side_effect=[None, existing])
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/products",
                json={"name": "Duplicate Barcode Product", "sku": "SKU-NEW", "barcode": "BAR-DUP"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# PUT /api/products/:id
# ---------------------------------------------------------------------------

class TestUpdateProduct:
    def test_admin_can_update_product_returns_200(self):
        existing = _make_fake_product(product_id="pid")
        updated = _make_fake_product(product_id="pid", name="Updated Name")
        token, user = _admin_token()
        db = _make_product_db(find_first_return=existing, update_return=updated)
        db.product.find_first = AsyncMock(return_value=existing)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.put(
                "/api/products/pid",
                json={"name": "Updated Name"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True

    def test_nonexistent_product_returns_404(self):
        token, user = _admin_token()
        db = _make_product_db(find_first_return=None)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.put(
                "/api/products/nonexistent-id",
                json={"name": "X"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 404
        assert body(resp)["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# DELETE /api/products/:id
# ---------------------------------------------------------------------------

class TestDeleteProduct:
    def test_admin_can_delete_product_returns_200(self):
        existing = _make_fake_product(product_id="pid")
        token, user = _admin_token()
        db = _make_product_db(find_first_return=existing, update_return=existing)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.delete(
                "/api/products/pid",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True

    def test_manager_cannot_delete_product_returns_403(self):
        token, user = _manager_token()
        db = _make_product_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.delete(
                "/api/products/some-id",
                cookies={"access_token": token},
            )

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/products/import
# ---------------------------------------------------------------------------

class TestImportProducts:
    def test_import_csv_returns_200_with_result(self):
        token, user = _admin_token()
        db = _make_product_db()
        db.product.find_first = AsyncMock(return_value=None)  # no dup SKUs
        db.product.create = AsyncMock(return_value=_make_fake_product())
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        csv_content = b"name,sku\nProduct A,SKU-A\nProduct B,SKU-B\n"

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/products/import",
                files={"file": ("products.csv", io.BytesIO(csv_content), "text/csv")},
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert "created" in b["data"]
        assert "skipped" in b["data"]
        assert "errors" in b["data"]

    def test_import_requires_admin_role(self):
        token, user = _manager_token()
        db = _make_product_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        csv_content = b"name,sku\nProduct A,SKU-A\n"

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/products/import",
                files={"file": ("products.csv", io.BytesIO(csv_content), "text/csv")},
                cookies={"access_token": token},
            )

        assert resp.status_code == 403
