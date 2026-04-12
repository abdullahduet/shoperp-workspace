# types — Context

## Purpose
TypeScript type definitions shared across the application.

## Key Files
- auth.types.ts → User, ApiResponse, LoginFormValues interfaces
- category.types.ts → Category, CategoryTreeNode, CategoryFormValues interfaces
- product.types.ts → Product, ProductFormValues, ImportResult, ProductFilters, Pagination interfaces
- inventory.types.ts → StockMovement, ValuationData, AdjustmentFormValues, MovementFilters interfaces

## Patterns
All types are plain interfaces (no classes). Import from here in services, hooks, components. Money values (unit_price, cost_price) are stored as paisa integers in Product; display as ৳(value/100).toFixed(2).

- supplier.types.ts → Supplier, SupplierFormValues interfaces
- purchase-order.types.ts → POItem, PurchaseOrder, POCreateFormValues, POItemFormValues, POFilters, POStatus interfaces

- promotion.types.ts → Promotion, PromotionFormValues, PromotionFilters, PromotionPayload, PromotionType, PromotionAppliesTo interfaces

- sale.types.ts → Sale, SaleItem, DailySummary, SaleFilters, SalePayload interfaces

- accounting.types.ts → Account, JournalEntryLine, JournalEntry, Expense, JournalEntryLineFormValues, JournalEntryPayload, ExpensePayload interfaces

- report.types.ts → DashboardSummary, TrendItem, Period, SalesReport, SalesReportItem, ProfitLossReport, TopProductsReport, TopProductItem, LowStockItem, PurchasesReport, PurchasesReportItem, ExpensesReport, ExpenseCategoryItem, InventoryValuationReport, InventoryValuationItem

## Last Updated
2026-04-12 — added report types (dashboard summary/trends, all report response shapes)
