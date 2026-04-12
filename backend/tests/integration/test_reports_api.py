"""
Integration tests for reports endpoints:
  GET /api/reports/sales
  GET /api/reports/profit-loss
  GET /api/reports/top-products
  GET /api/reports/low-stock
  GET /api/reports/purchases
  GET /api/reports/expenses
  GET /api/reports/inventory-valuation

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


def _make_fake_sale(
    *,
    sale_id: str = "sale-uuid-1",
    total_amount: int = 10000,
    payment_method: str = "cash",
    sale_date: datetime | None = None,
    sale_items: list | None = None,
) -> MagicMock:
    sale = MagicMock()
    sale.id = sale_id
    sale.totalAmount = total_amount
    sale.paymentMethod = payment_method
    sale.saleDate = sale_date or datetime(2026, 4, 1, 10, 0, 0, tzinfo=timezone.utc)
    sale.saleItems = sale_items or []
    return sale


def _make_fake_product(
    *,
    product_id: str = "product-uuid-1",
    name: str = "Widget",
    sku: str = "WGT-001",
    cost_price: int = 500,
    stock_quantity: int = 2,
    min_stock_level: int = 5,
) -> MagicMock:
    p = MagicMock()
    p.id = product_id
    p.name = name
    p.sku = sku
    p.costPrice = cost_price
    p.stockQuantity = stock_quantity
    p.minStockLevel = min_stock_level
    return p


def _make_fake_expense(
    *,
    expense_id: str = "expense-uuid-1",
    amount: int = 5000,
    category: str = "Rent",
) -> MagicMock:
    e = MagicMock()
    e.id = expense_id
    e.amount = amount
    e.category = category
    return e


def _make_fake_po(
    *,
    po_id: str = "po-uuid-1",
    total_amount: int = 20000,
    order_date: datetime | None = None,
) -> MagicMock:
    po = MagicMock()
    po.id = po_id
    po.totalAmount = total_amount
    po.orderDate = order_date or datetime(2026, 4, 5, 0, 0, 0, tzinfo=timezone.utc)
    return po


def _make_reports_db(
    *,
    sale_find_many_return=None,
    expense_find_many_return=None,
    po_find_many_return=None,
    product_find_many_return=None,
) -> MagicMock:
    """Build a mock Prisma client for reports/dashboard tests."""
    db = MagicMock()

    db.sale = MagicMock()
    db.sale.find_many = AsyncMock(return_value=sale_find_many_return or [])

    db.expense = MagicMock()
    db.expense.find_many = AsyncMock(return_value=expense_find_many_return or [])

    db.purchaseorder = MagicMock()
    db.purchaseorder.find_many = AsyncMock(return_value=po_find_many_return or [])

    db.product = MagicMock()
    db.product.find_many = AsyncMock(return_value=product_find_many_return or [])

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
# GET /api/reports/sales
# ---------------------------------------------------------------------------

class TestGetSalesReport:
    def test_admin_200(self):
        token, user = _admin_token()
        db = _make_reports_db(sale_find_many_return=[_make_fake_sale()])
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/reports/sales", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert "items" in b["data"]
        assert "totals" in b["data"]

    def test_staff_403(self):
        token, user = _staff_token()
        db = _make_reports_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/reports/sales", cookies={"access_token": token})

        assert resp.status_code == 403

    def test_csv_format_response(self):
        token, user = _admin_token()
        db = _make_reports_db(sale_find_many_return=[_make_fake_sale()])
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/reports/sales?format=csv", cookies={"access_token": token})

        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "attachment" in resp.headers["content-disposition"]


# ---------------------------------------------------------------------------
# GET /api/reports/profit-loss
# ---------------------------------------------------------------------------

class TestGetProfitLoss:
    def test_admin_200(self):
        token, user = _admin_token()
        db = _make_reports_db(sale_find_many_return=[], expense_find_many_return=[])
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/reports/profit-loss", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert "revenue" in b["data"]
        assert "net_profit" in b["data"]

    def test_staff_403(self):
        token, user = _staff_token()
        db = _make_reports_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/reports/profit-loss", cookies={"access_token": token})

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/reports/top-products
# ---------------------------------------------------------------------------

class TestGetTopProducts:
    def test_admin_200(self):
        token, user = _admin_token()
        db = _make_reports_db(sale_find_many_return=[])
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/reports/top-products", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert "items" in b["data"]

    def test_staff_403(self):
        token, user = _staff_token()
        db = _make_reports_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/reports/top-products", cookies={"access_token": token})

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/reports/low-stock
# ---------------------------------------------------------------------------

class TestGetLowStock:
    def test_all_roles_get_200(self):
        token, user = _staff_token()
        low_product = _make_fake_product(stock_quantity=1, min_stock_level=5)
        db = _make_reports_db(product_find_many_return=[low_product])
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/reports/low-stock", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert isinstance(b["data"], list)

    def test_unauthenticated_401(self):
        db = _make_reports_db()
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/reports/low-stock")

        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/reports/purchases
# ---------------------------------------------------------------------------

class TestGetPurchasesReport:
    def test_admin_200(self):
        token, user = _admin_token()
        db = _make_reports_db(po_find_many_return=[_make_fake_po()])
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/reports/purchases", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert "items" in b["data"]

    def test_staff_403(self):
        token, user = _staff_token()
        db = _make_reports_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/reports/purchases", cookies={"access_token": token})

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/reports/expenses
# ---------------------------------------------------------------------------

class TestGetExpensesReport:
    def test_admin_200(self):
        token, user = _admin_token()
        db = _make_reports_db(expense_find_many_return=[_make_fake_expense()])
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/reports/expenses", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert "items" in b["data"]

    def test_staff_403(self):
        token, user = _staff_token()
        db = _make_reports_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/reports/expenses", cookies={"access_token": token})

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/reports/inventory-valuation
# ---------------------------------------------------------------------------

class TestGetInventoryValuation:
    def test_admin_200(self):
        token, user = _admin_token()
        product = _make_fake_product(stock_quantity=10, min_stock_level=2)
        db = _make_reports_db(product_find_many_return=[product])
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/reports/inventory-valuation", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert "total_value" in b["data"]
        assert "items" in b["data"]

    def test_staff_403(self):
        token, user = _staff_token()
        db = _make_reports_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/reports/inventory-valuation", cookies={"access_token": token})

        assert resp.status_code == 403
