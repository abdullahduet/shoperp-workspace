# Task 0013: Sales Recording Frontend

## Branch: task/0013-sales-frontend

## Context Bundle

### Relevant API Endpoints

**Prefix: `/api/sales`**

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | `/api/sales` | Yes | all | Paginated list. Params: `page`, `limit`, `start_date` (YYYY-MM-DD), `end_date`, `payment_method` |
| GET | `/api/sales/daily-summary` | Yes | admin, manager | Today's stats |
| GET | `/api/sales/:id` | Yes | all | Sale detail with items |
| POST | `/api/sales` | Yes | all | Record a sale |

**Sale response shape:**
```ts
interface Sale {
  id: string;
  sale_number: string;
  sale_date: string;          // ISO datetime
  customer_name: string | null;
  subtotal: number;           // paisa
  discount_amount: number;    // paisa
  tax_amount: number;         // paisa
  total_amount: number;       // paisa
  payment_method: string;     // cash | card | mobile | credit
  promotion_id: string | null;
  notes: string | null;
  recorded_by: string | null;
  items: SaleItem[];
  created_at: string;
}

interface SaleItem {
  id: string;
  product_id: string;
  quantity: number;
  unit_price: number;   // paisa
  discount: number;     // paisa (always 0 — promotion discount is at sale level)
  total_price: number;  // paisa
  created_at: string;
}
```

**Daily summary response shape:**
```ts
interface DailySummary {
  date: string;                    // YYYY-MM-DD
  total_sales: number;             // paisa
  transaction_count: number;
  payment_breakdown: {
    cash: number;
    card: number;
    mobile: number;
    credit: number;
  };
}
```

**POST /api/sales request body:**
```ts
{
  items: Array<{ product_id: string; quantity: number; unit_price: number }>;  // unit_price in paisa
  payment_method?: 'cash' | 'card' | 'mobile' | 'credit';  // default 'cash'
  customer_name?: string;
  notes?: string;
}
```
Note: server auto-applies best promotion — client does NOT send `promotion_id`.

**List response:** `{ success: true, data: Sale[], pagination: Pagination }`

### Relevant Patterns

**API client:** `import apiClient from '../api/client';` — axios with `withCredentials: true`, base URL `/api`.

**Money display:** All monetary fields are in paisa. Display: `৳${(value / 100).toFixed(2)}`. Input: user enters in ৳, submit `Math.round(input * 100)`.

**Pagination type:** `import type { Pagination } from '../types/product.types';`

**Role check pattern (positive):**
```tsx
const user = useAuthStore((state) => state.user);
const canViewSummary = user?.role === 'admin' || user?.role === 'manager';
```

**useFieldArray pattern (from PurchaseOrderFormPage.tsx):**
```tsx
import { useForm, useFieldArray, useWatch } from 'react-hook-form';
const { fields, append, remove } = useFieldArray({ control, name: 'items' });
const watchedItems = useWatch({ control, name: 'items' });
// Compute running subtotal from watchedItems
const subtotalPaisa = (watchedItems ?? []).reduce((sum, item) => {
  const qty = typeof item.quantity === 'number' ? item.quantity : 0;
  const unitPaisa = Math.round((typeof item.unit_price === 'number' ? item.unit_price : 0) * 100);
  return sum + qty * unitPaisa;
}, 0);
```

**Optional fields — send as `undefined`, NOT `""`:**
```ts
customer_name: values.customer_name || undefined,
notes: values.notes || undefined,
```

**useNavigate for redirect after record:**
```tsx
const navigate = useNavigate();
// After successful record:
navigate(`/sales/${newSale.id}`);
```

**Payment method badge colors:**
```tsx
const PAYMENT_BADGE: Record<string, string> = {
  cash: 'bg-green-100 text-green-700',
  card: 'bg-blue-100 text-blue-700',
  mobile: 'bg-purple-100 text-purple-700',
  credit: 'bg-orange-100 text-orange-700',
};
```

**Date display:** `new Date(date_string).toLocaleDateString()`

**Hook pattern (from usePurchaseOrders.ts):**
```ts
export function useSales(filters: Record<string, unknown> = {}) {
  return useQuery({
    queryKey: ['sales', filters],
    queryFn: () => saleService.list(filters),
  });
}
```

### Architecture Rules That Apply

- Rule 17: All server state via TanStack Query.
- Rule 18: All forms use React Hook Form + Zod.
- Rule 19: Pages handle loading skeleton, error display, empty state.
- Rule 20: No direct API calls from components. All calls go through service files.
- Optional fields sent as `undefined` not `""`.
- Role checks must be positive pattern.

## What to Build

### 1. Types — `frontend/src/types/sale.types.ts`

```ts
export interface SaleItem {
  id: string;
  product_id: string;
  quantity: number;
  unit_price: number;
  discount: number;
  total_price: number;
  created_at: string;
}

export interface Sale {
  id: string;
  sale_number: string;
  sale_date: string;
  customer_name: string | null;
  subtotal: number;
  discount_amount: number;
  tax_amount: number;
  total_amount: number;
  payment_method: string;
  promotion_id: string | null;
  notes: string | null;
  recorded_by: string | null;
  items: SaleItem[];
  created_at: string;
}

export interface DailySummary {
  date: string;
  total_sales: number;
  transaction_count: number;
  payment_breakdown: {
    cash: number;
    card: number;
    mobile: number;
    credit: number;
  };
}

export interface SaleFilters {
  start_date?: string;
  end_date?: string;
  payment_method?: string;
}

export interface SalePayload {
  items: Array<{ product_id: string; quantity: number; unit_price: number }>;
  payment_method?: string;
  customer_name?: string;
  notes?: string;
}
```

### 2. Service — `frontend/src/services/sale.service.ts`

```ts
import apiClient from '../api/client';
import type { Sale, DailySummary, SalePayload } from '../types/sale.types';
import type { Pagination } from '../types/product.types';

export const saleService = {
  list: async (params: {
    page?: number;
    limit?: number;
    start_date?: string;
    end_date?: string;
    payment_method?: string;
  }): Promise<{ data: Sale[]; pagination: Pagination }> => {
    const res = await apiClient.get('/sales', { params });
    return { data: res.data.data, pagination: res.data.pagination };
  },

  getById: async (id: string): Promise<Sale> => {
    const res = await apiClient.get(`/sales/${id}`);
    return res.data.data;
  },

  getDailySummary: async (): Promise<DailySummary> => {
    const res = await apiClient.get('/sales/daily-summary');
    return res.data.data;
  },

  create: async (data: SalePayload): Promise<Sale> => {
    const res = await apiClient.post('/sales', data);
    return res.data.data;
  },
};
```

### 3. Hooks — `frontend/src/hooks/useSales.ts`

```ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { saleService } from '../services/sale.service';
import type { SalePayload, SaleFilters } from '../types/sale.types';

export function useSales(filters: SaleFilters & { page?: number; limit?: number } = {}) {
  return useQuery({
    queryKey: ['sales', filters],
    queryFn: () => saleService.list(filters),
  });
}

export function useSale(id?: string) {
  return useQuery({
    queryKey: ['sales', id],
    queryFn: () => saleService.getById(id!),
    enabled: !!id,
  });
}

export function useDailySummary() {
  return useQuery({
    queryKey: ['sales', 'daily-summary'],
    queryFn: () => saleService.getDailySummary(),
  });
}

export function useRecordSale() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SalePayload) => saleService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sales'] });
    },
  });
}
```

### 4. Pages

#### `frontend/src/pages/SalesPage.tsx`

**List page with filter bar and conditional daily summary panel.**

**Filter bar fields:** `start_date` (date input), `end_date` (date input), `payment_method` (select: All / Cash / Card / Mobile / Credit), Apply button.

**Daily Summary panel (admin/manager only):** Shown above the table. Uses `useDailySummary()` hook. Cards:
- Today's Revenue: `৳${(summary.total_sales / 100).toFixed(2)}`
- Transactions: `summary.transaction_count`
- Cash / Card / Mobile / Credit breakdown (4 smaller cards each showing payment method total in ৳)

**Table columns:** Sale #, Date, Customer, Payment Method (badge), Subtotal (৳), Discount (৳), Total (৳), Actions.

**Actions:** Eye icon (view) → navigate to `/sales/:id` — all roles.

**Payment method badge colors:**
- `cash` → `bg-green-100 text-green-700`
- `card` → `bg-blue-100 text-blue-700`
- `mobile` → `bg-purple-100 text-purple-700`
- `credit` → `bg-orange-100 text-orange-700`

**"Record Sale" button** in page header → navigate to `/sales/new` — all roles.

**Pagination:** Standard prev/next buttons.

**Empty state:** "No sales found." message.

#### `frontend/src/pages/RecordSalePage.tsx`

**Form page for recording a new sale.**

**Form fields:**

1. **Items section (useFieldArray)** — dynamic rows, each with:
   - `Product ID` (text input — user enters UUID or SKU; keep it simple, no product picker for now)
   - `Quantity` (number input, min 1)
   - `Unit Price (৳)` (number input, min 0 — user enters in ৳, backend receives paisa)
   - Row total: `৳${(qty * unitPrice).toFixed(2)}` (computed display, not a form field)
   - Trash icon to remove row (disabled when only 1 row)
   
2. **"+ Add Item" button** below the rows.

3. **Subtotal display:** `Subtotal: ৳${subtotalDisplay}` below the items table (computed from watchedItems; promotion discount applied server-side so not shown here).

4. **Payment Method** (select: Cash / Card / Mobile / Credit, default Cash)

5. **Customer Name** (text input, optional)

6. **Notes** (textarea, optional)

**Zod schema:**
```ts
const itemSchema = z.object({
  product_id: z.string().min(1, 'Product ID required'),
  quantity: z
    .number({ invalid_type_error: 'Enter a valid quantity' })
    .int()
    .min(1, 'Must be at least 1'),
  unit_price: z
    .number({ invalid_type_error: 'Enter a valid price' })
    .min(0, 'Must be 0 or more'),
});

const saleSchema = z.object({
  items: z.array(itemSchema).min(1, 'At least one item required'),
  payment_method: z.enum(['cash', 'card', 'mobile', 'credit']).default('cash'),
  customer_name: z.string().optional().default(''),
  notes: z.string().optional().default(''),
});
```

**Payload construction:**
```ts
const payload: SalePayload = {
  items: values.items.map((item) => ({
    product_id: item.product_id,
    quantity: item.quantity,
    unit_price: Math.round(item.unit_price * 100),  // ৳ → paisa
  })),
  payment_method: values.payment_method,
  customer_name: values.customer_name || undefined,
  notes: values.notes || undefined,
};
```

**On success:** Navigate to `/sales/${newSale.id}`.

**Cancel link:** `← Back to Sales` → navigates to `/sales`.

**Error display:** Show mutation error message if recording fails (e.g., "Insufficient stock for product ...").

#### `frontend/src/pages/SaleDetailPage.tsx`

**Detail view for a single sale.**

**Header section:**
- Sale number, date (`new Date(sale.sale_date).toLocaleString()`), customer name (or "Walk-in" if null)
- Payment method badge

**Summary cards row (4 cards):**
- Subtotal: `৳${(sale.subtotal / 100).toFixed(2)}`
- Discount: `৳${(sale.discount_amount / 100).toFixed(2)}`
- Tax: `৳${(sale.tax_amount / 100).toFixed(2)}`
- Total: `৳${(sale.total_amount / 100).toFixed(2)}` — highlight this card (bold, larger text)

**Promotion applied:** If `sale.promotion_id !== null`, show a green info banner: "Promotion applied — discount: ৳X.XX"

**Items table columns:** Product ID, Quantity, Unit Price (৳), Total Price (৳).

**Notes:** If `sale.notes`, show below the items table.

**Back button:** `← Back to Sales` → `/sales`.

### 5. Wire Up

**`frontend/src/components/layout/AppLayout.tsx`**
- Enable Sales nav item: change `{ label: 'Sales', ..., enabled: false }` to `enabled: true`

**`frontend/src/router/index.tsx`**
- Import SalesPage, RecordSalePage, SaleDetailPage
- Add routes (CRITICAL: `/sales/new` BEFORE `/sales/:id`):
  ```tsx
  <Route path="sales" element={<SalesPage />} />
  <Route path="sales/new" element={<RecordSalePage />} />
  <Route path="sales/:id" element={<SaleDetailPage />} />
  ```

**Update CONTEXT.md** in every directory touched.

## Acceptance Criteria

- [ ] `tsc --noEmit` exits 0 (strict mode, no type errors)
- [ ] `SalesPage` renders table with filter bar and pagination
- [ ] Daily summary panel visible to admin/manager, hidden for staff (positive role check)
- [ ] Payment method badges show correct colors (green/blue/purple/orange)
- [ ] "Record Sale" button navigates to `/sales/new`
- [ ] `RecordSalePage` renders dynamic line item rows via `useFieldArray`
- [ ] Add/remove rows work; minimum 1 row (remove disabled when only 1 row)
- [ ] Running subtotal displayed and updates as items change (client-side, pre-promotion)
- [ ] `unit_price` submitted as `Math.round(input * 100)` paisa
- [ ] Optional fields (`customer_name`, `notes`) sent as `undefined` not `""`
- [ ] On success, navigate to `/sales/:id`
- [ ] `SaleDetailPage` shows header, 4 summary cards, items table
- [ ] Promotion applied banner shown when `promotion_id !== null`
- [ ] Route ordering: `/sales/new` before `/sales/:id` in router
- [ ] Sales nav item enabled in AppLayout
- [ ] CONTEXT.md updated in all touched directories

## Files to Create/Modify

**New:**
- `frontend/src/types/sale.types.ts`
- `frontend/src/services/sale.service.ts`
- `frontend/src/hooks/useSales.ts`
- `frontend/src/pages/SalesPage.tsx`
- `frontend/src/pages/RecordSalePage.tsx`
- `frontend/src/pages/SaleDetailPage.tsx`

**Modified:**
- `frontend/src/components/layout/AppLayout.tsx` — enable Sales nav item
- `frontend/src/router/index.tsx` — add 3 sales routes
- `frontend/src/types/CONTEXT.md`
- `frontend/src/services/CONTEXT.md`
- `frontend/src/hooks/CONTEXT.md`
- `frontend/src/pages/CONTEXT.md`

## Known Pitfalls

1. **Route ordering** — `/sales/new` must appear BEFORE `/sales/:id` in `router/index.tsx`. If reversed, React Router tries to match "new" as a sale UUID.

2. **unit_price in form is ৳, submit as paisa** — `Math.round(item.unit_price * 100)`. The form stores ৳ (decimal), submit multiplies by 100. Running subtotal also multiplies: `Math.round(item.unit_price * 100) * item.quantity`.

3. **DailySummary is admin/manager only** — use positive role check: `const canViewSummary = user?.role === 'admin' || user?.role === 'manager';`. Don't call `useDailySummary()` hook at all for staff (conditional query with `enabled: canViewSummary`). Or call it but only render if `canViewSummary`.

4. **useFieldArray minimum** — disable the remove button when `fields.length === 1` to prevent empty items array. `<button disabled={fields.length === 1} onClick={() => remove(index)}>`.

5. **Error from record sale** — the mutation error is an Axios error. Extract message: `(error as AxiosError<{error: string}>)?.response?.data?.error || 'Failed to record sale'`. Show it clearly to the user (not just in console).

6. **Row total display** — computed from watched values, not a Zod field:
   ```tsx
   const rowTotal = (typeof item.unit_price === 'number' ? item.unit_price : 0) *
                    (typeof item.quantity === 'number' ? item.quantity : 0);
   // Display: `৳${rowTotal.toFixed(2)}` (this is in ৳ since unit_price in form is ৳)
   ```

7. **Subtotal display** — also in ৳ (not paisa) since the form stores ৳:
   ```tsx
   const subtotalDisplay = (watchedItems ?? []).reduce((sum, item) => {
     return sum + (typeof item.unit_price === 'number' ? item.unit_price : 0) *
                  (typeof item.quantity === 'number' ? item.quantity : 0);
   }, 0).toFixed(2);
   // Display: `৳${subtotalDisplay}`
   ```

8. **`useWatch` for items** — use `useWatch({ control, name: 'items' })` to reactively compute subtotal. Without this, changes to items won't trigger re-render of the subtotal.

9. **`useDailySummary` hook with `enabled`** — if you call the hook conditionally, TypeScript may warn. Better to always call it but pass `enabled: canViewSummary`:
   ```ts
   export function useDailySummary(enabled = true) {
     return useQuery({
       queryKey: ['sales', 'daily-summary'],
       queryFn: () => saleService.getDailySummary(),
       enabled,
     });
   }
   ```

## Exit Signal

```bash
cd frontend && npx tsc --noEmit
# Must exit 0 with no type errors
```
