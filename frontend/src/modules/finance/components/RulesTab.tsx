import { useMemo, useState } from "react";
import { Plus, X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import {
  useRecurringRules,
  useCreateRecurringRule,
  useUpdateRecurringRule,
  useAccounts,
  useCategories,
} from "../hooks";
import { formatRub } from "../types";
import type { Account, Category, RecurringRuleCreatePayload } from "../types";

const DAY_LABELS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

// ---------------------------------------------------------------------------
// Toggle button for a single rule
// ---------------------------------------------------------------------------

function RuleToggle({ ruleId, active }: { ruleId: string; active: boolean }) {
  const update = useUpdateRecurringRule(ruleId);
  return (
    <button
      onClick={() => update.mutate({ active: !active })}
      disabled={update.isPending}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors disabled:opacity-40 ${
        active ? "bg-white/80" : "bg-white/15"
      }`}
    >
      <span
        className={`inline-block h-4 w-4 rounded-full bg-black transition-transform ${
          active ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </button>
  );
}

// ---------------------------------------------------------------------------
// Add-rule modal
// ---------------------------------------------------------------------------

interface AddRuleModalProps {
  open: boolean;
  onClose: () => void;
  accounts: Account[];
  categories: Category[];
}

function AddRuleModal({ open, onClose, accounts, categories }: AddRuleModalProps) {
  const today = new Date().toISOString().slice(0, 10);
  const [type, setType] = useState<"expense" | "income">("expense");
  const [amountRub, setAmountRub] = useState("");
  const [accountId, setAccountId] = useState(accounts[0]?.id ?? "");
  const [categoryId, setCategoryId] = useState("");
  const [frequency, setFrequency] = useState<"monthly" | "weekly">("monthly");
  const [dayOfMonth, setDayOfMonth] = useState("1");
  const [dayOfWeek, setDayOfWeek] = useState(0);
  const [description, setDescription] = useState("");
  const [nextDueDate, setNextDueDate] = useState(today);

  const create = useCreateRecurringRule();
  const filteredCategories = categories.filter((c) => c.type === type);

  function reset() {
    setType("expense");
    setAmountRub("");
    setAccountId(accounts[0]?.id ?? "");
    setCategoryId("");
    setFrequency("monthly");
    setDayOfMonth("1");
    setDayOfWeek(0);
    setDescription("");
    setNextDueDate(today);
    create.reset();
  }

  function handleClose() {
    reset();
    onClose();
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const kopecks = Math.round(parseFloat(amountRub.replace(",", ".")) * 100);
    const payload: RecurringRuleCreatePayload = {
      account_id: accountId,
      amount_kopecks: type === "expense" ? -kopecks : kopecks,
      frequency,
      ...(frequency === "monthly" && { day_of_month: parseInt(dayOfMonth) }),
      ...(frequency === "weekly" && { day_of_week: dayOfWeek }),
      ...(categoryId && { category_id: categoryId }),
      ...(description.trim() && { description: description.trim() }),
      next_due_date: nextDueDate,
    };
    create.mutate(payload, { onSuccess: handleClose });
  }

  const validAmount =
    /^\d+([.,]\d{0,2})?$/.test(amountRub.trim()) &&
    parseFloat(amountRub.replace(",", ".")) > 0;

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
            className="relative w-full max-w-md bg-brand-gray rounded-3xl p-6 flex flex-col gap-5 max-h-[90vh] overflow-y-auto"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 20, opacity: 0 }}
            transition={{ duration: 0.25 }}
          >
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Новое правило</h2>
              <button onClick={handleClose} className="text-white/40 hover:text-white/70 transition-colors">
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              {/* Type */}
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

              {/* Frequency */}
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">Периодичность</label>
                <div className="flex gap-2">
                  {(["monthly", "weekly"] as const).map((f) => (
                    <button
                      key={f}
                      type="button"
                      onClick={() => setFrequency(f)}
                      className={`flex-1 h-10 rounded-xl text-sm font-medium transition-colors ${
                        frequency === f ? "bg-white text-black" : "bg-black/40 text-white/60 hover:text-white/80"
                      }`}
                    >
                      {f === "monthly" ? "Ежемесячно" : "Еженедельно"}
                    </button>
                  ))}
                </div>
              </div>

              {/* Frequency details */}
              {frequency === "monthly" && (
                <div className="flex flex-col gap-2">
                  <label className="text-sm font-medium text-white">День месяца (1–28)</label>
                  <input
                    type="number"
                    min={1}
                    max={28}
                    value={dayOfMonth}
                    onChange={(e) => setDayOfMonth(e.target.value)}
                    required
                    className="bg-black/40 rounded-xl h-11 px-4 text-white focus:outline-none focus:ring-2 focus:ring-white/20 [color-scheme:dark]"
                  />
                </div>
              )}

              {frequency === "weekly" && (
                <div className="flex flex-col gap-2">
                  <label className="text-sm font-medium text-white">День недели</label>
                  <div className="flex gap-1">
                    {DAY_LABELS.map((label, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => setDayOfWeek(idx)}
                        className={`flex-1 h-9 rounded-xl text-xs font-medium transition-colors ${
                          dayOfWeek === idx
                            ? "bg-white text-black"
                            : "bg-black/40 text-white/60 hover:text-white/80"
                        }`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Description */}
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">
                  Описание <span className="text-white/40 font-normal">— необязательно</span>
                </label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Например: Аренда"
                  className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
                />
              </div>

              {/* Next due date */}
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">Первое срабатывание</label>
                <input
                  type="date"
                  value={nextDueDate}
                  onChange={(e) => setNextDueDate(e.target.value)}
                  required
                  className="bg-black/40 rounded-xl h-11 px-4 text-white focus:outline-none focus:ring-2 focus:ring-white/20 [color-scheme:dark]"
                />
              </div>

              {create.isError && (
                <p className="text-red-400 text-sm">Не удалось создать правило</p>
              )}

              <button
                type="submit"
                disabled={create.isPending || !validAmount || !accountId}
                className="w-full h-12 bg-white text-black font-semibold rounded-xl hover:bg-white/90 active:scale-[0.98] transition-transform disabled:opacity-40"
              >
                {create.isPending ? "Создаём…" : "Создать правило"}
              </button>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ---------------------------------------------------------------------------
// Rules tab
// ---------------------------------------------------------------------------

export default function RulesTab() {
  const [addOpen, setAddOpen] = useState(false);

  const { data: rules = [], isLoading, isError } = useRecurringRules();
  const { data: accounts = [] } = useAccounts();
  const { data: categories = [] } = useCategories();

  const accountMap = useMemo(
    () => Object.fromEntries(accounts.map((a) => [a.id, a])),
    [accounts]
  );
  const categoryMap = useMemo(
    () => Object.fromEntries(categories.map((c) => [c.id, c])),
    [categories]
  );

  function ruleLabel(rule: (typeof rules)[0]): string {
    if (rule.frequency === "monthly") {
      return `${rule.day_of_month}-го числа каждого месяца`;
    }
    const day = rule.day_of_week !== null ? DAY_LABELS[rule.day_of_week] : "?";
    return `Каждую неделю (${day})`;
  }

  return (
    <>
      <div className="flex items-center justify-between px-1">
        <p className="text-sm text-white/40">Регулярные операции</p>
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
        <p className="text-center text-white/40 pt-8 text-sm">Не удалось загрузить правила</p>
      )}

      {!isLoading && !isError && rules.length === 0 && (
        <div className="flex flex-col items-center gap-4 pt-16 text-center">
          <p className="text-white/40 text-sm">
            {accounts.length === 0
              ? "Создайте счёт на вкладке «Счета», затем добавьте правило"
              : "Правил пока нет"}
          </p>
          {accounts.length > 0 && (
            <button
              onClick={() => setAddOpen(true)}
              className="h-12 px-6 bg-white text-black font-semibold rounded-xl hover:bg-white/90 active:scale-[0.98] transition-transform"
            >
              Добавить правило
            </button>
          )}
        </div>
      )}

      {!isLoading && rules.length > 0 && (
        <div className="flex flex-col gap-3">
          {rules.map((rule) => {
            const isExpense = rule.amount_kopecks < 0;
            const account = accountMap[rule.account_id];
            const category = rule.category_id ? categoryMap[rule.category_id] : null;

            return (
              <div
                key={rule.id}
                className={`bg-brand-gray rounded-3xl px-5 py-4 flex items-center gap-3 ${
                  !rule.active ? "opacity-50" : ""
                }`}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-sm font-semibold ${
                        isExpense ? "text-red-400" : "text-green-400"
                      }`}
                    >
                      {formatRub(rule.amount_kopecks)}
                    </span>
                    {category && (
                      <span className="text-xs text-white/50">{category.name}</span>
                    )}
                  </div>
                  <p className="text-xs text-white/40 mt-0.5">{ruleLabel(rule)}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    {account && (
                      <span className="text-xs text-white/30">{account.name}</span>
                    )}
                    {rule.description && (
                      <span className="text-xs text-white/30 truncate">· {rule.description}</span>
                    )}
                  </div>
                </div>
                <RuleToggle ruleId={rule.id} active={rule.active} />
              </div>
            );
          })}
        </div>
      )}

      <AddRuleModal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        accounts={accounts}
        categories={categories}
      />
    </>
  );
}
