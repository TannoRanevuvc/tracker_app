import { useState } from "react";
import { Pencil, Plus, Trash2, X } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import {
  useAccounts,
  useCreateAccount,
  useUpdateAccount,
  useSetAccountBalance,
  useDeleteAccount,
  useCategories,
  useCreateCategory,
  useDeleteCategory,
} from "../hooks";
import { formatRub, type Account } from "../types";

// ---------------------------------------------------------------------------
// Add-account modal
// ---------------------------------------------------------------------------

function AddAccountModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [name, setName] = useState("");
  const create = useCreateAccount();

  function handleClose() {
    setName("");
    create.reset();
    onClose();
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    create.mutate({ name: name.trim() }, { onSuccess: handleClose });
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <motion.div className="absolute inset-0 bg-black/60" onClick={handleClose} />
          <motion.div
            className="relative w-full max-w-md bg-brand-gray rounded-3xl p-6 flex flex-col gap-5"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 20, opacity: 0 }}
            transition={{ duration: 0.25 }}
          >
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Новый счёт</h2>
              <button onClick={handleClose} className="text-white/40 hover:text-white/70 transition-colors">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">Название</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Например: Тинькофф"
                  required
                  className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
                />
              </div>
              {create.isError && <p className="text-red-400 text-sm">Не удалось создать счёт</p>}
              <button
                type="submit"
                disabled={create.isPending || !name.trim()}
                className="w-full h-12 bg-white text-black font-semibold rounded-xl hover:bg-white/90 active:scale-[0.98] transition-transform disabled:opacity-40"
              >
                {create.isPending ? "Создаём…" : "Создать"}
              </button>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ---------------------------------------------------------------------------
// Edit-account modal
// ---------------------------------------------------------------------------

function kopecksToRub(kopecks: number): string {
  return (kopecks / 100).toFixed(2).replace(".", ",");
}

function rubToKopecks(rub: string): number {
  return Math.round(parseFloat(rub.replace(",", ".")) * 100);
}

function EditAccountModal({
  account,
  onClose,
}: {
  account: Account;
  onClose: () => void;
}) {
  const [name, setName] = useState(account.name);
  const [balanceStr, setBalanceStr] = useState(kopecksToRub(account.balance_kopecks));
  const [error, setError] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);
  const update = useUpdateAccount(account.id);
  const setBalance = useSetAccountBalance(account.id);

  function handleClose() {
    update.reset();
    setBalance.reset();
    setError(null);
    onClose();
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const trimmedName = name.trim();
    const newBalanceKopecks = rubToKopecks(balanceStr);

    if (!trimmedName) return;
    if (isNaN(newBalanceKopecks)) {
      setError("Введите корректную сумму");
      return;
    }

    const nameChanged = trimmedName !== account.name;
    const balanceChanged = newBalanceKopecks !== account.balance_kopecks;

    if (!nameChanged && !balanceChanged) {
      onClose();
      return;
    }

    setIsPending(true);
    try {
      if (nameChanged) await update.mutateAsync({ name: trimmedName });
      if (balanceChanged) await setBalance.mutateAsync({ balance_kopecks: newBalanceKopecks });
      onClose();
    } catch {
      setError("Не удалось сохранить изменения");
    } finally {
      setIsPending(false);
    }
  }

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
      >
        <motion.div className="absolute inset-0 bg-black/60" onClick={handleClose} />
        <motion.div
          className="relative w-full max-w-md bg-brand-gray rounded-3xl p-6 flex flex-col gap-5"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 20, opacity: 0 }}
          transition={{ duration: 0.25 }}
        >
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Редактировать счёт</h2>
            <button onClick={handleClose} className="text-white/40 hover:text-white/70 transition-colors">
              <X size={20} />
            </button>
          </div>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-white">Название</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                autoFocus
                className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
              />
            </div>
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-white">Баланс, ₽</label>
              <input
                type="text"
                inputMode="decimal"
                value={balanceStr}
                onChange={(e) => setBalanceStr(e.target.value)}
                className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
              />
              <p className="text-xs text-white/30">Задаёт начальный баланс напрямую, без создания транзакции</p>
            </div>
            {error && <p className="text-red-400 text-sm">{error}</p>}
            <button
              type="submit"
              disabled={isPending || !name.trim()}
              className="w-full h-12 bg-white text-black font-semibold rounded-xl hover:bg-white/90 active:scale-[0.98] transition-transform disabled:opacity-40"
            >
              {isPending ? "Сохраняем…" : "Сохранить"}
            </button>
          </form>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

// ---------------------------------------------------------------------------
// Add-category modal
// ---------------------------------------------------------------------------

function AddCategoryModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [name, setName] = useState("");
  const [type, setType] = useState<"expense" | "income">("expense");
  const create = useCreateCategory();

  function handleClose() {
    setName("");
    setType("expense");
    create.reset();
    onClose();
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    create.mutate({ name: name.trim(), type }, { onSuccess: handleClose });
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <motion.div className="absolute inset-0 bg-black/60" onClick={handleClose} />
          <motion.div
            className="relative w-full max-w-md bg-brand-gray rounded-3xl p-6 flex flex-col gap-5"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 20, opacity: 0 }}
            transition={{ duration: 0.25 }}
          >
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Новая категория</h2>
              <button onClick={handleClose} className="text-white/40 hover:text-white/70 transition-colors">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="flex gap-2">
                {(["expense", "income"] as const).map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setType(t)}
                    className={`flex-1 h-10 rounded-xl text-sm font-medium transition-colors ${
                      type === t ? "bg-white text-black" : "bg-black/40 text-white/60 hover:text-white/80"
                    }`}
                  >
                    {t === "expense" ? "Расход" : "Доход"}
                  </button>
                ))}
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">Название</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Например: Продукты"
                  required
                  className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
                />
              </div>
              {create.isError && <p className="text-red-400 text-sm">Не удалось создать категорию</p>}
              <button
                type="submit"
                disabled={create.isPending || !name.trim()}
                className="w-full h-12 bg-white text-black font-semibold rounded-xl hover:bg-white/90 active:scale-[0.98] transition-transform disabled:opacity-40"
              >
                {create.isPending ? "Создаём…" : "Создать"}
              </button>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ---------------------------------------------------------------------------
// Accounts tab
// ---------------------------------------------------------------------------

export default function AccountsTab() {
  const [addAccountOpen, setAddAccountOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState<Account | null>(null);
  const [addCategoryOpen, setAddCategoryOpen] = useState(false);
  const [accountError, setAccountError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const { data: accounts = [], isLoading: loadingAccounts } = useAccounts();
  const { data: categories = [], isLoading: loadingCategories } = useCategories();
  const deleteAccount = useDeleteAccount();
  const deleteCategory = useDeleteCategory();

  const expenseCategories = categories.filter((c) => c.type === "expense");
  const incomeCategories = categories.filter((c) => c.type === "income");

  function handleDeleteAccount(id: string) {
    setAccountError(null);
    deleteAccount.mutate(id, {
      onError: (err) => setAccountError(err.message),
    });
  }

  function handleDeleteCategory(id: string) {
    setDeleteError(null);
    deleteCategory.mutate(id, {
      onError: (err) => setDeleteError(err.message),
    });
  }

  return (
    <>
      {/* Accounts section */}
      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between px-1">
          <h2 className="text-sm font-medium text-white/60">Счета</h2>
          <button
            onClick={() => setAddAccountOpen(true)}
            className="h-7 px-3 rounded-xl bg-white/10 text-xs text-white/70 hover:bg-white/15 hover:text-white transition-colors flex items-center gap-1"
          >
            <Plus size={12} />
            Счёт
          </button>
        </div>

        {accountError && (
          <p className="text-red-400 text-sm px-1">{accountError}</p>
        )}

        {loadingAccounts && (
          <div className="flex justify-center py-6">
            <div className="h-5 w-5 rounded-full border-2 border-white/20 border-t-white animate-spin" />
          </div>
        )}

        {!loadingAccounts && accounts.length === 0 && (
          <p className="text-center text-white/40 text-sm py-4">
            Счетов пока нет
          </p>
        )}

        {accounts.map((account) => (
          <div
            key={account.id}
            className="bg-brand-gray rounded-3xl px-5 py-4 flex items-center justify-between gap-3"
          >
            <span className="font-medium text-white truncate">{account.name}</span>
            <div className="flex items-center gap-2 shrink-0">
              <span
                className={`text-sm font-semibold ${
                  account.balance_kopecks < 0 ? "text-red-400" : "text-white"
                }`}
              >
                {formatRub(account.balance_kopecks, false)}
              </span>
              <button
                onClick={() => { setAccountError(null); setEditingAccount(account); }}
                className="h-7 w-7 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/30 hover:text-white/70 transition-colors"
              >
                <Pencil size={13} />
              </button>
              <button
                onClick={() => handleDeleteAccount(account.id)}
                disabled={deleteAccount.isPending}
                className="h-7 w-7 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/30 hover:text-red-400 transition-colors disabled:opacity-40"
              >
                <Trash2 size={13} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Categories section */}
      <div className="flex flex-col gap-3 mt-2">
        <div className="flex items-center justify-between px-1">
          <h2 className="text-sm font-medium text-white/60">Категории</h2>
          <button
            onClick={() => setAddCategoryOpen(true)}
            className="h-7 px-3 rounded-xl bg-white/10 text-xs text-white/70 hover:bg-white/15 hover:text-white transition-colors flex items-center gap-1"
          >
            <Plus size={12} />
            Категория
          </button>
        </div>

        {deleteError && (
          <p className="text-red-400 text-sm px-1">{deleteError}</p>
        )}

        {loadingCategories && (
          <div className="flex justify-center py-4">
            <div className="h-5 w-5 rounded-full border-2 border-white/20 border-t-white animate-spin" />
          </div>
        )}

        {!loadingCategories && categories.length === 0 && (
          <p className="text-center text-white/40 text-sm py-4">
            Категорий пока нет
          </p>
        )}

        {expenseCategories.length > 0 && (
          <div className="flex flex-col gap-2">
            <p className="text-xs text-white/30 px-1">Расходы</p>
            {expenseCategories.map((cat) => (
              <div
                key={cat.id}
                className="bg-brand-gray rounded-3xl px-5 py-3 flex items-center justify-between"
              >
                <span className="text-sm text-white">{cat.name}</span>
                <button
                  onClick={() => handleDeleteCategory(cat.id)}
                  disabled={deleteCategory.isPending}
                  className="h-7 w-7 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/30 hover:text-red-400 transition-colors disabled:opacity-40"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))}
          </div>
        )}

        {incomeCategories.length > 0 && (
          <div className="flex flex-col gap-2">
            <p className="text-xs text-white/30 px-1">Доходы</p>
            {incomeCategories.map((cat) => (
              <div
                key={cat.id}
                className="bg-brand-gray rounded-3xl px-5 py-3 flex items-center justify-between"
              >
                <span className="text-sm text-white">{cat.name}</span>
                <button
                  onClick={() => handleDeleteCategory(cat.id)}
                  disabled={deleteCategory.isPending}
                  className="h-7 w-7 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/30 hover:text-red-400 transition-colors disabled:opacity-40"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <AddAccountModal open={addAccountOpen} onClose={() => setAddAccountOpen(false)} />
      {editingAccount && (
        <EditAccountModal account={editingAccount} onClose={() => setEditingAccount(null)} />
      )}
      <AddCategoryModal open={addCategoryOpen} onClose={() => setAddCategoryOpen(false)} />
    </>
  );
}
