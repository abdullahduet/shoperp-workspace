import apiClient from '../api/client';
import type { Supplier, SupplierFormValues } from '../types/supplier.types';
import type { Pagination } from '../types/product.types';

export const supplierService = {
  list: async (params: {
    page?: number;
    limit?: number;
    search?: string;
    is_active?: boolean;
  }): Promise<{ data: Supplier[]; pagination: Pagination }> => {
    const res = await apiClient.get('/suppliers', { params });
    return { data: res.data.data, pagination: res.data.pagination };
  },

  getById: async (id: string): Promise<Supplier> => {
    const res = await apiClient.get(`/suppliers/${id}`);
    return res.data.data;
  },

  create: async (data: SupplierFormValues): Promise<Supplier> => {
    const res = await apiClient.post('/suppliers', data);
    return res.data.data;
  },

  update: async (id: string, data: Partial<SupplierFormValues>): Promise<Supplier> => {
    const res = await apiClient.put(`/suppliers/${id}`, data);
    return res.data.data;
  },

  remove: async (id: string): Promise<void> => {
    await apiClient.delete(`/suppliers/${id}`);
  },
};
