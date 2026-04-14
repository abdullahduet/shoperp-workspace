"""Expenses repository — database queries only. No business logic."""
from __future__ import annotations


class ExpenseRepository:
    def __init__(self, prisma) -> None:
        self.prisma = prisma

    async def find_by_id(self, expense_id: str):
        """Return an expense by id (not deleted), or None."""
        return await self.prisma.expense.find_first(
            where={"id": expense_id, "deletedAt": None}
        )

    async def find_paginated(self, skip: int, take: int, where: dict) -> tuple:
        """Return (list[Expense], total_count)."""
        items = await self.prisma.expense.find_many(
            skip=skip,
            take=take,
            where=where,
            order=[{"createdAt": "desc"}],
        )
        total = await self.prisma.expense.count(where=where)
        return items, total

    async def update(self, expense_id: str, data: dict):
        """Update an expense record and return the updated object."""
        return await self.prisma.expense.update(
            where={"id": expense_id},
            data=data,
        )

    async def soft_delete(self, expense_id: str) -> None:
        """Soft delete an expense by setting deletedAt to now."""
        from datetime import datetime, timezone

        await self.prisma.expense.update(
            where={"id": expense_id},
            data={"deletedAt": datetime.now(tz=timezone.utc)},
        )

    async def count_today_journal_entries(self, today_str: str) -> int:
        """Count journal entries whose entryNumber starts with JE-{today_str}."""
        return await self.prisma.journalentry.count(
            where={"entryNumber": {"startsWith": f"JE-{today_str}"}}
        )

    async def find_account_by_code(self, code: str):
        """Return an Account by its code, or None."""
        return await self.prisma.account.find_first(
            where={"code": code}
        )

    async def create_expense_atomic(
        self,
        expense_data: dict,
        entry_number: str,
        debit_account_id: str,
        credit_account_id: str,
    ):
        """Atomically create expense + journal entry + 2 journal entry lines."""
        async with self.prisma.tx() as tx:
            expense = await tx.expense.create(data=expense_data)
            entry = await tx.journalentry.create(
                data={
                    "entryNumber": entry_number,
                    "description": (
                        f"Expense: {expense_data.get('category', 'General')} "
                        f"— {expense_data.get('description', '')}"
                    ),
                    "referenceType": "expense",
                    "referenceId": str(expense.id),
                    "createdBy": expense_data.get("recordedBy"),
                }
            )
            await tx.journalentryline.create(
                data={
                    "journalEntryId": entry.id,
                    "accountId": debit_account_id,
                    "debitAmount": expense_data["amount"],
                    "creditAmount": 0,
                    "description": "Expense recorded",
                }
            )
            await tx.journalentryline.create(
                data={
                    "journalEntryId": entry.id,
                    "accountId": credit_account_id,
                    "debitAmount": 0,
                    "creditAmount": expense_data["amount"],
                    "description": "Cash paid",
                }
            )
        return await self.prisma.expense.find_first(where={"id": expense.id})
