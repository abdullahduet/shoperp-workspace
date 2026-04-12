# expenses — Context

## Purpose
Handles expense recording (cash outflows). Creating an expense atomically creates a balanced double-entry journal entry (debit Miscellaneous Expense code=6500 / credit Cash code=1000). The journal entry is immutable once created — updating an expense only modifies the expense record itself. Supports soft delete (admin only).

## Key Files
- schemas.py → Pydantic models: ExpenseCreate, ExpenseUpdate, ExpenseResponse; dataclass PaginatedExpenses; PaymentMethod literal
- repository.py → DB queries only: find_by_id, find_paginated, update, soft_delete, count_today_journal_entries, find_account_by_code, create_expense_atomic (transaction)
- service.py → Business logic: list (with date/category filters), create (looks up accounts, generates entry number, calls atomic repo), update (expense only), delete (soft), _generate_entry_number
- controller.py → HTTP handlers: list_expenses, create_expense, update_expense, delete_expense
- router.py → Routes under /expenses prefix; GET/POST on root (admin+manager), PUT/{id} (admin+manager), DELETE/{id} (admin only)

## Patterns
- `create_expense_atomic` uses `async with self.prisma.tx() as tx` covering expense + journal entry + 2 journal entry lines.
- Journal entry `referenceType="expense"`, `referenceId=expense.id`.
- Auto journal entry: debit account code="6500" (Misc Expense), credit code="1000" (Cash), amount=expense.amount.
- `obj.date` from Prisma `@db.Date` is a `datetime` object — use `.strftime("%Y-%m-%d")` in model_validate.
- Category filter uses Prisma `contains` with `mode: insensitive` for case-insensitive partial match.
- Delete returns 200 with `success_response(None, "Expense deleted")`.
- Journal entry number format: `JE-YYYYMMDD-NNN`.

## Last Updated
2026-04-12 — initial implementation (task/0014)
