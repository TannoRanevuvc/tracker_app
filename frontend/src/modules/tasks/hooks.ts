import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/core/api-client";

export function useTasks() {
  return useQuery({
    queryKey: ["tasks"],
    queryFn: () => apiClient.get("/tasks/"),
  });
}

export function useCreateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => apiClient.post("/tasks/", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function useCompleteTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (taskId: number) => apiClient.post(`/tasks/${taskId}/complete`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}
