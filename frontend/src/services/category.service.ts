import apiClient from '../api/client';
import type { Category, CategoryTreeNode, CategoryFormValues } from '../types/category.types';

export const categoryService = {
  list: async (): Promise<Category[]> => {
    const res = await apiClient.get('/categories');
    return res.data.data;
  },
  tree: async (): Promise<CategoryTreeNode[]> => {
    const res = await apiClient.get('/categories/tree');
    return res.data.data;
  },
  create: async (data: Partial<CategoryFormValues>): Promise<Category> => {
    const res = await apiClient.post('/categories', data);
    return res.data.data;
  },
  update: async (id: string, data: Partial<CategoryFormValues>): Promise<Category> => {
    const res = await apiClient.put(`/categories/${id}`, data);
    return res.data.data;
  },
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/categories/${id}`);
  },
};
