# Completed Tasks

Agents MUST update this file after every task is verified and merged. This prevents duplicate work.

## Format

```
### [YYYY-MM-DD] Task NNNN — Title
- **Module:** module name
- **Agent:** who did the work
- **What:** brief description
- **Files:** list of files created/modified
- **Tests:** pass count or "not yet tested"
- **Merge:** commit hash
```

## Completed Work

### [2026-04-11] Task 0013 — Sales Recording Frontend
- **Module:** Phase 6 / Sales Recording
- **Agent:** Engineer
- **What:** SalesPage (list table, date/payment_method filters, pagination, daily summary panel for admin/manager). RecordSalePage (useFieldArray dynamic items, running subtotal in ৳, unit_price→paisa conversion, AxiosError display, redirect to detail on success). SaleDetailPage (header with payment badge, 4 summary cards, items table, promotion applied banner). Sales nav item enabled.
- **Files:** 6 new (sale.types.ts, sale.service.ts, useSales.ts, SalesPage.tsx, RecordSalePage.tsx, SaleDetailPage.tsx) + 2 modified (AppLayout.tsx, router/index.tsx) + 4 CONTEXT.md updates
- **Tests:** tsc --noEmit exits 0 (strict mode)
- **Merge:** phase/6-sales-recording
- **QA note:** APPROVED. All 16 criteria met first submission.

### [2026-04-11] Task 0012 — Sales Recording Backend
- **Module:** Phase 6 / Sales Recording
- **Agent:** Engineer
- **What:** 4 endpoints (GET /sales paginated, GET /sales/daily-summary admin/manager only, GET /sales/:id, POST /sales). Atomic transaction: sale + sale_items + stock deductions + stock_movements (type="out") + journal entry (debit Cash 1000, credit Revenue 4000, balanced). Sale number auto-generated (SALE-YYYYMMDD-NNN). Promotion auto-applied server-side via PromotionService.get_best_discount(). Tax computed from product.taxRate (Decimal). Added get_best_discount() to PromotionService. Fixed pre-existing lint in 5 test files.
- **Files:** 10 new (sales module: schemas, repository, service, controller, router, CONTEXT, __init__, 2 test files) + 4 modified (promotions/service.py, main.py, modules/CONTEXT.md, promotions/CONTEXT.md) + 5 lint fixes
- **Tests:** 406 total passing (28 new: 16 unit + 12 integration + 2 TestGetBestDiscount in promotions)
- **Merge:** phase/6-sales-recording
- **QA note:** 1 defect fixed — promotions/CONTEXT.md not updated to include get_best_discount; 5 pre-existing lint errors (unused imports, E702 semicolons) fixed before merge.

### [2026-04-11] Task 0011 — Promotions Frontend
- **Module:** Phase 5 / Promotions
- **Agent:** Engineer
- **What:** PromotionsPage with inline create/edit modal. Type badges (blue/purple/orange). 4-state status computation (Active/Scheduled/Expired/Inactive) from date range + is_active. Type-dependent value display (% / ৳ / —) and form input (hidden for bogo, ৳ conversion for fixed, plain for percentage). Datetime-local inputs with ISO conversion. Product IDs textarea shown only for applies_to='specific'. Nav item enabled.
- **Files:** 10 — types/promotion.types.ts, services/promotion.service.ts, hooks/usePromotions.ts, pages/PromotionsPage.tsx, AppLayout.tsx, router/index.tsx, 4 CONTEXT.md updates
- **Tests:** tsc --noEmit exits 0 (strict mode)
- **Merge:** 39f11bd
- **QA note:** APPROVED. All criteria met first submission.

### [2026-04-11] Task 0010 — Promotions Backend
- **Module:** Phase 5 / Promotions
- **Agent:** Engineer
- **What:** 6 endpoints (list/active/get/create/update/delete). Discount engine: percentage=`int(subtotal*value/100)`, fixed=`min(value,subtotal)`, bogo=`sum(qty//2 * unit_price)` for qualifying products. `applies_to='specific'` scopes BOGO to promotion_products. Min-purchase guard. Product associations in transaction. `product_ids=None` in update preserves existing products.
- **Files:** 11 — backend/src/modules/promotions/{schemas,repository,service,controller,router,CONTEXT}.py + __init__.py; 2 test files; backend/src/main.py modified
- **Tests:** 37 new (23 unit + 14 integration), 376 total passing
- **Merge:** 78a838b
- **QA note:** APPROVED. All 7 calculate_discount scenarios tested. All criteria met first submission.

### [2026-04-11] Task 0009 — Suppliers + Purchases Frontend
- **Module:** Phase 4 / Suppliers + Purchases
- **Agent:** Engineer
- **What:** SuppliersPage (inline create/edit modal, admin-only delete, search + active filter, pagination). PurchaseOrdersPage (list with supplier + status filters, status badges with 5 color states, inline cancel). PurchaseOrderDetailPage (header details, items table ৳, status+role gated action buttons: Submit/Edit/Delete/Receive/Cancel, receive items modal with per-item remaining qty validation). PurchaseOrderFormPage (create only, dynamic line items via useFieldArray, running subtotal ৳, unit_cost paisa conversion). Nav enabled for Suppliers + Purchases.
- **Files:** 16 — 2 types, 2 services, 2 hooks, 4 pages, AppLayout + router + 4 CONTEXT.md updates
- **Tests:** tsc --noEmit exits 0 (strict mode)
- **Merge:** 1724874
- **QA note:** APPROVED. Advisory: "Edit PO" link in detail page navigates to unregistered `/purchases/:id/edit` route (intentional — edit not in scope for this task).

### [2026-04-11] Task 0008 — Suppliers + Purchases Backend
- **Module:** Phase 4 / Suppliers + Purchases
- **Agent:** Engineer
- **What:** Suppliers module (5 endpoints: list/get/create/update/delete) + Purchase Orders module (9 endpoints: list/get/create/update/delete/submit/receive/cancel). PO number auto-generation (PO-YYYYMMDD-NNN). Receive transaction atomically updates received quantities, product stock, and creates stock_movement records (Rule #22). Partial vs full receive detection. Cancel allowed for draft/ordered only.
- **Files:** 21 — backend/src/modules/suppliers/{schemas,repository,service,controller,router,CONTEXT}.py + __init__.py; backend/src/modules/purchase_orders/{schemas,repository,service,controller,router,CONTEXT}.py + __init__.py; 4 test files; backend/src/main.py modified
- **Tests:** 57 new (22 unit suppliers + 15 unit POs + 9 integration suppliers + 14 integration POs = 57), 339 total passing
- **Merge:** a966c68
- **QA note:** 1 blocker fixed — `update_draft` wiped items on notes-only update (items_data=[] unconditionally). Fixed: signature `items_data: list[dict] | None`; service passes `None` when caller omits items. 4 lint fixes (unused imports/variables in test files).

### [2026-04-11] Task 0007 — Inventory Frontend
- **Module:** Phase 3 / Inventory Tracking
- **Agent:** Engineer
- **What:** InventoryMovementsPage (paginated table, product/type/date filters, adjustment modal role-gated to admin/manager), InventoryValuationPage (3 stat cards with ৳ formatting). Inventory nav link enabled.
- **Files:** 12 — types/inventory.types.ts, services/inventory.service.ts, hooks/useInventory.ts, pages/{InventoryMovements,InventoryValuation}Page.tsx, AppLayout.tsx, router/index.tsx, 5 CONTEXT.md updates
- **Tests:** tsc --noEmit exits 0
- **Merge:** phase/3-inventory-tracking (merged 2026-04-11)
- **QA note:** APPROVED. 2 warnings fixed in-place by Lead (positive role check for adjust button; `notes?: string` optional type)

### [2026-04-11] Task 0006 — Inventory Backend
- **Module:** Phase 3 / Inventory Tracking
- **Agent:** Engineer
- **What:** 3 endpoints — movements (paginated, filtered), manual adjust (atomic tx: update product.stockQuantity + create stock_movement), valuation (sum in service layer). Negative stock guard, inactive product guard.
- **Files:** 11 — backend/src/modules/inventory/{__init__,schemas,repository,service,controller,router,CONTEXT}.py + 2 test files + main.py modified
- **Tests:** 23 new, 282 total passing
- **Merge:** phase/3-inventory-tracking (merged 2026-04-11)
- **QA note:** 1 blocker fixed — valuation arithmetic was in repository (Rule #11 violation); moved sum/len to service. 2 warnings fixed — added staff-200 and inactive-product-422 integration tests.

### [2026-04-11] Task 0005 — Products + Categories Frontend
- **Module:** Phase 2 / Products + Categories
- **Agent:** Engineer
- **What:** 5 pages (CategoriesPage with inline modal, ProductsPage paginated+filtered, ProductDetailPage, ProductFormPage create+edit, ProductImportPage CSV). Services, hooks, types. Paisa ↔ ৳ conversion, debounced search, role-aware actions, nav links enabled.
- **Files:** 18 — frontend/src/types/{category,product}.types.ts; services/{category,product}.service.ts; hooks/{useCategories,useProducts}.ts; pages/{Categories,Products,ProductDetail,ProductForm,ProductImport}Page.tsx; AppLayout.tsx, router/index.tsx, 5 CONTEXT.md updates
- **Tests:** tsc --noEmit exits 0 (strict mode)
- **Merge:** phase/2-products-categories (merged 2026-04-11)
- **QA note:** 2 blockers fixed — sort key split broken for multi-underscore field names (`stock_quantity`, `unit_price`); optional nullable fields sent as `""` instead of `undefined`, causing Prisma UUID/unique errors

### [2026-04-11] Task 0004 — Products + Categories Backend
- **Module:** Phase 2 / Products + Categories
- **Agent:** Engineer
- **What:** Full CRUD for categories (5 endpoints: list, tree, create, update, delete) and products (7 endpoints: list, low-stock, import, get, create, update, delete). Paginated list with search/filter/sort. CSV bulk import. Soft delete with guard (category blocked if has active products).
- **Files:** 22 files — backend/src/modules/categories/{schemas,repository,service,controller,router,CONTEXT}.py + __init__.py; backend/src/modules/products/{schemas,repository,service,controller,router,CONTEXT}.py + __init__.py; 5 test files; backend/src/main.py modified
- **Tests:** 73 new, 259 total passing
- **Merge:** phase/2-products-categories (merged 2026-04-11)
- **QA note:** 1 blocker fixed — `has_active_products` was missing `isActive=True` filter; 2 warnings fixed — added 3 missing integration tests (422/409 error paths) and `Literal["asc","desc"]` validation on order param

### [2026-04-11] Task 0003 — Auth Frontend
- **Module:** Foundation / Auth
- **Agent:** Engineer
- **What:** Full React/TS frontend scaffold — axios client (withCredentials, 401 interceptor), Zustand v5 auth store, TanStack Query hooks (useCurrentUser/useLogin/useLogout), React Hook Form + Zod login form, protected routes, AppLayout with collapsible sidebar, docker-compose frontend service
- **Files:** frontend/ (33 files created) — Dockerfile, package.json, tsconfig.json, vite.config.ts, tailwind.config.ts, postcss.config.ts, index.html, src/main.tsx, src/App.tsx, src/index.css, src/types/auth.types.ts, src/api/client.ts, src/store/auth.store.ts, src/services/auth.service.ts, src/hooks/useAuth.ts, src/components/ui/{LoadingSkeleton,ErrorDisplay}.tsx, src/components/layout/{AppLayout,AuthLayout}.tsx, src/pages/{LoginPage,DashboardPage}.tsx, src/router/{index,ProtectedRoute}.tsx, 8×CONTEXT.md; docker-compose.yml updated
- **Tests:** tsc --noEmit exits 0 (strict mode, no type errors)
- **Merge:** phase/1-foundation-auth (merged 2026-04-11)
- **QA note:** APPROVED — all 9 acceptance criteria met; 3 warnings noted as future backlog (dead VITE_API_URL env var, no redirect-if-authed on /login, no 404 catch-all route)

### [2026-04-11] Task 0002 — Auth Backend
- **Module:** Foundation / Auth
- **Agent:** Engineer
- **What:** JWT cookie auth, users module (register/login/logout/me/password), core/auth.py with get_current_user + require_roles dependencies
- **Files:** src/core/auth.py, src/modules/auth/{router,controller,service,repository,schemas,CONTEXT}.py, 3 test files (unit: 53 + integration: 29 + schemas: 16 = 98 new tests)
- **Tests:** 186 total passing (unit + integration)
- **Merge:** phase/1-foundation-auth (merged 2026-04-11)
- **QA note:** 2 blocking defects fixed — password min_length=8 moved to Pydantic Field (Rule #12)

### [2026-04-11] Task 0001 — Infrastructure Scaffold
- **Module:** Foundation
- **Agent:** Engineer
- **What:** Docker Compose setup, FastAPI app skeleton, Prisma schema (15 tables), DB migration, seed data (13 accounts), typed exceptions, response helpers, health endpoint
- **Files:** docker-compose.yml, backend/Dockerfile, backend/requirements.txt, backend/prisma/schema.prisma, backend/prisma/migrations/, backend/prisma/seed.py, backend/src/main.py, backend/src/config.py, backend/src/database.py, backend/src/core/exceptions.py, backend/src/core/responses.py, backend/src/modules/health/router.py, backend/tests/ (104 tests)
- **Tests:** 104 passed (31 exceptions, 37 responses, 24 exception handler, 12 health)
- **Merge:** 211f2ae
