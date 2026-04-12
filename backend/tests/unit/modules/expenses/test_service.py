"""
Unit tests for src/modules/expenses/service.py

All repository calls are mocked. Tests verify business logic only.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.expenses.repository import ExpenseRepository
from src.modules.expenses.schemas import (
    ExpenseCreate,
    ExpenseResponse,
    ExpenseUpdate,
)
from src.modules.expenses.service import ExpenseService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def _make_service() -> tuple[ExpenseService, AsyncMock]:
    repo = AsyncMock(spec=ExpenseRepository)
    service = ExpenseService(repo)
    return service, repo


def _make_expense_create(**kwargs) -> ExpenseCreate:
    defaults = {
        "category": "Rent",
        "description": "Monthly office rent",
        "amount": 500000,
    }
    defaults.update(kwargs)
    return ExpenseCreate(**defaults)


# ---------------------------------------------------------------------------
# TestCreate
# ---------------------------------------------------------------------------

class TestCreate:
    @pytest.mark.asyncio
    async def test_raises_if_accounts_not_seeded(self):
        service, repo = _make_service()
        repo.find_account_by_code.return_value = None

        with pytest.raises(ValidationError, match="not seeded"):
            await service.create(_make_expense_create(), recorded_by="user-1")

    @pytest.mark.asyncio
    async def test_creates_expense_and_calls_repo_atomic(self):
        service, repo = _make_service()
        expense_account = _make_fake_account("expense-account-uuid")
        cash_account = _make_fake_account("cash-account-uuid")
        repo.find_account_by_code.side_effect = [expense_account, cash_account]
        repo.count_today_journal_entries.return_value = 0
        fake_expense = _make_fake_expense()
        repo.create_expense_atomic.return_value = fake_expense

        result = await service.create(_make_expense_create(), recorded_by="user-1")

        assert isinstance(result, ExpenseResponse)
        repo.create_expense_atomic.assert_called_once()
        call_args = repo.create_expense_atomic.call_args
        expense_data = call_args.args[0]
        debit_id = call_args.args[2]
        credit_id = call_args.args[3]
        assert expense_data["category"] == "Rent"
        assert expense_data["amount"] == 500000
        assert debit_id == "expense-account-uuid"
        assert credit_id == "cash-account-uuid"

    @pytest.mark.asyncio
    async def test_uses_today_if_date_not_provided(self):
        service, repo = _make_service()
        expense_account = _make_fake_account("expense-account-uuid")
        cash_account = _make_fake_account("cash-account-uuid")
        repo.find_account_by_code.side_effect = [expense_account, cash_account]
        repo.count_today_journal_entries.return_value = 0
        fake_expense = _make_fake_expense()
        repo.create_expense_atomic.return_value = fake_expense

        # Pass no date
        input_data = ExpenseCreate(
            category="Utilities",
            description="Electric bill",
            amount=100000,
        )
        await service.create(input_data, recorded_by="user-1")

        call_args = repo.create_expense_atomic.call_args
        expense_data = call_args.args[0]
        # date should be a datetime object (from today)
        assert "date" in expense_data
        assert hasattr(expense_data["date"], "year")


# ---------------------------------------------------------------------------
# TestUpdate
# ---------------------------------------------------------------------------

class TestUpdate:
    @pytest.mark.asyncio
    async def test_raises_not_found_if_missing(self):
        service, repo = _make_service()
        repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.update("nonexistent-id", ExpenseUpdate())

    @pytest.mark.asyncio
    async def test_updates_only_provided_fields(self):
        service, repo = _make_service()
        fake_expense = _make_fake_expense()
        updated_expense = _make_fake_expense(category="Utilities", amount=200000)
        repo.find_by_id.return_value = fake_expense
        repo.update.return_value = updated_expense

        await service.update(
            "expense-uuid-1",
            ExpenseUpdate(category="Utilities", amount=200000),
        )

        call_args = repo.update.call_args
        data = call_args.args[1]
        assert data.get("category") == "Utilities"
        assert data.get("amount") == 200000
        # description not in update input — should not be in data
        assert "description" not in data

    @pytest.mark.asyncio
    async def test_does_not_update_journal_entry(self):
        """Verify update calls repo.update (not any journal entry method)."""
        service, repo = _make_service()
        fake_expense = _make_fake_expense()
        repo.find_by_id.return_value = fake_expense
        repo.update.return_value = fake_expense

        await service.update("expense-uuid-1", ExpenseUpdate(category="Transport"))

        repo.update.assert_called_once()
        # No journal entry methods should be called
        repo.create_expense_atomic.assert_not_called()
        repo.count_today_journal_entries.assert_not_called()


# ---------------------------------------------------------------------------
# TestDelete
# ---------------------------------------------------------------------------

class TestDelete:
    @pytest.mark.asyncio
    async def test_raises_not_found_if_missing(self):
        service, repo = _make_service()
        repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.delete("nonexistent-id")

    @pytest.mark.asyncio
    async def test_soft_deletes_expense(self):
        service, repo = _make_service()
        fake_expense = _make_fake_expense()
        repo.find_by_id.return_value = fake_expense
        repo.soft_delete.return_value = None

        await service.delete("expense-uuid-1")

        repo.soft_delete.assert_called_once_with("expense-uuid-1")


# ---------------------------------------------------------------------------
# TestList
# ---------------------------------------------------------------------------

class TestList:
    @pytest.mark.asyncio
    async def test_returns_paginated_expenses(self):
        service, repo = _make_service()
        fake_expense = _make_fake_expense()
        repo.find_paginated.return_value = ([fake_expense], 1)

        result = await service.list(
            page=1, limit=20,
            start_date=None, end_date=None, category=None,
        )

        assert result.total == 1
        assert len(result.items) == 1
        assert isinstance(result.items[0], ExpenseResponse)

    @pytest.mark.asyncio
    async def test_applies_category_filter(self):
        service, repo = _make_service()
        repo.find_paginated.return_value = ([], 0)

        await service.list(
            page=1, limit=20,
            start_date=None, end_date=None, category="Rent",
        )

        call_args = repo.find_paginated.call_args
        where = call_args.args[2]
        assert "category" in where
        assert where["category"] == {"contains": "Rent", "mode": "insensitive"}

    @pytest.mark.asyncio
    async def test_applies_date_range_filter(self):
        service, repo = _make_service()
        repo.find_paginated.return_value = ([], 0)

        await service.list(
            page=1, limit=20,
            start_date="2026-04-01", end_date="2026-04-30", category=None,
        )

        call_args = repo.find_paginated.call_args
        where = call_args.args[2]
        assert "date" in where
        assert "gte" in where["date"]
        assert "lte" in where["date"]
