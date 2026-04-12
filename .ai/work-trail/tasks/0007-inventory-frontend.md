# Task 0007: Inventory Frontend

## Branch: task/0007-inventory-frontend
## Assigned to: engineer
## Status: not started

## Context Bundle

### API Contract

```
GET  /api/inventory/movements   → { success, data: StockMovementResponse[], pagination }
POST /api/inventory/adjust      → { success, data: StockMovementResponse }   [admin, manager]
GET  /api/inventory/valuation   → { success, data: { total_value, product_count, currency } }
```

**GET /inventory/movements query params:**
- `page`, `limit` (default 20)
- `product_id` (UUID string)
- `movement_type` (`in` | `out` | `adjustment`)
- `start_date`, `end_date` (YYYY-MM-DD strings)

### TypeScript Types

```typescript
// src/types/inventory.types.ts

export interface StockMovement {
  id: string;
  product_id: string;
  product_name: string;
  product_sku: string;
  movement_type: 'in' | 'out' | 'adjustment';
  quantity: number;
  stock_before: number;
  stock_after: number;
  reference_type: string | null;
  reference_id: string | null;
  notes: string | null;
  performed_by: string | null;
  created_at: string;
}

export interface ValuationData {
  total_value: number;   // paisa integer
  product_count: number;
  currency: string;
}

export interface AdjustmentFormValues {
  product_id: string;
  quantity: number;       // signed: positive = stock in, negative = stock out
  notes: string;
}

export interface MovementFilters {
  product_id?: string;
  movement_type?: 'in' | 'out' | 'adjustment';
  start_date?: string;
  end_date?: string;
}
```

### Code Patterns to Follow

Identical to existing patterns in `src/services/`, `src/hooks/`, `src/pages/`.

**Service:**
```typescript
// src/services/inventory.service.ts
export const inventoryService = {
  listMovements: async (params: MovementFilters & { page?: number; limit?: number }) => {
    const res = await apiClient.get('/inventory/movements', { params });
    return { data: res.data.data as StockMovement[], pagination: res.data.pagination };
  },
  adjust: async (data: AdjustmentFormValues): Promise<StockMovement> => {
    const res = await apiClient.post('/inventory/adjust', data);
    return res.data.data;
  },
  getValuation: async (): Promise<ValuationData> => {
    const res = await apiClient.get('/inventory/valuation');
    return res.data.data;
  },
};
```

**Hook:**
```typescript
// src/hooks/useInventory.ts
export function useMovements(filters: MovementFilters & { page?: number; limit?: number } = {}) {
  return useQuery({
    queryKey: ['inventory', 'movements', filters],
    queryFn: () => inventoryService.listMovements(filters),
  });
}

export function useValuation() {
  return useQuery({
    queryKey: ['inventory', 'valuation'],
    queryFn: inventoryService.getValuation,
  });
}

export function useAdjust() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: inventoryService.adjust,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['inventory', 'movements'] }),
  });
}
```

### Architecture Rules That Apply

- Rule #17: TanStack Query for all server state
- Rule #18: React Hook Form + Zod for the adjustment form
- Rule #19: Loading / error / empty states on every page
- Rule #20: No direct API calls from components

## What to Build

### New Files

```
frontend/src/types/inventory.types.ts
frontend/src/services/inventory.service.ts
frontend/src/hooks/useInventory.ts
frontend/src/pages/InventoryMovementsPage.tsx
frontend/src/pages/InventoryValuationPage.tsx
```

### Pages

#### `InventoryMovementsPage.tsx`

Paginated table of stock movements with filters:

- **Header:** "Stock Movements" title
- **Filter bar:** Product ID input (text, optional), Movement Type select (All / In / Out / Adjustment), Start Date input (`<input type="date">`), End Date input
- **Table columns:** Date/time, Product (name + SKU badge), Type (badge: In=green, Out=red, Adjustment=yellow), Qty (signed: +10 / -5), Before → After (e.g. "90 → 100"), Reference, Notes
- **Pagination:** prev/next with "Page X of Y"
- **Empty state:** "No stock movements found."
- **Loading:** `<LoadingSkeleton />`
- **Error:** `<ErrorDisplay message={...} />`
- **Adjust button:** "New Adjustment" button (admin/manager only — show if `user.role !== 'staff'`) opens an inline modal

**Adjustment modal** (inline, no library):
- Form fields: Product ID (text input, required — in a real app this would be a product search; for now a plain text input for the UUID), Quantity (number input, non-zero — positive = add stock, negative = remove), Notes (textarea, optional)
- Zod schema: `product_id: z.string().min(1)`, `quantity: z.number().int().refine(v => v !== 0, 'Must be non-zero')`, `notes: z.string().optional()`
- On submit: `useAdjust()` mutation; close modal on success; show server error inside modal on failure
- Submit button disabled while pending

#### `InventoryValuationPage.tsx`

A simple summary page:

- **Header:** "Inventory Valuation"
- **Stat cards (3):**
  - Total Inventory Value: `৳{(total_value / 100).toFixed(2)}` (big number)
  - Products in Stock: `product_count`
  - Currency: BDT
- Use `useValuation()` hook
- Loading: skeleton cards
- Error: `<ErrorDisplay />`

### Navigation

Update `frontend/src/components/layout/AppLayout.tsx`:
- Enable the **Inventory** nav link → `/inventory/movements`
- Keep all other disabled links as-is

### Router

Update `frontend/src/router/index.tsx`:
- Add under the protected layout:
  - `/inventory/movements` → `<InventoryMovementsPage />`
  - `/inventory/valuation` → `<InventoryValuationPage />`

### CONTEXT.md Updates

Update:
- `frontend/src/types/CONTEXT.md`
- `frontend/src/services/CONTEXT.md`
- `frontend/src/hooks/CONTEXT.md`
- `frontend/src/pages/CONTEXT.md`
- `frontend/src/router/CONTEXT.md`

## Acceptance Criteria

- [ ] `/inventory/movements` loads paginated movements table
- [ ] Filters (product_id, movement_type, start_date, end_date) update the table
- [ ] "New Adjustment" button visible to admin/manager, hidden to staff
- [ ] Adjustment modal: Zod validation, server error display, closes on success
- [ ] After successful adjustment, movements list refreshes (query invalidation)
- [ ] `/inventory/valuation` shows total_value (৳ formatted), product_count, currency
- [ ] Inventory nav link is active in AppLayout
- [ ] No TypeScript errors: `tsc --noEmit` exits 0

## Known Pitfalls

- `quantity` in the form should be a number input. Use `valueAsNumber` in RHF register: `register('quantity', { valueAsNumber: true })`
- Quantity can be negative — do NOT use `min={0}` on the number input
- Filter changes should reset page to 1
- `useMovements` queryKey must include the filters object so TanStack Query refetches on change
- The user role check for "New Adjustment" button: `user?.role !== 'staff'` — get user from `useCurrentUser()`

## Exit Signal

```bash
cd /Users/abdullah/projects/shoperp-workspace/frontend && npx tsc --noEmit
# 0 errors
```

## Outcome (filled by Lead after merge)

_Not yet completed._
