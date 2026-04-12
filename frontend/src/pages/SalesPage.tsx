import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, Plus } from 'lucide-react';
import { useSales, useDailySummary } from '../hooks/useSales';
import { useAuthStore } from '../store/auth.store';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ErrorDisplay } from '../components/ui/ErrorDisplay';

const PAYMENT_BADGE: Record<string, string> = {
  cash: 'bg-green-100 text-green-700',
  card: 'bg-blue-100 text-blue-700',
  mobile: 'bg-purple-100 text-purple-700',
  credit: 'bg-orange-100 text-orange-700',
};

export function SalesPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('');
  const [appliedStartDate, setAppliedStartDate] = useState('');
  const [appliedEndDate, setAppliedEndDate] = useState('');
  const [appliedPaymentMethod, setAppliedPaymentMethod] = useState('');

  const user = useAuthStore((state) => state.user);
  const canViewSummary = user?.role === 'admin' || user?.role === 'manager';

  const { data, isLoading, isError, error } = useSales({
    page,
    limit: 20,
    start_date: appliedStartDate || undefined,
    end_date: appliedEndDate || undefined,
    payment_method: appliedPaymentMethod || undefined,
  });

  const { data: summary, isLoading: summaryLoading } = useDailySummary(canViewSummary);

  function applyFilters() {
    setPage(1);
    setAppliedStartDate(startDate);
    setAppliedEndDate(endDate);
    setAppliedPaymentMethod(paymentMethod);
  }

  function resetFilters() {
    setStartDate('');
    setEndDate('');
    setPaymentMethod('');
    setPage(1);
    setAppliedStartDate('');
    setAppliedEndDate('');
    setAppliedPaymentMethod('');
  }

  if (isLoading) return <LoadingSkeleton />;
  if (isError)
    return (
      <ErrorDisplay
        message={error instanceof Error ? error.message : 'Failed to load sales'}
      />
    );

  const sales = data?.data ?? [];
  const pagination = data?.pagination;

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Sales</h1>
        <button
          onClick={() => navigate('/sales/new')}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
        >
          <Plus size={16} />
          Record Sale
        </button>
      </div>

      {/* Daily Summary Panel — admin/manager only */}
      {canViewSummary && summary && !summaryLoading && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-gray-600 uppercase mb-3">Today's Summary</h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6 mb-2">
            {/* Today's Revenue */}
            <div className="col-span-2 sm:col-span-1 lg:col-span-2 bg-white rounded-lg border border-gray-200 p-4">
              <p className="text-xs text-gray-500 mb-1">Today's Revenue</p>
              <p className="text-xl font-bold text-gray-900 font-mono">
                ৳{(summary.total_sales / 100).toFixed(2)}
              </p>
            </div>
            {/* Transactions */}
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <p className="text-xs text-gray-500 mb-1">Transactions</p>
              <p className="text-xl font-bold text-gray-900">{summary.transaction_count}</p>
            </div>
            {/* Payment breakdown */}
            <div className="bg-white rounded-lg border border-green-200 p-4">
              <p className="text-xs text-gray-500 mb-1">Cash</p>
              <p className="text-base font-semibold text-green-700 font-mono">
                ৳{(summary.payment_breakdown.cash / 100).toFixed(2)}
              </p>
            </div>
            <div className="bg-white rounded-lg border border-blue-200 p-4">
              <p className="text-xs text-gray-500 mb-1">Card</p>
              <p className="text-base font-semibold text-blue-700 font-mono">
                ৳{(summary.payment_breakdown.card / 100).toFixed(2)}
              </p>
            </div>
            <div className="bg-white rounded-lg border border-purple-200 p-4">
              <p className="text-xs text-gray-500 mb-1">Mobile</p>
              <p className="text-base font-semibold text-purple-700 font-mono">
                ৳{(summary.payment_breakdown.mobile / 100).toFixed(2)}
              </p>
            </div>
            <div className="bg-white rounded-lg border border-orange-200 p-4">
              <p className="text-xs text-gray-500 mb-1">Credit</p>
              <p className="text-base font-semibold text-orange-700 font-mono">
                ৳{(summary.payment_breakdown.credit / 100).toFixed(2)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <input
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
          placeholder="Start date"
        />
        <input
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
          placeholder="End date"
        />
        <select
          value={paymentMethod}
          onChange={(e) => setPaymentMethod(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
        >
          <option value="">All Payment Methods</option>
          <option value="cash">Cash</option>
          <option value="card">Card</option>
          <option value="mobile">Mobile</option>
          <option value="credit">Credit</option>
        </select>
        <button
          onClick={applyFilters}
          className="px-3 py-1.5 bg-gray-800 text-white rounded text-sm"
        >
          Apply
        </button>
        <button
          onClick={resetFilters}
          className="px-3 py-1.5 border border-gray-300 rounded text-sm text-gray-600"
        >
          Reset
        </button>
      </div>

      {/* Table */}
      {sales.length === 0 ? (
        <p className="text-gray-500 py-12 text-center">No sales found.</p>
      ) : (
        <div className="overflow-x-auto rounded border border-gray-200">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
              <tr>
                {['Sale #', 'Date', 'Customer', 'Payment Method', 'Subtotal', 'Discount', 'Total', 'Actions'].map(
                  (h) => (
                    <th key={h} className="px-4 py-3 text-left font-medium">
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sales.map((sale) => (
                <tr key={sale.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-gray-900 font-medium">
                    {sale.sale_number}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {new Date(sale.sale_date).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-gray-700">{sale.customer_name ?? 'Walk-in'}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        PAYMENT_BADGE[sale.payment_method] ?? 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {sale.payment_method}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-gray-700">
                    ৳{(sale.subtotal / 100).toFixed(2)}
                  </td>
                  <td className="px-4 py-3 font-mono text-gray-700">
                    ৳{(sale.discount_amount / 100).toFixed(2)}
                  </td>
                  <td className="px-4 py-3 font-mono text-gray-900 font-semibold">
                    ৳{(sale.total_amount / 100).toFixed(2)}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => navigate(`/sales/${sale.id}`)}
                      className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded"
                      title="View"
                    >
                      <Eye size={15} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {pagination && pagination.total_pages > 1 && (
        <div className="flex items-center justify-between mt-4 text-sm text-gray-600">
          <span>
            Page {pagination.page} of {pagination.total_pages} ({pagination.total} total)
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1 border rounded disabled:opacity-40"
            >
              Prev
            </button>
            <button
              onClick={() => setPage((p) => Math.min(pagination.total_pages, p + 1))}
              disabled={page >= pagination.total_pages}
              className="px-3 py-1 border rounded disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
