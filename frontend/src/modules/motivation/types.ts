export interface RecentAchievement {
  code: string;
  name: string;
  unlocked_at: string;
}

export interface MotivationSummary {
  xp_total: number;
  level: number;
  xp_to_next_level: number;
  recent_achievements: RecentAchievement[];
}

export interface Achievement {
  code: string;
  name: string;
  description: string;
  unlocked: boolean;
  unlocked_at: string | null;
}
