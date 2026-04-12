# hooks — Context

## Purpose
Custom React hooks that compose TanStack Query mutations/queries with service calls and navigation.

## Key Files
- useAuth.ts → useCurrentUser (query), useLogin (mutation), useLogout (mutation)
- useCategories.ts → useCategories, useCategoryTree, useCreateCategory, useUpdateCategory, useDeleteCategory
- useProducts.ts → useProducts (paginated with filters), useProduct (by id), useCreateProduct, useUpdateProduct, useDeleteProduct
- useInventory.ts → useMovements (paginated with filters), useValuation, useAdjust (mutation)

## Patterns
Hooks use TanStack Query v5 syntax. useCurrentUser has staleTime: Infinity to avoid refetch on focus. Mutations update the Zustand store on success. useProducts queryKey includes the full filters object so TanStack Query refetches when any filter changes.

- useSuppliers.ts → useSuppliers, useSupplier, useCreateSupplier, useUpdateSupplier, useDeleteSupplier
- usePurchaseOrders.ts → usePurchaseOrders, usePurchaseOrder, useCreatePO, useUpdatePO, useDeletePO, useSubmitPO, useReceivePO (also invalidates inventory), useCancelPO

- usePromotions.ts → usePromotions, useActivePromotions, usePromotion, useCreatePromotion, useUpdatePromotion, useDeletePromotion

- useSales.ts → useSales (paginated with filters), useSale (by id), useDailySummary (enabled param for role-gating), useRecordSale (mutation)

- useAccounting.ts → useAccounts, useJournalEntries, useCreateJournalEntry, useExpenses, useCreateExpense, useUpdateExpense, useDeleteExpense

- useReports.ts → useDashboardSummary(enabled), useDashboardTrends(enabled) — both take enabled param to prevent firing for staff role

## Last Updated
2026-04-12 — added useReports (useDashboardSummary, useDashboardTrends with enabled param for role-gating)
