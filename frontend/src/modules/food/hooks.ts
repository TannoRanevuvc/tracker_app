import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/core/api-client";
import type {
  DailyGoal,
  GoalCreatePayload,
  MealEntry,
  MealEntryCreatePayload,
  Product,
  ProductCreatePayload,
  Summary,
} from "./types";

export function useProducts(q?: string) {
  const qs = q ? `?q=${encodeURIComponent(q)}` : "";
  return useQuery<Product[]>({
    queryKey: ["food", "products", q ?? ""],
    queryFn: () => apiClient.get<Product[]>(`/food/products${qs}`),
  });
}

export function useCreateProduct() {
  const qc = useQueryClient();
  return useMutation<Product, Error, ProductCreatePayload>({
    mutationFn: (payload) => apiClient.post<Product>("/food/products", payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["food", "products"] }),
  });
}

export function useMealEntries(date: string) {
  return useQuery<MealEntry[]>({
    queryKey: ["food", "meal-entries", date],
    queryFn: () => apiClient.get<MealEntry[]>(`/food/meal-entries?date=${date}`),
  });
}

export function useCreateMealEntry() {
  const qc = useQueryClient();
  return useMutation<MealEntry, Error, MealEntryCreatePayload>({
    mutationFn: (payload) => apiClient.post<MealEntry>("/food/meal-entries", payload),
    onSuccess: (_data, variables) => {
      const date = variables.logged_at
        ? variables.logged_at.slice(0, 10)
        : new Date().toISOString().slice(0, 10);
      qc.invalidateQueries({ queryKey: ["food", "meal-entries", date] });
      qc.invalidateQueries({ queryKey: ["food", "summary", date] });
    },
  });
}

export function useDeleteMealEntry(date: string) {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (entryId) => {
      const resp = await apiClient.delete(`/food/meal-entries/${entryId}`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["food", "meal-entries", date] });
      qc.invalidateQueries({ queryKey: ["food", "summary", date] });
    },
  });
}

export function useSummary(date: string) {
  return useQuery<Summary>({
    queryKey: ["food", "summary", date],
    queryFn: () => apiClient.get<Summary>(`/food/summary?date=${date}`),
  });
}

export function useCurrentGoal() {
  return useQuery<DailyGoal | null>({
    queryKey: ["food", "goal"],
    queryFn: async () => {
      const resp = await fetch("/api/food/goals/current", { credentials: "include" });
      if (resp.status === 404) return null;
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      return resp.json() as Promise<DailyGoal>;
    },
  });
}

export function useCreateGoal() {
  const qc = useQueryClient();
  return useMutation<DailyGoal, Error, GoalCreatePayload>({
    mutationFn: (payload) => apiClient.post<DailyGoal>("/food/goals", payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["food", "goal"] });
      qc.invalidateQueries({ queryKey: ["food", "summary"] });
    },
  });
}
