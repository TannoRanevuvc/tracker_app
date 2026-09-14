import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/core/api-client";
import type {
  Habit,
  HabitCreatePayload,
  HabitUpdatePayload,
} from "./types";

export function useHabits(includeArchived = false) {
  return useQuery<Habit[]>({
    queryKey: ["habits", { includeArchived }],
    queryFn: () =>
      apiClient.get<Habit[]>(
        `/habits${includeArchived ? "?include_archived=true" : ""}`
      ),
  });
}

export function useHabit(habitId: string) {
  return useQuery<Habit>({
    queryKey: ["habits", habitId],
    queryFn: () => apiClient.get<Habit>(`/habits/${habitId}`),
  });
}

export function useCreateHabit() {
  const qc = useQueryClient();
  return useMutation<Habit, Error, HabitCreatePayload>({
    mutationFn: (payload) => apiClient.post<Habit>("/habits", payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["habits"] }),
  });
}

export function useUpdateHabit(habitId: string) {
  const qc = useQueryClient();
  return useMutation<Habit, Error, HabitUpdatePayload>({
    mutationFn: (payload) =>
      apiClient.patch<Habit>(`/habits/${habitId}`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["habits"] }),
  });
}

export function useArchiveHabit() {
  const qc = useQueryClient();
  return useMutation<Habit, Error, string>({
    mutationFn: (habitId) =>
      apiClient.post<Habit>(`/habits/${habitId}/archive`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["habits"] }),
  });
}

export function useCheckin() {
  const qc = useQueryClient();
  return useMutation<void, Error, { habitId: string; date?: string }>({
    mutationFn: ({ habitId, date }) =>
      apiClient
        .post(`/habits/${habitId}/checkins`, date ? { date } : undefined)
        .then(() => undefined),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["habits"] }),
  });
}

export function useDeleteCheckin() {
  const qc = useQueryClient();
  return useMutation<void, Error, { habitId: string; date: string }>({
    mutationFn: ({ habitId, date }) =>
      apiClient
        .delete(`/habits/${habitId}/checkins/${date}`)
        .then(() => undefined),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["habits"] }),
  });
}
