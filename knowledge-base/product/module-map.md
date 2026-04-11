# ShopERP — Module Map

## Module Status

| # | Module | Priority | Status | Dependencies | Phase |
|---|--------|----------|--------|-------------|-------|
| 1 | Foundation + Auth | P0 | Not Started | None | 1 |
| 2 | Products + Categories | P1 | Not Started | Auth | 2 |
| 3 | Inventory Tracking | P1 | Not Started | Products | 3 |
| 4 | Suppliers + Purchases | P2 | Not Started | Products, Inventory | 4 |
| 5 | Promotions | P3 | Not Started | Products | 5 |
| 6 | Sales Recording | P3 | Not Started | Products, Inventory, Promotions | 6 |
| 7 | Accounting | P4 | Not Started | Sales, Purchases | 7 |
| 8 | Reports + Dashboard | P5 | Not Started | All modules | 8 |

## Dependency Graph

```
Auth (P0)
  └── Products + Categories (P1)
        ├── Inventory Tracking (P1)
        │     ├── Suppliers + Purchases (P2)
        │     │     └── Accounting (P4) ──┐
        │     └── Sales Recording (P3) ───┤
        │           └── Accounting (P4) ──┤
        └── Promotions (P3)               │
              └── Sales Recording (P3)    │
                                          └── Reports + Dashboard (P5)
```

## Phase Definitions

**Phase 1 — Foundation:** Project scaffolding, Docker, database, auth middleware, shared utilities, error handling, health check. Exit: `docker compose up` works, auth endpoints functional, tests pass.

**Phase 2 — Products:** Categories CRUD, products CRUD with search/filter/pagination, CSV import, low-stock query. Exit: all product endpoints functional with tests.

**Phase 3 — Inventory:** Stock movement tracking, manual adjustment, valuation report. Exit: stock movements recorded on every stock change.

**Phase 4 — Suppliers + Purchases:** Supplier CRUD, PO lifecycle (draft→ordered→received→cancelled), partial receiving, stock integration. Exit: receiving a PO updates stock and creates movements.

**Phase 5 — Promotions:** Promotion CRUD, date-range enforcement, product association, discount calculation engine. Exit: promotions correctly calculate discounts.

**Phase 6 — Sales:** Sale recording with line items, promotion application, stock deduction, journal entry creation. Exit: recording a sale correctly updates stock and accounting.

**Phase 7 — Accounting:** Chart of accounts, journal entries, expense recording, P&L report. Exit: double-entry bookkeeping balances, P&L report is accurate.

**Phase 8 — Reports + Dashboard:** All report endpoints, CSV export, dashboard summary and trends, frontend dashboard page. Exit: all reports return correct data, dashboard renders.
