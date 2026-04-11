export interface StockMovement {
  id: string;
  product_id: string;
  product_name: string;
  product_sku: string;
  movement_type: 'in' | 'out' | 'adjustment';
  quantity: number;
  stock_before: number;
  stock_after: number;
  reference_type: string | null;
  reference_id: string | null;
  notes: string | null;
  performed_by: string | null;
  created_at: string;
}

export interface ValuationData {
  total_value: number;
  product_count: number;
  currency: string;
}

export interface AdjustmentFormValues {
  product_id: string;
  quantity: number;
  notes?: string;
}

export interface MovementFilters {
  product_id?: string;
  movement_type?: 'in' | 'out' | 'adjustment';
  start_date?: string;
  end_date?: string;
}
