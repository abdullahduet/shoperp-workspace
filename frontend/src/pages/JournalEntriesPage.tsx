import { useState } from 'react';
import { useForm, useFieldArray, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Plus, Trash2 } from 'lucide-react';
import {
  useJournalEntries,
  useCreateJournalEntry,
  useAccounts,
} from '../hooks/useAccounting';
import { useAuthStore } from '../store/auth.store';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ErrorDisplay } from '../components/ui/ErrorDisplay';
import type { Account, JournalEntryPayload } from '../types/accounting.types';

// ─── Helpers ─────────────────────────────────────────────────────────────────

const REF_BADGE: Record<string, string> = {
  sale: 'bg-green-100 text-green-700',
  expense: 'bg-red-100 text-red-700',
  purchase_order: 'bg-blue-100 text-blue-700',
  manual: 'bg-gray-100 text-gray-600',
};

// ─── Zod schema ──────────────────────────────────────────────────────────────

const lineSchema = z.object({
  account_id: z.string().min(1, 'Select an account'),
  debit_amount: z.number().min(0).default(0),
  credit_amount: z.number().min(0).default(0),
  description: z.string().optional().default(''),
});

const journalEntrySchema = z.object({
  description: z.string().min(1, 'Description required'),
  date: z.string().optional().default(''),
  lines: z.array(lineSchema).min(2, 'At least 2 lines required'),
});

type JournalEntrySchemaValues = z.infer<typeof journalEntrySchema>;

// ─── Modal ───────────────────────────────────────────────────────────────────

interface JournalEntryModalProps {
  accounts: Account[];
  onClose: () => void;
}

function JournalEntryModal({ accounts, onClose }: JournalEntryModalProps) {
  const createJournalEntry = useCreateJournalEntry();

  const {
    register,
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<JournalEntrySchemaValues>({
    resolver: zodResolver(journalEntrySchema),
    defaultValues: {
      description: '',
      date: '',
      lines: [
        { account_id: '', debit_amount: 0, credit_amount: 0, description: '' },
        { account_id: '', debit_amount: 0, credit_amount: 0, description: '' },
      ],
    },
  });

  const { fields, append, remove } = useFieldArray({ control, name: 'lines' });

  const watchedLines = useWatch({ control, name: 'lines' });
  const totalDebit = (watchedLines ?? []).reduce(
    (s, l) => s + (Number(l.debit_amount) || 0),
    0,
  );
  const totalCredit = (watchedLines ?? []).reduce(
    (s, l) => s + (Number(l.credit_amount) || 0),
    0,
  );
  const isBalanced = totalDebit > 0 && totalDebit === totalCredit;

  const isPending = createJournalEntry.isPending;
  const mutationError = createJournalEntry.error;

  const onSubmit = (values: JournalEntrySchemaValues) => {
    const payload: JournalEntryPayload = {
      description: values.description,
      date: values.date || undefined,
      lines: values.lines.map((line) => ({
        account_id: line.account_id,
        debit_amount: Math.round(line.debit_amount * 100),
        credit_amount: Math.round(line.credit_amount * 100),
        description: line.description || undefined,
      })),
    };
    createJournalEntry.mutate(payload, { onSuccess: onClose });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl mx-4 p-6 max-h-[90vh] overflow-y-auto">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">New Journal Entry</h2>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
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

          {/* Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Date <span className="text-gray-400 font-normal">(optional — defaults to today)</span>
            </label>
            <input
              type="date"
              {...register('date')}
              className="w-full max-w-xs px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Lines */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-gray-900">Lines</h3>
              <button
                type="button"
                onClick={() =>
                  append({ account_id: '', debit_amount: 0, credit_amount: 0, description: '' })
                }
                className="flex items-center gap-1.5 px-3 py-1.5 border border-gray-300 text-sm text-gray-700 rounded-md hover:bg-gray-50"
              >
                <Plus size={14} />
                Add Line
              </button>
            </div>

            {errors.lines && !Array.isArray(errors.lines) && (
              <p className="mb-2 text-xs text-red-600">{errors.lines.message}</p>
            )}

            {/* Column headers */}
            <div className="grid grid-cols-12 gap-2 text-xs font-medium text-gray-500 uppercase mb-2 px-1">
              <span className="col-span-4">Account</span>
              <span className="col-span-2">Debit (৳)</span>
              <span className="col-span-2">Credit (৳)</span>
              <span className="col-span-3">Note</span>
              <span className="col-span-1"></span>
            </div>

            <div className="space-y-2">
              {fields.map((field, index) => (
                <div key={field.id} className="grid grid-cols-12 gap-2 items-start">
                  {/* Account */}
                  <div className="col-span-4">
                    <select
                      {...register(`lines.${index}.account_id`)}
                      className="w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select account…</option>
                      {accounts.map((account) => (
                        <option key={account.id} value={account.id}>
                          {account.code} — {account.name}
                        </option>
                      ))}
                    </select>
                    {errors.lines?.[index]?.account_id && (
                      <p className="mt-0.5 text-xs text-red-600">
                        {errors.lines[index]?.account_id?.message}
                      </p>
                    )}
                  </div>

                  {/* Debit */}
                  <div className="col-span-2">
                    <input
                      type="number"
                      min={0}
                      step="0.01"
                      {...register(`lines.${index}.debit_amount`, { valueAsNumber: true })}
                      className="w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  {/* Credit */}
                  <div className="col-span-2">
                    <input
                      type="number"
                      min={0}
                      step="0.01"
                      {...register(`lines.${index}.credit_amount`, { valueAsNumber: true })}
                      className="w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  {/* Note */}
                  <div className="col-span-3">
                    <input
                      type="text"
                      {...register(`lines.${index}.description`)}
                      placeholder="Optional note"
                      className="w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  {/* Remove */}
                  <div className="col-span-1 flex justify-center">
                    <button
                      type="button"
                      onClick={() => remove(index)}
                      disabled={fields.length <= 2}
                      className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded disabled:opacity-30 disabled:cursor-not-allowed mt-1"
                      title="Remove line"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Balance display */}
            <div className="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between">
              <span className="text-sm text-gray-600">
                Debit Total:{' '}
                <span className="font-mono font-medium">৳{totalDebit.toFixed(2)}</span>
                {' | '}
                Credit Total:{' '}
                <span className="font-mono font-medium">৳{totalCredit.toFixed(2)}</span>
              </span>
              {isBalanced ? (
                <span className="text-sm font-medium text-green-600">Balanced</span>
              ) : (
                <span className="text-sm font-medium text-red-600">Unbalanced</span>
              )}
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
              {isPending ? 'Saving...' : 'Create Entry'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export function JournalEntriesPage() {
  const [page, setPage] = useState(1);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [referenceType, setReferenceType] = useState('');
  const [appliedStartDate, setAppliedStartDate] = useState('');
  const [appliedEndDate, setAppliedEndDate] = useState('');
  const [appliedReferenceType, setAppliedReferenceType] = useState('');
  const [modalOpen, setModalOpen] = useState(false);

  const user = useAuthStore((state) => state.user);
  const isAdmin = user?.role === 'admin';

  const { data, isLoading, isError, error } = useJournalEntries({
    page,
    limit: 20,
    start_date: appliedStartDate || undefined,
    end_date: appliedEndDate || undefined,
    reference_type: appliedReferenceType || undefined,
  });

  const { data: accounts = [] } = useAccounts();

  function applyFilters() {
    setPage(1);
    setAppliedStartDate(startDate);
    setAppliedEndDate(endDate);
    setAppliedReferenceType(referenceType);
  }

  function resetFilters() {
    setStartDate('');
    setEndDate('');
    setReferenceType('');
    setPage(1);
    setAppliedStartDate('');
    setAppliedEndDate('');
    setAppliedReferenceType('');
  }

  function handleClose() {
    setModalOpen(false);
  }

  if (isLoading) return <LoadingSkeleton />;
  if (isError)
    return (
      <ErrorDisplay
        message={error instanceof Error ? error.message : 'Failed to load journal entries'}
      />
    );

  const entries = data?.data ?? [];
  const pagination = data?.pagination;

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Journal Entries</h1>
        {isAdmin && (
          <button
            onClick={() => setModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
          >
            <Plus size={16} />
            New Entry
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <input
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
          placeholder="Start date"
        />
        <input
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
          placeholder="End date"
        />
        <select
          value={referenceType}
          onChange={(e) => setReferenceType(e.target.value)}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm"
        >
          <option value="">All Types</option>
          <option value="sale">Sale</option>
          <option value="expense">Expense</option>
          <option value="purchase_order">Purchase Order</option>
          <option value="manual">Manual</option>
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
      {entries.length === 0 ? (
        <p className="text-gray-500 py-12 text-center">No journal entries found.</p>
      ) : (
        <div className="overflow-x-auto rounded border border-gray-200">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
              <tr>
                {['Entry #', 'Date', 'Description', 'Reference Type', 'Lines', 'Created'].map(
                  (h) => (
                    <th key={h} className="px-4 py-3 text-left font-medium">
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {entries.map((entry) => (
                <tr key={entry.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-gray-900">{entry.entry_number}</td>
                  <td className="px-4 py-3 text-gray-600 whitespace-nowrap">{entry.date}</td>
                  <td className="px-4 py-3 text-gray-700">{entry.description}</td>
                  <td className="px-4 py-3">
                    {entry.reference_type ? (
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                          REF_BADGE[entry.reference_type] ?? 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {entry.reference_type.replace('_', ' ')}
                      </span>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {entry.lines.length} {entry.lines.length === 1 ? 'line' : 'lines'}
                  </td>
                  <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                    {new Date(entry.created_at).toLocaleDateString()}
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
      {modalOpen && <JournalEntryModal accounts={accounts} onClose={handleClose} />}
    </div>
  );
}
