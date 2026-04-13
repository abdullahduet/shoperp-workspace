"""
Integration tests for sales endpoints:
  GET  /api/sales
  GET  /api/sales/daily-summary
  GET  /api/sales/{sale_id}
  POST /api/sales

Tests run against the FastAPI TestClient with the Prisma DB layer mocked.
No live database is required.
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
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


def _make_fake_sale_item(
    *,
    item_id: str = "item-uuid-1",
    product_id: str = "prod-uuid-1",
    product_name: str = "Test Product",
    product_sku: str = "SKU-001",
    quantity: int = 2,
    unit_price: int = 50000,
    discount: int = 0,
    total_price: int = 100000,
) -> MagicMock:
    item = MagicMock()
    item.id = item_id
    item.productId = product_id
    item.quantity = quantity
    item.unitPrice = unit_price
    item.discount = discount
    item.totalPrice = total_price
    item.createdAt = datetime(2026, 4, 11, tzinfo=timezone.utc)
    product = MagicMock()
    product.name = product_name
    product.sku = product_sku
    item.product = product
    return item


def _make_fake_sale(
    *,
    sale_id: str = "sale-uuid-1",
    sale_number: str = "SALE-20260411-001",
    subtotal: int = 100000,
    discount_amount: int = 0,
    tax_amount: int = 0,
    total_amount: int = 100000,
    payment_method: str = "cash",
    promotion_id: str | None = None,
    customer_name: str | None = None,
    notes: str | None = None,
    recorded_by: str | None = "user-uuid-1",
    sale_items: list | None = None,
) -> MagicMock:
    sale = MagicMock()
    sale.id = sale_id
    sale.saleNumber = sale_number
    sale.saleDate = datetime(2026, 4, 11, tzinfo=timezone.utc)
    sale.customerName = customer_name
    sale.subtotal = subtotal
    sale.discountAmount = discount_amount
    sale.taxAmount = tax_amount
    sale.totalAmount = total_amount
    sale.paymentMethod = payment_method
    sale.promotionId = promotion_id
    sale.notes = notes
    sale.recordedBy = recorded_by
    sale.saleItems = sale_items if sale_items is not None else []
    sale.createdAt = datetime(2026, 4, 11, tzinfo=timezone.utc)
    return sale


def _make_fake_product(
    *,
    product_id: str = "prod-uuid-1",
    stock_quantity: int = 100,
    tax_rate: Decimal = Decimal("0"),
    is_active: bool = True,
) -> MagicMock:
    product = MagicMock()
    product.id = product_id
    product.stockQuantity = stock_quantity
    product.taxRate = tax_rate
    product.isActive = is_active
    product.deletedAt = None
    return product


def _make_fake_account(account_id: str = "account-uuid-1") -> MagicMock:
    account = MagicMock()
    account.id = account_id
    return account


def _make_fake_journal_entry(entry_id: str = "je-uuid-1") -> MagicMock:
    entry = MagicMock()
    entry.id = entry_id
    return entry


def _make_sales_db(
    *,
    sale_find_many_return=None,
    sale_find_first_return=None,
    sale_count_return: int = 0,
    je_count_return: int = 0,
    product_find_first_return=None,
    account_find_first_return=None,
    promotion_find_many_return=None,
) -> MagicMock:
    """Build a mock Prisma client with all sales-related model stubs."""
    db = MagicMock()

    # sale
    db.sale = MagicMock()
    db.sale.find_many = AsyncMock(return_value=sale_find_many_return or [])
    db.sale.find_first = AsyncMock(return_value=sale_find_first_return)
    db.sale.count = AsyncMock(return_value=sale_count_return)

    # saleitem
    db.saleitem = MagicMock()
    db.saleitem.create = AsyncMock(return_value=None)

    # product
    db.product = MagicMock()
    if product_find_first_return is not None:
        db.product.find_first = AsyncMock(return_value=product_find_first_return)
    else:
        db.product.find_first = AsyncMock(return_value=_make_fake_product())
    db.product.update = AsyncMock(return_value=None)

    # stockmovement
    db.stockmovement = MagicMock()
    db.stockmovement.create = AsyncMock(return_value=None)

    # account
    db.account = MagicMock()
    if account_find_first_return is not None:
        db.account.find_first = AsyncMock(return_value=account_find_first_return)
    else:
        db.account.find_first = AsyncMock(return_value=_make_fake_account())

    # journalentry
    db.journalentry = MagicMock()
    db.journalentry.count = AsyncMock(return_value=je_count_return)

    # journalentryline
    db.journalentryline = MagicMock()
    db.journalentryline.create = AsyncMock(return_value=None)

    # promotion (for PromotionService.get_best_discount)
    db.promotion = MagicMock()
    db.promotion.find_many = AsyncMock(return_value=promotion_find_many_return or [])

    # user
    db.user = MagicMock()
    db.user.find_first = AsyncMock(return_value=None)

    # Transaction mock
    mock_tx = MagicMock()
    mock_tx.sale = MagicMock()
    created_sale = sale_find_first_return or _make_fake_sale()
    mock_tx.sale.create = AsyncMock(return_value=created_sale)
    mock_tx.saleitem = MagicMock()
    mock_tx.saleitem.create = AsyncMock(return_value=None)
    mock_tx.product = MagicMock()
    mock_tx.product.update = AsyncMock(return_value=None)
    mock_tx.stockmovement = MagicMock()
    mock_tx.stockmovement.create = AsyncMock(return_value=None)
    mock_tx.journalentry = MagicMock()
    mock_tx.journalentry.create = AsyncMock(return_value=_make_fake_journal_entry())
    mock_tx.journalentryline = MagicMock()
    mock_tx.journalentryline.create = AsyncMock(return_value=None)

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
# GET /api/sales
# ---------------------------------------------------------------------------

class TestListSales:
    def test_all_roles_get_200_paginated_response(self):
        fake_sale = _make_fake_sale(sale_items=[_make_fake_sale_item()])
        token, user = _staff_token()
        db = _make_sales_db(sale_find_many_return=[fake_sale], sale_count_return=1)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/sales", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert "pagination" in b
        assert b["pagination"]["total"] == 1
        assert len(b["data"]) == 1

    def test_date_filter_passed_to_service(self):
        token, user = _admin_token()
        db = _make_sales_db(sale_find_many_return=[], sale_count_return=0)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get(
                "/api/sales?start_date=2026-04-01&end_date=2026-04-30",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/sales/{sale_id}
# ---------------------------------------------------------------------------

class TestGetSale:
    def test_returns_200_with_sale_detail(self):
        sale_item = _make_fake_sale_item()
        fake_sale = _make_fake_sale(sale_items=[sale_item])
        token, user = _admin_token()
        db = _make_sales_db(sale_find_first_return=fake_sale)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/sales/sale-uuid-1", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert b["data"]["id"] == "sale-uuid-1"
        assert "items" in b["data"]

    def test_returns_404_for_missing_sale(self):
        token, user = _admin_token()
        db = _make_sales_db(sale_find_first_return=None)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/sales/nonexistent-id", cookies={"access_token": token})

        assert resp.status_code == 404
        assert body(resp)["code"] == "NOT_FOUND"

    def test_unauthenticated_gets_401(self):
        db = _make_sales_db()
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/sales/sale-uuid-1")

        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/sales/daily-summary
# ---------------------------------------------------------------------------

class TestGetDailySummary:
    def test_admin_gets_200_with_summary(self):
        token, user = _admin_token()
        db = _make_sales_db(sale_find_many_return=[])
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/sales/daily-summary", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert "total_sales" in b["data"]
        assert "transaction_count" in b["data"]
        assert "payment_breakdown" in b["data"]

    def test_manager_gets_200_with_summary(self):
        token, user = _manager_token()
        db = _make_sales_db(sale_find_many_return=[])
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/sales/daily-summary", cookies={"access_token": token})

        assert resp.status_code == 200

    def test_staff_gets_403(self):
        token, user = _staff_token()
        db = _make_sales_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/sales/daily-summary", cookies={"access_token": token})

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/sales
# ---------------------------------------------------------------------------

class TestRecordSale:
    def _valid_payload(self) -> dict:
        return {
            "items": [
                {"product_id": "prod-uuid-1", "quantity": 2, "unit_price": 50000}
            ],
            "payment_method": "cash",
        }

    def test_any_role_can_record_sale_returns_201(self):
        sale_item = _make_fake_sale_item()
        fake_sale = _make_fake_sale(sale_items=[sale_item])
        token, user = _staff_token()
        db = _make_sales_db(sale_find_first_return=fake_sale)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/sales",
                json=self._valid_payload(),
                cookies={"access_token": token},
            )

        assert resp.status_code == 201
        b = body(resp)
        assert b["success"] is True
        assert b["message"] == "Sale recorded successfully"

    def test_returns_422_for_empty_items_list(self):
        token, user = _admin_token()
        db = _make_sales_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/sales",
                json={"items": [], "payment_method": "cash"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 422

    def test_returns_422_for_invalid_payment_method(self):
        token, user = _admin_token()
        db = _make_sales_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/sales",
                json={
                    "items": [{"product_id": "prod-uuid-1", "quantity": 1, "unit_price": 1000}],
                    "payment_method": "bitcoin",
                },
                cookies={"access_token": token},
            )

        assert resp.status_code == 422

    def test_returns_422_for_zero_quantity(self):
        token, user = _admin_token()
        db = _make_sales_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/sales",
                json={
                    "items": [{"product_id": "prod-uuid-1", "quantity": 0, "unit_price": 1000}],
                    "payment_method": "cash",
                },
                cookies={"access_token": token},
            )

        assert resp.status_code == 422
