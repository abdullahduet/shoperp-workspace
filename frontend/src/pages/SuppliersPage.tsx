import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Pencil, Trash2, Plus } from 'lucide-react';
import {
  useSuppliers,
  useCreateSupplier,
  useUpdateSupplier,
  useDeleteSupplier,
} from '../hooks/useSuppliers';
import { useAuthStore } from '../store/auth.store';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ErrorDisplay } from '../components/ui/ErrorDisplay';
import type { Supplier, SupplierFormValues } from '../types/supplier.types';

const supplierSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  contact_person: z.string().optional().default(''),
  phone: z.string().optional().default(''),
  email: z.string().email('Invalid email').optional().or(z.literal('')).default(''),
  address: z.string().optional().default(''),
  city: z.string().optional().default(''),
  country: z.string().optional().default(''),
  payment_terms: z.string().optional().default(''),
  is_active: z.boolean().default(true),
  notes: z.string().optional().default(''),
});

type SupplierSchemaValues = z.infer<typeof supplierSchema>;

interface SupplierModalProps {
  editing: Supplier | null;
  onClose: () => void;
}

function SupplierModal({ editing, onClose }: SupplierModalProps) {
  const createSupplier = useCreateSupplier();
  const updateSupplier = useUpdateSupplier();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SupplierSchemaValues>({
    resolver: zodResolver(supplierSchema),
    defaultValues: editing
      ? {
          name: editing.name,
          contact_person: editing.contact_person ?? '',
          phone: editing.phone ?? '',
          email: editing.email ?? '',
          address: editing.address ?? '',
          city: editing.city ?? '',
          country: editing.country ?? '',
          payment_terms: editing.payment_terms ?? '',
          is_active: editing.is_active,
          notes: editing.notes ?? '',
        }
      : {
          name: '',
          contact_person: '',
          phone: '',
          email: '',
          address: '',
          city: '',
          country: '',
          payment_terms: '',
          is_active: true,
          notes: '',
        },
  });

  const isPending = createSupplier.isPending || updateSupplier.isPending;
  const mutationError = createSupplier.error || updateSupplier.error;

  const onSubmit = (values: SupplierSchemaValues) => {
    const payload: SupplierFormValues = {
      name: values.name,
      contact_person: values.contact_person || undefined,
      phone: values.phone || undefined,
      email: values.email || undefined,
      address: values.address || undefined,
      city: values.city || undefined,
      country: values.country || undefined,
      payment_terms: values.payment_terms || undefined,
      is_active: values.is_active,
      notes: values.notes || undefined,
    };

    if (editing) {
      updateSupplier.mutate({ id: editing.id, data: payload }, { onSuccess: onClose });
    } else {
      createSupplier.mutate(payload, { onSuccess: onClose });
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 p-6 max-h-[90vh] overflow-y-auto">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          {editing ? 'Edit Supplier' : 'New Supplier'}
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

          {/* Contact Person */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contact Person</label>
            <input
              type="text"
              {...register('contact_person')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Phone + Email */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
              <input
                type="text"
                {...register('phone')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                {...register('email')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {errors.email && (
                <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>
              )}
            </div>
          </div>

          {/* Address */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
            <input
              type="text"
              {...register('address')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* City + Country */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
              <input
                type="text"
                {...register('city')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Country</label>
              <input
                type="text"
                {...register('country')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Payment Terms */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Payment Terms</label>
            <input
              type="text"
              {...register('payment_terms')}
              placeholder="e.g. Net 30"
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <textarea
              {...register('notes')}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Is Active */}
          <div className="flex items-center gap-3">
            <input
              id="supplier_is_active"
              type="checkbox"
              {...register('is_active')}
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="supplier_is_active" className="text-sm font-medium text-gray-700">
              Active
            </label>
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

export function SuppliersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [activeFilter, setActiveFilter] = useState('');
  const [appliedSearch, setAppliedSearch] = useState('');
  const [appliedActive, setAppliedActive] = useState<boolean | undefined>(undefined);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Supplier | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const user = useAuthStore((state) => state.user);
  const canEdit = user?.role === 'admin' || user?.role === 'manager';
  const isAdmin = user?.role === 'admin';

  const { data, isLoading, isError, error } = useSuppliers({
    page,
    limit: 20,
    search: appliedSearch || undefined,
    is_active: appliedActive,
  });

  const deleteSupplier = useDeleteSupplier();

  function applyFilters() {
    setPage(1);
    setAppliedSearch(search);
    setAppliedActive(
      activeFilter === 'true' ? true : activeFilter === 'false' ? false : undefined,
    );
  }

  function resetFilters() {
    setSearch('');
    setActiveFilter('');
    setPage(1);
    setAppliedSearch('');
    setAppliedActive(undefined);
  }

  function handleNew() {
    setEditing(null);
    setModalOpen(true);
  }

  function handleEdit(supplier: Supplier) {
    setEditing(supplier);
    setModalOpen(true);
  }

  function handleClose() {
    setModalOpen(false);
    setEditing(null);
  }

  function handleDelete(id: string) {
    if (!window.confirm('Delete this supplier?')) return;
    setDeleteError(null);
    deleteSupplier.mutate(id, {
      onError: (err) => setDeleteError(err.message),
    });
  }

  if (isLoading) return <LoadingSkeleton />;
  if (isError) return <ErrorDisplay message={error instanceof Error ? error.message : 'Failed to load suppliers'} />;

  const suppliers = data?.data ?? [];
  const pagination = data?.pagination;

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Suppliers</h1>
        {canEdit && (
          <button
            onClick={handleNew}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
          >
            <Plus size={16} />
            New Supplier
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
        <input
          type="text"
          placeholder="Search by name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && applyFilters()}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm w-64"
        />
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
      {suppliers.length === 0 ? (
        <p className="text-gray-500 py-12 text-center">No suppliers found.</p>
      ) : (
        <div className="overflow-x-auto rounded border border-gray-200">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
              <tr>
                {['Name', 'Contact Person', 'Phone', 'Email', 'City', 'Status', 'Actions'].map(
                  (h) => (
                    <th key={h} className="px-4 py-3 text-left font-medium">
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {suppliers.map((supplier) => (
                <tr key={supplier.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{supplier.name}</td>
                  <td className="px-4 py-3 text-gray-600">{supplier.contact_person ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-600">{supplier.phone ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-600">{supplier.email ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-600">{supplier.city ?? '—'}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        supplier.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {supplier.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {canEdit && (
                        <button
                          onClick={() => handleEdit(supplier)}
                          className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded"
                          title="Edit"
                        >
                          <Pencil size={15} />
                        </button>
                      )}
                      {isAdmin && (
                        <button
                          onClick={() => handleDelete(supplier.id)}
                          disabled={deleteSupplier.isPending}
                          className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded disabled:opacity-50"
                          title="Delete"
                        >
                          <Trash2 size={15} />
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

      {/* Modal */}
      {modalOpen && <SupplierModal editing={editing} onClose={handleClose} />}
    </div>
  );
}
