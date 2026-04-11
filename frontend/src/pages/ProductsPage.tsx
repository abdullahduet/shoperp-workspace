import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, Pencil, Trash2, Plus, Upload, ChevronLeft, ChevronRight } from 'lucide-react';
import { useProducts, useDeleteProduct } from '../hooks/useProducts';
import { useCategories } from '../hooks/useCategories';
import { useAuthStore } from '../store/auth.store';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ErrorDisplay } from '../components/ui/ErrorDisplay';
import type { ProductFilters } from '../types/product.types';

export function ProductsPage() {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [categoryId, setCategoryId] = useState<string | undefined>();
  const [isActive, setIsActive] = useState<boolean | undefined>();
  const [sort, setSort] = useState<ProductFilters['sort']>('name');
  const [order, setOrder] = useState<'asc' | 'desc'>('asc');
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [categoryId, isActive, sort, order]);

  const { data, isLoading, isError, error } = useProducts({
    page,
    limit: 20,
    search: debouncedSearch || undefined,
    category_id: categoryId,
    is_active: isActive,
    sort,
    order,
  });

  const { data: categories } = useCategories();
  const deleteProduct = useDeleteProduct();

  const handleDelete = (id: string) => {
    if (!window.confirm('Delete this product?')) return;
    setDeleteError(null);
    deleteProduct.mutate(id, {
      onError: (err) => setDeleteError(err.message),
    });
  };

  const products = data?.data ?? [];
  const pagination = data?.pagination;

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Products</h1>
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/products/import')}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-50"
          >
            <Upload size={16} />
            Import CSV
          </button>
          <button
            onClick={() => navigate('/products/new')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
          >
            <Plus size={16} />
            New Product
          </button>
        </div>
      </div>

      {/* Filter bar */}
      <div className="flex flex-wrap gap-3 mb-4">
        <input
          type="text"
          placeholder="Search products..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-56"
        />
        <select
          value={categoryId ?? ''}
          onChange={(e) => setCategoryId(e.target.value || undefined)}
          className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Categories</option>
          {(categories ?? []).map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <select
          value={isActive === undefined ? '' : isActive ? 'true' : 'false'}
          onChange={(e) => {
            const v = e.target.value;
            setIsActive(v === '' ? undefined : v === 'true');
          }}
          className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">All Status</option>
          <option value="true">Active</option>
          <option value="false">Inactive</option>
        </select>
        <select
          value={`${sort}_${order}`}
          onChange={(e) => {
            const lastIdx = e.target.value.lastIndexOf('_');
            const s = e.target.value.substring(0, lastIdx) as ProductFilters['sort'];
            const o = e.target.value.substring(lastIdx + 1) as 'asc' | 'desc';
            setSort(s);
            setOrder(o);
          }}
          className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="name_asc">Name A-Z</option>
          <option value="name_desc">Name Z-A</option>
          <option value="sku_asc">SKU A-Z</option>
          <option value="sku_desc">SKU Z-A</option>
          <option value="stock_quantity_asc">Stock Low-High</option>
          <option value="stock_quantity_desc">Stock High-Low</option>
          <option value="unit_price_asc">Price Low-High</option>
          <option value="unit_price_desc">Price High-Low</option>
        </select>
      </div>

      {/* Delete error */}
      {deleteError && (
        <p className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md px-4 py-2">
          {deleteError}
        </p>
      )}

      {/* Content */}
      {isLoading ? (
        <LoadingSkeleton />
      ) : isError ? (
        <ErrorDisplay message={error?.message ?? 'Failed to load products'} />
      ) : products.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-lg border border-gray-200">
          <p className="text-gray-500 mb-4">No products found.</p>
          <button
            onClick={() => navigate('/products/new')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 mx-auto"
          >
            <Plus size={16} />
            New Product
          </button>
        </div>
      ) : (
        <>
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">
                    SKU
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Name
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Category
                  </th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Unit Price
                  </th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Stock
                  </th>
                  <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Status
                  </th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {products.map((product) => {
                  const categoryName = product.category_id
                    ? ((categories ?? []).find((c) => c.id === product.category_id)?.name ?? '—')
                    : '—';
                  const isLowStock = product.stock_quantity < product.min_stock_level;
                  return (
                    <tr key={product.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono text-gray-600">{product.sku}</td>
                      <td className="px-4 py-3 font-medium text-gray-900">{product.name}</td>
                      <td className="px-4 py-3 text-gray-600">{categoryName}</td>
                      <td className="px-4 py-3 text-right text-gray-900">
                        ৳{(product.unit_price / 100).toFixed(2)}
                      </td>
                      <td
                        className={`px-4 py-3 text-right font-medium ${
                          isLowStock ? 'text-red-600' : 'text-gray-900'
                        }`}
                      >
                        {product.stock_quantity}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                            product.is_active
                              ? 'bg-green-100 text-green-700'
                              : 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          {product.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => navigate(`/products/${product.id}`)}
                            className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded"
                            title="View"
                          >
                            <Eye size={15} />
                          </button>
                          {(user?.role === 'admin' || user?.role === 'manager') && (
                            <button
                              onClick={() => navigate(`/products/${product.id}/edit`)}
                              className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded"
                              title="Edit"
                            >
                              <Pencil size={15} />
                            </button>
                          )}
                          {user?.role === 'admin' && (
                            <button
                              onClick={() => handleDelete(product.id)}
                              disabled={deleteProduct.isPending}
                              className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded disabled:opacity-50"
                              title="Delete"
                            >
                              <Trash2 size={15} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {pagination && (
            <div className="flex items-center justify-between mt-4 text-sm text-gray-600">
              <span>
                Page {pagination.page} of {pagination.total_pages} ({pagination.total} total)
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={pagination.page <= 1}
                  className="flex items-center gap-1 px-3 py-1.5 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft size={14} />
                  Prev
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(pagination.total_pages, p + 1))}
                  disabled={pagination.page >= pagination.total_pages}
                  className="flex items-center gap-1 px-3 py-1.5 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                  <ChevronRight size={14} />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
