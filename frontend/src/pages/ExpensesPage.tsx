import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Pencil, Trash2, Plus } from 'lucide-react';
import {
  useExpenses,
  useCreateExpense,
  useUpdateExpense,
  useDeleteExpense,
} from '../hooks/useAccounting';
import { useAuthStore } from '../store/auth.store';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ErrorDisplay } from '../components/ui/ErrorDisplay';
import type { Expense, ExpensePayload } from '../types/accounting.types';

// ─── Helpers ─────────────────────────────────────────────────────────────────

const PAYMENT_BADGE: Record<string, string> = {
  cash: 'bg-green-100 text-green-700',
  card: 'bg-blue-100 text-blue-700',
  mobile: 'bg-purple-100 text-purple-700',
  credit: 'bg-orange-100 text-orange-700',
};

// ─── Zod schema ──────────────────────────────────────────────────────────────

const expenseSchema = z.object({
  category: z.string().min(1, 'Category required'),
  description: z.string().min(1, 'Description required'),
  amount: z
    .number({ invalid_type_error: 'Enter a valid amount' })
    .positive('Must be greater than 0'),
  payment_method: z.enum(['cash', 'card', 'mobile', 'credit']).default('cash'),
  date: z.string().optional().default(''),
  notes: z.string().optional().default(''),
});

type ExpenseSchemaValues = z.infer<typeof expenseSchema>;

// ─── Modal ───────────────────────────────────────────────────────────────────

interface ExpenseModalProps {
  editing: Expense | null;
  onClose: () => void;
}

function ExpenseModal({ editing, onClose }: ExpenseModalProps) {
  const createExpense = useCreateExpense();
  const updateExpense = useUpdateExpense();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ExpenseSchemaValues>({
    resolver: zodResolver(expenseSchema),
    defaultValues: editing
      ? {
          category: editing.category,
          description: editing.description,
          amount: editing.amount / 100,
          payment_method: editing.payment_method as 'cash' | 'card' | 'mobile' | 'credit',
          date: editing.date,
          notes: editing.notes ?? '',
        }
      : {
          category: '',
          description: '',
          amount: 0,
          payment_method: 'cash',
          date: '',
          notes: '',
        },
  });

  const isPending = createExpense.isPending || updateExpense.isPending;
  const mutationError = createExpense.error ?? updateExpense.error;

  const onSubmit = (values: ExpenseSchemaValues) => {
    const payload: ExpensePayload = {
      category: values.category,
      description: values.description,
      amount: Math.round(values.amount * 100),
      payment_method: values.payment_method,
      date: values.date || undefined,
      notes: values.notes || undefined,
    };

    if (editing) {
      updateExpense.mutate({ id: editing.id, data: payload }, { onSuccess: onClose });
    } else {
      createExpense.mutate(payload, { onSuccess: onClose });
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 p-6 max-h-[90vh] overflow-y-auto">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          {editing ? 'Edit Expense' : 'Record Expense'}
        </h2>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          {/* Category */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              {...register('category')}
              placeholder="e.g. Rent, Utilities, Salary"
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.category && (
              <p className="mt-1 text-xs text-red-600">{errors.category.message}</p>
            )}
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              {...register('description')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.description && (
              <p className="mt-1 text-xs text-red-600">{errors.description.message}</p>
            )}
          </div>

          {/* Amount */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Amount (৳) <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              min={0}
              step="0.01"
              {...register('amount', { valueAsNumber: true })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.amount && (
              <p className="mt-1 text-xs text-red-600">{errors.amount.message}</p>
            )}
          </div>

          {/* Payment Method */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Payment Method
            </label>
            <select
              {...register('payment_method')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="cash">Cash</option>
              <option value="card">Card</option>
              <option value="mobile">Mobile</option>
              <option value="credit">Credit</option>
            </select>
          </div>

          {/* Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Date <span className="text-gray-400 font-normal">(optional — defaults to today)</span>
            </label>
            <input
              type="date"
              {...register('date')}
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
              {isPending ? 'Saving...' : editing ? 'Save Changes' : 'Record Expense'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export function ExpensesPage() {
  const [page, setPage] = useState(1);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [category, setCategory] = useState('');
  const [appliedStartDate, setAppliedStartDate] = useState('');
  const [appliedEndDate, setAppliedEndDate] = useState('');
  const [appliedCategory, setAppliedCategory] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Expense | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const user = useAuthStore((state) => state.user);
  const canManage = user?.role === 'admin' || user?.role === 'manager';
  const isAdmin = user?.role === 'admin';

  const { data, isLoading, isError, error } = useExpenses({
    page,
    limit: 20,
    start_date: appliedStartDate || undefined,
    end_date: appliedEndDate || undefined,
    category: appliedCategory || undefined,
  });

  const deleteExpense = useDeleteExpense();

  function applyFilters() {
    setPage(1);
    setAppliedStartDate(startDate);
    setAppliedEndDate(endDate);
    setAppliedCategory(category);
  }

  function resetFilters() {
    setStartDate('');
    setEndDate('');
    setCategory('');
    setPage(1);
    setAppliedStartDate('');
    setAppliedEndDate('');
    setAppliedCategory('');
  }

  function handleNew() {
    setEditing(null);
    setModalOpen(true);
  }

  function handleEdit(expense: Expense) {
    setEditing(expense);
    setModalOpen(true);
  }

  function handleClose() {
    setModalOpen(false);
    setEditing(null);
  }

  function handleDelete(id: string) {
    if (!window.confirm('Delete this expense?')) return;
    setDeleteError(null);
    deleteExpense.mutate(id, {
      onError: (err) => setDeleteError(err.message),
    });
  }

  if (isLoading) return <LoadingSkeleton />;
  if (isError)
    return (
      <ErrorDisplay
        message={error instanceof Error ? error.message : 'Failed to load expenses'}
      />
    );

  const expenses = data?.data ?? [];
  const pagination = data?.pagination;

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Expenses</h1>
        {canManage && (
          <button
            onClick={handleNew}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
          >
            <Plus size={16} />
            Record Expense
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
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
        />
        <input
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
        />
        <input
          type="text"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && applyFilters()}
          placeholder="Category..."
          className="border border-gray-300 rounded px-3 py-1.5 text-sm w-40"
        />
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
      {expenses.length === 0 ? (
        <p className="text-gray-500 py-12 text-center">No expenses found.</p>
      ) : (
        <div className="overflow-x-auto rounded border border-gray-200">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
              <tr>
                {['Date', 'Category', 'Description', 'Amount', 'Payment Method', 'Actions'].map(
                  (h) => (
                    <th key={h} className="px-4 py-3 text-left font-medium">
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {expenses.map((expense) => (
                <tr key={expense.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-600 whitespace-nowrap">{expense.date}</td>
                  <td className="px-4 py-3 font-medium text-gray-900">{expense.category}</td>
                  <td className="px-4 py-3 text-gray-700">{expense.description}</td>
                  <td className="px-4 py-3 font-mono text-gray-900">
                    ৳{(expense.amount / 100).toFixed(2)}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        PAYMENT_BADGE[expense.payment_method] ?? 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {expense.payment_method}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {canManage && (
                        <button
                          onClick={() => handleEdit(expense)}
                          className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded"
                          title="Edit"
                        >
                          <Pencil size={15} />
                        </button>
                      )}
                      {isAdmin && (
                        <button
                          onClick={() => handleDelete(expense.id)}
                          disabled={deleteExpense.isPending}
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
      {modalOpen && <ExpenseModal editing={editing} onClose={handleClose} />}
    </div>
  );
}
