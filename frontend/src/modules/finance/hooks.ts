import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/core/api-client";
import type {
  Account,
  AccountCreatePayload,
  AccountSetBalancePayload,
  AccountUpdatePayload,
  Budget,
  BudgetCreatePayload,
  Category,
  CategoryCreatePayload,
  RecurringRule,
  RecurringRuleCreatePayload,
  RecurringRuleUpdatePayload,
  Summary,
  Transaction,
  TransactionCreatePayload,
} from "./types";

export function useAccounts() {
  return useQuery<Account[]>({
    queryKey: ["finance", "accounts"],
    queryFn: () => apiClient.get<Account[]>("/finance/accounts"),
  });
}

export function useCreateAccount() {
  const qc = useQueryClient();
  return useMutation<Account, Error, AccountCreatePayload>({
    mutationFn: (payload) => apiClient.post<Account>("/finance/accounts", payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["finance", "accounts"] }),
  });
}

export function useUpdateAccount(accountId: string) {
  const qc = useQueryClient();
  return useMutation<Account, Error, AccountUpdatePayload>({
    mutationFn: (payload) =>
      apiClient.patch<Account>(`/finance/accounts/${accountId}`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["finance", "accounts"] }),
  });
}

export function useSetAccountBalance(accountId: string) {
  const qc = useQueryClient();
  return useMutation<Account, Error, AccountSetBalancePayload>({
    mutationFn: (payload) =>
      apiClient.patch<Account>(`/finance/accounts/${accountId}/balance`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["finance", "accounts"] }),
  });
}

export function useDeleteAccount() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (accountId) => {
      const resp = await apiClient.delete(`/finance/accounts/${accountId}`);
      if (!resp.ok) {
        throw new Error(
          resp.status === 409
            ? "Нельзя удалить: у счёта есть транзакции"
            : `HTTP ${resp.status}`
        );
      }
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["finance", "accounts"] });
      qc.invalidateQueries({ queryKey: ["finance", "transactions"] });
      qc.invalidateQueries({ queryKey: ["finance", "summary"] });
    },
  });
}

export function useCategories() {
  return useQuery<Category[]>({
    queryKey: ["finance", "categories"],
    queryFn: () => apiClient.get<Category[]>("/finance/categories"),
  });
}

export function useCreateCategory() {
  const qc = useQueryClient();
  return useMutation<Category, Error, CategoryCreatePayload>({
    mutationFn: (payload) => apiClient.post<Category>("/finance/categories", payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["finance", "categories"] }),
  });
}

export function useDeleteCategory() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (categoryId) => {
      const resp = await apiClient.delete(`/finance/categories/${categoryId}`);
      if (!resp.ok) {
        throw new Error(
          resp.status === 409
            ? "Нельзя удалить: у категории есть транзакции"
            : `HTTP ${resp.status}`
        );
      }
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["finance", "categories"] }),
  });
}

export interface TransactionFilters {
  account_id?: string;
  category_id?: string;
  from?: string;
  to?: string;
}

export function useTransactions(filters: TransactionFilters = {}) {
  const params = new URLSearchParams();
  if (filters.account_id) params.set("account_id", filters.account_id);
  if (filters.category_id) params.set("category_id", filters.category_id);
  if (filters.from) params.set("from", filters.from);
  if (filters.to) params.set("to", filters.to);
  const qs = params.toString();

  return useQuery<Transaction[]>({
    queryKey: ["finance", "transactions", filters],
    queryFn: () =>
      apiClient.get<Transaction[]>(`/finance/transactions${qs ? `?${qs}` : ""}`),
  });
}

export function useCreateTransaction() {
  const qc = useQueryClient();
  return useMutation<Transaction, Error, TransactionCreatePayload>({
    mutationFn: (payload) =>
      apiClient.post<Transaction>("/finance/transactions", payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["finance", "transactions"] });
      qc.invalidateQueries({ queryKey: ["finance", "accounts"] });
      qc.invalidateQueries({ queryKey: ["finance", "summary"] });
    },
  });
}

export function useDeleteTransaction() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (txnId) => {
      const resp = await apiClient.delete(`/finance/transactions/${txnId}`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["finance", "transactions"] });
      qc.invalidateQueries({ queryKey: ["finance", "accounts"] });
      qc.invalidateQueries({ queryKey: ["finance", "summary"] });
    },
  });
}

export function useRecurringRules() {
  return useQuery<RecurringRule[]>({
    queryKey: ["finance", "recurring-rules"],
    queryFn: () => apiClient.get<RecurringRule[]>("/finance/recurring-rules"),
  });
}

export function useCreateRecurringRule() {
  const qc = useQueryClient();
  return useMutation<RecurringRule, Error, RecurringRuleCreatePayload>({
    mutationFn: (payload) =>
      apiClient.post<RecurringRule>("/finance/recurring-rules", payload),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["finance", "recurring-rules"] }),
  });
}

export function useUpdateRecurringRule(ruleId: string) {
  const qc = useQueryClient();
  return useMutation<RecurringRule, Error, RecurringRuleUpdatePayload>({
    mutationFn: (payload) =>
      apiClient.patch<RecurringRule>(`/finance/recurring-rules/${ruleId}`, payload),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["finance", "recurring-rules"] }),
  });
}

export function useCreateBudget() {
  const qc = useQueryClient();
  return useMutation<Budget, Error, BudgetCreatePayload>({
    mutationFn: (payload) => apiClient.post<Budget>("/finance/budgets", payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["finance", "summary"] }),
  });
}

export function useSummary(period: string) {
  return useQuery<Summary>({
    queryKey: ["finance", "summary", period],
    queryFn: () => apiClient.get<Summary>(`/finance/summary?period=${period}`),
  });
}
