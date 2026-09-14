import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/core/api-client";

export function useMeals() {
  return useQuery({
    queryKey: ["food", "meals"],
    queryFn: () => apiClient.get("/food/meals"),
  });
}

export function useLogMeal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => apiClient.post("/food/meals", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["food"] }),
  });
}

export function useProducts() {
  return useQuery({
    queryKey: ["food", "products"],
    queryFn: () => apiClient.get("/food/products"),
  });
}

export function useDailySummary(date: string) {
  return useQuery({
    queryKey: ["food", "daily", date],
    queryFn: () => apiClient.get(`/food/daily?date=${date}`),
  });
}
