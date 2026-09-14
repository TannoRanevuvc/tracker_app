import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/core/api-client";
import type { Task, TaskCreatePayload, TaskUpdatePayload } from "./types";

export type TaskFilter = "all" | "active" | "done";

function tasksPath(filter: TaskFilter): string {
  if (filter === "active") return "/tasks?status=todo";
  if (filter === "done") return "/tasks?status=done";
  return "/tasks";
}

export function useTasks(filter: TaskFilter = "all") {
  return useQuery<Task[]>({
    queryKey: ["tasks", filter],
    queryFn: () => apiClient.get<Task[]>(tasksPath(filter)),
  });
}

export function useTask(taskId: string) {
  return useQuery<Task>({
    queryKey: ["tasks", taskId],
    queryFn: () => apiClient.get<Task>(`/tasks/${taskId}`),
  });
}

export function useCreateTask() {
  const qc = useQueryClient();
  return useMutation<Task, Error, TaskCreatePayload>({
    mutationFn: (payload) => apiClient.post<Task>("/tasks", payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function useUpdateTask(taskId: string) {
  const qc = useQueryClient();
  return useMutation<Task, Error, TaskUpdatePayload>({
    mutationFn: (payload) => apiClient.patch<Task>(`/tasks/${taskId}`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function useCompleteTask() {
  const qc = useQueryClient();
  return useMutation<Task, Error, string>({
    mutationFn: (taskId) => apiClient.post<Task>(`/tasks/${taskId}/complete`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function useReopenTask() {
  const qc = useQueryClient();
  return useMutation<Task, Error, string>({
    mutationFn: (taskId) => apiClient.post<Task>(`/tasks/${taskId}/reopen`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

export function useDeleteTask() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (taskId) =>
      apiClient.delete(`/tasks/${taskId}`).then(() => undefined),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}
