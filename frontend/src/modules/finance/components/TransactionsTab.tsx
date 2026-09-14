import { useMemo, useState } from "react";
import { Plus, Trash2, RefreshCw, Utensils } from "lucide-react";
import { X } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import {
  useTransactions,
  useCreateTransaction,
  useDeleteTransaction,
  useAccounts,
  useCategories,
} from "../hooks";
import type { Account, Category, TransactionCreatePayload } from "../types";
import { formatRub, currentMonthRange } from "../types";

const SOURCE_ICON: Record<string, React.ReactNode> = {
  recurring: <RefreshCw size={11} className="text-white/30" />,
  food_module: <Utensils size={11} className="text-white/30" />,
};

const listVariants = {
  visible: { opacity: 1, transition: { staggerChildren: 0.05, delayChildren: 0.05 } },
  hidden: { opacity: 0 },
};
const itemVariants = {
  hidden: { opacity: 0, y: 8 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3 } },
};

// ---------------------------------------------------------------------------
// Add-transaction modal
// ---------------------------------------------------------------------------

interface AddTransactionModalProps {
  open: boolean;
  onClose: () => void;
  accounts: Account[];
  categories: Category[];
}

function AddTransactionModal({
  open,
  onClose,
  accounts,
  categories,
}: AddTransactionModalProps) {
  const today = new Date().toISOString().slice(0, 10);
  const [type, setType] = useState<"expense" | "income">("expense");
  const [amountRub, setAmountRub] = useState("");
  const [accountId, setAccountId] = useState(accounts[0]?.id ?? "");
  const [categoryId, setCategoryId] = useState("");
  const [date, setDate] = useState(today);
  const [description, setDescription] = useState("");

  const create = useCreateTransaction();
  const filteredCategories = categories.filter((c) => c.type === type);

  function reset() {
    setType("expense");
    setAmountRub("");
    setAccountId(accounts[0]?.id ?? "");
    setCategoryId("");
    setDate(today);
    setDescription("");
    create.reset();
  }

  function handleClose() {
    reset();
    onClose();
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const kopecks = Math.round(parseFloat(amountRub.replace(",", ".")) * 100);
    const payload: TransactionCreatePayload = {
      account_id: accountId,
      amount_kopecks: type === "expense" ? -kopecks : kopecks,
      occurred_at: date,
      ...(categoryId && { category_id: categoryId }),
      ...(description.trim() && { description: description.trim() }),
    };
    create.mutate(payload, { onSuccess: handleClose });
  }

  const validAmount = /^\d+([.,]\d{0,2})?$/.test(amountRub.trim()) && parseFloat(amountRub.replace(",", ".")) > 0;

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
              <h2 className="text-lg font-semibold">Новая транзакция</h2>
              <button onClick={handleClose} className="text-white/40 hover:text-white/70 transition-colors">
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              {/* Type toggle */}
              <div className="flex gap-2">
                {(["expense", "income"] as const).map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => { setType(t); setCategoryId(""); }}
                    className={`flex-1 h-10 rounded-xl text-sm font-medium transition-colors ${
                      type === t ? "bg-white text-black" : "bg-black/40 text-white/60 hover:text-white/80"
                    }`}
                  >
                    {t === "expense" ? "Расход" : "Доход"}
                  </button>
                ))}
              </div>

              {/* Amount */}
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">Сумма, ₽</label>
                <input
                  type="text"
                  inputMode="decimal"
                  value={amountRub}
                  onChange={(e) => setAmountRub(e.target.value)}
                  placeholder="0"
                  required
                  className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
                />
              </div>

              {/* Account */}
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">Счёт</label>
                <select
                  value={accountId}
                  onChange={(e) => setAccountId(e.target.value)}
                  required
                  className="bg-black/40 rounded-xl h-11 px-4 text-white focus:outline-none focus:ring-2 focus:ring-white/20 [color-scheme:dark]"
                >
                  {accounts.map((a) => (
                    <option key={a.id} value={a.id}>{a.name}</option>
                  ))}
                </select>
              </div>

              {/* Category */}
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">
                  Категория <span className="text-white/40 font-normal">— необязательно</span>
                </label>
                <select
                  value={categoryId}
                  onChange={(e) => setCategoryId(e.target.value)}
                  className="bg-black/40 rounded-xl h-11 px-4 text-white focus:outline-none focus:ring-2 focus:ring-white/20 [color-scheme:dark]"
                >
                  <option value="">Без категории</option>
                  {filteredCategories.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>

              {/* Date */}
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">Дата</label>
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  required
                  className="bg-black/40 rounded-xl h-11 px-4 text-white focus:outline-none focus:ring-2 focus:ring-white/20 [color-scheme:dark]"
                />
              </div>

              {/* Description */}
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">
                  Описание <span className="text-white/40 font-normal">— необязательно</span>
                </label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Например: продукты"
                  className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
                />
              </div>

              {create.isError && (
                <p className="text-red-400 text-sm">Не удалось создать транзакцию</p>
              )}

              <button
                type="submit"
                disabled={create.isPending || !validAmount || !accountId}
                className="w-full h-12 bg-white text-black font-semibold rounded-xl hover:bg-white/90 active:scale-[0.98] transition-transform disabled:opacity-40 mt-1"
              >
                {create.isPending ? "Сохраняем…" : "Добавить"}
              </button>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ---------------------------------------------------------------------------
// Transactions tab
// ---------------------------------------------------------------------------

export default function TransactionsTab() {
  const [addOpen, setAddOpen] = useState(false);
  const { from, to } = currentMonthRange();

  const { data: transactions = [], isLoading, isError } = useTransactions({ from, to });
  const { data: accounts = [] } = useAccounts();
  const { data: categories = [] } = useCategories();
  const deleteTransaction = useDeleteTransaction();

  const accountMap = useMemo(
    () => Object.fromEntries(accounts.map((a) => [a.id, a])),
    [accounts]
  );
  const categoryMap = useMemo(
    () => Object.fromEntries(categories.map((c) => [c.id, c])),
    [categories]
  );

  const sorted = useMemo(
    () => [...transactions].sort((a, b) => b.occurred_at.localeCompare(a.occurred_at)),
    [transactions]
  );

  function formatDate(iso: string): string {
    return new Date(iso + "T00:00:00").toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "short",
    });
  }

  return (
    <>
      <div className="flex items-center justify-between px-1">
        <p className="text-sm text-white/40">Текущий месяц</p>
        <button
          onClick={() => setAddOpen(true)}
          disabled={accounts.length === 0}
          title={accounts.length === 0 ? "Сначала создайте счёт" : undefined}
          className="h-8 w-8 rounded-xl bg-white text-black flex items-center justify-center hover:bg-white/90 active:scale-[0.98] transition-transform disabled:opacity-40"
        >
          <Plus size={16} />
        </button>
      </div>

      {isLoading && (
        <div className="flex justify-center pt-12">
          <div className="h-6 w-6 rounded-full border-2 border-white/20 border-t-white animate-spin" />
        </div>
      )}

      {isError && (
        <p className="text-center text-white/40 pt-12 text-sm">
          Не удалось загрузить транзакции
        </p>
      )}

      {!isLoading && !isError && sorted.length === 0 && (
        <div className="flex flex-col items-center gap-4 pt-16 text-center">
          <p className="text-white/40 text-sm">
            {accounts.length === 0
              ? "Создайте счёт на вкладке «Счета», затем добавьте транзакцию"
              : "Транзакций в этом месяце нет"}
          </p>
          {accounts.length > 0 && (
            <button
              onClick={() => setAddOpen(true)}
              className="h-12 px-6 bg-white text-black font-semibold rounded-xl hover:bg-white/90 active:scale-[0.98] transition-transform"
            >
              Добавить транзакцию
            </button>
          )}
        </div>
      )}

      {!isLoading && sorted.length > 0 && (
        <motion.div
          className="flex flex-col gap-2"
          variants={listVariants}
          initial="hidden"
          animate="visible"
        >
          {sorted.map((txn) => {
            const isExpense = txn.amount_kopecks < 0;
            const account = accountMap[txn.account_id];
            const category = txn.category_id ? categoryMap[txn.category_id] : null;

            return (
              <motion.div
                key={txn.id}
                variants={itemVariants}
                className="bg-brand-gray rounded-3xl px-5 py-4 flex items-center gap-3"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm font-medium text-white truncate">
                      {category?.name ?? (txn.description ?? "Без категории")}
                    </span>
                    {SOURCE_ICON[txn.source]}
                  </div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-white/40">{formatDate(txn.occurred_at)}</span>
                    {account && (
                      <span className="text-xs text-white/30">· {account.name}</span>
                    )}
                    {category && txn.description && (
                      <span className="text-xs text-white/30 truncate">· {txn.description}</span>
                    )}
                  </div>
                </div>
                <span
                  className={`text-sm font-semibold shrink-0 ${
                    isExpense ? "text-red-400" : "text-green-400"
                  }`}
                >
                  {formatRub(txn.amount_kopecks)}
                </span>
                <button
                  onClick={() => deleteTransaction.mutate(txn.id)}
                  disabled={deleteTransaction.isPending}
                  className="h-8 w-8 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/30 hover:text-red-400 transition-colors disabled:opacity-40 shrink-0"
                >
                  <Trash2 size={13} />
                </button>
              </motion.div>
            );
          })}
        </motion.div>
      )}

      <AddTransactionModal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        accounts={accounts}
        categories={categories}
      />
    </>
  );
}
