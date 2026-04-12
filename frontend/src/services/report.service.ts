import apiClient from '../api/client';
import type {
  DashboardSummary,
  TrendItem,
  SalesReport,
  ProfitLossReport,
  TopProductsReport,
  LowStockItem,
  PurchasesReport,
  ExpensesReport,
  InventoryValuationReport,
} from '../types/report.types';

interface DateParams {
  start_date?: string;
  end_date?: string;
}

export const reportService = {
  getDashboardSummary: async (): Promise<DashboardSummary> => {
    const res = await apiClient.get('/dashboard/summary');
    return res.data.data;
  },

  getDashboardTrends: async (): Promise<TrendItem[]> => {
    const res = await apiClient.get('/dashboard/trends');
    return res.data.data;
  },

  getSalesReport: async (params: DateParams): Promise<SalesReport> => {
    const res = await apiClient.get('/reports/sales', { params });
    return res.data.data;
  },

  getProfitLoss: async (params: DateParams): Promise<ProfitLossReport> => {
    const res = await apiClient.get('/reports/profit-loss', { params });
    return res.data.data;
  },

  getTopProducts: async (params: DateParams & { limit?: number }): Promise<TopProductsReport> => {
    const res = await apiClient.get('/reports/top-products', { params });
    return res.data.data;
  },

  getLowStock: async (): Promise<LowStockItem[]> => {
    const res = await apiClient.get('/reports/low-stock');
    return res.data.data;
  },

  getPurchasesReport: async (params: DateParams): Promise<PurchasesReport> => {
    const res = await apiClient.get('/reports/purchases', { params });
    return res.data.data;
  },

  getExpensesReport: async (params: DateParams): Promise<ExpensesReport> => {
    const res = await apiClient.get('/reports/expenses', { params });
    return res.data.data;
  },

  getInventoryValuation: async (): Promise<InventoryValuationReport> => {
    const res = await apiClient.get('/reports/inventory-valuation');
    return res.data.data;
  },

  downloadCsv: async (
    path: string,
    params: Record<string, string | number | undefined>,
  ): Promise<void> => {
    const res = await apiClient.get(path, {
      params: { ...params, format: 'csv' },
      responseType: 'blob',
    });
    const url = URL.createObjectURL(
      new Blob([res.data as BlobPart], { type: 'text/csv' }),
    );
    const a = document.createElement('a');
    a.href = url;
    a.download = `${path.split('/').pop() ?? 'report'}-report.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },
};
