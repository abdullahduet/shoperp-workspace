import apiClient from '../api/client';
import type { StockMovement, ValuationData, AdjustmentFormValues, MovementFilters } from '../types/inventory.types';
import type { Pagination } from '../types/product.types';

export const inventoryService = {
  listMovements: async (
    params: MovementFilters & { page?: number; limit?: number },
  ): Promise<{ data: StockMovement[]; pagination: Pagination }> => {
    const res = await apiClient.get('/inventory/movements', { params });
    return { data: res.data.data, pagination: res.data.pagination };
  },
  adjust: async (data: AdjustmentFormValues): Promise<StockMovement> => {
    const res = await apiClient.post('/inventory/adjust', {
      product_id: data.product_id,
      quantity: data.quantity,
      notes: data.notes || undefined,
    });
    return res.data.data;
  },
  getValuation: async (): Promise<ValuationData> => {
    const res = await apiClient.get('/inventory/valuation');
    return res.data.data;
  },
};
