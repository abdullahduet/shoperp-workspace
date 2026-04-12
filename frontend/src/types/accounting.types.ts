export interface Account {
  id: string;
  code: string;
  name: string;
  type: string;
  parent_id: string | null;
  is_active: boolean;
  created_at: string;
}

export interface JournalEntryLine {
  id: string;
  account_id: string;
  debit_amount: number;
  credit_amount: number;
  description: string | null;
}

export interface JournalEntry {
  id: string;
  entry_number: string;
  date: string;
  description: string;
  reference_type: string | null;
  reference_id: string | null;
  created_by: string | null;
  lines: JournalEntryLine[];
  created_at: string;
}

export interface Expense {
  id: string;
  date: string;
  category: string;
  description: string;
  amount: number;
  payment_method: string;
  receipt_url: string | null;
  notes: string | null;
  recorded_by: string | null;
  created_at: string;
}

export interface JournalEntryLineFormValues {
  account_id: string;
  debit_amount: number;
  credit_amount: number;
  description: string;
}

export interface JournalEntryPayload {
  description: string;
  date?: string;
  lines: Array<{
    account_id: string;
    debit_amount: number;
    credit_amount: number;
    description?: string;
  }>;
}

export interface ExpensePayload {
  category: string;
  description: string;
  amount: number; // paisa
  payment_method?: string;
  date?: string;
  notes?: string;
}
