import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { accountingService } from '../services/accounting.service';
import type { JournalEntryPayload, ExpensePayload } from '../types/accounting.types';

export function useSeedAccounts() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => accountingService.seedAccounts(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    },
  });
}

export function useAccounts() {
  return useQuery({
    queryKey: ['accounts'],
    queryFn: () => accountingService.listAccounts(),
  });
}

export function useJournalEntries(filters: Record<string, unknown> = {}) {
  return useQuery({
    queryKey: ['journal-entries', filters],
    queryFn: () => accountingService.listJournalEntries(filters),
  });
}

export function useCreateJournalEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: JournalEntryPayload) => accountingService.createJournalEntry(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journal-entries'] });
    },
  });
}

export function useExpenses(filters: Record<string, unknown> = {}) {
  return useQuery({
    queryKey: ['expenses', filters],
    queryFn: () => accountingService.listExpenses(filters),
  });
}

export function useCreateExpense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ExpensePayload) => accountingService.createExpense(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] });
    },
  });
}

export function useUpdateExpense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ExpensePayload> }) =>
      accountingService.updateExpense(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] });
    },
  });
}

export function useDeleteExpense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => accountingService.deleteExpense(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] });
    },
  });
}
