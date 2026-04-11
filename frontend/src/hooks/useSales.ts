import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { saleService } from '../services/sale.service';
import type { SalePayload, SaleFilters } from '../types/sale.types';

export function useSales(filters: SaleFilters & { page?: number; limit?: number } = {}) {
  return useQuery({
    queryKey: ['sales', filters],
    queryFn: () => saleService.list(filters),
  });
}

export function useSale(id?: string) {
  return useQuery({
    queryKey: ['sales', id],
    queryFn: () => saleService.getById(id!),
    enabled: !!id,
  });
}

export function useDailySummary(enabled = true) {
  return useQuery({
    queryKey: ['sales', 'daily-summary'],
    queryFn: () => saleService.getDailySummary(),
    enabled,
  });
}

export function useRecordSale() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SalePayload) => saleService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sales'] });
    },
  });
}
