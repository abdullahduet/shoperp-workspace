import apiClient from '../api/client';
import type {
  Product,
  ProductFormValues,
  ProductFilters,
  ImportResult,
  Pagination,
} from '../types/product.types';

export const productService = {
  list: async (
    params: ProductFilters & { page?: number; limit?: number },
  ): Promise<{ data: Product[]; pagination: Pagination }> => {
    const res = await apiClient.get('/products', { params });
    return { data: res.data.data, pagination: res.data.pagination };
  },
  lowStock: async (): Promise<Product[]> => {
    const res = await apiClient.get('/products/low-stock');
    return res.data.data;
  },
  getById: async (id: string): Promise<Product> => {
    const res = await apiClient.get(`/products/${id}`);
    return res.data.data;
  },
  create: async (data: Omit<ProductFormValues, 'id'>): Promise<Product> => {
    const res = await apiClient.post('/products', data);
    return res.data.data;
  },
  update: async (id: string, data: Partial<ProductFormValues>): Promise<Product> => {
    const res = await apiClient.put(`/products/${id}`, data);
    return res.data.data;
  },
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/products/${id}`);
  },
  import: async (file: File): Promise<ImportResult> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post('/products/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data.data;
  },
};
