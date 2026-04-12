"""
Integration tests for expenses endpoints:
  GET    /api/expenses
  POST   /api/expenses
  PUT    /api/expenses/:id
  DELETE /api/expenses/:id

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


def _make_fake_account(account_id: str = "account-uuid-1") -> MagicMock:
    account = MagicMock()
    account.id = account_id
    return account


def _make_fake_expense(
    *,
    expense_id: str = "expense-uuid-1",
    category: str = "Rent",
    description: str = "Monthly office rent",
    amount: int = 500000,
    payment_method: str = "cash",
    receipt_url: str | None = None,
    notes: str | None = None,
    recorded_by: str | None = "user-uuid-1",
) -> MagicMock:
    expense = MagicMock()
    expense.id = expense_id
    expense.date = datetime(2026, 4, 1, tzinfo=timezone.utc)
    expense.category = category
    expense.description = description
    expense.amount = amount
    expense.paymentMethod = payment_method
    expense.receiptUrl = receipt_url
    expense.notes = notes
    expense.recordedBy = recorded_by
    expense.createdAt = datetime(2026, 4, 1, tzinfo=timezone.utc)
    expense.deletedAt = None
    return expense


def _make_fake_journal_entry(entry_id: str = "je-uuid-1") -> MagicMock:
    entry = MagicMock()
    entry.id = entry_id
    return entry


def _make_expenses_db(
    *,
    expense_find_many_return=None,
    expense_find_first_return=None,
    expense_count_return: int = 0,
    expense_update_return=None,
    account_find_first_return=None,
    je_count_return: int = 0,
) -> MagicMock:
    """Build a mock Prisma client with expenses-related model stubs."""
    db = MagicMock()

    # expense
    db.expense = MagicMock()
    db.expense.find_many = AsyncMock(return_value=expense_find_many_return or [])
    if expense_find_first_return is not None:
        db.expense.find_first = AsyncMock(return_value=expense_find_first_return)
    else:
        db.expense.find_first = AsyncMock(return_value=_make_fake_expense())
    db.expense.count = AsyncMock(return_value=expense_count_return)
    if expense_update_return is not None:
        db.expense.update = AsyncMock(return_value=expense_update_return)
    else:
        db.expense.update = AsyncMock(return_value=_make_fake_expense())

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

    # user
    db.user = MagicMock()
    db.user.find_first = AsyncMock(return_value=None)

    # Transaction mock
    mock_tx = MagicMock()
    created_expense = expense_find_first_return or _make_fake_expense()
    mock_tx.expense = MagicMock()
    mock_tx.expense.create = AsyncMock(return_value=created_expense)
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
# GET /api/expenses
# ---------------------------------------------------------------------------

class TestListExpenses:
    def test_admin_gets_200_paginated(self):
        fake_expense = _make_fake_expense()
        token, user = _admin_token()
        db = _make_expenses_db(
            expense_find_many_return=[fake_expense], expense_count_return=1
        )
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get(
                "/api/expenses",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert "pagination" in b
        assert b["pagination"]["total"] == 1
        assert len(b["data"]) == 1

    def test_staff_gets_403(self):
        token, user = _staff_token()
        db = _make_expenses_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get(
                "/api/expenses",
                cookies={"access_token": token},
            )

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/expenses
# ---------------------------------------------------------------------------

class TestCreateExpense:
    def _valid_payload(self) -> dict:
        return {
            "category": "Rent",
            "description": "Monthly office rent",
            "amount": 500000,
            "payment_method": "cash",
        }

    def test_admin_creates_expense_returns_201(self):
        fake_expense = _make_fake_expense()
        token, user = _admin_token()
        db = _make_expenses_db(expense_find_first_return=fake_expense)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/expenses",
                json=self._valid_payload(),
                cookies={"access_token": token},
            )

        assert resp.status_code == 201
        b = body(resp)
        assert b["success"] is True
        assert b["data"]["category"] == "Rent"

    def test_manager_creates_expense_returns_201(self):
        fake_expense = _make_fake_expense()
        token, user = _manager_token()
        db = _make_expenses_db(expense_find_first_return=fake_expense)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/expenses",
                json=self._valid_payload(),
                cookies={"access_token": token},
            )

        assert resp.status_code == 201

    def test_staff_gets_403(self):
        token, user = _staff_token()
        db = _make_expenses_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/expenses",
                json=self._valid_payload(),
                cookies={"access_token": token},
            )

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PUT /api/expenses/:id
# ---------------------------------------------------------------------------

class TestUpdateExpense:
    def test_admin_updates_expense_returns_200(self):
        fake_expense = _make_fake_expense()
        updated_expense = _make_fake_expense(category="Utilities")
        token, user = _admin_token()
        db = _make_expenses_db(
            expense_find_first_return=fake_expense,
            expense_update_return=updated_expense,
        )
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.put(
                "/api/expenses/expense-uuid-1",
                json={"category": "Utilities"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True

    def test_staff_gets_403(self):
        token, user = _staff_token()
        db = _make_expenses_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.put(
                "/api/expenses/expense-uuid-1",
                json={"category": "Utilities"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /api/expenses/:id
# ---------------------------------------------------------------------------

class TestDeleteExpense:
    def test_admin_deletes_expense_returns_200(self):
        fake_expense = _make_fake_expense()
        token, user = _admin_token()
        db = _make_expenses_db(expense_find_first_return=fake_expense)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.delete(
                "/api/expenses/expense-uuid-1",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert b["message"] == "Expense deleted"

    def test_manager_gets_403_on_delete(self):
        token, user = _manager_token()
        db = _make_expenses_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.delete(
                "/api/expenses/expense-uuid-1",
                cookies={"access_token": token},
            )

        assert resp.status_code == 403
