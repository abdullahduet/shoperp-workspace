import apiClient from '../api/client';
import type { EligiblePromotion, Promotion, PromotionPayload } from '../types/promotion.types';
import type { Pagination } from '../types/product.types';

export const promotionService = {
  list: async (params: {
    page?: number;
    limit?: number;
    is_active?: boolean;
    type?: string;
  }): Promise<{ data: Promotion[]; pagination: Pagination }> => {
    const res = await apiClient.get('/promotions', { params });
    return { data: res.data.data, pagination: res.data.pagination };
  },

  getActive: async (): Promise<Promotion[]> => {
    const res = await apiClient.get('/promotions/active');
    return res.data.data;
  },

  getEligible: async (
    subtotal: number,
    items: Array<{ product_id: string; quantity: number; unit_price: number }>,
  ): Promise<EligiblePromotion[]> => {
    const res = await apiClient.get('/promotions/eligible', {
      params: { subtotal, items: JSON.stringify(items) },
    });
    return res.data.data;
  },

  getById: async (id: string): Promise<Promotion> => {
    const res = await apiClient.get(`/promotions/${id}`);
    return res.data.data;
  },

  create: async (data: PromotionPayload): Promise<Promotion> => {
    const res = await apiClient.post('/promotions', data);
    return res.data.data;
  },

  update: async (id: string, data: Partial<PromotionPayload>): Promise<Promotion> => {
    const res = await apiClient.put(`/promotions/${id}`, data);
    return res.data.data;
  },

  remove: async (id: string): Promise<void> => {
    await apiClient.delete(`/promotions/${id}`);
  },
};
