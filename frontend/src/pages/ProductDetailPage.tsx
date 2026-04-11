import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Pencil } from 'lucide-react';
import { useProduct } from '../hooks/useProducts';
import { useCategories } from '../hooks/useCategories';
import { useAuthStore } from '../store/auth.store';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ErrorDisplay } from '../components/ui/ErrorDisplay';

export function ProductDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);

  const { data: product, isLoading, isError, error } = useProduct(id!);
  const { data: categories } = useCategories();

  if (isLoading) return <LoadingSkeleton />;
  if (isError) return <ErrorDisplay message={error?.message ?? 'Failed to load product'} />;
  if (!product) return <ErrorDisplay message="Product not found" />;

  const categoryName = product.category_id
    ? ((categories ?? []).find((c) => c.id === product.category_id)?.name ?? '—')
    : '—';

  const isLowStock = product.stock_quantity < product.min_stock_level;

  return (
    <div>
      {/* Back + actions */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={() => navigate('/products')}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft size={16} />
          Products
        </button>
        {(user?.role === 'admin' || user?.role === 'manager') && (
          <button
            onClick={() => navigate(`/products/${product.id}/edit`)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
          >
            <Pencil size={15} />
            Edit
          </button>
        )}
      </div>

      {/* Heading */}
      <div className="flex items-center gap-3 mb-4">
        <h1 className="text-2xl font-bold text-gray-900">{product.name}</h1>
        <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-sm font-mono rounded">
          {product.sku}
        </span>
      </div>

      {/* Low stock warning */}
      {isLowStock && (
        <div className="mb-4 px-4 py-3 bg-yellow-50 border border-yellow-200 rounded-md text-sm text-yellow-800">
          Low stock: {product.stock_quantity} units remaining (min: {product.min_stock_level})
        </div>
      )}

      {/* Two-column layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left card: info */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
            Product Info
          </h2>
          <dl className="space-y-3">
            <div>
              <dt className="text-xs text-gray-500">Name</dt>
              <dd className="text-sm text-gray-900 font-medium">{product.name}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">SKU</dt>
              <dd className="text-sm text-gray-900 font-mono">{product.sku}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Barcode</dt>
              <dd className="text-sm text-gray-900">{product.barcode ?? '—'}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Category</dt>
              <dd className="text-sm text-gray-900">{categoryName}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Description</dt>
              <dd className="text-sm text-gray-900 whitespace-pre-line">
                {product.description ?? '—'}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Unit of Measure</dt>
              <dd className="text-sm text-gray-900">{product.unit_of_measure}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Status</dt>
              <dd>
                <span
                  className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                    product.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {product.is_active ? 'Active' : 'Inactive'}
                </span>
              </dd>
            </div>
          </dl>
        </div>

        {/* Right card: pricing + stock */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
            Pricing &amp; Stock
          </h2>
          <dl className="space-y-3">
            <div>
              <dt className="text-xs text-gray-500">Unit Price</dt>
              <dd className="text-sm text-gray-900 font-medium">
                ৳{(product.unit_price / 100).toFixed(2)}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Cost Price</dt>
              <dd className="text-sm text-gray-900">
                ৳{(product.cost_price / 100).toFixed(2)}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Tax Rate</dt>
              <dd className="text-sm text-gray-900">{product.tax_rate}%</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Stock Quantity</dt>
              <dd
                className={`text-sm font-medium ${
                  isLowStock ? 'text-red-600' : 'text-gray-900'
                }`}
              >
                {product.stock_quantity}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Min Stock Level</dt>
              <dd className="text-sm text-gray-900">{product.min_stock_level}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}
