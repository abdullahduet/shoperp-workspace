import apiClient from '../api/client';
import type { Promotion, PromotionPayload } from '../types/promotion.types';
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
