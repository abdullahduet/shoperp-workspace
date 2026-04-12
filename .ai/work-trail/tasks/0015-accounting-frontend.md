# Task 0015: Accounting Frontend

## Branch: task/0015-accounting-frontend

## Context Bundle

### Relevant API Endpoints

**Prefix: `/api/accounting`**

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | `/api/accounting/accounts` | Yes | admin, manager | All active accounts |
| GET | `/api/accounting/journal-entries` | Yes | admin, manager | Paginated. Params: `page`, `limit`, `start_date`, `end_date`, `reference_type` |
| POST | `/api/accounting/journal-entries` | Yes | admin | Create balanced manual entry |

**Prefix: `/api/expenses`**

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | `/api/expenses` | Yes | admin, manager | Paginated. Params: `page`, `limit`, `start_date`, `end_date`, `category` |
| POST | `/api/expenses` | Yes | admin, manager | Create expense + auto journal entry |
| PUT | `/api/expenses/:id` | Yes | admin, manager | Update expense |
| DELETE | `/api/expenses/:id` | Yes | admin | Soft delete |

**Account response shape:**
```ts
interface Account {
  id: string;
  code: string;
  name: string;
  type: string;   // asset | liability | equity | revenue | expense
  parent_id: string | null;
  is_active: boolean;
  created_at: string;
}
```

**JournalEntry response shape:**
```ts
interface JournalEntryLine {
  id: string;
  account_id: string;
  debit_amount: number;   // paisa
  credit_amount: number;  // paisa
  description: string | null;
}

interface JournalEntry {
  id: string;
  entry_number: string;
  date: string;           // YYYY-MM-DD
  description: string;
  reference_type: string | null;    // 'sale' | 'expense' | 'manual' | 'purchase_order'
  reference_id: string | null;
  created_by: string | null;
  lines: JournalEntryLine[];
  created_at: string;
}
```

**Expense response shape:**
```ts
interface Expense {
  id: string;
  date: string;           // YYYY-MM-DD
  category: string;
  description: string;
  amount: number;         // paisa
  payment_method: string;
  receipt_url: string | null;
  notes: string | null;
  recorded_by: string | null;
  created_at: string;
}
```

**POST /api/accounting/journal-entries request:**
```ts
{
  description: string;
  date?: string;    // YYYY-MM-DD, optional
  lines: Array<{
    account_id: string;
    debit_amount: number;    // paisa
    credit_amount: number;   // paisa
    description?: string;
  }>;
}
```

**POST/PUT /api/expenses request:**
```ts
{
  category: string;
  description: string;
  amount: number;          // paisa — user enters ৳, submit Math.round(input * 100)
  payment_method?: string;
  date?: string;           // YYYY-MM-DD
  notes?: string;
}
```

### Relevant Patterns

**API client:** `import apiClient from '../api/client';`

**Money display:** paisa → ৳: `৳${(value / 100).toFixed(2)}`. Input ৳ → paisa: `Math.round(input * 100)`.

**Role check (positive):**
```tsx
const user = useAuthStore((state) => state.user);
const isAdmin = user?.role === 'admin';
const canManage = user?.role === 'admin' || user?.role === 'manager';
```

**Existing Pagination type:** `import type { Pagination } from '../types/product.types';`

**Reference type badge colors:**
```tsx
const REF_BADGE: Record<string, string> = {
  sale: 'bg-green-100 text-green-700',
  expense: 'bg-red-100 text-red-700',
  purchase_order: 'bg-blue-100 text-blue-700',
  manual: 'bg-gray-100 text-gray-600',
};
```

**Account type badge colors:**
```tsx
const ACCOUNT_TYPE_BADGE: Record<string, string> = {
  asset: 'bg-blue-100 text-blue-700',
  liability: 'bg-red-100 text-red-700',
  equity: 'bg-purple-100 text-purple-700',
  revenue: 'bg-green-100 text-green-700',
  expense: 'bg-orange-100 text-orange-700',
};
```

**Hook pattern (match useSales.ts exactly):**
```ts
export function useAccounts() {
  return useQuery({
    queryKey: ['accounts'],
    queryFn: () => accountingService.listAccounts(),
  });
}
```

**Inline create/edit modal pattern:** Follow SuppliersPage.tsx (same pattern as PromotionsPage) — modal opens over the list, same page, no separate route.

**Inline modal for journal entry creation** — similar pattern but with dynamic line items (useFieldArray).

### Architecture Rules That Apply

- Rule 17: All server state via TanStack Query.
- Rule 18: Forms use React Hook Form + Zod.
- Rule 19: Pages handle loading skeleton, error, empty state.
- Rule 20: No direct API calls from components.
- Optional fields sent as `undefined` not `""`.
- Role checks: positive pattern only.

## What to Build

### 1. Types — `frontend/src/types/accounting.types.ts`

```ts
export interface Account {
  id: string;
  code: string;
  name: string;
  type: string;
  parent_id: string | null;
  is_active: boolean;
  created_at: string;
}

export interface JournalEntryLine {
  id: string;
  account_id: string;
  debit_amount: number;
  credit_amount: number;
  description: string | null;
}

export interface JournalEntry {
  id: string;
  entry_number: string;
  date: string;
  description: string;
  reference_type: string | null;
  reference_id: string | null;
  created_by: string | null;
  lines: JournalEntryLine[];
  created_at: string;
}

export interface Expense {
  id: string;
  date: string;
  category: string;
  description: string;
  amount: number;
  payment_method: string;
  receipt_url: string | null;
  notes: string | null;
  recorded_by: string | null;
  created_at: string;
}

export interface JournalEntryLineFormValues {
  account_id: string;
  debit_amount: number;
  credit_amount: number;
  description: string;
}

export interface JournalEntryPayload {
  description: string;
  date?: string;
  lines: Array<{
    account_id: string;
    debit_amount: number;
    credit_amount: number;
    description?: string;
  }>;
}

export interface ExpensePayload {
  category: string;
  description: string;
  amount: number;    // paisa
  payment_method?: string;
  date?: string;
  notes?: string;
}
```

### 2. Service — `frontend/src/services/accounting.service.ts`

```ts
import apiClient from '../api/client';
import type { Account, JournalEntry, Expense, JournalEntryPayload, ExpensePayload } from '../types/accounting.types';
import type { Pagination } from '../types/product.types';

export const accountingService = {
  listAccounts: async (): Promise<Account[]> => {
    const res = await apiClient.get('/accounting/accounts');
    return res.data.data;
  },

  listJournalEntries: async (params: {
    page?: number;
    limit?: number;
    start_date?: string;
    end_date?: string;
    reference_type?: string;
  }): Promise<{ data: JournalEntry[]; pagination: Pagination }> => {
    const res = await apiClient.get('/accounting/journal-entries', { params });
    return { data: res.data.data, pagination: res.data.pagination };
  },

  createJournalEntry: async (data: JournalEntryPayload): Promise<JournalEntry> => {
    const res = await apiClient.post('/accounting/journal-entries', data);
    return res.data.data;
  },

  listExpenses: async (params: {
    page?: number;
    limit?: number;
    start_date?: string;
    end_date?: string;
    category?: string;
  }): Promise<{ data: Expense[]; pagination: Pagination }> => {
    const res = await apiClient.get('/expenses', { params });
    return { data: res.data.data, pagination: res.data.pagination };
  },

  createExpense: async (data: ExpensePayload): Promise<Expense> => {
    const res = await apiClient.post('/expenses', data);
    return res.data.data;
  },

  updateExpense: async (id: string, data: Partial<ExpensePayload>): Promise<Expense> => {
    const res = await apiClient.put(`/expenses/${id}`, data);
    return res.data.data;
  },

  deleteExpense: async (id: string): Promise<void> => {
    await apiClient.delete(`/expenses/${id}`);
  },
};
```

### 3. Hooks — `frontend/src/hooks/useAccounting.ts`

```ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { accountingService } from '../services/accounting.service';
import type { JournalEntryPayload, ExpensePayload } from '../types/accounting.types';

export function useAccounts() {
  return useQuery({
    queryKey: ['accounts'],
    queryFn: () => accountingService.listAccounts(),
  });
}

export function useJournalEntries(filters: Record<string, unknown> = {}) {
  return useQuery({
    queryKey: ['journal-entries', filters],
    queryFn: () => accountingService.listJournalEntries(filters),
  });
}

export function useCreateJournalEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: JournalEntryPayload) => accountingService.createJournalEntry(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journal-entries'] });
    },
  });
}

export function useExpenses(filters: Record<string, unknown> = {}) {
  return useQuery({
    queryKey: ['expenses', filters],
    queryFn: () => accountingService.listExpenses(filters),
  });
}

export function useCreateExpense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ExpensePayload) => accountingService.createExpense(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] });
    },
  });
}

export function useUpdateExpense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ExpensePayload> }) =>
      accountingService.updateExpense(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] });
    },
  });
}

export function useDeleteExpense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => accountingService.deleteExpense(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] });
    },
  });
}
```

### 4. Pages

#### `frontend/src/pages/AccountsPage.tsx`

**Read-only chart of accounts.** No create/edit (accounts are seeded, not user-managed).

**Page layout:**
- Header: "Chart of Accounts"
- Table columns: Code, Name, Type (badge), Parent (code if parentId not null, else "—"), Active (yes/no)
- Grouped by account type in the table (assets first, then liabilities, equity, revenue, expense) — just sort by `code` which achieves this naturally since codes are 1000s, 2000s, etc.
- No filters needed (small dataset, all shown at once — no pagination)

**Account type badges:** (blue/red/purple/green/orange per the Relevant Patterns section)

Loading skeleton, error display, empty state ("No accounts found.").

This page is admin/manager only — but since the nav will link here and the route is protected by the backend (403 for staff), just render normally. Staff will get a 403 from the API and the error state will handle it.

#### `frontend/src/pages/JournalEntriesPage.tsx`

**List + inline create modal (admin only creates).**

**Filter bar:** start_date (date input), end_date (date input), reference_type (select: All / Sale / Expense / Purchase Order / Manual), Apply button.

**Table columns:** Entry #, Date, Description, Reference Type (badge), Lines count (e.g. "2 lines"), Created, Actions.

**Actions:** No actions except the "New Entry" button in the header for admins.

**"New Entry" button:** Shown only to admins (`isAdmin`). Opens the create modal.

**Create Modal (admin only) — `JournalEntryModal`:**

Fields:
1. **Description** (text, required)
2. **Date** (date input `type="date"`, optional — leave blank for today)
3. **Lines section (useFieldArray)** — dynamic rows, minimum 2:
   - **Account** (select dropdown from `useAccounts()` data — show `code — name` as option text)
   - **Debit (৳)** (number input, default 0)
   - **Credit (৳)** (number input, default 0)
   - **Note** (text input, optional)
   - Remove button (disabled when only 2 rows)

4. **Running balance display:** `Debit Total: ৳X.XX | Credit Total: ৳X.XX` — shown below the lines. If they match, show green "✓ Balanced". If not, show red "✗ Unbalanced".

5. **"+ Add Line" button.**

**Zod schema:**
```ts
const lineSchema = z.object({
  account_id: z.string().min(1, 'Select an account'),
  debit_amount: z.number().min(0).default(0),
  credit_amount: z.number().min(0).default(0),
  description: z.string().optional().default(''),
});

const journalEntrySchema = z.object({
  description: z.string().min(1, 'Description required'),
  date: z.string().optional().default(''),
  lines: z.array(lineSchema).min(2, 'At least 2 lines required'),
});
```

**Payload construction:**
```ts
const payload: JournalEntryPayload = {
  description: values.description,
  date: values.date || undefined,
  lines: values.lines.map((line) => ({
    account_id: line.account_id,
    debit_amount: Math.round(line.debit_amount * 100),   // ৳ → paisa
    credit_amount: Math.round(line.credit_amount * 100), // ৳ → paisa
    description: line.description || undefined,
  })),
};
```

**Balance display (computed from watchedLines):**
```tsx
const watchedLines = useWatch({ control, name: 'lines' });
const totalDebit = (watchedLines ?? []).reduce((s, l) => s + (Number(l.debit_amount) || 0), 0);
const totalCredit = (watchedLines ?? []).reduce((s, l) => s + (Number(l.credit_amount) || 0), 0);
const isBalanced = totalDebit > 0 && totalDebit === totalCredit;
```

**Pagination:** Standard prev/next.

#### `frontend/src/pages/ExpensesPage.tsx`

**List + inline create/edit modal.** Same pattern as SuppliersPage.

**Filter bar:** start_date (date), end_date (date), category (text input for partial match), Apply button.

**Table columns:** Date, Category, Description, Amount (৳), Payment Method (badge), Actions.

**Payment method badge colors** (same as sales):
- `cash` → `bg-green-100 text-green-700`
- `card` → `bg-blue-100 text-blue-700`
- `mobile` → `bg-purple-100 text-purple-700`
- `credit` → `bg-orange-100 text-orange-700`

**Actions:**
- Edit (pencil icon) — admin/manager
- Delete (trash icon) — admin only with `window.confirm`

**"Record Expense" button:** admin/manager.

**Create/Edit Modal (`ExpenseModal`):**

Fields:
1. **Category** (text input, required — e.g., "Rent", "Utilities", "Salary")
2. **Description** (text input, required)
3. **Amount (৳)** (number input, required — user enters ৳, submit `Math.round(value * 100)`)
4. **Payment Method** (select: Cash / Card / Mobile / Credit, default Cash)
5. **Date** (date input `type="date"`, optional — leave blank for today)
6. **Notes** (textarea, optional)

**Zod schema:**
```ts
const expenseSchema = z.object({
  category: z.string().min(1, 'Category required'),
  description: z.string().min(1, 'Description required'),
  amount: z.number({ invalid_type_error: 'Enter a valid amount' }).positive('Must be greater than 0'),
  payment_method: z.enum(['cash', 'card', 'mobile', 'credit']).default('cash'),
  date: z.string().optional().default(''),
  notes: z.string().optional().default(''),
});
```

**Edit pre-fill:**
```ts
reset({
  category: editing.category,
  description: editing.description,
  amount: editing.amount / 100,    // paisa → ৳ for display
  payment_method: editing.payment_method as 'cash' | 'card' | 'mobile' | 'credit',
  date: editing.date,              // already YYYY-MM-DD
  notes: editing.notes ?? '',
});
```

**Payload construction:**
```ts
const payload: ExpensePayload = {
  category: values.category,
  description: values.description,
  amount: Math.round(values.amount * 100),  // ৳ → paisa
  payment_method: values.payment_method,
  date: values.date || undefined,
  notes: values.notes || undefined,
};
```

**Pagination:** Standard prev/next.

### 5. Wire Up

**`frontend/src/components/layout/AppLayout.tsx`**
- Enable `Accounting` nav item: `enabled: false` → `enabled: true`

**`frontend/src/router/index.tsx`**
- Import AccountsPage, JournalEntriesPage, ExpensesPage
- Add routes:
  ```tsx
  <Route path="accounting/accounts" element={<AccountsPage />} />
  <Route path="accounting/journal-entries" element={<JournalEntriesPage />} />
  <Route path="expenses" element={<ExpensesPage />} />
  ```

Note: The `Accounting` nav link in AppLayout points to `/accounting` — update it to point to `/accounting/accounts` or `/accounting/journal-entries`. Either is fine; use `/accounting/accounts` as the landing page.

**Update CONTEXT.md** in every directory touched.

## Acceptance Criteria

- [ ] `tsc --noEmit` exits 0 (strict mode, no type errors)
- [ ] `AccountsPage` renders table with code, name, type badge, no pagination (small dataset)
- [ ] Account type badges in correct colors (blue/red/purple/green/orange)
- [ ] `JournalEntriesPage` renders paginated list with reference type filter
- [ ] Reference type badges (green/red/blue/gray)
- [ ] "New Entry" button visible only to admin
- [ ] Create modal has dynamic line rows via `useFieldArray`, minimum 2 rows
- [ ] Running debit/credit totals displayed with balanced/unbalanced indicator
- [ ] Line amounts (৳) converted to paisa on submit (`Math.round(x * 100)`)
- [ ] `ExpensesPage` renders paginated list with date/category filters
- [ ] Create/edit expense modal with all fields
- [ ] `amount` submitted as `Math.round(input * 100)` paisa; edit pre-fills as ৳
- [ ] Delete requires `window.confirm`, admin only
- [ ] Optional fields sent as `undefined` not `""`
- [ ] Accounting nav item enabled, pointing to `/accounting/accounts`
- [ ] CONTEXT.md updated in all touched directories

## Files to Create/Modify

**New:**
- `frontend/src/types/accounting.types.ts`
- `frontend/src/services/accounting.service.ts`
- `frontend/src/hooks/useAccounting.ts`
- `frontend/src/pages/AccountsPage.tsx`
- `frontend/src/pages/JournalEntriesPage.tsx`
- `frontend/src/pages/ExpensesPage.tsx`

**Modified:**
- `frontend/src/components/layout/AppLayout.tsx` — enable Accounting nav, update `to` to `/accounting/accounts`
- `frontend/src/router/index.tsx` — add 3 routes
- `frontend/src/types/CONTEXT.md`
- `frontend/src/services/CONTEXT.md`
- `frontend/src/hooks/CONTEXT.md`
- `frontend/src/pages/CONTEXT.md`

## Known Pitfalls

1. **Account select in journal entry modal** — use `useAccounts()` hook to populate a `<select>` dropdown. Show `{account.code} — {account.name}` as option text, `account.id` as value. Load accounts once in the parent page, pass as prop to modal, or use the hook inside the modal.

2. **Balance indicator** — use `useWatch` (not `getValues`) for reactive updates. Only mark as balanced if `totalDebit > 0 && totalDebit === totalCredit`.

3. **Remove line button** — disabled when `fields.length <= 2` (minimum 2 lines for a valid journal entry).

4. **Accounting nav item `to` field** — the AppLayout currently has `to: '/accounting'` for the Accounting item. Update to `to: '/accounting/accounts'` so it navigates to a real page. Also add the route `accounting` → redirect or alias to `accounting/accounts`.

   Actually, simplest: just change `to: '/accounting'` to `to: '/accounting/accounts'` in AppLayout. No redirect needed.

5. **JournalEntriesPage — account name in lines** — When displaying a journal entry's lines in the table, you only have `account_id` (UUID). To show the account name/code alongside, you'd need to cross-reference the accounts list. For simplicity: in the list table just show the count of lines (e.g. "2 lines"). In a future detail page, you could show account names. This is sufficient for Phase 7.

6. **ExpensePage edit pre-fill for date** — `editing.date` is already in `YYYY-MM-DD` format from the API (backend serializes with `.strftime("%Y-%m-%d")`). Directly assign to the form field.

7. **`window.confirm` for delete** — call before mutation: `if (!window.confirm('Delete this expense?')) return;`

8. **Category filter in expense list** — send as query param `category` to the API. The backend does case-insensitive contains matching. Clear the filter on Apply if the input is empty.

## Exit Signal

```bash
cd frontend && npx tsc --noEmit
# Must exit 0 with no type errors
```
