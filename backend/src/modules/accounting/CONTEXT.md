# accounting — Context

## Purpose
Provides double-entry bookkeeping functionality. Manages the chart of accounts and journal entries. Supports listing all active accounts, paginated journal entry retrieval with date/reference_type filters, and creating manual balanced journal entries (admin only). All journal entries must balance: sum(debit_amount) == sum(credit_amount).

## Key Files
- schemas.py → Pydantic models: AccountResponse, JournalEntryCreate, JournalEntryLineCreate, JournalEntryLineResponse, JournalEntryResponse; dataclass PaginatedJournalEntries
- repository.py → DB queries only: find_all_accounts, find_journal_entries_paginated (with lines included), count_today_journal_entries, find_account_by_id, create_journal_entry_with_lines (transaction)
- service.py → Business logic: list_accounts, list_journal_entries (with filters), create_journal_entry (validates balance Rule #21), _generate_entry_number
- controller.py → HTTP handlers: list_accounts, list_journal_entries, create_journal_entry
- router.py → Routes under /accounting prefix; GET /accounts and GET /journal-entries (admin+manager), POST /journal-entries (admin only)

## Patterns
- Journal entry number format: `JE-YYYYMMDD-NNN`.
- `obj.date` from Prisma `@db.Date` is a `datetime` object — use `.strftime("%Y-%m-%d")` in model_validate.
- When writing dates: pass `datetime(year, month, day, tzinfo=timezone.utc)`.
- Balance validation (Rule #21): raise `ValidationError` if total_debit != total_credit or both are zero.
- `find_journal_entries_paginated` always includes `journalEntryLines` so model_validate works.
- Manual entries use `referenceType="manual"`.

## Last Updated
2026-04-12 — initial implementation (task/0014)
