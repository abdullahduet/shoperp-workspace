import { useValuation } from '../hooks/useInventory';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ErrorDisplay } from '../components/ui/ErrorDisplay';

export function InventoryValuationPage() {
  const { data, isLoading, isError, error } = useValuation();

  if (isLoading) return <LoadingSkeleton />;
  if (isError) return <ErrorDisplay message={error instanceof Error ? error.message : 'Failed to load valuation'} />;

  const totalBDT = data ? (data.total_value / 100).toFixed(2) : '0.00';

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Inventory Valuation</h1>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
          <p className="text-sm text-gray-500 mb-1">Total Inventory Value</p>
          <p className="text-3xl font-bold text-gray-900">৳{totalBDT}</p>
          <p className="text-xs text-gray-400 mt-1">{data?.currency ?? 'BDT'}</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
          <p className="text-sm text-gray-500 mb-1">Products in Stock</p>
          <p className="text-3xl font-bold text-gray-900">{data?.product_count ?? 0}</p>
          <p className="text-xs text-gray-400 mt-1">active products with stock &gt; 0</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
          <p className="text-sm text-gray-500 mb-1">Currency</p>
          <p className="text-3xl font-bold text-gray-900">{data?.currency ?? 'BDT'}</p>
          <p className="text-xs text-gray-400 mt-1">Bangladeshi Taka</p>
        </div>
      </div>
    </div>
  );
}
