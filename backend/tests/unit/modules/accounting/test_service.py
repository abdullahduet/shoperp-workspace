"""
Unit tests for src/modules/accounting/service.py

All repository calls are mocked. Tests verify business logic only.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.accounting.repository import AccountingRepository
from src.modules.accounting.schemas import (
    JournalEntryCreate,
    JournalEntryLineCreate,
    JournalEntryResponse,
    AccountResponse,
)
from src.modules.accounting.service import AccountingService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_account(
    *,
    account_id: str = "account-uuid-1",
    code: str = "1000",
    name: str = "Cash",
    account_type: str = "asset",
    parent_id: str | None = None,
    is_active: bool = True,
) -> MagicMock:
    account = MagicMock()
    account.id = account_id
    account.code = code
    account.name = name
    account.type = account_type
    account.parentId = parent_id
    account.isActive = is_active
    account.createdAt = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return account


def _make_fake_je_line(
    *,
    line_id: str = "line-uuid-1",
    account_id: str = "account-uuid-1",
    debit_amount: int = 5000,
    credit_amount: int = 0,
    description: str | None = None,
) -> MagicMock:
    line = MagicMock()
    line.id = line_id
    line.accountId = account_id
    line.debitAmount = debit_amount
    line.creditAmount = credit_amount
    line.description = description
    return line


def _make_fake_journal_entry(
    *,
    entry_id: str = "je-uuid-1",
    entry_number: str = "JE-20260412-001",
    description: str = "Test entry",
    reference_type: str | None = "manual",
    reference_id: str | None = None,
    created_by: str | None = "user-uuid-1",
    lines: list | None = None,
) -> MagicMock:
    entry = MagicMock()
    entry.id = entry_id
    entry.entryNumber = entry_number
    entry.date = datetime(2026, 4, 12, tzinfo=timezone.utc)
    entry.description = description
    entry.referenceType = reference_type
    entry.referenceId = reference_id
    entry.createdBy = created_by
    entry.journalEntryLines = lines or []
    entry.createdAt = datetime(2026, 4, 12, tzinfo=timezone.utc)
    return entry


def _make_service() -> tuple[AccountingService, AsyncMock]:
    repo = AsyncMock(spec=AccountingRepository)
    service = AccountingService(repo)
    return service, repo


def _make_balanced_je_create(
    account_id_1: str = "account-uuid-1",
    account_id_2: str = "account-uuid-2",
    amount: int = 5000,
) -> JournalEntryCreate:
    return JournalEntryCreate(
        description="Test manual entry",
        lines=[
            JournalEntryLineCreate(
                account_id=account_id_1, debit_amount=amount, credit_amount=0
            ),
            JournalEntryLineCreate(
                account_id=account_id_2, debit_amount=0, credit_amount=amount
            ),
        ],
    )


# ---------------------------------------------------------------------------
# TestListAccounts
# ---------------------------------------------------------------------------

class TestListAccounts:
    @pytest.mark.asyncio
    async def test_returns_list_of_account_responses(self):
        service, repo = _make_service()
        fake_account = _make_fake_account()
        repo.find_all_accounts.return_value = [fake_account]

        result = await service.list_accounts()

        assert len(result) == 1
        assert isinstance(result[0], AccountResponse)
        assert result[0].id == "account-uuid-1"
        assert result[0].code == "1000"
        assert result[0].name == "Cash"
        assert result[0].type == "asset"
        assert result[0].is_active is True


# ---------------------------------------------------------------------------
# TestListJournalEntries
# ---------------------------------------------------------------------------

class TestListJournalEntries:
    @pytest.mark.asyncio
    async def test_returns_paginated_entries(self):
        service, repo = _make_service()
        line1 = _make_fake_je_line(debit_amount=5000, credit_amount=0)
        line2 = _make_fake_je_line(
            line_id="line-uuid-2", debit_amount=0, credit_amount=5000
        )
        fake_entry = _make_fake_journal_entry(lines=[line1, line2])
        repo.find_journal_entries_paginated.return_value = ([fake_entry], 1)

        result = await service.list_journal_entries(
            page=1, limit=20,
            start_date=None, end_date=None, reference_type=None,
        )

        assert result.total == 1
        assert len(result.items) == 1
        assert isinstance(result.items[0], JournalEntryResponse)

    @pytest.mark.asyncio
    async def test_applies_start_date_filter(self):
        service, repo = _make_service()
        repo.find_journal_entries_paginated.return_value = ([], 0)

        await service.list_journal_entries(
            page=1, limit=20,
            start_date="2026-04-01", end_date=None, reference_type=None,
        )

        call_args = repo.find_journal_entries_paginated.call_args
        where = call_args.args[2]
        assert "date" in where
        assert "gte" in where["date"]

    @pytest.mark.asyncio
    async def test_applies_end_date_filter(self):
        service, repo = _make_service()
        repo.find_journal_entries_paginated.return_value = ([], 0)

        await service.list_journal_entries(
            page=1, limit=20,
            start_date=None, end_date="2026-04-30", reference_type=None,
        )

        call_args = repo.find_journal_entries_paginated.call_args
        where = call_args.args[2]
        assert "date" in where
        assert "lte" in where["date"]

    @pytest.mark.asyncio
    async def test_applies_reference_type_filter(self):
        service, repo = _make_service()
        repo.find_journal_entries_paginated.return_value = ([], 0)

        await service.list_journal_entries(
            page=1, limit=20,
            start_date=None, end_date=None, reference_type="sale",
        )

        call_args = repo.find_journal_entries_paginated.call_args
        where = call_args.args[2]
        assert where.get("referenceType") == "sale"


# ---------------------------------------------------------------------------
# TestCreateJournalEntry
# ---------------------------------------------------------------------------

class TestCreateJournalEntry:
    @pytest.mark.asyncio
    async def test_raises_validation_error_if_debits_not_equal_credits(self):
        service, repo = _make_service()

        unbalanced = JournalEntryCreate(
            description="Unbalanced entry",
            lines=[
                JournalEntryLineCreate(
                    account_id="account-uuid-1", debit_amount=5000, credit_amount=0
                ),
                JournalEntryLineCreate(
                    account_id="account-uuid-2", debit_amount=0, credit_amount=3000
                ),
            ],
        )

        with pytest.raises(ValidationError, match="does not balance"):
            await service.create_journal_entry(unbalanced, created_by="user-1")

    @pytest.mark.asyncio
    async def test_raises_validation_error_if_amounts_are_zero(self):
        service, repo = _make_service()

        zero_entry = JournalEntryCreate(
            description="Zero entry",
            lines=[
                JournalEntryLineCreate(
                    account_id="account-uuid-1", debit_amount=0, credit_amount=0
                ),
                JournalEntryLineCreate(
                    account_id="account-uuid-2", debit_amount=0, credit_amount=0
                ),
            ],
        )

        with pytest.raises(ValidationError, match="non-zero"):
            await service.create_journal_entry(zero_entry, created_by="user-1")

    @pytest.mark.asyncio
    async def test_raises_not_found_if_account_missing(self):
        service, repo = _make_service()
        repo.find_account_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.create_journal_entry(
                _make_balanced_je_create(), created_by="user-1"
            )

    @pytest.mark.asyncio
    async def test_creates_balanced_entry_with_correct_data(self):
        service, repo = _make_service()
        fake_account_1 = _make_fake_account(account_id="account-uuid-1")
        fake_account_2 = _make_fake_account(account_id="account-uuid-2", code="4000")
        repo.find_account_by_id.side_effect = [fake_account_1, fake_account_2]
        repo.count_today_journal_entries.return_value = 0

        line1 = _make_fake_je_line(debit_amount=5000, credit_amount=0)
        line2 = _make_fake_je_line(
            line_id="line-uuid-2", debit_amount=0, credit_amount=5000
        )
        fake_entry = _make_fake_journal_entry(lines=[line1, line2])
        repo.create_journal_entry_with_lines.return_value = fake_entry

        result = await service.create_journal_entry(
            _make_balanced_je_create(amount=5000), created_by="user-1"
        )

        assert isinstance(result, JournalEntryResponse)
        assert len(result.lines) == 2
        repo.create_journal_entry_with_lines.assert_called_once()
        call_args = repo.create_journal_entry_with_lines.call_args
        entry_data = call_args.args[0]
        lines_data = call_args.args[1]
        assert entry_data["referenceType"] == "manual"
        assert entry_data["createdBy"] == "user-1"
        assert lines_data[0]["debitAmount"] == 5000
        assert lines_data[1]["creditAmount"] == 5000
