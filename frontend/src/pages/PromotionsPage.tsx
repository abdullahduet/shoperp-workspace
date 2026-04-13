import { useState } from 'react';
import { useForm, useWatch, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Pencil, Trash2, Plus } from 'lucide-react';
import {
  usePromotions,
  useCreatePromotion,
  useUpdatePromotion,
  useDeletePromotion,
} from '../hooks/usePromotions';
import { useAuthStore } from '../store/auth.store';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ErrorDisplay } from '../components/ui/ErrorDisplay';
import { ProductMultiSelect } from '../components/ui/ProductSearchSelect';
import type { Promotion, PromotionPayload } from '../types/promotion.types';

// ─── Helpers ────────────────────────────────────────────────────────────────

function getPromotionStatus(promo: Promotion): 'Active' | 'Inactive' | 'Scheduled' | 'Expired' {
  if (!promo.is_active) return 'Inactive';
  const now = new Date();
  const start = new Date(promo.start_date);
  const end = new Date(promo.end_date);
  if (now < start) return 'Scheduled';
  if (now > end) return 'Expired';
  return 'Active';
}

const STATUS_BADGE: Record<string, string> = {
  Active: 'bg-green-100 text-green-800',
  Inactive: 'bg-gray-100 text-gray-600',
  Scheduled: 'bg-blue-100 text-blue-700',
  Expired: 'bg-red-100 text-red-700',
};

const TYPE_BADGE: Record<string, string> = {
  percentage: 'bg-blue-100 text-blue-700',
  fixed: 'bg-purple-100 text-purple-700',
  bogo: 'bg-orange-100 text-orange-700',
};

function displayValue(promo: Promotion): string {
  if (promo.type === 'percentage') return `${promo.value}%`;
  if (promo.type === 'fixed') return `৳${(promo.value / 100).toFixed(2)}`;
  return '—';
}

// ─── Zod schema ─────────────────────────────────────────────────────────────

const promotionSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  type: z.enum(['percentage', 'fixed', 'bogo']),
  value: z.number().min(0).default(0),
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().min(1, 'End date is required'),
  min_purchase_amount: z.number().min(0).default(0),
  applies_to: z.enum(['all', 'specific']),
  is_active: z.boolean().default(true),
  auto_apply: z.boolean().default(false),
  product_ids: z.array(z.string()).default([]),
});

type PromotionSchemaValues = z.infer<typeof promotionSchema>;

// ─── Modal ──────────────────────────────────────────────────────────────────

interface PromotionModalProps {
  editing: Promotion | null;
  onClose: () => void;
}

function PromotionModal({ editing, onClose }: PromotionModalProps) {
  const createPromotion = useCreatePromotion();
  const updatePromotion = useUpdatePromotion();

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<PromotionSchemaValues>({
    resolver: zodResolver(promotionSchema),
    defaultValues: editing
      ? {
          name: editing.name,
          type: editing.type,
          value:
            editing.type === 'fixed'
              ? editing.value / 100
              : editing.type === 'bogo'
              ? 0
              : editing.value,
          start_date: editing.start_date.slice(0, 16),
          end_date: editing.end_date.slice(0, 16),
          min_purchase_amount: editing.min_purchase_amount / 100,
          applies_to: editing.applies_to,
          is_active: editing.is_active,
          product_ids: editing.applies_to === 'specific' ? editing.product_ids : [],
          auto_apply: editing.auto_apply,
        }
      : {
          name: '',
          type: 'percentage',
          value: 0,
          start_date: '',
          end_date: '',
          min_purchase_amount: 0,
          applies_to: 'all',
          is_active: true,
          auto_apply: false,
          product_ids: [],
        },
  });

  const watchedType = useWatch({ control, name: 'type' });
  const watchedAppliesTo = useWatch({ control, name: 'applies_to' });

  const isPending = createPromotion.isPending || updatePromotion.isPending;
  const mutationError = createPromotion.error ?? updatePromotion.error;

  const onSubmit = (values: PromotionSchemaValues) => {
    const payload: PromotionPayload = {
      name: values.name,
      type: values.type,
      value:
        values.type === 'fixed'
          ? Math.round(values.value * 100)
          : values.type === 'bogo'
          ? 0
          : values.value,
      start_date: new Date(values.start_date).toISOString(),
      end_date: new Date(values.end_date).toISOString(),
      min_purchase_amount: Math.round(values.min_purchase_amount * 100),
      applies_to: values.applies_to,
      is_active: values.is_active,
      auto_apply: values.auto_apply,
      product_ids: values.applies_to === 'specific' ? values.product_ids : [],
    };

    if (editing) {
      updatePromotion.mutate({ id: editing.id, data: payload }, { onSuccess: onClose });
    } else {
      createPromotion.mutate(payload, { onSuccess: onClose });
    }
  };

  const valueLabelMap: Record<string, string> = {
    percentage: 'Discount (%)',
    fixed: 'Discount Amount (৳)',
    bogo: '',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 p-6 max-h-[90vh] overflow-y-auto">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          {editing ? 'Edit Promotion' : 'New Promotion'}
        </h2>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              {...register('name')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.name && (
              <p className="mt-1 text-xs text-red-600">{errors.name.message}</p>
            )}
          </div>

          {/* Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
            <select
              {...register('type')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="percentage">Percentage</option>
              <option value="fixed">Fixed</option>
              <option value="bogo">BOGO</option>
            </select>
          </div>

          {/* Value — hidden for bogo */}
          {watchedType !== 'bogo' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {valueLabelMap[watchedType] ?? 'Value'}
              </label>
              <input
                type="number"
                step={watchedType === 'fixed' ? '0.01' : '1'}
                min="0"
                {...register('value', { valueAsNumber: true })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {errors.value && (
                <p className="mt-1 text-xs text-red-600">{errors.value.message}</p>
              )}
            </div>
          )}

          {/* Start / End Date */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Date <span className="text-red-500">*</span>
              </label>
              <input
                type="datetime-local"
                {...register('start_date')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {errors.start_date && (
                <p className="mt-1 text-xs text-red-600">{errors.start_date.message}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Date <span className="text-red-500">*</span>
              </label>
              <input
                type="datetime-local"
                {...register('end_date')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {errors.end_date && (
                <p className="mt-1 text-xs text-red-600">{errors.end_date.message}</p>
              )}
            </div>
          </div>

          {/* Min Purchase Amount */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Minimum Purchase Amount (৳)
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              {...register('min_purchase_amount', { valueAsNumber: true })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Applies To */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Applies To</label>
            <select
              {...register('applies_to')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Products</option>
              <option value="specific">Specific Products</option>
            </select>
          </div>

          {/* Product IDs — shown only when applies_to='specific' */}
          {watchedAppliesTo === 'specific' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Products</label>
              <Controller
                control={control}
                name="product_ids"
                render={({ field }) => (
                  <ProductMultiSelect
                    value={field.value}
                    onChange={field.onChange}
                  />
                )}
              />
            </div>
          )}

          {/* Is Active */}
          <div className="flex items-center gap-3">
            <input
              id="promotion_is_active"
              type="checkbox"
              {...register('is_active')}
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="promotion_is_active" className="text-sm font-medium text-gray-700">
              Active
            </label>
          </div>

          {/* Auto Apply */}
          <div className="flex items-start gap-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2.5">
            <input
              id="promotion_auto_apply"
              type="checkbox"
              {...register('auto_apply')}
              className="mt-0.5 h-4 w-4 rounded border-gray-300 text-amber-600 focus:ring-amber-500"
            />
            <div>
              <label htmlFor="promotion_auto_apply" className="text-sm font-medium text-gray-700">
                Auto-apply
              </label>
              <p className="text-xs text-gray-500 mt-0.5">
                When enabled, this promotion is automatically applied to every eligible sale.
                Leave off to make it manual-only (staff must select it on the Record Sale page).
              </p>
            </div>
          </div>

          {/* Server error */}
          {mutationError && (
            <div className="rounded-md bg-red-50 border border-red-200 p-3">
              <p className="text-sm text-red-700">{mutationError.message}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isPending}
              className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isPending ? 'Saving...' : editing ? 'Save Changes' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export function PromotionsPage() {
  const [page, setPage] = useState(1);
  const [typeFilter, setTypeFilter] = useState('');
  const [activeFilter, setActiveFilter] = useState('');
  const [appliedType, setAppliedType] = useState('');
  const [appliedActive, setAppliedActive] = useState<boolean | undefined>(undefined);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Promotion | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const user = useAuthStore((state) => state.user);
  const canEdit = user?.role === 'admin' || user?.role === 'manager';
  const isAdmin = user?.role === 'admin';

  const { data, isLoading, isError, error } = usePromotions({
    page,
    limit: 20,
    type: appliedType || undefined,
    is_active: appliedActive,
  });

  const deletePromotion = useDeletePromotion();

  function applyFilters() {
    setPage(1);
    setAppliedType(typeFilter);
    setAppliedActive(
      activeFilter === 'true' ? true : activeFilter === 'false' ? false : undefined,
    );
  }

  function resetFilters() {
    setTypeFilter('');
    setActiveFilter('');
    setPage(1);
    setAppliedType('');
    setAppliedActive(undefined);
  }

  function handleNew() {
    setEditing(null);
    setModalOpen(true);
  }

  function handleEdit(promo: Promotion) {
    setEditing(promo);
    setModalOpen(true);
  }

  function handleClose() {
    setModalOpen(false);
    setEditing(null);
  }

  function handleDelete(id: string) {
    if (!window.confirm('Delete this promotion?')) return;
    setDeleteError(null);
    deletePromotion.mutate(id, {
      onError: (err) => setDeleteError(err.message),
    });
  }

  if (isLoading) return <LoadingSkeleton />;
  if (isError)
    return (
      <ErrorDisplay
        message={error instanceof Error ? error.message : 'Failed to load promotions'}
      />
    );

  const promotions = data?.data ?? [];
  const pagination = data?.pagination;

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Promotions</h1>
        {canEdit && (
          <button
            onClick={handleNew}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
          >
            <Plus size={16} />
            New Promotion
          </button>
        )}
      </div>

      {/* Delete error */}
      {deleteError && (
        <p className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md px-4 py-2">
          {deleteError}
        </p>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
        >
          <option value="">All Types</option>
          <option value="percentage">Percentage</option>
          <option value="fixed">Fixed</option>
          <option value="bogo">BOGO</option>
        </select>
        <select
          value={activeFilter}
          onChange={(e) => setActiveFilter(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
        >
          <option value="">All Status</option>
          <option value="true">Active</option>
          <option value="false">Inactive</option>
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
      {promotions.length === 0 ? (
        <p className="text-gray-500 py-12 text-center">No promotions found.</p>
      ) : (
        <div className="overflow-x-auto rounded border border-gray-200">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
              <tr>
                {[
                  'Name',
                  'Type',
                  'Value',
                  'Date Range',
                  'Min Purchase',
                  'Scope',
                  'Auto-apply',
                  'Status',
                  'Actions',
                ].map((h) => (
                  <th key={h} className="px-4 py-3 text-left font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {promotions.map((promo) => {
                const status = getPromotionStatus(promo);
                return (
                  <tr key={promo.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{promo.name}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                          TYPE_BADGE[promo.type] ?? 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {promo.type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-700 font-mono">{displayValue(promo)}</td>
                    <td className="px-4 py-3 text-gray-600 whitespace-nowrap">
                      {new Date(promo.start_date).toLocaleDateString()} —{' '}
                      {new Date(promo.end_date).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-gray-600 font-mono">
                      {promo.min_purchase_amount > 0
                        ? `৳${(promo.min_purchase_amount / 100).toFixed(2)}`
                        : '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-600">{promo.applies_to}</td>
                    <td className="px-4 py-3">
                      {promo.auto_apply ? (
                        <span className="px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">Auto</span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-500">Manual</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                          STATUS_BADGE[status] ?? 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {canEdit && (
                          <button
                            onClick={() => handleEdit(promo)}
                            className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded"
                            title="Edit"
                          >
                            <Pencil size={15} />
                          </button>
                        )}
                        {isAdmin && (
                          <button
                            onClick={() => handleDelete(promo.id)}
                            disabled={deletePromotion.isPending}
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

      {/* Modal */}
      {modalOpen && <PromotionModal editing={editing} onClose={handleClose} />}
    </div>
  );
}
