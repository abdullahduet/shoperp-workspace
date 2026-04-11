import apiClient from '../api/client';
import type { Sale, DailySummary, SalePayload } from '../types/sale.types';
import type { Pagination } from '../types/product.types';

export const saleService = {
  list: async (params: {
    page?: number;
    limit?: number;
    start_date?: string;
    end_date?: string;
    payment_method?: string;
  }): Promise<{ data: Sale[]; pagination: Pagination }> => {
    const res = await apiClient.get('/sales', { params });
    return { data: res.data.data, pagination: res.data.pagination };
  },

  getById: async (id: string): Promise<Sale> => {
    const res = await apiClient.get(`/sales/${id}`);
    return res.data.data;
  },

  getDailySummary: async (): Promise<DailySummary> => {
    const res = await apiClient.get('/sales/daily-summary');
    return res.data.data;
  },

  create: async (data: SalePayload): Promise<Sale> => {
    const res = await apiClient.post('/sales', data);
    return res.data.data;
  },
};
