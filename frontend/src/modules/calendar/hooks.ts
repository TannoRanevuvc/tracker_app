import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/core/api-client";
import type { CalendarEvent, EventCreatePayload, EventUpdatePayload, CalendarItem } from "./types";
import { DEFAULT_EVENT_COLOR } from "./types";

export function useCalendarEvents(start: string, end: string) {
  return useQuery<CalendarEvent[]>({
    queryKey: ["calendar", start, end],
    queryFn: () =>
      apiClient.get<CalendarEvent[]>(
        `/calendar/events?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`
      ),
    enabled: !!start && !!end,
  });
}

interface RawTask {
  id: string;
  title: string;
  due_date?: string;
  status: string;
}

export function useTasksForCalendar() {
  return useQuery<CalendarItem[]>({
    queryKey: ["tasks", "all"],
    queryFn: async () => {
      const tasks = await apiClient.get<RawTask[]>("/tasks");
      return tasks
        .filter((t) => !!t.due_date && t.status !== "done")
        .map((t) => ({
          id: t.id,
          title: t.title,
          start_at: `${t.due_date}T00:00:00`,
          all_day: true,
          color: "#6b7280",
          source: "task" as const,
        }));
    },
  });
}

export function useCreateEvent() {
  const qc = useQueryClient();
  return useMutation<CalendarEvent, Error, EventCreatePayload>({
    mutationFn: (payload) => apiClient.post<CalendarEvent>("/calendar/events", payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["calendar"] }),
  });
}

export function useUpdateEvent(eventId: string) {
  const qc = useQueryClient();
  return useMutation<CalendarEvent, Error, EventUpdatePayload>({
    mutationFn: (payload) =>
      apiClient.patch<CalendarEvent>(`/calendar/events/${eventId}`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["calendar"] }),
  });
}

export function useDeleteEvent() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (eventId) =>
      apiClient.delete(`/calendar/events/${eventId}`).then(() => undefined),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["calendar"] }),
  });
}

export { DEFAULT_EVENT_COLOR };
