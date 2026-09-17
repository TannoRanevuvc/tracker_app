export type MealType = "breakfast" | "lunch" | "dinner" | "snack";

export interface Product {
  id: string;
  user_id: string | null;
  external_id: string | null;
  name: string;
  kcal_per_100g: number;
  protein_g_per_100g: number;
  fat_g_per_100g: number;
  carbs_g_per_100g: number;
  created_at: string;
}

export interface MealEntry {
  id: string;
  user_id: string;
  product_id: string;
  quantity_g: number;
  meal_type: MealType;
  logged_at: string;
  price_kopecks: number | null;
  kcal: number;
  protein_g: number;
  fat_g: number;
  carbs_g: number;
}

export interface DailyGoal {
  id: string;
  user_id: string;
  kcal_goal: number;
  protein_goal_g: number | null;
  fat_goal_g: number | null;
  carbs_goal_g: number | null;
  effective_from: string;
}

export interface Summary {
  kcal_total: number;
  protein_total: number;
  fat_total: number;
  carbs_total: number;
  kcal_goal: number | null;
  goal_reached: boolean;
}

export interface ProductCreatePayload {
  name: string;
  kcal_per_100g: number;
  protein_g_per_100g: number;
  fat_g_per_100g: number;
  carbs_g_per_100g: number;
}

export interface MealEntryCreatePayload {
  product_id: string;
  quantity_g: number;
  meal_type: MealType;
  logged_at?: string;
  price_kopecks?: number;
}

export interface GoalCreatePayload {
  kcal_goal: number;
  protein_goal_g?: number;
  fat_goal_g?: number;
  carbs_goal_g?: number;
  effective_from: string;
}

export const MEAL_TYPE_LABELS: Record<MealType, string> = {
  breakfast: "Завтрак",
  lunch: "Обед",
  dinner: "Ужин",
  snack: "Перекус",
};

export const MEAL_TYPES: MealType[] = ["breakfast", "lunch", "dinner", "snack"];

export interface ExternalProductPreview {
  external_id: string;
  name: string;
  kcal_per_100g: number;
  protein_g_per_100g: number;
  fat_g_per_100g: number;
  carbs_g_per_100g: number;
}

export interface ImportExternalPayload {
  external_id: string;
}
