import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useSale } from '../hooks/useSales';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ErrorDisplay } from '../components/ui/ErrorDisplay';

const PAYMENT_BADGE: Record<string, string> = {
  cash: 'bg-green-100 text-green-700',
  card: 'bg-blue-100 text-blue-700',
  mobile: 'bg-purple-100 text-purple-700',
  credit: 'bg-orange-100 text-orange-700',
};

export function SaleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: sale, isLoading, isError, error } = useSale(id);

  if (isLoading) return <LoadingSkeleton />;
  if (isError || !sale)
    return (
      <ErrorDisplay
        message={error instanceof Error ? error.message : 'Failed to load sale'}
      />
    );

  return (
    <div>
      {/* Back */}
      <button
        onClick={() => navigate('/sales')}
        className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft size={16} />
        Back to Sales
      </button>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 font-mono">{sale.sale_number}</h1>
          <p className="text-gray-500 text-sm mt-1">
            {new Date(sale.sale_date).toLocaleString()} &mdash;{' '}
            {sale.customer_name ?? 'Walk-in'}
          </p>
        </div>
        <span
          className={`px-3 py-1 rounded text-sm font-medium ${
            PAYMENT_BADGE[sale.payment_method] ?? 'bg-gray-100 text-gray-700'
          }`}
        >
          {sale.payment_method}
        </span>
      </div>

      {/* Promotion banner */}
      {sale.promotion_id !== null && (
        <div className="mb-6 rounded-md bg-green-50 border border-green-200 px-4 py-3 flex items-center gap-2">
          <span className="text-green-700 text-sm font-medium">
            Promotion applied — discount: ৳{(sale.discount_amount / 100).toFixed(2)}
          </span>
        </div>
      )}

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 mb-6">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-xs text-gray-500 mb-1">Subtotal</p>
          <p className="text-lg font-semibold text-gray-900 font-mono">
            ৳{(sale.subtotal / 100).toFixed(2)}
          </p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-xs text-gray-500 mb-1">Discount</p>
          <p className="text-lg font-semibold text-gray-900 font-mono">
            ৳{(sale.discount_amount / 100).toFixed(2)}
          </p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-xs text-gray-500 mb-1">Tax</p>
          <p className="text-lg font-semibold text-gray-900 font-mono">
            ৳{(sale.tax_amount / 100).toFixed(2)}
          </p>
        </div>
        <div className="bg-white rounded-lg border border-blue-200 bg-blue-50 p-4">
          <p className="text-xs text-blue-600 mb-1 font-medium">Total</p>
          <p className="text-2xl font-bold text-blue-900 font-mono">
            ৳{(sale.total_amount / 100).toFixed(2)}
          </p>
        </div>
      </div>

      {/* Items Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden mb-6">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-900">Items</h2>
        </div>
        {sale.items.length === 0 ? (
          <p className="text-gray-500 text-sm py-6 text-center">No items.</p>
        ) : (
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-gray-500 uppercase text-xs">
              <tr>
                {['Product', 'SKU', 'Quantity', 'Unit Price', 'Total Price'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sale.items.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{item.product_name}</td>
                  <td className="px-4 py-3 font-mono text-gray-500 text-xs">{item.product_sku}</td>
                  <td className="px-4 py-3 text-gray-700">{item.quantity}</td>
                  <td className="px-4 py-3 font-mono text-gray-700">
                    ৳{(item.unit_price / 100).toFixed(2)}
                  </td>
                  <td className="px-4 py-3 font-mono text-gray-900 font-medium">
                    ৳{(item.total_price / 100).toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Notes */}
      {sale.notes && (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-xs text-gray-500 mb-1 font-medium uppercase">Notes</p>
          <p className="text-sm text-gray-700">{sale.notes}</p>
        </div>
      )}
    </div>
  );
}
