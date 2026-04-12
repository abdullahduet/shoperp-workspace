export interface DashboardSummary {
  today_sales: number;
  today_transactions: number;
  month_revenue: number;
  month_profit: number;
  low_stock_count: number;
}

export interface TrendItem {
  month: string;
  revenue: number;
  transaction_count: number;
}

export interface Period {
  start: string;
  end: string;
}

export interface SalesReportItem {
  date: string;
  total_amount: number;
  transaction_count: number;
  payment_breakdown: { cash: number; card: number; mobile: number; credit: number };
}

export interface SalesReport {
  period: Period;
  items: SalesReportItem[];
  totals: { total_amount: number; transaction_count: number };
}

export interface ProfitLossReport {
  period: Period;
  revenue: number;
  cogs: number;
  gross_profit: number;
  expenses: number;
  net_profit: number;
}

export interface TopProductItem {
  product_id: string;
  name: string;
  sku: string;
  total_quantity: number;
  total_revenue: number;
}

export interface TopProductsReport {
  period: Period;
  items: TopProductItem[];
}

export interface LowStockItem {
  id: string;
  name: string;
  sku: string;
  stock_quantity: number;
  min_stock_level: number;
}

export interface PurchasesReportItem {
  date: string;
  total_amount: number;
  order_count: number;
}

export interface PurchasesReport {
  period: Period;
  items: PurchasesReportItem[];
  totals: { total_amount: number; order_count: number };
}

export interface ExpenseCategoryItem {
  category: string;
  total_amount: number;
  count: number;
}

export interface ExpensesReport {
  period: Period;
  items: ExpenseCategoryItem[];
  totals: { total_amount: number };
}

export interface InventoryValuationItem {
  product_id: string;
  name: string;
  sku: string;
  stock_quantity: number;
  cost_price: number;
  value: number;
}

export interface InventoryValuationReport {
  total_value: number;
  product_count: number;
  currency: string;
  items: InventoryValuationItem[];
}
