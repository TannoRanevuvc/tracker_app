export interface CalendarEvent {
  id: string;
  title: string;
  description?: string;
  start_at: string;
  end_at?: string;
  all_day: boolean;
  color?: string;
  created_at: string;
  updated_at: string;
}

export interface EventCreatePayload {
  title: string;
  start_at: string;
  end_at?: string;
  all_day: boolean;
  color?: string;
  description?: string;
}

export interface EventUpdatePayload {
  title?: string;
  start_at?: string;
  end_at?: string;
  all_day?: boolean;
  color?: string;
  description?: string;
}

export interface CalendarItem {
  id: string;
  title: string;
  start_at: string;
  end_at?: string;
  all_day: boolean;
  color?: string;
  source: "calendar" | "task" | "note";
}

export const COLOR_PRESETS = [
  "#3b82f6",
  "#22c55e",
  "#f97316",
  "#a855f7",
  "#ef4444",
  "#ec4899",
  "#eab308",
  "#06b6d4",
];

export const DEFAULT_EVENT_COLOR = "#3b82f6";
