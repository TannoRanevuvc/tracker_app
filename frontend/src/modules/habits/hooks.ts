import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/core/api-client";

export function useHabits() {
  return useQuery({
    queryKey: ["habits"],
    queryFn: () => apiClient.get("/habits/"),
  });
}

export function useCreateHabit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => apiClient.post("/habits/", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["habits"] }),
  });
}

export function useCheckHabit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (habitId: number) => apiClient.post(`/habits/${habitId}/check`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["habits"] }),
  });
}
