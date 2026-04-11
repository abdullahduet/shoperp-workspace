# Task 0011: Promotions Frontend

## Branch: task/0011-promotions-frontend

## Context Bundle

### Relevant API Endpoints

**Prefix: `/api/promotions`**

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | `/api/promotions` | Yes | all | Paginated list. Params: `page`, `limit`, `is_active` (bool), `type` (str) |
| GET | `/api/promotions/active` | Yes | all | Currently active (date range + is_active=true) |
| GET | `/api/promotions/:id` | Yes | all | Single promotion detail |
| POST | `/api/promotions` | Yes | admin, manager | Create promotion |
| PUT | `/api/promotions/:id` | Yes | admin, manager | Update promotion |
| DELETE | `/api/promotions/:id` | Yes | admin | Soft delete |

**Promotion response shape:**
```ts
{
  id: string;
  name: string;
  type: 'percentage' | 'fixed' | 'bogo';
  value: number;             // percentage points or paisa; 0 for bogo
  start_date: string;        // ISO datetime
  end_date: string;          // ISO datetime
  min_purchase_amount: number; // paisa integer
  applies_to: 'all' | 'specific';
  is_active: boolean;
  product_ids: string[];     // populated when applies_to='specific'
  created_at: string;
}
```

**Create/update body:**
```ts
{
  name: string;
  type: 'percentage' | 'fixed' | 'bogo';
  value: number;             // % points or paisa; send 0 for bogo
  start_date: string;        // ISO datetime string e.g. "2026-06-01T00:00:00+00:00"
  end_date: string;
  min_purchase_amount?: number; // paisa integer (default 0)
  applies_to: 'all' | 'specific';
  is_active?: boolean;
  product_ids?: string[];    // required when applies_to='specific'
}
```

**List response:** `{ success: true, data: Promotion[], pagination: Pagination }`

### Relevant Patterns

**API client:** `import apiClient from '../api/client';` — axios with `withCredentials: true`, base URL `/api`.

**Money display:** `min_purchase_amount` is in paisa. Display: `৳${(value / 100).toFixed(2)}`. Submit: `Math.round(input * 100)`.

**`value` field** — NOT always money:
- For `type='percentage'`: `value` = percentage points (e.g. 20 = 20%). Display as `${value}%`. Input as plain number.
- For `type='fixed'`: `value` = paisa discount. Display as `৳${(value / 100).toFixed(2)}`. Input in ৳, submit `Math.round(input * 100)`.
- For `type='bogo'`: `value` = 0 always. Hide input or disable.

**Date display:** `new Date(date_string).toLocaleDateString()`

**Date input for forms:** Use `<input type="datetime-local">`. When submitting, append `+00:00` if not already present to make it a valid ISO datetime for the backend:
```ts
const toIsoString = (localStr: string) => localStr ? localStr + ':00.000Z'.replace('Z', '+00:00') : '';
// Simpler: just use the value directly — the backend accepts ISO strings
// Best: store as "YYYY-MM-DDTHH:mm" (datetime-local format) and submit as:
// new Date(value).toISOString()  — converts to UTC ISO string
```

**Role check pattern (positive):**
```tsx
const user = useAuthStore((state) => state.user);
const canEdit = user?.role === 'admin' || user?.role === 'manager';
const isAdmin = user?.role === 'admin';
```

**Hook/service pattern (from useSuppliers.ts):**
```ts
export function usePromotions(filters = {}) {
  return useQuery({
    queryKey: ['promotions', filters],
    queryFn: () => promotionService.list(filters),
  });
}
```

**Existing Pagination type:**
```ts
import type { Pagination } from '../types/product.types';
```

**Status badge color pattern (from PurchaseOrdersPage.tsx):**
```tsx
const badge = isCurrentlyActive
  ? 'bg-green-100 text-green-800'
  : 'bg-gray-100 text-gray-600';
```

A promotion is "currently active" if `is_active === true AND new Date() >= new Date(start_date) AND new Date() <= new Date(end_date)`.

### Architecture Rules That Apply

- Rule 17: All server state via TanStack Query.
- Rule 18: Forms via React Hook Form + Zod.
- Rule 19: Pages handle loading skeleton, error, empty state.
- Rule 20: No direct API calls from components.
- Optional fields sent as `undefined` not `""`.
- Role checks must be positive pattern.

## What to Build

### 1. Types — `frontend/src/types/promotion.types.ts`

```ts
export type PromotionType = 'percentage' | 'fixed' | 'bogo';
export type PromotionAppliesTo = 'all' | 'specific';

export interface Promotion {
  id: string;
  name: string;
  type: PromotionType;
  value: number;
  start_date: string;
  end_date: string;
  min_purchase_amount: number;
  applies_to: PromotionAppliesTo;
  is_active: boolean;
  product_ids: string[];
  created_at: string;
}

export interface PromotionFormValues {
  name: string;
  type: PromotionType;
  value: number;
  start_date: string;
  end_date: string;
  min_purchase_amount: number;
  applies_to: PromotionAppliesTo;
  is_active: boolean;
  product_ids: string[];
}

export interface PromotionFilters {
  is_active?: boolean;
  type?: string;
}
```

### 2. Service — `frontend/src/services/promotion.service.ts`

Methods:
- `list(params: { page?, limit?, is_active?, type? })` → `{ data: Promotion[]; pagination: Pagination }`
- `getActive()` → `Promotion[]`
- `getById(id)` → `Promotion`
- `create(data: PromotionPayload)` → `Promotion`
- `update(id, data: Partial<PromotionPayload>)` → `Promotion`
- `remove(id)` → `void`

Where `PromotionPayload`:
```ts
interface PromotionPayload {
  name: string;
  type: PromotionType;
  value: number;        // already in correct unit (% or paisa)
  start_date: string;   // ISO datetime string
  end_date: string;
  min_purchase_amount: number; // paisa
  applies_to: PromotionAppliesTo;
  is_active: boolean;
  product_ids: string[];
}
```

### 3. Hooks — `frontend/src/hooks/usePromotions.ts`

- `usePromotions(filters?)` — queryKey: `['promotions', filters]`
- `useActivePromotions()` — queryKey: `['promotions', 'active']`
- `usePromotion(id)` — queryKey: `['promotions', id]`, enabled: `!!id`
- `useCreatePromotion()` — invalidates `['promotions']`
- `useUpdatePromotion()` — invalidates `['promotions']`
- `useDeletePromotion()` — invalidates `['promotions']`

### 4. Page — `frontend/src/pages/PromotionsPage.tsx`

**Single page with inline create/edit modal** (same pattern as SuppliersPage).

**List table columns:** Name, Type badge, Value display, Date Range, Min Purchase, Scope, Status badge, Actions.

**Type badge colors:**
- `percentage` → blue: `bg-blue-100 text-blue-700`
- `fixed` → purple: `bg-purple-100 text-purple-700`
- `bogo` → orange: `bg-orange-100 text-orange-700`

**Value display logic:**
- `percentage` → `${value}%`
- `fixed` → `৳${(value / 100).toFixed(2)}`
- `bogo` → `—` (BOGO has no value)

**Status badge:** Show "Active" (green) if `is_active && now >= start_date && now <= end_date`. Show "Inactive" (gray) otherwise. Show "Scheduled" (blue) if `is_active && now < start_date`. Show "Expired" (red) if `is_active && now > end_date`.

**Filter bar:** `type` filter dropdown (All Types / Percentage / Fixed / BOGO), `is_active` filter (All / Active / Inactive). Apply button.

**Actions:** Edit (Pencil) for admin/manager; Delete (Trash) for admin only with `window.confirm`.

**Create/Edit Modal (`PromotionModal`):**

Fields:
1. **Name** (text, required)
2. **Type** (select: percentage / fixed / bogo)
3. **Value** — label and behavior changes by type:
   - `percentage`: label "Discount (%)", plain number input (0-100), submit as-is
   - `fixed`: label "Discount Amount (৳)", ৳ input, submit `Math.round(value * 100)`
   - `bogo`: hide the value field entirely (submit `value: 0`)
4. **Start Date** (`datetime-local` input)
5. **End Date** (`datetime-local` input)
6. **Minimum Purchase Amount (৳)** (number input, default 0, submit `Math.round(value * 100)`)
7. **Applies To** (select: All Products / Specific Products)
8. **Product IDs** (textarea for comma-separated UUIDs, shown only when `applies_to='specific'`; hint text: "Enter product UUIDs, one per line or comma-separated") — parse on submit: `value.split(/[\n,]+/).map(s => s.trim()).filter(Boolean)`
9. **Is Active** (checkbox)

**Date conversion for form:**
- When populating edit form from existing promotion: convert ISO datetime to `datetime-local` format by taking the first 16 chars: `existing.start_date.slice(0, 16)`
- When submitting: `new Date(values.start_date).toISOString()`

**Payload construction (no `""` for optional fields, correct unit conversion):**
```ts
const payload: PromotionPayload = {
  name: values.name,
  type: values.type,
  value: values.type === 'fixed'
    ? Math.round(values.value * 100)
    : values.type === 'bogo'
    ? 0
    : values.value,  // percentage: plain number
  start_date: new Date(values.start_date).toISOString(),
  end_date: new Date(values.end_date).toISOString(),
  min_purchase_amount: Math.round(values.min_purchase_amount * 100),
  applies_to: values.applies_to,
  is_active: values.is_active,
  product_ids: values.applies_to === 'specific'
    ? productIdsText.split(/[\n,]+/).map(s => s.trim()).filter(Boolean)
    : [],
};
```

**Pagination:** Standard prev/next buttons.

### 5. Wire Up

**`frontend/src/components/layout/AppLayout.tsx`**
- Enable `Promotions` nav item: `enabled: true`

**`frontend/src/router/index.tsx`**
- Import `PromotionsPage`
- Add: `<Route path="promotions" element={<PromotionsPage />} />`

**Update CONTEXT.md** in every directory touched.

## Acceptance Criteria

- [ ] `tsc --noEmit` exits 0 (strict mode, no type errors)
- [ ] `PromotionsPage` renders table with type + status filter bar + pagination
- [ ] Type badges render in correct colors (blue/purple/orange)
- [ ] Status badge shows Active/Inactive/Scheduled/Expired correctly based on `is_active` + date range
- [ ] Value column displays `${value}%` for percentage, `৳x.xx` for fixed, `—` for bogo
- [ ] Create modal: value field hidden for bogo, label changes for percentage vs fixed
- [ ] Edit modal pre-fills all fields from existing promotion
- [ ] Date fields use `datetime-local` input; form converts to ISO on submit
- [ ] `fixed` value submitted as `Math.round(input * 100)` paisa
- [ ] `percentage` value submitted as plain number (no conversion)
- [ ] `min_purchase_amount` submitted as `Math.round(input * 100)` paisa
- [ ] `product_ids` textarea shown only when `applies_to='specific'`
- [ ] Optional fields never sent as `""`; `product_ids=[]` sent when `applies_to='all'`
- [ ] Delete requires `window.confirm`; admin only
- [ ] Promotions nav item enabled in AppLayout
- [ ] CONTEXT.md updated in all touched directories

## Files to Create/Modify

**New:**
- `frontend/src/types/promotion.types.ts`
- `frontend/src/services/promotion.service.ts`
- `frontend/src/hooks/usePromotions.ts`
- `frontend/src/pages/PromotionsPage.tsx`

**Modified:**
- `frontend/src/components/layout/AppLayout.tsx` — enable Promotions nav item
- `frontend/src/router/index.tsx` — add promotions route
- `frontend/src/types/CONTEXT.md`
- `frontend/src/services/CONTEXT.md`
- `frontend/src/hooks/CONTEXT.md`
- `frontend/src/pages/CONTEXT.md`

## Known Pitfalls

1. **`value` unit conversion is type-dependent** — percentage is plain (20 = 20%), fixed is paisa (submit `Math.round(v * 100)`), bogo sends 0. Display in table must also account for this.

2. **`datetime-local` ↔ ISO conversion** — `datetime-local` input yields `"2026-06-01T00:00"`. When submitting: `new Date(values.start_date).toISOString()` converts to UTC ISO. When editing: `existing.start_date.slice(0, 16)` strips the timezone for the input.

3. **product_ids in edit mode** — When editing a promotion with `applies_to='specific'`, pre-populate the textarea with `existing.product_ids.join('\n')`.

4. **Status computation is client-side** — The API returns `is_active` (bool) and date range. The "Active/Inactive/Scheduled/Expired" label is computed in the component:
   ```ts
   const now = new Date();
   const start = new Date(promo.start_date);
   const end = new Date(promo.end_date);
   if (!promo.is_active) return 'Inactive';
   if (now < start) return 'Scheduled';
   if (now > end) return 'Expired';
   return 'Active';
   ```

5. **Zod schema for product_ids** — Keep it as `z.string().optional().default('')` in the form (textarea value). Parse the actual IDs only in `onSubmit`. The Zod schema does NOT need to be a `list[str]` type for the form itself.

6. **Watch `type` field** — Use `useWatch({ control, name: 'type' })` to reactively show/hide the value field and product_ids textarea. Do NOT use uncontrolled logic for this.

## Exit Signal

```bash
cd frontend && npx tsc --noEmit
# Must exit 0 with no type errors
```
