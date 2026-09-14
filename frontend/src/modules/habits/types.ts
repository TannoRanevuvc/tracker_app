export interface Habit {
  id: string;
  name: string;
  frequency_type: "daily" | "weekly_days";
  weekly_days: number[] | null;
  created_at: string;
  archived_at: string | null;
  current_streak: number;
  done_today: boolean;
}

export interface Checkin {
  id: string;
  habit_id: string;
  date: string;
  note: string | null;
  created_at: string;
}

export interface HabitCreatePayload {
  name: string;
  frequency_type: "daily" | "weekly_days";
  weekly_days?: number[];
}

export interface HabitUpdatePayload {
  name?: string;
  frequency_type?: "daily" | "weekly_days";
  weekly_days?: number[];
}
