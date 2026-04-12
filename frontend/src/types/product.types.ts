export interface Product {
  id: string;
  name: string;
  sku: string;
  barcode: string | null;
  category_id: string | null;
  description: string | null;
  unit_price: number; // paisa integer
  cost_price: number; // paisa integer
  tax_rate: number; // percentage float
  stock_quantity: number;
  min_stock_level: number;
  unit_of_measure: string;
  image_url: string | null;
  is_active: boolean;
  created_at: string;
}

export interface ProductFormValues {
  name: string;
  sku: string;
  barcode?: string;
  category_id?: string;
  description: string;
  unit_price: number;
  cost_price: number;
  tax_rate: number;
  stock_quantity: number;
  min_stock_level: number;
  unit_of_measure: string;
  image_url?: string;
  is_active: boolean;
}

export interface ImportResult {
  created: number;
  skipped: number;
  errors: Array<{ row: number; sku: string; reason: string }>;
}

export interface ProductFilters {
  search?: string;
  category_id?: string;
  is_active?: boolean;
  sort?: 'name' | 'sku' | 'stock_quantity' | 'unit_price';
  order?: 'asc' | 'desc';
}

export interface Pagination {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}
