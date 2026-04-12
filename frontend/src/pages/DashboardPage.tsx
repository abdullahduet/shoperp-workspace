import { useAuthStore } from '../store/auth.store';
import { useDashboardSummary, useDashboardTrends } from '../hooks/useReports';
import type { TrendItem } from '../types/report.types';

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

function TrendChart({ trends }: { trends: TrendItem[] }) {
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
            {t.month.slice(5)}
          </span>
        </div>
      ))}
    </div>
  );
}

export function DashboardPage() {
  const user = useAuthStore((state) => state.user);
  const canViewStats = user?.role === 'admin' || user?.role === 'manager';

  const { data: summary, isLoading: summaryLoading } = useDashboardSummary(canViewStats);
  const { data: trends, isLoading: trendsLoading } = useDashboardTrends(canViewStats);

  if (!canViewStats) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Dashboard</h1>
        <p className="text-gray-500">Welcome to ShopERP. Use the navigation to access your modules.</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {summaryLoading ? (
        <div className="text-gray-400 text-sm mb-6">Loading stats…</div>
      ) : summary ? (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5 mb-8">
          <StatCard
            label="Today's Sales"
            value={`৳${(summary.today_sales / 100).toFixed(2)}`}
            color="blue"
          />
          <StatCard
            label="Today's Transactions"
            value={summary.today_transactions.toString()}
            color="indigo"
          />
          <StatCard
            label="Month Revenue"
            value={`৳${(summary.month_revenue / 100).toFixed(2)}`}
            color="green"
          />
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

      {trendsLoading ? (
        <div className="text-gray-400 text-sm">Loading trends…</div>
      ) : trends && trends.length > 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">
            Monthly Revenue (Last 12 Months)
          </h2>
          <TrendChart trends={trends} />
        </div>
      ) : null}
    </div>
  );
}
