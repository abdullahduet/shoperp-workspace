import { useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMovements, useAdjust } from '../hooks/useInventory';
import { useCurrentUser } from '../hooks/useAuth';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ErrorDisplay } from '../components/ui/ErrorDisplay';
import { ProductSearchSelect } from '../components/ui/ProductSearchSelect';
import type { MovementFilters, AdjustmentFormValues } from '../types/inventory.types';

const adjustSchema = z.object({
  product_id: z.string().min(1, 'Product ID is required'),
  quantity: z.number().int().refine(v => v !== 0, { message: 'Must be non-zero' }),
  notes: z.string().optional(),
});

export function InventoryMovementsPage() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<MovementFilters>({});
  const [filterProductId, setFilterProductId] = useState('');
  const [movementType, setMovementType] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [adjustError, setAdjustError] = useState<string | null>(null);

  const { data: currentUserData } = useCurrentUser();
  const user = currentUserData;
  const canAdjust = user?.role === 'admin' || user?.role === 'manager';

  const { data, isLoading, isError, error } = useMovements({ ...filters, page, limit: 20 });
  const adjust = useAdjust();

  const { register, control, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<AdjustmentFormValues>({
    resolver: zodResolver(adjustSchema),
    defaultValues: { product_id: '', quantity: 0, notes: '' },
  });

  function applyFilters() {
    setPage(1);
    setFilters({
      product_id: filterProductId || undefined,
      movement_type: (movementType as MovementFilters['movement_type']) || undefined,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    });
  }

  function resetFilters() {
    setFilterProductId('');
    setMovementType('');
    setStartDate('');
    setEndDate('');
    setPage(1);
    setFilters({});
  }

  async function onSubmit(values: AdjustmentFormValues) {
    setAdjustError(null);
    try {
      await adjust.mutateAsync(values);
      setModalOpen(false);
      reset();
    } catch (e: unknown) {
      setAdjustError(e instanceof Error ? e.message : 'Adjustment failed');
    }
  }

  function typeBadge(type: string) {
    const styles: Record<string, string> = {
      in: 'bg-green-100 text-green-800',
      out: 'bg-red-100 text-red-800',
      adjustment: 'bg-yellow-100 text-yellow-800',
    };
    return (
      <span className={`px-2 py-0.5 rounded text-xs font-medium ${styles[type] ?? 'bg-gray-100 text-gray-700'}`}>
        {type}
      </span>
    );
  }

  if (isLoading) return <LoadingSkeleton />;
  if (isError) return <ErrorDisplay message={error instanceof Error ? error.message : 'Failed to load movements'} />;

  const movements = data?.data ?? [];
  const pagination = data?.pagination;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Stock Movements</h1>
        {canAdjust && (
          <button
            onClick={() => { setModalOpen(true); setAdjustError(null); reset(); }}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm font-medium"
          >
            New Adjustment
          </button>
        )}
      </div>

      {/* Filter bar */}
      <div className="flex flex-wrap gap-3 mb-4">
        <div className="w-72">
          <ProductSearchSelect
            value={filterProductId}
            onChange={(id) => setFilterProductId(id)}
            placeholder="Filter by product…"
          />
        </div>
        <select
          value={movementType}
          onChange={e => setMovementType(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
        >
          <option value="">All Types</option>
          <option value="in">In</option>
          <option value="out">Out</option>
          <option value="adjustment">Adjustment</option>
        </select>
        <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm" />
        <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm" />
        <button onClick={applyFilters}
          className="px-3 py-1.5 bg-gray-800 text-white rounded text-sm">Apply</button>
        <button onClick={resetFilters}
          className="px-3 py-1.5 border border-gray-300 rounded text-sm text-gray-600">Reset</button>
      </div>

      {/* Table */}
      {movements.length === 0 ? (
        <p className="text-gray-500 py-12 text-center">No stock movements found.</p>
      ) : (
        <div className="overflow-x-auto rounded border border-gray-200">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
              <tr>
                {['Date', 'Product', 'Type', 'Qty', 'Stock Change', 'Reference', 'Notes'].map(h => (
                  <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {movements.map(m => (
                <tr key={m.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap text-gray-500">
                    {new Date(m.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-medium text-gray-900">{m.product_name}</span>
                    <span className="ml-2 text-xs text-gray-400 font-mono">{m.product_sku}</span>
                  </td>
                  <td className="px-4 py-3">{typeBadge(m.movement_type)}</td>
                  <td className="px-4 py-3 font-mono">
                    <span className={m.quantity > 0 ? 'text-green-600' : 'text-red-600'}>
                      {m.quantity > 0 ? `+${m.quantity}` : m.quantity}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-gray-500">
                    {m.stock_before} → {m.stock_after}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{m.reference_type ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-500 max-w-xs truncate">{m.notes ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {pagination && pagination.total_pages > 1 && (
        <div className="flex items-center justify-between mt-4 text-sm text-gray-600">
          <span>Page {pagination.page} of {pagination.total_pages} ({pagination.total} total)</span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1 border rounded disabled:opacity-40"
            >Prev</button>
            <button
              onClick={() => setPage(p => Math.min(pagination.total_pages, p + 1))}
              disabled={page >= pagination.total_pages}
              className="px-3 py-1 border rounded disabled:opacity-40"
            >Next</button>
          </div>
        </div>
      )}

      {/* Adjustment Modal */}
      {modalOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
            <h2 className="text-lg font-semibold mb-4">New Stock Adjustment</h2>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Product</label>
                <Controller
                  control={control}
                  name="product_id"
                  render={({ field }) => (
                    <ProductSearchSelect
                      value={field.value}
                      onChange={field.onChange}
                      onBlur={field.onBlur}
                      hasError={!!errors.product_id}
                    />
                  )}
                />
                {errors.product_id && <p className="text-red-500 text-xs mt-1">{errors.product_id.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Quantity (positive = add, negative = remove)
                </label>
                <input
                  type="number"
                  {...register('quantity', { valueAsNumber: true })}
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                />
                {errors.quantity && <p className="text-red-500 text-xs mt-1">{errors.quantity.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes (optional)</label>
                <textarea
                  {...register('notes')}
                  rows={3}
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                />
              </div>
              {adjustError && <p className="text-red-500 text-sm">{adjustError}</p>}
              <div className="flex justify-end gap-3 pt-2">
                <button type="button" onClick={() => setModalOpen(false)}
                  className="px-4 py-2 border rounded text-sm text-gray-600">
                  Cancel
                </button>
                <button type="submit" disabled={isSubmitting || adjust.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded text-sm disabled:opacity-50">
                  {adjust.isPending ? 'Saving…' : 'Save Adjustment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
