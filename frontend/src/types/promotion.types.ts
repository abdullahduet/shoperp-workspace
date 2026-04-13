export type PromotionType = 'percentage' | 'fixed' | 'bogo';
export type PromotionAppliesTo = 'all' | 'specific';

export interface Promotion {
  id: string;
  name: string;
  type: PromotionType;
  value: number;
  start_date: string;
  end_date: string;
  min_purchase_amount: number;
  applies_to: PromotionAppliesTo;
  is_active: boolean;
  auto_apply: boolean;
  product_ids: string[];
  created_at: string;
}

export interface PromotionFormValues {
  name: string;
  type: PromotionType;
  value: number;
  start_date: string;
  end_date: string;
  min_purchase_amount: number;
  applies_to: PromotionAppliesTo;
  is_active: boolean;
  auto_apply: boolean;
  product_ids: string[];
}

export interface PromotionFilters {
  is_active?: boolean;
  type?: string;
}

export interface PromotionPayload {
  name: string;
  type: PromotionType;
  value: number;
  start_date: string;
  end_date: string;
  min_purchase_amount: number;
  applies_to: PromotionAppliesTo;
  is_active: boolean;
  auto_apply: boolean;
  product_ids: string[];
}

export interface EligiblePromotion {
  id: string;
  name: string;
  type: string;
  value: number;
  discount_amount: number;  // paisa
  auto_apply: boolean;
}
