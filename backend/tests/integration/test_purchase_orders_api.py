"""
Integration tests for purchase orders endpoints:
  GET    /api/purchase-orders
  POST   /api/purchase-orders
  GET    /api/purchase-orders/:id
  PUT    /api/purchase-orders/:id
  DELETE /api/purchase-orders/:id
  POST   /api/purchase-orders/:id/submit
  POST   /api/purchase-orders/:id/receive
  POST   /api/purchase-orders/:id/cancel

Tests run against the FastAPI TestClient with the Prisma DB layer mocked.
No live database is required.
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from src.core.auth import create_access_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def body(response) -> dict:
    return json.loads(response.content)


def _make_fake_product(*, product_id: str = "prod-uuid-1", stock_quantity: int = 50) -> MagicMock:
    product = MagicMock()
    product.id = product_id
    product.name = "Test Product"
    product.sku = "SKU-001"
    product.stockQuantity = stock_quantity
    product.deletedAt = None
    return product


def _make_fake_item(
    *,
    item_id: str = "item-uuid-1",
    po_id: str = "po-uuid-1",
    product_id: str = "prod-uuid-1",
    quantity: int = 10,
    received_quantity: int = 0,
    unit_cost: int = 500,
) -> MagicMock:
    item = MagicMock()
    item.id = item_id
    item.purchaseOrderId = po_id
    item.productId = product_id
    item.quantity = quantity
    item.receivedQuantity = received_quantity
    item.unitCost = unit_cost
    item.totalCost = quantity * unit_cost
    product = MagicMock()
    product.name = "Test Product"
    product.sku = "SKU-001"
    item.product = product
    return item


def _make_fake_po(
    *,
    po_id: str = "po-uuid-1",
    status: str = "draft",
    items: list | None = None,
) -> MagicMock:
    """Create a MagicMock that mimics a Prisma PurchaseOrder model."""
    po = MagicMock()
    po.id = po_id
    po.poNumber = "PO-20260411-001"
    po.supplierId = "supplier-uuid-1"
    po.status = status
    po.subtotal = 5000
    po.taxAmount = 0
    po.totalAmount = 5000
    po.createdBy = "user-uuid-1"
    po.orderDate = date.today()
    po.expectedDate = None
    po.createdAt = datetime(2026, 4, 11, tzinfo=timezone.utc)
    po.deletedAt = None
    po.notes = None
    supplier = MagicMock()
    supplier.name = "Test Supplier"
    po.supplier = supplier
    po.purchaseOrderItems = items if items is not None else [_make_fake_item(po_id=po_id)]
    return po


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


def _make_po_db(
    find_many_return=None,
    find_first_po_return=None,
    create_return=None,
    update_return=None,
    count_po_return: int = 0,
    find_first_product_return=None,
) -> MagicMock:
    """Build a mock Prisma client with purchase order method stubs."""
    db = MagicMock()

    # purchase order
    db.purchaseorder = MagicMock()
    db.purchaseorder.find_many = AsyncMock(return_value=find_many_return or [])
    db.purchaseorder.find_first = AsyncMock(return_value=find_first_po_return)
    db.purchaseorder.create = AsyncMock(return_value=create_return)
    db.purchaseorder.update = AsyncMock(return_value=update_return)
    db.purchaseorder.count = AsyncMock(return_value=count_po_return)

    # purchase order items
    db.purchaseorderitem = MagicMock()
    db.purchaseorderitem.find_first = AsyncMock(return_value=None)
    db.purchaseorderitem.delete_many = AsyncMock(return_value=None)
    db.purchaseorderitem.create = AsyncMock(return_value=None)
    db.purchaseorderitem.update = AsyncMock(return_value=None)

    # product
    db.product = MagicMock()
    db.product.find_first = AsyncMock(return_value=find_first_product_return)
    db.product.update = AsyncMock(return_value=None)

    # stock movement
    db.stockmovement = MagicMock()
    db.stockmovement.create = AsyncMock(return_value=None)

    # user
    db.user = MagicMock()
    db.user.find_first = AsyncMock(return_value=None)

    # Transaction mock
    mock_tx = MagicMock()
    mock_tx.purchaseorderitem = MagicMock()
    mock_tx.purchaseorderitem.delete_many = AsyncMock(return_value=None)
    mock_tx.purchaseorderitem.create = AsyncMock(return_value=None)
    mock_tx.purchaseorderitem.update = AsyncMock(return_value=None)
    mock_tx.purchaseorder = MagicMock()
    mock_tx.purchaseorder.update = AsyncMock(return_value=None)
    mock_tx.product = MagicMock()
    mock_tx.product.update = AsyncMock(return_value=None)
    mock_tx.stockmovement = MagicMock()
    mock_tx.stockmovement.create = AsyncMock(return_value=None)

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
# GET /api/purchase-orders
# ---------------------------------------------------------------------------

class TestListPOs:
    def test_admin_returns_200_paginated(self):
        fake_po = _make_fake_po()
        token, user = _admin_token()
        db = _make_po_db(find_many_return=[fake_po], count_po_return=1)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/purchase-orders", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert "pagination" in b
        assert isinstance(b["data"], list)

    def test_staff_returns_403(self):
        token, user = _staff_token()
        db = _make_po_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/purchase-orders", cookies={"access_token": token})

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/purchase-orders
# ---------------------------------------------------------------------------

class TestCreatePO:
    def test_manager_can_create_po_returns_201(self):
        fake_po = _make_fake_po()
        token, user = _manager_token()
        db = _make_po_db(create_return=fake_po, count_po_return=0)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/purchase-orders",
                json={
                    "supplier_id": "supplier-uuid-1",
                    "items": [{"product_id": "prod-uuid-1", "quantity": 5, "unit_cost": 1000}],
                },
                cookies={"access_token": token},
            )

        assert resp.status_code == 201
        b = body(resp)
        assert b["success"] is True

    def test_staff_cannot_create_po_returns_403(self):
        token, user = _staff_token()
        db = _make_po_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/purchase-orders",
                json={
                    "supplier_id": "supplier-uuid-1",
                    "items": [{"product_id": "prod-uuid-1", "quantity": 5, "unit_cost": 1000}],
                },
                cookies={"access_token": token},
            )

        assert resp.status_code == 403

    def test_missing_items_returns_422(self):
        token, user = _admin_token()
        db = _make_po_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/purchase-orders",
                json={"supplier_id": "supplier-uuid-1"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/purchase-orders/:id
# ---------------------------------------------------------------------------

class TestGetPO:
    def test_returns_200_with_po_detail(self):
        fake_po = _make_fake_po()
        token, user = _admin_token()
        db = _make_po_db(find_first_po_return=fake_po)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/purchase-orders/po-uuid-1", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert b["data"]["po_number"] == "PO-20260411-001"

    def test_returns_404_for_missing_po(self):
        token, user = _admin_token()
        db = _make_po_db(find_first_po_return=None)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/purchase-orders/nonexistent-id", cookies={"access_token": token})

        assert resp.status_code == 404
        assert body(resp)["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# PUT /api/purchase-orders/:id
# ---------------------------------------------------------------------------

class TestUpdatePO:
    def test_manager_can_update_draft_po_returns_200(self):
        fake_po = _make_fake_po(status="draft")
        updated_po = _make_fake_po(status="draft")
        token, user = _manager_token()
        db = _make_po_db(find_first_po_return=fake_po)
        db.purchaseorder.find_first = AsyncMock(side_effect=[fake_po, updated_po])
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.put(
                "/api/purchase-orders/po-uuid-1",
                json={"notes": "Updated notes"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True


# ---------------------------------------------------------------------------
# POST /api/purchase-orders/:id/submit
# ---------------------------------------------------------------------------

class TestSubmitPO:
    def test_submit_draft_po_returns_200(self):
        fake_po = _make_fake_po(status="draft")
        ordered_po = _make_fake_po(status="ordered")
        token, user = _admin_token()
        db = _make_po_db(find_first_po_return=fake_po, update_return=ordered_po)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/purchase-orders/po-uuid-1/submit",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True


# ---------------------------------------------------------------------------
# POST /api/purchase-orders/:id/receive
# ---------------------------------------------------------------------------

class TestReceivePO:
    def test_receive_items_returns_200(self):
        item = _make_fake_item(quantity=10, received_quantity=0)
        fake_po = _make_fake_po(status="ordered", items=[item])
        received_po = _make_fake_po(status="received", items=[item])
        product = _make_fake_product(stock_quantity=20)
        token, user = _admin_token()
        db = _make_po_db(
            find_first_po_return=fake_po,
            find_first_product_return=product,
        )
        db.purchaseorder.find_first = AsyncMock(side_effect=[fake_po, received_po])
        db.product.find_first = AsyncMock(return_value=product)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/purchase-orders/po-uuid-1/receive",
                json={"items": [{"item_id": "item-uuid-1", "received_quantity": 10}]},
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True


# ---------------------------------------------------------------------------
# POST /api/purchase-orders/:id/cancel
# ---------------------------------------------------------------------------

class TestCancelPO:
    def test_admin_can_cancel_po_returns_200(self):
        fake_po = _make_fake_po(status="ordered")
        cancelled_po = _make_fake_po(status="cancelled")
        token, user = _admin_token()
        db = _make_po_db(find_first_po_return=fake_po, update_return=cancelled_po)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/purchase-orders/po-uuid-1/cancel",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True

    def test_manager_cannot_cancel_po_returns_403(self):
        token, user = _manager_token()
        db = _make_po_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/purchase-orders/po-uuid-1/cancel",
                cookies={"access_token": token},
            )

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /api/purchase-orders/:id
# ---------------------------------------------------------------------------

class TestDeletePO:
    def test_admin_can_delete_draft_po_returns_200(self):
        fake_po = _make_fake_po(status="draft")
        token, user = _admin_token()
        db = _make_po_db(find_first_po_return=fake_po, update_return=fake_po)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.delete(
                "/api/purchase-orders/po-uuid-1",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True

    def test_admin_cannot_delete_non_draft_po_returns_422(self):
        fake_po = _make_fake_po(status="ordered")
        token, user = _admin_token()
        db = _make_po_db(find_first_po_return=fake_po)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.delete(
                "/api/purchase-orders/po-uuid-1",
                cookies={"access_token": token},
            )

        assert resp.status_code == 422
        assert body(resp)["code"] == "VALIDATION_ERROR"
