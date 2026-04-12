# pages — Context

## Purpose
Top-level page components rendered by the router. Each page maps to a URL route.

## Key Files
- LoginPage.tsx → auth form with React Hook Form + Zod, calls useLogin mutation
- DashboardPage.tsx → placeholder page for authenticated home route
- CategoriesPage.tsx → category CRUD table with inline modal (create/edit), admin-only delete
- ProductsPage.tsx → paginated product list with filter bar (search, category, status, sort), row actions
- ProductDetailPage.tsx → product detail view, two-column layout, low-stock warning
- ProductFormPage.tsx → create/edit product form (RHF + Zod), paisa conversion on submit
- ProductImportPage.tsx → CSV file upload for bulk product import, shows ImportResult
- InventoryMovementsPage.tsx → paginated stock movements table with filters (product_id, type, date range); role-gated adjustment modal
- InventoryValuationPage.tsx → three-card summary showing total value (paisa→BDT), product count, currency

## Patterns
Pages handle loading/error/empty states. Forms use React Hook Form + Zod validation. Server errors show below the form from mutation.error.message. Delete errors display as inline red paragraphs (not window.alert). Role-based UI: admin sees delete; admin+manager see edit. Prices stored as paisa; display = (value/100).toFixed(2); submit = Math.round(displayValue * 100).

- SuppliersPage.tsx → paginated supplier list with search + active filter; create/edit modal (admin/manager); admin-only soft-delete
- PurchaseOrdersPage.tsx → paginated PO list with supplier + status filters; status badges; navigate to detail; admin-only cancel
- PurchaseOrderDetailPage.tsx → PO header + items table; status+role gated actions (Submit, Edit, Delete, Receive, Cancel); receive items modal
- PurchaseOrderFormPage.tsx → create-only PO form; dynamic item rows via useFieldArray; running subtotal; unit_cost paisa conversion on submit

- PromotionsPage.tsx → paginated promotions list with type + status filters; type badges (blue/purple/orange); computed status (Active/Inactive/Scheduled/Expired); create/edit inline modal with type-dependent value field; admin/manager edit; admin-only delete

- SalesPage.tsx → paginated sales list with date range + payment method filters; daily summary panel (admin/manager only) with revenue, transaction count, and payment breakdown cards; payment method badges (green/blue/purple/orange)
- RecordSalePage.tsx → new sale form with dynamic item rows via useFieldArray; running subtotal (client-side, ৳ display); unit_price entered in ৳, submitted as paisa; optional customer_name and notes sent as undefined not ""
- SaleDetailPage.tsx → sale header (sale_number, date, customer, payment badge); 4 summary cards (subtotal/discount/tax/total); promotion applied green banner when promotion_id set; items table; notes section

- AccountsPage.tsx → read-only chart of accounts table; sorted by code; type badges (blue/red/purple/green/orange); parent code lookup; no pagination (small dataset)
- JournalEntriesPage.tsx → paginated journal entries list with date range + reference_type filter; reference type badges (green/red/blue/gray); admin-only "New Entry" button; create modal with dynamic line rows via useFieldArray (min 2); running debit/credit totals via useWatch; line amounts in ৳ submitted as paisa
- ExpensesPage.tsx → paginated expenses list with date range + category filter; payment method badges (green/blue/purple/orange); create/edit inline modal; amount in ৳ submitted as paisa; edit pre-fills amount as paisa→৳; admin-only delete with window.confirm

## Last Updated
2026-04-12 — added AccountsPage, JournalEntriesPage, ExpensesPage
