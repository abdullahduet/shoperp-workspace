# ShopERP — Product Requirements

## Overview

ShopERP is a mini retail back-office system (without POS) for managing a single retail shop. It handles inventory, suppliers, purchases, promotions, sales recording, accounting, and reporting.

## Users and Roles

- **Admin** — Full access to all modules including user management
- **Manager** — Can manage inventory, suppliers, purchases, promotions, view reports, record sales
- **Staff** — Can record sales, view inventory, view own activity

## Module Requirements

### 1. Authentication & User Management

**Registration:** Admin creates user accounts with email, password, name, and role assignment.

**Login:** Email + password authentication. Returns JWT token stored in HTTP-only cookie. Token expires after 7 days.

**Session:** JWT validated on every protected request via middleware. Invalid/expired tokens return 401.

**Password:** Bcrypt hashing with 12 salt rounds. Password change requires current password verification.

**Acceptance Criteria:**
- [ ] POST /auth/register creates user (admin only)
- [ ] POST /auth/login returns JWT in HTTP-only cookie
- [ ] POST /auth/logout clears token cookie
- [ ] GET /auth/me returns current user profile
- [ ] PUT /auth/me/password changes password with current password verification
- [ ] All routes except login/register require valid JWT
- [ ] Role-based middleware restricts endpoints by user role
- [ ] Passwords are never returned in any API response

### 2. Product & Category Management

**Categories:** Hierarchical (parent-child). Used to organize products. Categories can be nested one level deep.

**Products:** Core entity. Each product has: name, SKU (unique), barcode (optional, unique), category, unit price (selling), cost price (buying), tax rate (percentage), stock quantity, minimum stock level, unit of measure, active/inactive status.

**Acceptance Criteria:**
- [ ] Full CRUD for categories with parent-child support
- [ ] GET /categories/tree returns nested category structure
- [ ] Full CRUD for products with pagination, search (name, SKU), filter (category, active status)
- [ ] SKU uniqueness enforced at database level
- [ ] Barcode uniqueness enforced when provided
- [ ] POST /products/import accepts CSV with header row, creates products in batch
- [ ] GET /products/low-stock returns products where stock_quantity < min_stock_level
- [ ] Soft delete: products marked inactive, not removed

### 3. Inventory Tracking

**Stock Movements:** Every stock change is logged with: product, movement type (in/out/adjustment), quantity, stock before, stock after, reference (sale/PO/manual), who performed it, timestamp.

**Manual Adjustment:** Managers can adjust stock with a reason. Creates a stock movement record.

**Low Stock Alerts:** Products below minimum stock level appear in low-stock report and dashboard.

**Acceptance Criteria:**
- [ ] GET /inventory/movements returns paginated stock movement history with filters (product, type, date range)
- [ ] POST /inventory/adjust creates manual stock adjustment with reason (manager+ only)
- [ ] GET /inventory/valuation returns total inventory value (sum of stock_quantity × cost_price)
- [ ] Every stock change (sale, PO receive, adjustment) creates a stock_movement record
- [ ] stock_movement records are immutable (no update, no delete)

### 4. Supplier & Purchase Order Management

**Suppliers:** Name, contact person, phone, email, address, payment terms, active status.

**Purchase Orders:** Draft → Ordered → Partially Received → Received → Cancelled. Each PO has a supplier, line items (product + quantity + unit cost), auto-calculated totals. PO number auto-generated: `PO-YYYYMMDD-NNN`.

**Receiving:** Goods received against a PO. Supports partial receiving. Receiving auto-updates product stock and creates stock movement records.

**Acceptance Criteria:**
- [ ] Full CRUD for suppliers with search and filter
- [ ] GET /suppliers/:id/purchases returns supplier's PO history
- [ ] Full CRUD for purchase orders with line items
- [ ] PO number auto-generated and unique
- [ ] PO totals auto-calculated: subtotal + tax = total
- [ ] POST /purchase-orders/:id/submit changes status draft→ordered
- [ ] POST /purchase-orders/:id/receive accepts quantities per item, updates stock
- [ ] Partial receive: if not all items received, status = partially_received
- [ ] Full receive: all items received, status = received
- [ ] POST /purchase-orders/:id/cancel marks PO as cancelled (only if draft or ordered)
- [ ] Receiving creates stock_movement records for each item
- [ ] Receiving creates journal entry (debit Inventory, credit Accounts Payable)

### 5. Promotions & Discounts

**Types:** Percentage off, Fixed amount off, Buy-one-get-one (BOGO).

**Scope:** Applies to all products OR specific products only.

**Date Range:** Start date and end date. Auto-active within range.

**Conditions:** Optional minimum purchase amount.

**Stacking:** Only one promotion per sale. System selects the best (highest discount) automatically.

**Acceptance Criteria:**
- [ ] Full CRUD for promotions
- [ ] GET /promotions/active returns currently active promotions (within date range and is_active=true)
- [ ] Promotion with applies_to=specific has associated products via promotion_products table
- [ ] Percentage discount: discount = subtotal × (value / 100)
- [ ] Fixed discount: discount = min(value, subtotal) — cannot exceed subtotal
- [ ] BOGO: for qualifying products, every second item is free
- [ ] Date range enforcement: promotion only applies when current date is between start_date and end_date
- [ ] Minimum purchase amount enforced before discount applies

### 6. Sales Recording

This is NOT a POS. Sales are recorded manually or imported from an external POS system.

**Sale Structure:** Date, customer name (optional), line items (product + quantity + unit price), payment method, optional promotion applied. Sale number auto-generated: `SALE-YYYYMMDD-NNN`.

**Side Effects:** Recording a sale: deducts stock, creates stock movements, creates journal entry (debit Cash/Bank, credit Revenue).

**Acceptance Criteria:**
- [ ] POST /sales records a sale with line items
- [ ] Sale number auto-generated and unique
- [ ] Sale totals auto-calculated: subtotal - discount + tax = total
- [ ] Promotion auto-applied: best available promotion selected
- [ ] Stock deducted for each line item upon sale recording
- [ ] Stock movement records created for each line item
- [ ] Journal entry created: debit Cash, credit Sales Revenue
- [ ] GET /sales returns paginated list with filters (date range, payment method)
- [ ] GET /sales/:id returns sale detail with all line items
- [ ] GET /sales/daily-summary returns today's total sales, transaction count, payment breakdown

### 7. Accounting

**Chart of Accounts:** Pre-defined for retail: Cash, Accounts Receivable, Inventory, Accounts Payable, Sales Revenue, Cost of Goods Sold, Operating Expenses, Owner's Equity.

**Journal Entries:** Double-entry bookkeeping. Every entry has lines where sum(debits) = sum(credits). Entries reference their source (sale, purchase, expense, manual).

**Expenses:** Category, description, amount, payment method, date. Each expense auto-creates a journal entry.

**Acceptance Criteria:**
- [ ] GET /accounting/accounts returns chart of accounts
- [ ] GET /accounting/journal-entries returns entries with filters (date range, reference type)
- [ ] POST /accounting/journal-entries creates manual entry (admin only) — validates debits = credits
- [ ] Full CRUD for expenses with categories
- [ ] Expense recording auto-creates journal entry (debit Expense category, credit Cash)
- [ ] Sale recording auto-creates journal entry (debit Cash, credit Revenue)
- [ ] PO receiving auto-creates journal entry (debit Inventory, credit AP)
- [ ] Every journal entry: sum(debit_amount) == sum(credit_amount) — enforced at database constraint level
- [ ] GET /reports/profit-loss returns P&L for date range: Revenue - COGS - Expenses = Net Profit

### 8. Reports & Analytics

**Acceptance Criteria:**
- [ ] GET /reports/sales — sales by day/week/month for date range
- [ ] GET /reports/top-products — top N products by quantity sold
- [ ] GET /reports/low-stock — products below minimum stock level
- [ ] GET /reports/purchases — purchase summary for date range
- [ ] GET /reports/expenses — expense breakdown by category
- [ ] GET /reports/profit-loss — revenue, COGS, expenses, net profit for date range
- [ ] GET /reports/inventory-valuation — total value of current inventory
- [ ] All reports support `format` query param: `json` (default), `csv`

### 9. Dashboard

**Acceptance Criteria:**
- [ ] GET /dashboard/summary returns: today's sales total, today's transaction count, month's revenue, month's profit, low stock count
- [ ] GET /dashboard/trends returns: monthly sales totals for last 12 months
- [ ] Frontend dashboard page shows: stat cards, sales trend line chart, top 5 products bar chart, low stock alert list, recent 10 sales

## Non-Functional Requirements

- All API responses under 500ms for typical operations
- Pagination default: 20 items, max: 100 items
- Authentication on all routes except POST /auth/login
- Role-based access control on all mutation endpoints
- Input validation on all endpoints (Pydantic schemas)
- Consistent error response format across all endpoints
- All monetary values stored as integers (smallest currency unit)
- All dates in ISO 8601 format in API responses
- Database backup strategy documented
