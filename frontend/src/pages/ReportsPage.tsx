import { useState, useEffect } from 'react';
import { Download, Play } from 'lucide-react';
import { reportService } from '../services/report.service';
import type {
  SalesReport,
  ProfitLossReport,
  TopProductsReport,
  LowStockItem,
  PurchasesReport,
  ExpensesReport,
  InventoryValuationReport,
} from '../types/report.types';

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

interface DateParams {
  start_date?: string;
  end_date?: string;
}

export function ReportsPage() {
  const [reportType, setReportType] = useState<ReportType>('sales');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [reportData, setReportData] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Clear results when report type changes
  useEffect(() => {
    setReportData(null);
    setError(null);
  }, [reportType]);

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
        case 'sales':
          setReportData(await reportService.getSalesReport(params));
          break;
        case 'profit-loss':
          setReportData(await reportService.getProfitLoss(params));
          break;
        case 'top-products':
          setReportData(await reportService.getTopProducts(params));
          break;
        case 'low-stock':
          setReportData(await reportService.getLowStock());
          break;
        case 'purchases':
          setReportData(await reportService.getPurchasesReport(params));
          break;
        case 'expenses':
          setReportData(await reportService.getExpensesReport(params));
          break;
        case 'inventory-valuation':
          setReportData(await reportService.getInventoryValuation());
          break;
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load report');
    } finally {
      setLoading(false);
    }
  }

  async function downloadCsv() {
    const params: Record<string, string | undefined> = REPORT_META[reportType].hasDateRange
      ? { start_date: startDate || undefined, end_date: endDate || undefined }
      : {};
    await reportService.downloadCsv(`/reports/${reportType}`, params);
  }

  function renderResults() {
    if (!reportData) return null;

    switch (reportType) {
      case 'sales': {
        const data = reportData as SalesReport;
        return (
          <div>
            <p className="text-sm text-gray-500 mb-3">
              Period: {data.period.start} → {data.period.end} |{' '}
              Total: ৳{(data.totals.total_amount / 100).toFixed(2)} |{' '}
              Transactions: {data.totals.transaction_count}
            </p>
            <div className="overflow-x-auto rounded border border-gray-200">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
                  <tr>
                    {['Date', 'Transactions', 'Total', 'Cash', 'Card', 'Mobile', 'Credit'].map((h) => (
                      <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.items.map((item) => (
                    <tr key={item.date} className="hover:bg-gray-50">
                      <td className="px-4 py-3">{item.date}</td>
                      <td className="px-4 py-3">{item.transaction_count}</td>
                      <td className="px-4 py-3 font-mono">৳{(item.total_amount / 100).toFixed(2)}</td>
                      <td className="px-4 py-3 font-mono">৳{(item.payment_breakdown.cash / 100).toFixed(2)}</td>
                      <td className="px-4 py-3 font-mono">৳{(item.payment_breakdown.card / 100).toFixed(2)}</td>
                      <td className="px-4 py-3 font-mono">৳{(item.payment_breakdown.mobile / 100).toFixed(2)}</td>
                      <td className="px-4 py-3 font-mono">৳{(item.payment_breakdown.credit / 100).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {data.items.length === 0 && (
              <p className="text-gray-500 py-8 text-center">No sales in this period.</p>
            )}
          </div>
        );
      }

      case 'profit-loss': {
        const data = reportData as ProfitLossReport;
        const rows: [string, number][] = [
          ['Revenue', data.revenue],
          ['Cost of Goods Sold (COGS)', data.cogs],
          ['Gross Profit', data.gross_profit],
          ['Expenses', data.expenses],
          ['Net Profit', data.net_profit],
        ];
        return (
          <div>
            <p className="text-sm text-gray-500 mb-3">Period: {data.period.start} → {data.period.end}</p>
            <div className="overflow-x-auto rounded border border-gray-200 max-w-md">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium">Metric</th>
                    <th className="px-4 py-3 text-right font-medium">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {rows.map(([label, value]) => (
                    <tr key={label} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium">{label}</td>
                      <td className={`px-4 py-3 text-right font-mono font-semibold ${value < 0 ? 'text-red-600' : 'text-gray-900'}`}>
                        ৳{(value / 100).toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );
      }

      case 'top-products': {
        const data = reportData as TopProductsReport;
        return (
          <div>
            <p className="text-sm text-gray-500 mb-3">Period: {data.period.start} → {data.period.end}</p>
            <div className="overflow-x-auto rounded border border-gray-200">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
                  <tr>
                    {['Rank', 'Name', 'SKU', 'Qty Sold', 'Revenue'].map((h) => (
                      <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.items.map((item, idx) => (
                    <tr key={item.product_id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-gray-500">{idx + 1}</td>
                      <td className="px-4 py-3 font-medium">{item.name}</td>
                      <td className="px-4 py-3 font-mono text-gray-600">{item.sku}</td>
                      <td className="px-4 py-3">{item.total_quantity}</td>
                      <td className="px-4 py-3 font-mono">৳{(item.total_revenue / 100).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {data.items.length === 0 && (
              <p className="text-gray-500 py-8 text-center">No sales in this period.</p>
            )}
          </div>
        );
      }

      case 'low-stock': {
        const data = reportData as LowStockItem[];
        return (
          <div>
            <div className="overflow-x-auto rounded border border-gray-200">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
                  <tr>
                    {['Name', 'SKU', 'Stock', 'Min Level', 'Shortage'].map((h) => (
                      <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium">{item.name}</td>
                      <td className="px-4 py-3 font-mono text-gray-600">{item.sku}</td>
                      <td className="px-4 py-3 text-red-600 font-semibold">{item.stock_quantity}</td>
                      <td className="px-4 py-3">{item.min_stock_level}</td>
                      <td className="px-4 py-3 text-red-600 font-semibold">
                        {item.min_stock_level - item.stock_quantity}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {data.length === 0 && (
              <p className="text-green-600 py-8 text-center">All products are adequately stocked.</p>
            )}
          </div>
        );
      }

      case 'purchases': {
        const data = reportData as PurchasesReport;
        return (
          <div>
            <p className="text-sm text-gray-500 mb-3">
              Period: {data.period.start} → {data.period.end} |{' '}
              Total: ৳{(data.totals.total_amount / 100).toFixed(2)} |{' '}
              Orders: {data.totals.order_count}
            </p>
            <div className="overflow-x-auto rounded border border-gray-200">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
                  <tr>
                    {['Date', 'Orders', 'Total Amount'].map((h) => (
                      <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.items.map((item) => (
                    <tr key={item.date} className="hover:bg-gray-50">
                      <td className="px-4 py-3">{item.date}</td>
                      <td className="px-4 py-3">{item.order_count}</td>
                      <td className="px-4 py-3 font-mono">৳{(item.total_amount / 100).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {data.items.length === 0 && (
              <p className="text-gray-500 py-8 text-center">No purchases in this period.</p>
            )}
          </div>
        );
      }

      case 'expenses': {
        const data = reportData as ExpensesReport;
        return (
          <div>
            <p className="text-sm text-gray-500 mb-3">
              Period: {data.period.start} → {data.period.end} |{' '}
              Total: ৳{(data.totals.total_amount / 100).toFixed(2)}
            </p>
            <div className="overflow-x-auto rounded border border-gray-200">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
                  <tr>
                    {['Category', 'Count', 'Total Amount'].map((h) => (
                      <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.items.map((item) => (
                    <tr key={item.category} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium">{item.category}</td>
                      <td className="px-4 py-3">{item.count}</td>
                      <td className="px-4 py-3 font-mono">৳{(item.total_amount / 100).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {data.items.length === 0 && (
              <p className="text-gray-500 py-8 text-center">No expenses in this period.</p>
            )}
          </div>
        );
      }

      case 'inventory-valuation': {
        const data = reportData as InventoryValuationReport;
        return (
          <div>
            <div className="flex gap-6 mb-4 text-sm text-gray-700">
              <span>Total Value: <span className="font-semibold font-mono">৳{(data.total_value / 100).toFixed(2)}</span></span>
              <span>Products: <span className="font-semibold">{data.product_count}</span></span>
              <span>Currency: <span className="font-semibold">{data.currency}</span></span>
            </div>
            <div className="overflow-x-auto rounded border border-gray-200">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
                  <tr>
                    {['Name', 'SKU', 'Stock Qty', 'Cost Price', 'Value'].map((h) => (
                      <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.items.map((item) => (
                    <tr key={item.product_id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium">{item.name}</td>
                      <td className="px-4 py-3 font-mono text-gray-600">{item.sku}</td>
                      <td className="px-4 py-3">{item.stock_quantity}</td>
                      <td className="px-4 py-3 font-mono">৳{(item.cost_price / 100).toFixed(2)}</td>
                      <td className="px-4 py-3 font-mono font-semibold">৳{(item.value / 100).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {data.items.length === 0 && (
              <p className="text-gray-500 py-8 text-center">No inventory data.</p>
            )}
          </div>
        );
      }

      default:
        return null;
    }
  }

  const meta = REPORT_META[reportType];

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Reports</h1>

      {/* Controls */}
      <div className="flex flex-wrap gap-3 mb-6 items-end">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Report Type</label>
          <select
            value={reportType}
            onChange={(e) => setReportType(e.target.value as ReportType)}
            className="border border-gray-300 rounded px-3 py-1.5 text-sm"
          >
            {(Object.keys(REPORT_META) as ReportType[]).map((type) => (
              <option key={type} value={type}>
                {REPORT_META[type].label}
              </option>
            ))}
          </select>
        </div>

        {meta.hasDateRange && (
          <>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Start Date</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="border border-gray-300 rounded px-3 py-1.5 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">End Date</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="border border-gray-300 rounded px-3 py-1.5 text-sm"
              />
            </div>
          </>
        )}

        <button
          onClick={runReport}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-1.5 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 disabled:opacity-50"
        >
          <Play size={14} />
          {loading ? 'Loading…' : 'Run Report'}
        </button>

        {reportData !== null && (
          <button
            onClick={downloadCsv}
            className="flex items-center gap-2 px-4 py-1.5 border border-gray-300 text-gray-700 text-sm rounded hover:bg-gray-50"
          >
            <Download size={14} />
            Download CSV
          </button>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Results */}
      {renderResults()}
    </div>
  );
}
