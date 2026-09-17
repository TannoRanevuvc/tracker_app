export interface Account {
  id: string;
  user_id: string;
  name: string;
  balance_kopecks: number;
  created_at: string;
}

export interface Category {
  id: string;
  user_id: string;
  name: string;
  type: "income" | "expense";
}

export interface Transaction {
  id: string;
  user_id: string;
  account_id: string;
  category_id: string | null;
  amount_kopecks: number;
  occurred_at: string;
  description: string | null;
  recurring_rule_id: string | null;
  source: "manual" | "recurring" | "food_module";
  created_at: string;
}

export interface RecurringRule {
  id: string;
  user_id: string;
  account_id: string;
  category_id: string | null;
  amount_kopecks: number;
  description: string | null;
  frequency: "monthly" | "weekly";
  day_of_month: number | null;
  day_of_week: number | null;
  next_due_date: string;
  active: boolean;
}

export interface Budget {
  id: string;
  user_id: string;
  category_id: string;
  period: string;
  limit_kopecks: number;
}

export interface SummaryByCategoryItem {
  category_id: string | null;
  category_name: string | null;
  amount_kopecks: number;
}

export interface Summary {
  by_category: SummaryByCategoryItem[];
  total_income: number;
  total_expense: number;
}

export interface AccountCreatePayload {
  name: string;
}

export interface AccountUpdatePayload {
  name: string;
}

export interface CategoryCreatePayload {
  name: string;
  type: "income" | "expense";
}

export interface TransactionCreatePayload {
  account_id: string;
  amount_kopecks: number;
  category_id?: string;
  occurred_at: string;
  description?: string;
}

export interface RecurringRuleCreatePayload {
  account_id: string;
  amount_kopecks: number;
  category_id?: string;
  description?: string;
  frequency: "monthly" | "weekly";
  day_of_month?: number;
  day_of_week?: number;
  next_due_date?: string;
}

export interface RecurringRuleUpdatePayload {
  active?: boolean;
  amount_kopecks?: number;
}

export interface BudgetCreatePayload {
  category_id: string;
  period: string;
  limit_kopecks: number;
}

export function formatRub(kopecks: number, showSign = true): string {
  const abs = (Math.abs(kopecks) / 100).toLocaleString("ru-RU", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
  if (!showSign) return `${abs} ₽`;
  const sign = kopecks < 0 ? "−" : kopecks > 0 ? "+" : "";
  return `${sign}${abs} ₽`;
}

export function currentPeriod(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

export function currentMonthRange(): { from: string; to: string } {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();
  const mm = String(month + 1).padStart(2, "0");
  const lastDay = new Date(year, month + 1, 0).getDate();
  return {
    from: `${year}-${mm}-01`,
    to: `${year}-${mm}-${String(lastDay).padStart(2, "0")}`,
  };
}
