"""Accounting service — ALL business logic for accounts and journal entries."""
from __future__ import annotations

from datetime import date, datetime, timezone

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.accounting.repository import AccountingRepository
from src.modules.accounting.schemas import (
    AccountResponse,
    JournalEntryCreate,
    JournalEntryResponse,
    PaginatedJournalEntries,
)


class AccountingService:
    def __init__(self, repo: AccountingRepository) -> None:
        self.repo = repo

    async def list_accounts(self) -> list[AccountResponse]:
        """Return all active accounts."""
        accounts = await self.repo.find_all_accounts()
        return [AccountResponse.model_validate(a) for a in accounts]

    async def list_journal_entries(
        self,
        page: int,
        limit: int,
        start_date: str | None,
        end_date: str | None,
        reference_type: str | None,
    ) -> PaginatedJournalEntries:
        """Return a paginated list of journal entries with optional filters."""
        where: dict = {}
        if reference_type:
            where["referenceType"] = reference_type
        date_filter: dict = {}
        if start_date:
            date_filter["gte"] = date.fromisoformat(start_date)
        if end_date:
            date_filter["lte"] = date.fromisoformat(end_date)
        if date_filter:
            where["date"] = date_filter
        skip = (page - 1) * limit
        items, total = await self.repo.find_journal_entries_paginated(skip, limit, where)
        return PaginatedJournalEntries(
            items=[JournalEntryResponse.model_validate(e) for e in items],
            total=total,
        )

    async def create_journal_entry(
        self, input: JournalEntryCreate, created_by: str
    ) -> JournalEntryResponse:
        """Validate and create a balanced manual journal entry."""
        # Rule #21: validate balance
        total_debit = sum(line.debit_amount for line in input.lines)
        total_credit = sum(line.credit_amount for line in input.lines)
        if total_debit != total_credit:
            raise ValidationError(
                f"Journal entry does not balance: debits={total_debit}, credits={total_credit}"
            )
        if total_debit == 0:
            raise ValidationError("Journal entry must have non-zero amounts")

        # Validate each account exists
        for line in input.lines:
            account = await self.repo.find_account_by_id(line.account_id)
            if account is None:
                raise NotFoundError("Account", line.account_id)

        today = date.today()
        entry_date = date.fromisoformat(input.date) if input.date else today
        entry_number = await self._generate_entry_number()

        entry_data = {
            "entryNumber": entry_number,
            "date": datetime(
                entry_date.year, entry_date.month, entry_date.day, tzinfo=timezone.utc
            ),
            "description": input.description,
            "referenceType": "manual",
            "createdBy": created_by,
        }
        lines_data = [
            {
                "accountId": line.account_id,
                "debitAmount": line.debit_amount,
                "creditAmount": line.credit_amount,
                "description": line.description,
            }
            for line in input.lines
        ]
        entry = await self.repo.create_journal_entry_with_lines(entry_data, lines_data)
        return JournalEntryResponse.model_validate(entry)

    async def seed_accounts(self) -> int:
        """Upsert the default chart of accounts. Returns count of accounts ensured."""
        accounts = [
            {"code": "1000", "name": "Cash",                    "type": "asset"},
            {"code": "1100", "name": "Accounts Receivable",     "type": "asset"},
            {"code": "1200", "name": "Inventory",               "type": "asset"},
            {"code": "2000", "name": "Accounts Payable",        "type": "liability"},
            {"code": "3000", "name": "Owner's Equity",          "type": "equity"},
            {"code": "4000", "name": "Sales Revenue",           "type": "revenue"},
            {"code": "5000", "name": "Cost of Goods Sold",      "type": "expense"},
            {"code": "6000", "name": "Rent Expense",            "type": "expense"},
            {"code": "6100", "name": "Utilities Expense",       "type": "expense"},
            {"code": "6200", "name": "Salary Expense",          "type": "expense"},
            {"code": "6300", "name": "Marketing Expense",       "type": "expense"},
            {"code": "6400", "name": "Office Supplies Expense", "type": "expense"},
            {"code": "6500", "name": "Miscellaneous Expense",   "type": "expense"},
        ]
        await self.repo.upsert_accounts(accounts)
        return len(accounts)

    async def _generate_entry_number(self) -> str:
        """Generate a sequential journal entry number for today: JE-YYYYMMDD-NNN."""
        today_str = date.today().strftime("%Y%m%d")
        count = await self.repo.count_today_journal_entries(today_str)
        return f"JE-{today_str}-{count + 1:03d}"
