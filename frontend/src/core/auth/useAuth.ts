import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/core/api-client";

export function useAuth() {
  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: () => apiClient.get("/auth/me"),
    retry: false,
  });
}
