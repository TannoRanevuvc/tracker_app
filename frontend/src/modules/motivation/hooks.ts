import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/core/api-client";
import type { MotivationSummary, Achievement } from "./types";

export function useMotivationSummary() {
  return useQuery<MotivationSummary>({
    queryKey: ["motivation", "summary"],
    queryFn: () => apiClient.get<MotivationSummary>("/motivation/summary"),
  });
}

export function useMotivationAchievements() {
  return useQuery<Achievement[]>({
    queryKey: ["motivation", "achievements"],
    queryFn: () => apiClient.get<Achievement[]>("/motivation/achievements"),
  });
}
