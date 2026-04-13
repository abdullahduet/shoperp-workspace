import { useAccounts, useSeedAccounts } from '../hooks/useAccounting';
import { useAuthStore } from '../store/auth.store';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ErrorDisplay } from '../components/ui/ErrorDisplay';

const ACCOUNT_TYPE_BADGE: Record<string, string> = {
  asset: 'bg-blue-100 text-blue-700',
  liability: 'bg-red-100 text-red-700',
  equity: 'bg-purple-100 text-purple-700',
  revenue: 'bg-green-100 text-green-700',
  expense: 'bg-orange-100 text-orange-700',
};

export function AccountsPage() {
  const { data: accounts, isLoading, isError, error } = useAccounts();
  const seedAccounts = useSeedAccounts();
  const user = useAuthStore((state) => state.user);
  const isAdmin = user?.role === 'admin';
  const isEmpty = !isLoading && !isError && (accounts ?? []).length === 0;

  if (isLoading) return <LoadingSkeleton />;
  if (isError)
    return (
      <ErrorDisplay
        message={error instanceof Error ? error.message : 'Failed to load accounts'}
      />
    );

  const sorted = [...(accounts ?? [])].sort((a, b) => a.code.localeCompare(b.code));

  // Build a map for parent code lookups
  const accountMap = new Map((accounts ?? []).map((a) => [a.id, a]));

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Chart of Accounts</h1>
        {isAdmin && isEmpty && (
          <button
            onClick={() => seedAccounts.mutate()}
            disabled={seedAccounts.isPending}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {seedAccounts.isPending ? 'Seeding…' : 'Seed Default Accounts'}
          </button>
        )}
      </div>

      {seedAccounts.isSuccess && (
        <div className="mb-4 rounded-md bg-green-50 border border-green-200 px-4 py-2 text-sm text-green-700">
          {seedAccounts.data.seeded} default accounts seeded successfully.
        </div>
      )}
      {seedAccounts.isError && (
        <div className="mb-4 rounded-md bg-red-50 border border-red-200 px-4 py-2 text-sm text-red-700">
          {seedAccounts.error instanceof Error ? seedAccounts.error.message : 'Seeding failed'}
        </div>
      )}

      {sorted.length === 0 ? (
        <p className="text-gray-500 py-12 text-center">No accounts found.</p>
      ) : (
        <div className="overflow-x-auto rounded border border-gray-200">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
              <tr>
                {['Code', 'Name', 'Type', 'Parent', 'Active'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sorted.map((account) => {
                const parent = account.parent_id ? accountMap.get(account.parent_id) : null;
                return (
                  <tr key={account.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-gray-900">{account.code}</td>
                    <td className="px-4 py-3 font-medium text-gray-900">{account.name}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                          ACCOUNT_TYPE_BADGE[account.type] ?? 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {account.type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600 font-mono">
                      {parent ? parent.code : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                          account.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {account.is_active ? 'Yes' : 'No'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
