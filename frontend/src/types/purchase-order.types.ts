export type POStatus =
  | 'draft'
  | 'ordered'
  | 'partially_received'
  | 'received'
  | 'cancelled';

export interface POItem {
  id: string;
  purchase_order_id: string;
  product_id: string;
  product_name: string;
  product_sku: string;
  quantity: number;
  received_quantity: number;
  unit_cost: number; // paisa integer
  total_cost: number; // paisa integer
}

export interface PurchaseOrder {
  id: string;
  po_number: string;
  supplier_id: string;
  supplier_name: string;
  order_date: string;
  expected_date: string | null;
  status: POStatus;
  subtotal: number; // paisa integer
  tax_amount: number; // paisa integer
  total_amount: number; // paisa integer
  notes: string | null;
  created_by: string | null;
  created_at: string;
  items: POItem[];
}

export interface POItemFormValues {
  product_id: string;
  quantity: number;
  unit_cost: number; // display ৳ value (will be converted to paisa on submit)
}

export interface POCreateFormValues {
  supplier_id: string;
  expected_date?: string;
  notes?: string;
  items: POItemFormValues[];
}

export interface POFilters {
  supplier_id?: string;
  status?: string;
}
