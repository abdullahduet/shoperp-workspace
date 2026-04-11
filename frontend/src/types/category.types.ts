export interface Category {
  id: string;
  name: string;
  description: string | null;
  parent_id: string | null;
  sort_order: number;
  created_at: string;
}

export interface CategoryTreeNode {
  id: string;
  name: string;
  description: string | null;
  sort_order: number;
  children: CategoryTreeNode[];
}

export interface CategoryFormValues {
  name: string;
  description: string;
  parent_id: string;
  sort_order: number;
}
