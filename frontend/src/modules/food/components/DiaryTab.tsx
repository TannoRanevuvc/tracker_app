import { useMemo, useState } from "react";
import { Plus, Trash2, X, ChevronLeft, ChevronRight } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { useMealEntries, useCreateMealEntry, useDeleteMealEntry, useSummary, useProducts } from "../hooks";
import type { MealEntryCreatePayload, MealType } from "../types";
import { MEAL_TYPE_LABELS, MEAL_TYPES } from "../types";

const listVariants = {
  visible: { opacity: 1, transition: { staggerChildren: 0.04, delayChildren: 0.05 } },
  hidden: { opacity: 0 },
};
const itemVariants = {
  hidden: { opacity: 0, y: 6 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.25 } },
};

function toLocalDateString(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

// ---------------------------------------------------------------------------
// Add meal entry modal
// ---------------------------------------------------------------------------

interface AddEntryModalProps {
  open: boolean;
  onClose: () => void;
  date: string;
}

function AddEntryModal({ open, onClose, date }: AddEntryModalProps) {
  const { data: products = [] } = useProducts();
  const [productId, setProductId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [mealType, setMealType] = useState<MealType>("breakfast");

  const create = useCreateMealEntry();

  function reset() {
    setProductId("");
    setQuantity("");
    setMealType("breakfast");
    create.reset();
  }

  function handleClose() {
    reset();
    onClose();
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const payload: MealEntryCreatePayload = {
      product_id: productId,
      quantity_g: parseFloat(quantity.replace(",", ".")),
      meal_type: mealType,
      logged_at: `${date}T12:00:00+00:00`,
    };
    create.mutate(payload, { onSuccess: handleClose });
  }

  const validQty = /^\d+([.,]\d{0,1})?$/.test(quantity.trim()) && parseFloat(quantity.replace(",", ".")) > 0;

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
              <h2 className="text-lg font-semibold">Добавить приём пищи</h2>
              <button onClick={handleClose} className="text-white/40 hover:text-white/70 transition-colors">
                <X size={20} />
              </button>
            </div>

            {products.length === 0 ? (
              <p className="text-white/40 text-sm text-center py-4">
                Сначала добавьте продукты на вкладке «Продукты»
              </p>
            ) : (
              <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <div className="flex flex-col gap-2">
                  <label className="text-sm font-medium text-white">Продукт</label>
                  <select
                    value={productId}
                    onChange={(e) => setProductId(e.target.value)}
                    required
                    className="bg-black/40 rounded-xl h-11 px-4 text-white focus:outline-none focus:ring-2 focus:ring-white/20 [color-scheme:dark]"
                  >
                    <option value="">Выберите продукт</option>
                    {products.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.kcal_per_100g} ккал/100г)
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex flex-col gap-2">
                  <label className="text-sm font-medium text-white">Вес порции, г</label>
                  <input
                    type="text"
                    inputMode="decimal"
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                    placeholder="200"
                    required
                    className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
                  />
                </div>

                <div className="flex flex-col gap-2">
                  <label className="text-sm font-medium text-white">Приём пищи</label>
                  <div className="grid grid-cols-2 gap-2">
                    {MEAL_TYPES.map((t) => (
                      <button
                        key={t}
                        type="button"
                        onClick={() => setMealType(t)}
                        className={`h-10 rounded-xl text-sm font-medium transition-colors ${
                          mealType === t
                            ? "bg-white text-black"
                            : "bg-black/40 text-white/60 hover:text-white/80"
                        }`}
                      >
                        {MEAL_TYPE_LABELS[t]}
                      </button>
                    ))}
                  </div>
                </div>

                {create.isError && (
                  <p className="text-red-400 text-sm">Не удалось добавить запись</p>
                )}

                <button
                  type="submit"
                  disabled={create.isPending || !validQty || !productId}
                  className="w-full h-12 bg-white text-black font-semibold rounded-xl hover:bg-white/90 active:scale-[0.98] transition-transform disabled:opacity-40 mt-1"
                >
                  {create.isPending ? "Сохраняем…" : "Добавить"}
                </button>
              </form>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ---------------------------------------------------------------------------
// Summary card
// ---------------------------------------------------------------------------

interface SummaryCardProps {
  date: string;
}

function SummaryCard({ date }: SummaryCardProps) {
  const { data: summary } = useSummary(date);
  if (!summary) return null;

  const pct =
    summary.kcal_goal != null && summary.kcal_goal > 0
      ? Math.min(100, Math.round((summary.kcal_total / summary.kcal_goal) * 100))
      : null;

  return (
    <div className="bg-brand-gray rounded-3xl px-5 py-4 flex flex-col gap-3">
      <div className="flex items-end justify-between">
        <div className="flex items-end gap-1">
          <span className="text-2xl font-semibold">{summary.kcal_total}</span>
          <span className="text-white/40 text-sm mb-0.5">
            {summary.kcal_goal != null ? `/ ${summary.kcal_goal} ккал` : "ккал"}
          </span>
        </div>
        {summary.goal_reached && (
          <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-lg">Цель достигнута</span>
        )}
      </div>

      {pct != null && (
        <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${summary.goal_reached ? "bg-green-400" : "bg-white/60"}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      )}

      <div className="flex gap-4 text-xs text-white/50">
        <span>Б {summary.protein_total} г</span>
        <span>Ж {summary.fat_total} г</span>
        <span>У {summary.carbs_total} г</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Diary tab
// ---------------------------------------------------------------------------

export default function DiaryTab() {
  const today = toLocalDateString(new Date());
  const [date, setDate] = useState(today);
  const [addOpen, setAddOpen] = useState(false);

  const { data: entries = [], isLoading, isError } = useMealEntries(date);
  const { data: products = [] } = useProducts();
  const deleteEntry = useDeleteMealEntry(date);

  const productMap = useMemo(
    () => Object.fromEntries(products.map((p) => [p.id, p])),
    [products]
  );

  const grouped = useMemo(() => {
    const map: Record<MealType, typeof entries> = {
      breakfast: [],
      lunch: [],
      dinner: [],
      snack: [],
    };
    for (const e of entries) {
      map[e.meal_type].push(e);
    }
    return map;
  }, [entries]);

  function prevDay() {
    const d = new Date(date + "T00:00:00");
    d.setDate(d.getDate() - 1);
    setDate(toLocalDateString(d));
  }

  function nextDay() {
    const d = new Date(date + "T00:00:00");
    d.setDate(d.getDate() + 1);
    setDate(toLocalDateString(d));
  }

  function formatDateLabel(iso: string): string {
    if (iso === today) return "Сегодня";
    const d = new Date(iso + "T00:00:00");
    return d.toLocaleDateString("ru-RU", { day: "numeric", month: "long" });
  }

  const hasEntries = entries.length > 0;

  return (
    <>
      {/* Date navigator */}
      <div className="flex items-center justify-between px-1">
        <button
          onClick={prevDay}
          className="h-8 w-8 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/50 hover:text-white transition-colors"
        >
          <ChevronLeft size={16} />
        </button>
        <span className="text-sm font-medium">{formatDateLabel(date)}</span>
        <button
          onClick={nextDay}
          disabled={date >= today}
          className="h-8 w-8 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/50 hover:text-white transition-colors disabled:opacity-30"
        >
          <ChevronRight size={16} />
        </button>
      </div>

      <SummaryCard date={date} />

      <div className="flex items-center justify-between px-1">
        <p className="text-sm text-white/40">{hasEntries ? "Записи" : ""}</p>
        <button
          onClick={() => setAddOpen(true)}
          className="h-8 w-8 rounded-xl bg-white text-black flex items-center justify-center hover:bg-white/90 active:scale-[0.98] transition-transform"
        >
          <Plus size={16} />
        </button>
      </div>

      {isLoading && (
        <div className="flex justify-center pt-8">
          <div className="h-6 w-6 rounded-full border-2 border-white/20 border-t-white animate-spin" />
        </div>
      )}

      {isError && (
        <p className="text-center text-white/40 pt-8 text-sm">Не удалось загрузить данные</p>
      )}

      {!isLoading && !isError && !hasEntries && (
        <div className="flex flex-col items-center gap-4 pt-10 text-center">
          <p className="text-white/40 text-sm">Записей за этот день нет</p>
          <button
            onClick={() => setAddOpen(true)}
            className="h-12 px-6 bg-white text-black font-semibold rounded-xl hover:bg-white/90 active:scale-[0.98] transition-transform"
          >
            Добавить приём пищи
          </button>
        </div>
      )}

      {!isLoading && hasEntries && (
        <motion.div
          className="flex flex-col gap-3"
          variants={listVariants}
          initial="hidden"
          animate="visible"
        >
          {MEAL_TYPES.filter((t) => grouped[t].length > 0).map((mealType) => (
            <div key={mealType} className="flex flex-col gap-2">
              <p className="text-xs font-medium text-white/40 px-1">{MEAL_TYPE_LABELS[mealType]}</p>
              {grouped[mealType].map((entry) => {
                const product = productMap[entry.product_id];
                return (
                  <motion.div
                    key={entry.id}
                    variants={itemVariants}
                    className="bg-brand-gray rounded-3xl px-5 py-4 flex items-center gap-3"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">
                        {product?.name ?? "—"}
                      </p>
                      <p className="text-xs text-white/40 mt-0.5">
                        {entry.quantity_g} г · {entry.kcal} ккал · Б {entry.protein_g} · Ж {entry.fat_g} · У {entry.carbs_g}
                      </p>
                    </div>
                    <button
                      onClick={() => deleteEntry.mutate(entry.id)}
                      disabled={deleteEntry.isPending}
                      className="h-8 w-8 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/30 hover:text-red-400 transition-colors disabled:opacity-40 shrink-0"
                    >
                      <Trash2 size={13} />
                    </button>
                  </motion.div>
                );
              })}
            </div>
          ))}
        </motion.div>
      )}

      <AddEntryModal open={addOpen} onClose={() => setAddOpen(false)} date={date} />
    </>
  );
}
