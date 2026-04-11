import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import {
  usePurchaseOrder,
  useSubmitPO,
  useDeletePO,
  useReceivePO,
  useCancelPO,
} from '../hooks/usePurchaseOrders';
import { useAuthStore } from '../store/auth.store';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ErrorDisplay } from '../components/ui/ErrorDisplay';
import type { POItem, POStatus } from '../types/purchase-order.types';

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

interface ReceiveModalProps {
  items: POItem[];
  poId: string;
  onClose: () => void;
}

function ReceiveModal({ items, poId, onClose }: ReceiveModalProps) {
  const receivePO = useReceivePO();
  const [quantities, setQuantities] = useState<Record<string, number>>(() => {
    const init: Record<string, number> = {};
    items.forEach((item) => {
      const remaining = item.quantity - item.received_quantity;
      init[item.id] = remaining > 0 ? remaining : 0;
    });
    return init;
  });
  const [receiveError, setReceiveError] = useState<string | null>(null);

  const receivableItems = items.filter(
    (item) => item.quantity - item.received_quantity > 0,
  );

  function handleChange(itemId: string, value: number) {
    setQuantities((prev) => ({ ...prev, [itemId]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setReceiveError(null);

    const payload = receivableItems
      .filter((item) => quantities[item.id] > 0)
      .map((item) => ({
        item_id: item.id,
        received_quantity: quantities[item.id],
      }));

    if (payload.length === 0) {
      setReceiveError('Enter at least one received quantity > 0');
      return;
    }

    // Validate each qty doesn't exceed remaining
    for (const item of receivableItems) {
      const remaining = item.quantity - item.received_quantity;
      const qty = quantities[item.id] ?? 0;
      if (qty > remaining) {
        setReceiveError(
          `Received quantity for "${item.product_name}" cannot exceed remaining (${remaining})`,
        );
        return;
      }
    }

    try {
      await receivePO.mutateAsync({ id: poId, items: payload });
      onClose();
    } catch (err: unknown) {
      setReceiveError(err instanceof Error ? err.message : 'Failed to receive items');
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 p-6 max-h-[90vh] overflow-y-auto">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Receive Items</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          {receivableItems.length === 0 ? (
            <p className="text-gray-500 text-sm">All items have been fully received.</p>
          ) : (
            <div className="space-y-3">
              <div className="grid grid-cols-4 gap-2 text-xs font-medium text-gray-500 uppercase pb-2 border-b">
                <span className="col-span-2">Product</span>
                <span>Remaining</span>
                <span>Receive Qty</span>
              </div>
              {receivableItems.map((item) => {
                const remaining = item.quantity - item.received_quantity;
                return (
                  <div key={item.id} className="grid grid-cols-4 gap-2 items-center">
                    <div className="col-span-2">
                      <p className="text-sm font-medium text-gray-900">{item.product_name}</p>
                      <p className="text-xs text-gray-400 font-mono">{item.product_sku}</p>
                    </div>
                    <span className="text-sm text-gray-600">{remaining}</span>
                    <input
                      type="number"
                      min={1}
                      max={remaining}
                      value={quantities[item.id] ?? ''}
                      onChange={(e) =>
                        handleChange(item.id, parseInt(e.target.value, 10) || 0)
                      }
                      className="border border-gray-300 rounded px-2 py-1 text-sm w-full"
                    />
                  </div>
                );
              })}
            </div>
          )}

          {receiveError && (
            <div className="rounded-md bg-red-50 border border-red-200 p-3">
              <p className="text-sm text-red-700">{receiveError}</p>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            {receivableItems.length > 0 && (
              <button
                type="submit"
                disabled={receivePO.isPending}
                className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {receivePO.isPending ? 'Receiving...' : 'Confirm Receipt'}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}

export function PurchaseOrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [receiveModalOpen, setReceiveModalOpen] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const user = useAuthStore((state) => state.user);
  const canEdit = user?.role === 'admin' || user?.role === 'manager';
  const isAdmin = user?.role === 'admin';

  const { data: po, isLoading, isError, error } = usePurchaseOrder(id ?? '');
  const submitPO = useSubmitPO();
  const deletePO = useDeletePO();
  const cancelPO = useCancelPO();

  function handleSubmitOrder() {
    if (!po) return;
    if (!window.confirm('Submit this purchase order?')) return;
    setActionError(null);
    submitPO.mutate(po.id, {
      onError: (err) => setActionError(err.message),
    });
  }

  function handleDelete() {
    if (!po) return;
    if (!window.confirm('Delete this purchase order? This cannot be undone.')) return;
    setActionError(null);
    deletePO.mutate(po.id, {
      onSuccess: () => navigate('/purchases'),
      onError: (err) => setActionError(err.message),
    });
  }

  function handleCancel() {
    if (!po) return;
    if (!window.confirm('Cancel this purchase order?')) return;
    setActionError(null);
    cancelPO.mutate(po.id, {
      onError: (err) => setActionError(err.message),
    });
  }

  if (isLoading) return <LoadingSkeleton />;
  if (isError || !po)
    return (
      <ErrorDisplay
        message={error instanceof Error ? error.message : 'Failed to load purchase order'}
      />
    );

  return (
    <div>
      {/* Back */}
      <button
        onClick={() => navigate('/purchases')}
        className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft size={16} />
        Purchase Orders
      </button>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 font-mono">{po.po_number}</h1>
          <p className="text-gray-500 text-sm mt-1">{po.supplier_name}</p>
        </div>
        <span
          className={`px-3 py-1 rounded text-sm font-medium ${
            STATUS_BADGE[po.status] ?? 'bg-gray-100 text-gray-700'
          }`}
        >
          {STATUS_LABELS[po.status] ?? po.status}
        </span>
      </div>

      {/* Action error */}
      {actionError && (
        <p className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md px-4 py-2">
          {actionError}
        </p>
      )}

      {/* Action buttons */}
      <div className="flex flex-wrap gap-3 mb-6">
        {po.status === 'draft' && canEdit && (
          <button
            onClick={handleSubmitOrder}
            disabled={submitPO.isPending}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {submitPO.isPending ? 'Submitting...' : 'Submit Order'}
          </button>
        )}
        {po.status === 'draft' && canEdit && (
          <Link
            to={`/purchases/${po.id}/edit`}
            className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-50"
          >
            Edit PO
          </Link>
        )}
        {po.status === 'draft' && isAdmin && (
          <button
            onClick={handleDelete}
            disabled={deletePO.isPending}
            className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-md hover:bg-red-700 disabled:opacity-50"
          >
            {deletePO.isPending ? 'Deleting...' : 'Delete PO'}
          </button>
        )}
        {(po.status === 'ordered' || po.status === 'partially_received') && canEdit && (
          <button
            onClick={() => setReceiveModalOpen(true)}
            className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700"
          >
            Receive Items
          </button>
        )}
        {(po.status === 'draft' || po.status === 'ordered') && isAdmin && (
          <button
            onClick={handleCancel}
            disabled={cancelPO.isPending}
            className="px-4 py-2 border border-red-300 text-red-700 text-sm font-medium rounded-md hover:bg-red-50 disabled:opacity-50"
          >
            {cancelPO.isPending ? 'Cancelling...' : 'Cancel PO'}
          </button>
        )}
      </div>

      {/* PO Header Details */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <h2 className="text-base font-semibold text-gray-900 mb-4">Order Details</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Supplier</span>
            <p className="font-medium text-gray-900 mt-0.5">{po.supplier_name}</p>
          </div>
          <div>
            <span className="text-gray-500">Order Date</span>
            <p className="font-medium text-gray-900 mt-0.5">
              {new Date(po.order_date).toLocaleDateString()}
            </p>
          </div>
          <div>
            <span className="text-gray-500">Expected Date</span>
            <p className="font-medium text-gray-900 mt-0.5">
              {po.expected_date ? new Date(po.expected_date).toLocaleDateString() : '—'}
            </p>
          </div>
          <div>
            <span className="text-gray-500">Created By</span>
            <p className="font-medium text-gray-900 mt-0.5">{po.created_by ?? '—'}</p>
          </div>
          {po.notes && (
            <div className="col-span-2">
              <span className="text-gray-500">Notes</span>
              <p className="font-medium text-gray-900 mt-0.5">{po.notes}</p>
            </div>
          )}
        </div>
      </div>

      {/* Items Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden mb-6">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-900">Items</h2>
        </div>
        {po.items.length === 0 ? (
          <p className="text-gray-500 text-sm py-6 text-center">No items.</p>
        ) : (
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-gray-500 uppercase text-xs">
              <tr>
                {['Product', 'SKU', 'Ordered', 'Received', 'Unit Cost', 'Total'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {po.items.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{item.product_name}</td>
                  <td className="px-4 py-3 font-mono text-gray-500 text-xs">{item.product_sku}</td>
                  <td className="px-4 py-3 text-gray-700">{item.quantity}</td>
                  <td className="px-4 py-3 text-gray-700">{item.received_quantity}</td>
                  <td className="px-4 py-3 font-mono text-gray-700">
                    ৳{(item.unit_cost / 100).toFixed(2)}
                  </td>
                  <td className="px-4 py-3 font-mono text-gray-700">
                    ৳{(item.total_cost / 100).toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Totals */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 max-w-sm ml-auto">
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-500">Subtotal</span>
            <span className="font-mono text-gray-900">৳{(po.subtotal / 100).toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Tax</span>
            <span className="font-mono text-gray-900">৳{(po.tax_amount / 100).toFixed(2)}</span>
          </div>
          <div className="flex justify-between border-t border-gray-100 pt-2 font-semibold">
            <span className="text-gray-900">Total</span>
            <span className="font-mono text-gray-900">
              ৳{(po.total_amount / 100).toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {/* Receive Modal */}
      {receiveModalOpen && (
        <ReceiveModal
          items={po.items}
          poId={po.id}
          onClose={() => setReceiveModalOpen(false)}
        />
      )}
    </div>
  );
}
