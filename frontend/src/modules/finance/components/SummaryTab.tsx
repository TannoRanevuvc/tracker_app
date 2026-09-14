import { useState } from "react";
import { Plus, X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useSummary, useCreateBudget, useCategories } from "../hooks";
import { formatRub, currentPeriod } from "../types";
import type { BudgetCreatePayload, Category } from "../types";

// ---------------------------------------------------------------------------
// Add-budget modal
// ---------------------------------------------------------------------------

interface AddBudgetModalProps {
  open: boolean;
  onClose: () => void;
  period: string;
  categories: Category[];
}

function AddBudgetModal({ open, onClose, period, categories }: AddBudgetModalProps) {
  const [categoryId, setCategoryId] = useState(categories[0]?.id ?? "");
  const [limitRub, setLimitRub] = useState("");
  const create = useCreateBudget();

  const expenseCategories = categories.filter((c) => c.type === "expense");

  function handleClose() {
    setCategoryId(categories[0]?.id ?? "");
    setLimitRub("");
    create.reset();
    onClose();
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const payload: BudgetCreatePayload = {
      category_id: categoryId,
      period,
      limit_kopecks: Math.round(parseFloat(limitRub.replace(",", ".")) * 100),
    };
    create.mutate(payload, { onSuccess: handleClose });
  }

  const validLimit =
    /^\d+([.,]\d{0,2})?$/.test(limitRub.trim()) &&
    parseFloat(limitRub.replace(",", ".")) > 0;

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
              <h2 className="text-lg font-semibold">Установить лимит</h2>
              <button onClick={handleClose} className="text-white/40 hover:text-white/70 transition-colors">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">Категория расходов</label>
                <select
                  value={categoryId}
                  onChange={(e) => setCategoryId(e.target.value)}
                  required
                  className="bg-black/40 rounded-xl h-11 px-4 text-white focus:outline-none focus:ring-2 focus:ring-white/20 [color-scheme:dark]"
                >
                  {expenseCategories.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">Лимит, ₽</label>
                <input
                  type="text"
                  inputMode="decimal"
                  value={limitRub}
                  onChange={(e) => setLimitRub(e.target.value)}
                  placeholder="0"
                  required
                  className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
                />
              </div>
              <p className="text-xs text-white/40">Период: {period}</p>
              {create.isError && (
                <p className="text-red-400 text-sm">Не удалось установить лимит</p>
              )}
              <button
                type="submit"
                disabled={create.isPending || !categoryId || !validLimit}
                className="w-full h-12 bg-white text-black font-semibold rounded-xl hover:bg-white/90 active:scale-[0.98] transition-transform disabled:opacity-40"
              >
                {create.isPending ? "Сохраняем…" : "Установить"}
              </button>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ---------------------------------------------------------------------------
// Summary tab
// ---------------------------------------------------------------------------

function formatPeriodLabel(period: string): string {
  const [year, month] = period.split("-");
  const date = new Date(parseInt(year), parseInt(month) - 1, 1);
  return date.toLocaleDateString("ru-RU", { month: "long", year: "numeric" });
}

function prevPeriod(period: string): string {
  const [year, month] = period.split("-").map(Number);
  const d = new Date(year, month - 2, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function nextPeriod(period: string): string {
  const [year, month] = period.split("-").map(Number);
  const d = new Date(year, month, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export default function SummaryTab() {
  const [period, setPeriod] = useState(currentPeriod());
  const [addBudgetOpen, setAddBudgetOpen] = useState(false);

  const { data: summary, isLoading, isError } = useSummary(period);
  const { data: categories = [] } = useCategories();

  const expenseCategories = categories.filter((c) => c.type === "expense");

  return (
    <>
      {/* Period navigation */}
      <div className="flex items-center justify-between px-1">
        <button
          onClick={() => setPeriod(prevPeriod(period))}
          className="h-8 px-3 rounded-xl text-white/40 hover:text-white/70 hover:bg-white/5 transition-colors text-sm"
        >
          ‹
        </button>
        <span className="text-sm font-medium text-white capitalize">
          {formatPeriodLabel(period)}
        </span>
        <button
          onClick={() => setPeriod(nextPeriod(period))}
          className="h-8 px-3 rounded-xl text-white/40 hover:text-white/70 hover:bg-white/5 transition-colors text-sm"
        >
          ›
        </button>
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="h-6 w-6 rounded-full border-2 border-white/20 border-t-white animate-spin" />
        </div>
      )}

      {isError && (
        <p className="text-center text-white/40 pt-8 text-sm">
          Не удалось загрузить данные
        </p>
      )}

      {summary && (
        <>
          {/* Totals */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-brand-gray rounded-3xl p-4 flex flex-col gap-1">
              <span className="text-xs text-white/40">Доходы</span>
              <span className="text-lg font-semibold text-green-400">
                {formatRub(summary.total_income, false)}
              </span>
            </div>
            <div className="bg-brand-gray rounded-3xl p-4 flex flex-col gap-1">
              <span className="text-xs text-white/40">Расходы</span>
              <span className="text-lg font-semibold text-red-400">
                {formatRub(summary.total_expense, false)}
              </span>
            </div>
          </div>

          {/* By category */}
          {summary.by_category.length > 0 && (
            <div className="flex flex-col gap-2">
              <p className="text-xs text-white/30 px-1">По категориям</p>
              {[...summary.by_category]
                .sort((a, b) => Math.abs(b.amount_kopecks) - Math.abs(a.amount_kopecks))
                .map((item, idx) => {
                  const isExpense = item.amount_kopecks < 0;
                  return (
                    <div
                      key={item.category_id ?? `uncategorized-${idx}`}
                      className="bg-brand-gray rounded-3xl px-5 py-3 flex items-center justify-between"
                    >
                      <span className="text-sm text-white">
                        {item.category_name ?? "Без категории"}
                      </span>
                      <span
                        className={`text-sm font-semibold ${
                          isExpense ? "text-red-400" : "text-green-400"
                        }`}
                      >
                        {formatRub(item.amount_kopecks)}
                      </span>
                    </div>
                  );
                })}
            </div>
          )}

          {summary.by_category.length === 0 && (
            <p className="text-center text-white/40 text-sm py-4">
              Транзакций в этом периоде нет
            </p>
          )}

          {/* Budget action */}
          {expenseCategories.length > 0 && (
            <button
              onClick={() => setAddBudgetOpen(true)}
              className="flex items-center justify-center gap-2 h-11 rounded-xl border border-white/10 text-sm text-white/50 hover:text-white/70 hover:border-white/20 transition-colors"
            >
              <Plus size={14} />
              Установить лимит бюджета
            </button>
          )}
        </>
      )}

      <AddBudgetModal
        open={addBudgetOpen}
        onClose={() => setAddBudgetOpen(false)}
        period={period}
        categories={categories}
      />
    </>
  );
}
