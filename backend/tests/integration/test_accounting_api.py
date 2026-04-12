"""
Integration tests for accounting endpoints:
  GET   /api/accounting/accounts
  GET   /api/accounting/journal-entries
  POST  /api/accounting/journal-entries

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


def _make_fake_account(
    *,
    account_id: str = "account-uuid-1",
    code: str = "1000",
    name: str = "Cash",
    account_type: str = "asset",
) -> MagicMock:
    account = MagicMock()
    account.id = account_id
    account.code = code
    account.name = name
    account.type = account_type
    account.parentId = None
    account.isActive = True
    account.createdAt = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return account


def _make_fake_je_line(
    *,
    line_id: str = "line-uuid-1",
    account_id: str = "account-uuid-1",
    debit_amount: int = 5000,
    credit_amount: int = 0,
) -> MagicMock:
    line = MagicMock()
    line.id = line_id
    line.accountId = account_id
    line.debitAmount = debit_amount
    line.creditAmount = credit_amount
    line.description = None
    return line


def _make_fake_journal_entry(
    *,
    entry_id: str = "je-uuid-1",
    entry_number: str = "JE-20260412-001",
    lines: list | None = None,
) -> MagicMock:
    entry = MagicMock()
    entry.id = entry_id
    entry.entryNumber = entry_number
    entry.date = datetime(2026, 4, 12, tzinfo=timezone.utc)
    entry.description = "Test entry"
    entry.referenceType = "manual"
    entry.referenceId = None
    entry.createdBy = "user-uuid-1"
    entry.journalEntryLines = lines or []
    entry.createdAt = datetime(2026, 4, 12, tzinfo=timezone.utc)
    return entry


def _make_accounting_db(
    *,
    account_find_many_return=None,
    account_find_first_return=None,
    je_find_many_return=None,
    je_find_first_return=None,
    je_count_return: int = 0,
) -> MagicMock:
    """Build a mock Prisma client with accounting model stubs."""
    db = MagicMock()

    # account
    db.account = MagicMock()
    db.account.find_many = AsyncMock(return_value=account_find_many_return or [])
    if account_find_first_return is not None:
        db.account.find_first = AsyncMock(return_value=account_find_first_return)
    else:
        db.account.find_first = AsyncMock(return_value=_make_fake_account())

    # journalentry
    db.journalentry = MagicMock()
    db.journalentry.find_many = AsyncMock(return_value=je_find_many_return or [])
    if je_find_first_return is not None:
        db.journalentry.find_first = AsyncMock(return_value=je_find_first_return)
    else:
        db.journalentry.find_first = AsyncMock(return_value=_make_fake_journal_entry())
    db.journalentry.count = AsyncMock(return_value=je_count_return)

    # journalentryline
    db.journalentryline = MagicMock()
    db.journalentryline.create = AsyncMock(return_value=None)

    # user
    db.user = MagicMock()
    db.user.find_first = AsyncMock(return_value=None)

    # Transaction mock
    mock_tx = MagicMock()
    created_entry = je_find_first_return or _make_fake_journal_entry()
    mock_tx.journalentry = MagicMock()
    mock_tx.journalentry.create = AsyncMock(return_value=created_entry)
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
# GET /api/accounting/accounts
# ---------------------------------------------------------------------------

class TestListAccounts:
    def test_admin_gets_200_with_account_list(self):
        fake_account = _make_fake_account()
        token, user = _admin_token()
        db = _make_accounting_db(account_find_many_return=[fake_account])
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get(
                "/api/accounting/accounts",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert isinstance(b["data"], list)
        assert len(b["data"]) == 1
        assert b["data"][0]["code"] == "1000"

    def test_manager_gets_200(self):
        token, user = _manager_token()
        db = _make_accounting_db(account_find_many_return=[])
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get(
                "/api/accounting/accounts",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200

    def test_staff_gets_403(self):
        token, user = _staff_token()
        db = _make_accounting_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get(
                "/api/accounting/accounts",
                cookies={"access_token": token},
            )

        assert resp.status_code == 403

    def test_unauthenticated_gets_401(self):
        db = _make_accounting_db()
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/accounting/accounts")

        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/accounting/journal-entries
# ---------------------------------------------------------------------------

class TestListJournalEntries:
    def test_admin_gets_200_paginated(self):
        line1 = _make_fake_je_line(debit_amount=5000, credit_amount=0)
        line2 = _make_fake_je_line(
            line_id="line-uuid-2", debit_amount=0, credit_amount=5000
        )
        fake_entry = _make_fake_journal_entry(lines=[line1, line2])
        token, user = _admin_token()
        db = _make_accounting_db(je_find_many_return=[fake_entry], je_count_return=1)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get(
                "/api/accounting/journal-entries",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert "pagination" in b
        assert b["pagination"]["total"] == 1

    def test_staff_gets_403(self):
        token, user = _staff_token()
        db = _make_accounting_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get(
                "/api/accounting/journal-entries",
                cookies={"access_token": token},
            )

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/accounting/journal-entries
# ---------------------------------------------------------------------------

class TestCreateJournalEntry:
    def _valid_payload(self) -> dict:
        return {
            "description": "Manual adjustment",
            "lines": [
                {
                    "account_id": "account-uuid-1",
                    "debit_amount": 5000,
                    "credit_amount": 0,
                },
                {
                    "account_id": "account-uuid-2",
                    "debit_amount": 0,
                    "credit_amount": 5000,
                },
            ],
        }

    def test_admin_creates_balanced_entry_returns_201(self):
        line1 = _make_fake_je_line(debit_amount=5000, credit_amount=0)
        line2 = _make_fake_je_line(
            line_id="line-uuid-2", account_id="account-uuid-2",
            debit_amount=0, credit_amount=5000,
        )
        fake_entry = _make_fake_journal_entry(lines=[line1, line2])
        token, user = _admin_token()
        db = _make_accounting_db(je_find_first_return=fake_entry)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/accounting/journal-entries",
                json=self._valid_payload(),
                cookies={"access_token": token},
            )

        assert resp.status_code == 201
        b = body(resp)
        assert b["success"] is True
        assert "lines" in b["data"]

    def test_unbalanced_entry_returns_422(self):
        token, user = _admin_token()
        db = _make_accounting_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        unbalanced = {
            "description": "Unbalanced",
            "lines": [
                {"account_id": "account-uuid-1", "debit_amount": 5000, "credit_amount": 0},
                {"account_id": "account-uuid-2", "debit_amount": 0, "credit_amount": 3000},
            ],
        }

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/accounting/journal-entries",
                json=unbalanced,
                cookies={"access_token": token},
            )

        assert resp.status_code == 422

    def test_manager_gets_403_on_create(self):
        token, user = _manager_token()
        db = _make_accounting_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/accounting/journal-entries",
                json=self._valid_payload(),
                cookies={"access_token": token},
            )

        assert resp.status_code == 403

    def test_staff_gets_403_on_create(self):
        token, user = _staff_token()
        db = _make_accounting_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/accounting/journal-entries",
                json=self._valid_payload(),
                cookies={"access_token": token},
            )

        assert resp.status_code == 403
