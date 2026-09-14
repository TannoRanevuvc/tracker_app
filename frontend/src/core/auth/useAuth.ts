import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/core/api-client";

export interface User {
  id: string;
  email: string;
}

export function useAuth() {
  return useQuery<User>({
    queryKey: ["auth", "me"],
    queryFn: () => apiClient.get<User>("/auth/me"),
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
}
