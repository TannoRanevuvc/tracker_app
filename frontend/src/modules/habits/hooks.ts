import { useQuery, useMutation, useQueryClient, type QueryKey } from "@tanstack/react-query";
import { apiClient } from "@/core/api-client";
import type {
  Habit,
  HabitCreatePayload,
  HabitUpdatePayload,
} from "./types";

type PrevSnapshot = [QueryKey, Habit[] | undefined][];

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
  return useMutation<void, Error, { habitId: string; date?: string }, { prev: PrevSnapshot }>({
    mutationFn: ({ habitId, date }) =>
      apiClient
        .post(`/habits/${habitId}/checkins`, date ? { date } : undefined)
        .then(() => undefined),
    onMutate: async ({ habitId }) => {
      await qc.cancelQueries({ queryKey: ["habits"] });
      const prev = qc.getQueriesData<Habit[]>({ queryKey: ["habits"] });
      qc.setQueriesData<Habit[]>({ queryKey: ["habits"] }, (old) =>
        old?.map((h) => (h.id === habitId ? { ...h, done_today: true } : h))
      );
      return { prev };
    },
    onError: (_err, _vars, ctx) => {
      ctx?.prev.forEach(([key, data]) => qc.setQueryData(key, data));
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ["habits"] }),
  });
}

export function useDeleteCheckin() {
  const qc = useQueryClient();
  return useMutation<void, Error, { habitId: string; date: string }, { prev: PrevSnapshot }>({
    mutationFn: ({ habitId, date }) =>
      apiClient
        .delete(`/habits/${habitId}/checkins/${date}`)
        .then(() => undefined),
    onMutate: async ({ habitId }) => {
      await qc.cancelQueries({ queryKey: ["habits"] });
      const prev = qc.getQueriesData<Habit[]>({ queryKey: ["habits"] });
      qc.setQueriesData<Habit[]>({ queryKey: ["habits"] }, (old) =>
        old?.map((h) => (h.id === habitId ? { ...h, done_today: false } : h))
      );
      return { prev };
    },
    onError: (_err, _vars, ctx) => {
      ctx?.prev.forEach(([key, data]) => qc.setQueryData(key, data));
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ["habits"] }),
  });
}
