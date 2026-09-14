import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/core/api-client";

export function useTransactions() {
  return useQuery({
    queryKey: ["finance", "transactions"],
    queryFn: () => apiClient.get("/finance/transactions"),
  });
}

export function useCreateTransaction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: unknown) => apiClient.post("/finance/transactions", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["finance"] }),
  });
}

export function useAccounts() {
  return useQuery({
    queryKey: ["finance", "accounts"],
    queryFn: () => apiClient.get("/finance/accounts"),
  });
}
