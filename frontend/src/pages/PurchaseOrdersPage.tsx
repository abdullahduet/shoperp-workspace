import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, Plus, XCircle } from 'lucide-react';
import { usePurchaseOrders, useCancelPO } from '../hooks/usePurchaseOrders';
import { useSuppliers } from '../hooks/useSuppliers';
import { useAuthStore } from '../store/auth.store';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ErrorDisplay } from '../components/ui/ErrorDisplay';
import type { POStatus } from '../types/purchase-order.types';

const STATUS_BADGE: Record<POStatus, string> = {
  draft: 'bg-gray-100 text-gray-700',
  ordered: 'bg-blue-100 text-blue-700',
  partially_received: 'bg-yellow-100 text-yellow-800',
  received: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-700',
};

const STATUS_LABELS: Record<POStatus, string> = {
  draft: 'Draft',
  ordered: 'Ordered',
  partially_received: 'Partially Received',
  received: 'Received',
  cancelled: 'Cancelled',
};

export function PurchaseOrdersPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [supplierFilter, setSupplierFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [appliedSupplier, setAppliedSupplier] = useState('');
  const [appliedStatus, setAppliedStatus] = useState('');
  const [cancelError, setCancelError] = useState<string | null>(null);

  const user = useAuthStore((state) => state.user);
  const canEdit = user?.role === 'admin' || user?.role === 'manager';
  const isAdmin = user?.role === 'admin';

  const { data, isLoading, isError, error } = usePurchaseOrders({
    page,
    limit: 20,
    supplier_id: appliedSupplier || undefined,
    status: appliedStatus || undefined,
  });

  const { data: suppliersData } = useSuppliers({ is_active: true, limit: 100 });
  const cancelPO = useCancelPO();

  function applyFilters() {
    setPage(1);
    setAppliedSupplier(supplierFilter);
    setAppliedStatus(statusFilter);
  }

  function resetFilters() {
    setSupplierFilter('');
    setStatusFilter('');
    setPage(1);
    setAppliedSupplier('');
    setAppliedStatus('');
  }

  function handleCancel(id: string) {
    if (!window.confirm('Cancel this purchase order?')) return;
    setCancelError(null);
    cancelPO.mutate(id, {
      onError: (err) => setCancelError(err.message),
    });
  }

  if (isLoading) return <LoadingSkeleton />;
  if (isError)
    return (
      <ErrorDisplay
        message={error instanceof Error ? error.message : 'Failed to load purchase orders'}
      />
    );

  const orders = data?.data ?? [];
  const pagination = data?.pagination;
  const suppliers = suppliersData?.data ?? [];

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Purchase Orders</h1>
        {canEdit && (
          <button
            onClick={() => navigate('/purchases/new')}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
          >
            <Plus size={16} />
            New PO
          </button>
        )}
      </div>

      {/* Cancel error */}
      {cancelError && (
        <p className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md px-4 py-2">
          {cancelError}
        </p>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <select
          value={supplierFilter}
          onChange={(e) => setSupplierFilter(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm min-w-[180px]"
        >
          <option value="">All Suppliers</option>
          {suppliers.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
        >
          <option value="">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="ordered">Ordered</option>
          <option value="partially_received">Partially Received</option>
          <option value="received">Received</option>
          <option value="cancelled">Cancelled</option>
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
      {orders.length === 0 ? (
        <p className="text-gray-500 py-12 text-center">No purchase orders found.</p>
      ) : (
        <div className="overflow-x-auto rounded border border-gray-200">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
              <tr>
                {[
                  'PO Number',
                  'Supplier',
                  'Order Date',
                  'Expected Date',
                  'Status',
                  'Total',
                  'Actions',
                ].map((h) => (
                  <th key={h} className="px-4 py-3 text-left font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {orders.map((order) => (
                <tr key={order.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-gray-900 font-medium">
                    {order.po_number}
                  </td>
                  <td className="px-4 py-3 text-gray-700">{order.supplier_name}</td>
                  <td className="px-4 py-3 text-gray-600">
                    {new Date(order.order_date).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {order.expected_date
                      ? new Date(order.expected_date).toLocaleDateString()
                      : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        STATUS_BADGE[order.status] ?? 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {STATUS_LABELS[order.status] ?? order.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-700 font-mono">
                    ৳{(order.total_amount / 100).toFixed(2)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => navigate(`/purchases/${order.id}`)}
                        className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded"
                        title="View"
                      >
                        <Eye size={15} />
                      </button>
                      {isAdmin &&
                        (order.status === 'draft' || order.status === 'ordered') && (
                          <button
                            onClick={() => handleCancel(order.id)}
                            disabled={cancelPO.isPending}
                            className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded disabled:opacity-50"
                            title="Cancel"
                          >
                            <XCircle size={15} />
                          </button>
                        )}
                    </div>
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
