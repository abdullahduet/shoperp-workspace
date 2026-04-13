import apiClient from '../api/client';
import type {
  Account,
  JournalEntry,
  Expense,
  JournalEntryPayload,
  ExpensePayload,
} from '../types/accounting.types';
import type { Pagination } from '../types/product.types';

export const accountingService = {
  seedAccounts: async (): Promise<{ seeded: number }> => {
    const res = await apiClient.post('/accounting/seed-accounts');
    return res.data.data;
  },

  listAccounts: async (): Promise<Account[]> => {
    const res = await apiClient.get('/accounting/accounts');
    return res.data.data;
  },

  listJournalEntries: async (params: {
    page?: number;
    limit?: number;
    start_date?: string;
    end_date?: string;
    reference_type?: string;
  }): Promise<{ data: JournalEntry[]; pagination: Pagination }> => {
    const res = await apiClient.get('/accounting/journal-entries', { params });
    return { data: res.data.data, pagination: res.data.pagination };
  },

  createJournalEntry: async (data: JournalEntryPayload): Promise<JournalEntry> => {
    const res = await apiClient.post('/accounting/journal-entries', data);
    return res.data.data;
  },

  listExpenses: async (params: {
    page?: number;
    limit?: number;
    start_date?: string;
    end_date?: string;
    category?: string;
  }): Promise<{ data: Expense[]; pagination: Pagination }> => {
    const res = await apiClient.get('/expenses', { params });
    return { data: res.data.data, pagination: res.data.pagination };
  },

  createExpense: async (data: ExpensePayload): Promise<Expense> => {
    const res = await apiClient.post('/expenses', data);
    return res.data.data;
  },

  updateExpense: async (id: string, data: Partial<ExpensePayload>): Promise<Expense> => {
    const res = await apiClient.put(`/expenses/${id}`, data);
    return res.data.data;
  },

  deleteExpense: async (id: string): Promise<void> => {
    await apiClient.delete(`/expenses/${id}`);
  },
};
