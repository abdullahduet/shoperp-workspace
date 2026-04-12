# Task 0017: Reports + Dashboard Frontend

## Branch: task/0017-reports-frontend

## Context Bundle

### Relevant API Endpoints (already implemented in task/0016)

**Dashboard (admin + manager only):**
- `GET /api/dashboard/summary` → `{ today_sales, today_transactions, month_revenue, month_profit, low_stock_count }` (all in paisa)
- `GET /api/dashboard/trends` → `[{ month: "YYYY-MM", revenue, transaction_count }]` sorted descending

**Reports (admin + manager; low-stock: all roles):**
- `GET /api/reports/sales?start_date&end_date` → `{ period, items: [{ date, total_amount, transaction_count, payment_breakdown }], totals }`
- `GET /api/reports/profit-loss?start_date&end_date` → `{ period, revenue, cogs, gross_profit, expenses, net_profit }`
- `GET /api/reports/top-products?start_date&end_date&limit` → `{ period, items: [{ product_id, name, sku, total_quantity, total_revenue }] }`
- `GET /api/reports/low-stock` → `[{ id, name, sku, stock_quantity, min_stock_level }]`
- `GET /api/reports/purchases?start_date&end_date` → `{ period, items: [{ date, total_amount, order_count }], totals }`
- `GET /api/reports/expenses?start_date&end_date` → `{ period, items: [{ category, total_amount, count }], totals }`
- `GET /api/reports/inventory-valuation` → `{ total_value, product_count, currency, items: [{ product_id, name, sku, stock_quantity, cost_price, value }] }`

**CSV export:** Add `?format=csv` to any report endpoint → returns `text/csv` attachment.

### Existing Frontend Patterns

**Auth/role check:**
```tsx
import { useAuthStore } from '../store/auth.store';
const user = useAuthStore((state) => state.user);
const canViewDashboard = user?.role === 'admin' || user?.role === 'manager';
```

**API client** (`src/api/client.ts`): axios instance with `withCredentials: true`, base URL `/api`. For CSV blob download:
```ts
const res = await apiClient.get('/reports/sales', {
  params: { format: 'csv', start_date: '...' },
  responseType: 'blob',
});
const url = URL.createObjectURL(new Blob([res.data as BlobPart], { type: 'text/csv' }));
const a = document.createElement('a');
a.href = url;
a.download = 'report.csv';
document.body.appendChild(a);
a.click();
document.body.removeChild(a);
URL.revokeObjectURL(url);
```

**TanStack Query v5:** `useQuery({ queryKey, queryFn, enabled })`. Use `enabled` param to conditionally fetch.

**Money display:** `৳${(paisa / 100).toFixed(2)}` — always two decimal places.

**Tailwind patterns from existing pages:** Stat card = `bg-white rounded-lg border border-gray-200 p-4`, table = `min-w-full text-sm` with `bg-gray-50 text-gray-600 uppercase text-xs` header.

**Existing hooks/services pattern** — see `frontend/src/hooks/useAccounting.ts` and `frontend/src/services/accounting.service.ts` for canonical patterns.

**Existing router** (`frontend/src/router/index.tsx`): All protected routes live inside `<Route element={<AppLayout />}>`. Add new routes there.

**AppLayout nav** (`frontend/src/components/layout/AppLayout.tsx`): `NAV_ITEMS` array. Reports item currently: `{ label: 'Reports', icon: BarChart3, to: '/reports', enabled: false }` — change `enabled: false` to `enabled: true`.

### Architecture Rules That Apply

- No charts library to install — use CSS/Tailwind bar chart (proportional divs).
- Money: always paisa internally, display as `৳(value/100).toFixed(2)`.
- Reports are on-demand (triggered by "Run Report" button), NOT fetched on mount.
- Dashboard summary/trends require admin+manager — check role before fetching.
- `tsc --noEmit` must exit 0 (strict TypeScript).

---

## What to Build

### 1. Type definitions — `frontend/src/types/report.types.ts`

```ts
export interface DashboardSummary {
  today_sales: number;
  today_transactions: number;
  month_revenue: number;
  month_profit: number;
  low_stock_count: number;
}

export interface TrendItem {
  month: string; // "YYYY-MM"
  revenue: number;
  transaction_count: number;
}

export interface Period {
  start: string;
  end: string;
}

export interface SalesReportItem {
  date: string;
  total_amount: number;
  transaction_count: number;
  payment_breakdown: { cash: number; card: number; mobile: number; credit: number };
}

export interface SalesReport {
  period: Period;
  items: SalesReportItem[];
  totals: { total_amount: number; transaction_count: number };
}

export interface ProfitLossReport {
  period: Period;
  revenue: number;
  cogs: number;
  gross_profit: number;
  expenses: number;
  net_profit: number;
}

export interface TopProductItem {
  product_id: string;
  name: string;
  sku: string;
  total_quantity: number;
  total_revenue: number;
}

export interface TopProductsReport {
  period: Period;
  items: TopProductItem[];
}

export interface LowStockItem {
  id: string;
  name: string;
  sku: string;
  stock_quantity: number;
  min_stock_level: number;
}

export interface PurchasesReportItem {
  date: string;
  total_amount: number;
  order_count: number;
}

export interface PurchasesReport {
  period: Period;
  items: PurchasesReportItem[];
  totals: { total_amount: number; order_count: number };
}

export interface ExpenseCategoryItem {
  category: string;
  total_amount: number;
  count: number;
}

export interface ExpensesReport {
  period: Period;
  items: ExpenseCategoryItem[];
  totals: { total_amount: number };
}

export interface InventoryValuationItem {
  product_id: string;
  name: string;
  sku: string;
  stock_quantity: number;
  cost_price: number;
  value: number;
}

export interface InventoryValuationReport {
  total_value: number;
  product_count: number;
  currency: string;
  items: InventoryValuationItem[];
}
```

### 2. Service — `frontend/src/services/report.service.ts`

```ts
import apiClient from '../api/client';
import type {
  DashboardSummary,
  TrendItem,
  SalesReport,
  ProfitLossReport,
  TopProductsReport,
  LowStockItem,
  PurchasesReport,
  ExpensesReport,
  InventoryValuationReport,
} from '../types/report.types';

interface DateParams {
  start_date?: string;
  end_date?: string;
}

export const reportService = {
  getDashboardSummary: async (): Promise<DashboardSummary> => {
    const res = await apiClient.get('/dashboard/summary');
    return res.data.data;
  },

  getDashboardTrends: async (): Promise<TrendItem[]> => {
    const res = await apiClient.get('/dashboard/trends');
    return res.data.data;
  },

  getSalesReport: async (params: DateParams): Promise<SalesReport> => {
    const res = await apiClient.get('/reports/sales', { params });
    return res.data.data;
  },

  getProfitLoss: async (params: DateParams): Promise<ProfitLossReport> => {
    const res = await apiClient.get('/reports/profit-loss', { params });
    return res.data.data;
  },

  getTopProducts: async (params: DateParams & { limit?: number }): Promise<TopProductsReport> => {
    const res = await apiClient.get('/reports/top-products', { params });
    return res.data.data;
  },

  getLowStock: async (): Promise<LowStockItem[]> => {
    const res = await apiClient.get('/reports/low-stock');
    return res.data.data;
  },

  getPurchasesReport: async (params: DateParams): Promise<PurchasesReport> => {
    const res = await apiClient.get('/reports/purchases', { params });
    return res.data.data;
  },

  getExpensesReport: async (params: DateParams): Promise<ExpensesReport> => {
    const res = await apiClient.get('/reports/expenses', { params });
    return res.data.data;
  },

  getInventoryValuation: async (): Promise<InventoryValuationReport> => {
    const res = await apiClient.get('/reports/inventory-valuation');
    return res.data.data;
  },

  downloadCsv: async (
    path: string,
    params: Record<string, string | number | undefined>,
  ): Promise<void> => {
    const res = await apiClient.get(path, {
      params: { ...params, format: 'csv' },
      responseType: 'blob',
    });
    const url = URL.createObjectURL(
      new Blob([res.data as BlobPart], { type: 'text/csv' }),
    );
    const a = document.createElement('a');
    a.href = url;
    a.download = `${path.split('/').pop()}-report.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },
};
```

### 3. Hooks — `frontend/src/hooks/useReports.ts`

Only dashboard data is fetched via hooks (auto-fetched on mount when user has access). Reports are fetched imperatively on button click — no hooks needed for those.

```ts
import { useQuery } from '@tanstack/react-query';
import { reportService } from '../services/report.service';

export function useDashboardSummary(enabled: boolean) {
  return useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: () => reportService.getDashboardSummary(),
    enabled,
  });
}

export function useDashboardTrends(enabled: boolean) {
  return useQuery({
    queryKey: ['dashboard-trends'],
    queryFn: () => reportService.getDashboardTrends(),
    enabled,
  });
}
```

### 4. Updated DashboardPage — `frontend/src/pages/DashboardPage.tsx`

Replace the "coming soon" placeholder entirely.

**Layout:**
- For admin/manager: 5 stat cards + 12-month trend bar chart
- For staff: "Welcome to ShopERP" message + shortcut links (no restricted data)

**Stat cards (admin/manager):**
| Card | Value | Color accent |
|------|-------|-------------|
| Today's Sales | ৳ paisa converted | blue |
| Today's Transactions | integer | indigo |
| Month Revenue | ৳ paisa converted | green |
| Month Profit | ৳ paisa converted (green if >0, red if <0) | conditional |
| Low Stock Items | integer count (link to /reports if >0) | yellow if >0 |

**Trend bar chart — CSS bars, no library:**
```tsx
function TrendChart({ trends }: { trends: TrendItem[] }) {
  // trends are sorted descending from API — reverse to show oldest → newest
  const displayed = [...trends].reverse();
  const maxRevenue = Math.max(...displayed.map((t) => t.revenue), 1);

  return (
    <div className="flex items-end gap-1 h-28">
      {displayed.map((t) => (
        <div key={t.month} className="flex flex-col items-center flex-1 min-w-0">
          <div
            className="w-full bg-blue-400 rounded-t hover:bg-blue-500 transition-colors"
            style={{ height: `${Math.max((t.revenue / maxRevenue) * 100, 2)}%` }}
            title={`${t.month}: ৳${(t.revenue / 100).toFixed(2)} (${t.transaction_count} sales)`}
          />
          <span className="text-[9px] text-gray-400 mt-1 truncate w-full text-center">
            {t.month.slice(5)} {/* Extract MM from YYYY-MM */}
          </span>
        </div>
      ))}
    </div>
  );
}
```

**Full DashboardPage structure:**
```tsx
export function DashboardPage() {
  const user = useAuthStore((state) => state.user);
  const canViewStats = user?.role === 'admin' || user?.role === 'manager';

  const { data: summary, isLoading: summaryLoading } = useDashboardSummary(canViewStats);
  const { data: trends, isLoading: trendsLoading } = useDashboardTrends(canViewStats);

  if (!canViewStats) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>
        <p className="text-gray-500">Welcome to ShopERP. Use the navigation to access your modules.</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {/* Stat cards */}
      {summaryLoading ? (
        <div className="text-gray-400 text-sm mb-6">Loading stats…</div>
      ) : summary ? (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5 mb-8">
          <StatCard label="Today's Sales" value={`৳${(summary.today_sales / 100).toFixed(2)}`} color="blue" />
          <StatCard label="Today's Transactions" value={summary.today_transactions.toString()} color="indigo" />
          <StatCard label="Month Revenue" value={`৳${(summary.month_revenue / 100).toFixed(2)}`} color="green" />
          <StatCard
            label="Month Profit"
            value={`৳${(summary.month_profit / 100).toFixed(2)}`}
            color={summary.month_profit >= 0 ? 'green' : 'red'}
          />
          <StatCard
            label="Low Stock Items"
            value={summary.low_stock_count.toString()}
            color={summary.low_stock_count > 0 ? 'yellow' : 'gray'}
          />
        </div>
      ) : null}

      {/* Trend chart */}
      {trendsLoading ? (
        <div className="text-gray-400 text-sm">Loading trends…</div>
      ) : trends && trends.length > 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Monthly Revenue (Last 12 Months)</h2>
          <TrendChart trends={trends} />
        </div>
      ) : null}
    </div>
  );
}
```

**StatCard helper component** (inline in DashboardPage.tsx, not a separate file):
```tsx
const COLOR_MAP: Record<string, string> = {
  blue: 'border-blue-200 text-blue-700',
  indigo: 'border-indigo-200 text-indigo-700',
  green: 'border-green-200 text-green-700',
  red: 'border-red-200 text-red-700',
  yellow: 'border-yellow-200 text-yellow-700',
  gray: 'border-gray-200 text-gray-700',
};

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className={`bg-white rounded-lg border p-4 ${COLOR_MAP[color] ?? COLOR_MAP.gray}`}>
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-xl font-bold font-mono">{value}</p>
    </div>
  );
}
```

### 5. New ReportsPage — `frontend/src/pages/ReportsPage.tsx`

**Report types with metadata:**
```ts
type ReportType =
  | 'sales'
  | 'profit-loss'
  | 'top-products'
  | 'low-stock'
  | 'purchases'
  | 'expenses'
  | 'inventory-valuation';

const REPORT_META: Record<ReportType, { label: string; hasDateRange: boolean }> = {
  sales: { label: 'Sales Report', hasDateRange: true },
  'profit-loss': { label: 'Profit & Loss', hasDateRange: true },
  'top-products': { label: 'Top Products', hasDateRange: true },
  'low-stock': { label: 'Low Stock', hasDateRange: false },
  purchases: { label: 'Purchases', hasDateRange: true },
  expenses: { label: 'Expenses', hasDateRange: true },
  'inventory-valuation': { label: 'Inventory Valuation', hasDateRange: false },
};
```

**Page layout:**
1. Header: "Reports" title
2. Controls row: report type `<select>`, start date input, end date input (hidden when not applicable), "Run Report" button, "Download CSV" button (only visible when report data is loaded)
3. Results area: appropriate table for the selected report type, or "No data" message
4. State: `reportType`, `startDate`, `endDate`, `reportData` (typed as the current report type's return), `loading`, `error`

**Fetch on button click (not on mount):**
```tsx
async function runReport() {
  setLoading(true);
  setError(null);
  setReportData(null);
  try {
    const params: DateParams = {
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    };
    switch (reportType) {
      case 'sales': setReportData(await reportService.getSalesReport(params)); break;
      case 'profit-loss': setReportData(await reportService.getProfitLoss(params)); break;
      case 'top-products': setReportData(await reportService.getTopProducts(params)); break;
      case 'low-stock': setReportData(await reportService.getLowStock()); break;
      case 'purchases': setReportData(await reportService.getPurchasesReport(params)); break;
      case 'expenses': setReportData(await reportService.getExpensesReport(params)); break;
      case 'inventory-valuation': setReportData(await reportService.getInventoryValuation()); break;
    }
  } catch (e) {
    setError(e instanceof Error ? e.message : 'Failed to load report');
  } finally {
    setLoading(false);
  }
}
```

**CSV download:**
```tsx
async function downloadCsv() {
  const params = REPORT_META[reportType].hasDateRange
    ? { start_date: startDate || undefined, end_date: endDate || undefined }
    : {};
  await reportService.downloadCsv(`/reports/${reportType}`, params);
}
```

**Result tables — one per report type.** Use a `renderResults()` helper that returns the correct table based on `reportType` and `reportData`.

**Sales table columns:** Date | Transactions | Total Amount | Cash | Card | Mobile | Credit
**P&L table columns:** Metric | Amount (display in ৳)
**Top Products columns:** Rank | Name | SKU | Qty Sold | Revenue
**Low Stock columns:** Name | SKU | Stock | Min Level | Shortage
**Purchases columns:** Date | Orders | Total Amount
**Expenses columns:** Category | Count | Total Amount
**Inventory Valuation columns:** Name | SKU | Stock Qty | Cost Price | Value; plus summary header row with total_value and product_count

**TypeScript:** `reportData` must be typed. Use a discriminated union or cast inside each render branch. Simplest approach: `reportData: unknown` at state level, cast inside switch in `renderResults()` with `as SalesReport` etc.

**Totals row:** For reports that have `totals`, add a summary footer row or a summary callout above the table.

### 6. Modify `AppLayout.tsx`

Change Reports nav item from `enabled: false` to `enabled: true`:
```ts
{ label: 'Reports', icon: BarChart3, to: '/reports', enabled: true },
```

### 7. Modify `router/index.tsx`

Add import and routes:
```tsx
import { DashboardPage } from '../pages/DashboardPage';   // already imported
import { ReportsPage } from '../pages/ReportsPage';        // new

// Inside protected routes:
<Route index element={<DashboardPage />} />
<Route path="reports" element={<ReportsPage />} />
```

---

## Acceptance Criteria

- [ ] `tsc --noEmit` exits 0 (no TypeScript errors)
- [ ] DashboardPage shows 5 stat cards + trend bar chart for admin/manager
- [ ] DashboardPage shows a non-error welcome message for staff role (no 403 errors reaching the user)
- [ ] Trend bars reflect relative revenue proportions (tallest bar = highest revenue month)
- [ ] ReportsPage at `/reports` — report type selector, date inputs visible only for reports that support date range
- [ ] "Run Report" button fetches and displays a results table
- [ ] "Download CSV" button appears after report runs and triggers file download
- [ ] All 7 report types display correct table columns
- [ ] Money values display as ৳ with 2 decimal places
- [ ] Reports nav link is enabled in sidebar
- [ ] CONTEXT.md updated in all touched directories

---

## Files to Create

- `frontend/src/types/report.types.ts`
- `frontend/src/services/report.service.ts`
- `frontend/src/hooks/useReports.ts`
- `frontend/src/pages/ReportsPage.tsx`

## Files to Modify

- `frontend/src/pages/DashboardPage.tsx` — full rewrite
- `frontend/src/components/layout/AppLayout.tsx` — enable Reports nav
- `frontend/src/router/index.tsx` — add /reports route
- `frontend/src/pages/CONTEXT.md` — add DashboardPage and ReportsPage entries
- `frontend/src/services/CONTEXT.md` — add report.service.ts entry
- `frontend/src/hooks/CONTEXT.md` — add useReports.ts entry
- `frontend/src/types/CONTEXT.md` — add report.types.ts entry

---

## Known Pitfalls

1. **`enabled` param in useQuery** — `useDashboardSummary(false)` must NOT fire the query. Pass `canViewStats` directly. Don't violate React hooks rules by calling hooks conditionally.

2. **`reportData` typing** — `useState<unknown>(null)` is fine. Inside the render switch, cast: `const data = reportData as SalesReport`. TypeScript won't complain inside a narrowed switch branch.

3. **CSV download with blob** — `responseType: 'blob'` on the axios request. The `res.data` will be a `Blob` object, not a string. `new Blob([res.data as BlobPart], { type: 'text/csv' })` works.

4. **Trend chart: reversed order** — API returns trends descending (newest first). Reverse the array before rendering bars left-to-right.

5. **Trend chart: zero revenue** — `maxRevenue = Math.max(...revenues, 1)` prevents divide-by-zero. Use `Math.max((revenue / maxRevenue) * 100, 2)` for `height` to ensure even zero-revenue months have a tiny visible bar.

6. **P&L table** — This is not a list report; it's a single row of metrics. Render it as a two-column key/value table: `["Revenue", "COGS", "Gross Profit", "Expenses", "Net Profit"]` as rows.

7. **Low stock: shortage column** — `shortage = item.min_stock_level - item.stock_quantity`. Color red to signal urgency.

8. **Reports reset on type change** — When `reportType` changes, clear `reportData` and `error` so stale results don't persist. Use a `useEffect` or reset in the type change handler.

---

## Exit Signal

```bash
cd /Users/abdullah/projects/shoperp-workspace/frontend
npx tsc --noEmit
# Must exit 0. Report any type errors.
```
