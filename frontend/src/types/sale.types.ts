export interface SaleItem {
  id: string;
  product_id: string;
  quantity: number;
  unit_price: number;
  discount: number;
  total_price: number;
  created_at: string;
}

export interface Sale {
  id: string;
  sale_number: string;
  sale_date: string;
  customer_name: string | null;
  subtotal: number;
  discount_amount: number;
  tax_amount: number;
  total_amount: number;
  payment_method: string;
  promotion_id: string | null;
  notes: string | null;
  recorded_by: string | null;
  items: SaleItem[];
  created_at: string;
}

export interface DailySummary {
  date: string;
  total_sales: number;
  transaction_count: number;
  payment_breakdown: {
    cash: number;
    card: number;
    mobile: number;
    credit: number;
  };
}

export interface SaleFilters {
  start_date?: string;
  end_date?: string;
  payment_method?: string;
}

export interface SalePayload {
  items: Array<{ product_id: string; quantity: number; unit_price: number }>;
  payment_method?: string;
  customer_name?: string;
  notes?: string;
}
