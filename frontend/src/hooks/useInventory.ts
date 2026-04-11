import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { inventoryService } from '../services/inventory.service';
import type { AdjustmentFormValues, MovementFilters } from '../types/inventory.types';

export function useMovements(filters: MovementFilters & { page?: number; limit?: number } = {}) {
  return useQuery({
    queryKey: ['inventory', 'movements', filters],
    queryFn: () => inventoryService.listMovements(filters),
  });
}

export function useValuation() {
  return useQuery({
    queryKey: ['inventory', 'valuation'],
    queryFn: inventoryService.getValuation,
  });
}

export function useAdjust() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: AdjustmentFormValues) => inventoryService.adjust(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory', 'movements'] });
    },
  });
}
