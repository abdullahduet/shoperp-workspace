# services — Context

## Purpose
Service layer that wraps API calls. Components never call apiClient directly — they go through services.

## Key Files
- auth.service.ts → login, logout, me functions returning typed data
- category.service.ts → list, tree, create, update, delete for categories
- product.service.ts → list (paginated), lowStock, getById, create, update, delete, import (CSV multipart)
- inventory.service.ts → listMovements (paginated with filters), adjust (stock adjustment), getValuation

## Patterns
Each service function is async, unwraps `response.data.data`, and returns the typed entity. Errors propagate naturally from the axios interceptor. The product list returns `{ data, pagination }`. Import uses FormData with multipart/form-data header.

- supplier.service.ts → list (paginated + filters), getById, create, update, remove for suppliers
- purchase-order.service.ts → list (paginated + filters), getById, create, update, remove, submit, receive, cancel for purchase orders

- promotion.service.ts → list (paginated + filters), getActive, getById, create, update, remove for promotions

- sale.service.ts → list (paginated + filters), getById, getDailySummary, create for sales

- accounting.service.ts → listAccounts, listJournalEntries, createJournalEntry, listExpenses, createExpense, updateExpense, deleteExpense

## Last Updated
2026-04-12 — added accounting service (accounts, journal entries, expenses)
