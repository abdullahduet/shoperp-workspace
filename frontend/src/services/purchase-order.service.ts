import apiClient from '../api/client';
import type { PurchaseOrder } from '../types/purchase-order.types';
import type { Pagination } from '../types/product.types';

export interface POCreatePayload {
  supplier_id: string;
  expected_date?: string;
  notes?: string;
  items: Array<{ product_id: string; quantity: number; unit_cost: number }>;
}

export interface POUpdatePayload {
  expected_date?: string;
  notes?: string;
  items?: Array<{ product_id: string; quantity: number; unit_cost: number }>;
}

export const purchaseOrderService = {
  list: async (params: {
    page?: number;
    limit?: number;
    supplier_id?: string;
    status?: string;
  }): Promise<{ data: PurchaseOrder[]; pagination: Pagination }> => {
    const res = await apiClient.get('/purchase-orders', { params });
    return { data: res.data.data, pagination: res.data.pagination };
  },

  getById: async (id: string): Promise<PurchaseOrder> => {
    const res = await apiClient.get(`/purchase-orders/${id}`);
    return res.data.data;
  },

  create: async (data: POCreatePayload): Promise<PurchaseOrder> => {
    const res = await apiClient.post('/purchase-orders', data);
    return res.data.data;
  },

  update: async (id: string, data: POUpdatePayload): Promise<PurchaseOrder> => {
    const res = await apiClient.put(`/purchase-orders/${id}`, data);
    return res.data.data;
  },

  remove: async (id: string): Promise<void> => {
    await apiClient.delete(`/purchase-orders/${id}`);
  },

  submit: async (id: string): Promise<PurchaseOrder> => {
    const res = await apiClient.post(`/purchase-orders/${id}/submit`);
    return res.data.data;
  },

  receive: async (
    id: string,
    items: Array<{ item_id: string; received_quantity: number }>,
  ): Promise<PurchaseOrder> => {
    const res = await apiClient.post(`/purchase-orders/${id}/receive`, { items });
    return res.data.data;
  },

  cancel: async (id: string): Promise<PurchaseOrder> => {
    const res = await apiClient.post(`/purchase-orders/${id}/cancel`);
    return res.data.data;
  },
};
