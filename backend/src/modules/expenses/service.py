"""Expenses service — ALL business logic for expense recording and retrieval."""
from __future__ import annotations

from datetime import date, datetime, timezone

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.expenses.repository import ExpenseRepository
from src.modules.expenses.schemas import (
    ExpenseCreate,
    ExpenseResponse,
    ExpenseUpdate,
    PaginatedExpenses,
)


class ExpenseService:
    def __init__(self, repo: ExpenseRepository) -> None:
        self.repo = repo

    async def list(
        self,
        page: int,
        limit: int,
        start_date: str | None,
        end_date: str | None,
        category: str | None,
    ) -> PaginatedExpenses:
        """Return a paginated list of expenses with optional filters."""
        where: dict = {"deletedAt": None}
        if category:
            where["category"] = {"contains": category, "mode": "insensitive"}
        date_filter: dict = {}
        if start_date:
            date_filter["gte"] = date.fromisoformat(start_date)
        if end_date:
            date_filter["lte"] = date.fromisoformat(end_date)
        if date_filter:
            where["date"] = date_filter
        skip = (page - 1) * limit
        items, total = await self.repo.find_paginated(skip, limit, where)
        return PaginatedExpenses(
            items=[ExpenseResponse.model_validate(e) for e in items],
            total=total,
        )

    async def create(self, input: ExpenseCreate, recorded_by: str) -> ExpenseResponse:
        """Create an expense with an atomically linked journal entry."""
        # Look up accounts
        expense_account = await self.repo.find_account_by_code("6500")  # Misc Expense
        cash_account = await self.repo.find_account_by_code("1000")     # Cash
        if expense_account is None or cash_account is None:
            raise ValidationError(
                "Chart of accounts not seeded. Run prisma/seed.py first."
            )

        today = date.today()
        expense_date = date.fromisoformat(input.date) if input.date else today
        entry_number = await self._generate_entry_number()

        expense_data: dict = {
            "date": datetime(
                expense_date.year, expense_date.month, expense_date.day,
                tzinfo=timezone.utc,
            ),
            "category": input.category,
            "description": input.description,
            "amount": input.amount,
            "paymentMethod": input.payment_method,
            "recordedBy": recorded_by,
        }
        if input.receipt_url:
            expense_data["receiptUrl"] = input.receipt_url
        if input.notes:
            expense_data["notes"] = input.notes

        expense = await self.repo.create_expense_atomic(
            expense_data, entry_number, expense_account.id, cash_account.id
        )
        return ExpenseResponse.model_validate(expense)

    async def update(self, expense_id: str, input: ExpenseUpdate) -> ExpenseResponse:
        """Update expense fields only (journal entry is immutable once created)."""
        existing = await self.repo.find_by_id(expense_id)
        if existing is None:
            raise NotFoundError("Expense", expense_id)

        data: dict = {}
        if input.category is not None:
            data["category"] = input.category
        if input.description is not None:
            data["description"] = input.description
        if input.amount is not None:
            data["amount"] = input.amount
        if input.payment_method is not None:
            data["paymentMethod"] = input.payment_method
        if input.date is not None:
            d = date.fromisoformat(input.date)
            data["date"] = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
        if input.receipt_url is not None:
            data["receiptUrl"] = input.receipt_url
        if input.notes is not None:
            data["notes"] = input.notes

        expense = await self.repo.update(expense_id, data)
        return ExpenseResponse.model_validate(expense)

    async def delete(self, expense_id: str) -> None:
        """Soft delete an expense."""
        existing = await self.repo.find_by_id(expense_id)
        if existing is None:
            raise NotFoundError("Expense", expense_id)
        await self.repo.soft_delete(expense_id)

    async def _generate_entry_number(self) -> str:
        """Generate a sequential journal entry number for today: JE-YYYYMMDD-NNN."""
        today_str = date.today().strftime("%Y%m%d")
        count = await self.repo.count_today_journal_entries(today_str)
        return f"JE-{today_str}-{count + 1:03d}"
