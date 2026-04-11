import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { promotionService } from '../services/promotion.service';
import type { PromotionPayload } from '../types/promotion.types';

export function usePromotions(
  filters: { page?: number; limit?: number; is_active?: boolean; type?: string } = {},
) {
  return useQuery({
    queryKey: ['promotions', filters],
    queryFn: () => promotionService.list(filters),
  });
}

export function useActivePromotions() {
  return useQuery({
    queryKey: ['promotions', 'active'],
    queryFn: () => promotionService.getActive(),
  });
}

export function usePromotion(id: string) {
  return useQuery({
    queryKey: ['promotions', id],
    queryFn: () => promotionService.getById(id),
    enabled: !!id,
  });
}

export function useCreatePromotion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: PromotionPayload) => promotionService.create(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['promotions'] }),
  });
}

export function useUpdatePromotion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<PromotionPayload> }) =>
      promotionService.update(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['promotions'] }),
  });
}

export function useDeletePromotion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => promotionService.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['promotions'] }),
  });
}
