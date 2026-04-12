# sales — Context

## Purpose
Handles sale recording (retail transactions), sale retrieval, and daily summaries. A sale atomically deducts stock, records stock movements, and creates a balanced double-entry journal entry (debit Cash / credit Revenue). The best active promotion is auto-selected server-side; clients never specify a promotion.

## Key Files
- schemas.py → Pydantic models: SaleCreate, SaleItemCreate, SaleResponse, SaleItemResponse, DailySummaryResponse
- repository.py → DB queries only: find_by_id, find_paginated, find_today_sales, count helpers, create_sale_atomic (transaction)
- service.py → Business logic: record_sale (validate, discount, tax, totals), list, get_by_id, get_daily_summary
- controller.py → HTTP handlers: list_sales, get_sale, get_daily_summary, record_sale
- router.py → Route registration; /daily-summary BEFORE /{sale_id}

## Patterns
- `create_sale_atomic` uses `async with self.prisma.tx() as tx` covering sale + items + stock updates + stock movements + journal entry + journal entry lines.
- `sale.id` is available immediately after `tx.sale.create(...)` and used as `referenceId` for both stock movements and journal entry.
- Tax rate: `product.taxRate` is Prisma Decimal; always cast via `float(product.taxRate)` before arithmetic.
- Journal entry balance (Rule #21): debit Cash (code=1000) == credit Revenue (code=4000) == totalAmount.
- Promotion is auto-selected by calling `PromotionService.get_best_discount(subtotal, items)`.
- Payment methods: cash, card, mobile, credit.
- Sale number format: `SALE-YYYYMMDD-NNN`. Journal entry number: `JE-YYYYMMDD-NNN`.

## Last Updated
2026-04-11 — initial implementation (task/0012)
