import { useState } from "react";
import { Globe, Plus, X } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import {
  useProducts,
  useCreateProduct,
  useSearchExternal,
  useImportExternal,
} from "../hooks";
import type { ExternalProductPreview, ProductCreatePayload } from "../types";

const listVariants = {
  visible: { opacity: 1, transition: { staggerChildren: 0.04, delayChildren: 0.05 } },
  hidden: { opacity: 0 },
};
const itemVariants = {
  hidden: { opacity: 0, y: 6 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.25 } },
};

// ---------------------------------------------------------------------------
// Add product modal (manual entry, Stage 1 — unchanged)
// ---------------------------------------------------------------------------

interface AddProductModalProps {
  open: boolean;
  onClose: () => void;
}

function AddProductModal({ open, onClose }: AddProductModalProps) {
  const [name, setName] = useState("");
  const [kcal, setKcal] = useState("");
  const [protein, setProtein] = useState("");
  const [fat, setFat] = useState("");
  const [carbs, setCarbs] = useState("");

  const create = useCreateProduct();

  function reset() {
    setName("");
    setKcal("");
    setProtein("");
    setFat("");
    setCarbs("");
    create.reset();
  }

  function handleClose() {
    reset();
    onClose();
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const payload: ProductCreatePayload = {
      name: name.trim(),
      kcal_per_100g: parseFloat(kcal.replace(",", ".")),
      protein_g_per_100g: parseFloat(protein.replace(",", ".")),
      fat_g_per_100g: parseFloat(fat.replace(",", ".")),
      carbs_g_per_100g: parseFloat(carbs.replace(",", ".")),
    };
    create.mutate(payload, { onSuccess: handleClose });
  }

  const validNum = (s: string) =>
    /^\d+([.,]\d{0,2})?$/.test(s.trim()) && parseFloat(s.replace(",", ".")) >= 0;
  const valid =
    name.trim().length > 0 &&
    validNum(kcal) &&
    validNum(protein) &&
    validNum(fat) &&
    validNum(carbs);

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
              <h2 className="text-lg font-semibold">Новый продукт</h2>
              <button
                onClick={handleClose}
                className="text-white/40 hover:text-white/70 transition-colors"
              >
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
                  placeholder="Гречка"
                  required
                  className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
                />
              </div>

              <p className="text-xs text-white/40 -mb-1">На 100 г продукта</p>

              <div className="grid grid-cols-2 gap-3">
                {(
                  [
                    { label: "Ккал", value: kcal, set: setKcal, placeholder: "110" },
                    { label: "Белки, г", value: protein, set: setProtein, placeholder: "4" },
                    { label: "Жиры, г", value: fat, set: setFat, placeholder: "1" },
                    { label: "Углев., г", value: carbs, set: setCarbs, placeholder: "23" },
                  ] as const
                ).map(({ label, value, set, placeholder }) => (
                  <div key={label} className="flex flex-col gap-2">
                    <label className="text-sm font-medium text-white">{label}</label>
                    <input
                      type="text"
                      inputMode="decimal"
                      value={value}
                      onChange={(e) => set(e.target.value)}
                      placeholder={placeholder}
                      required
                      className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
                    />
                  </div>
                ))}
              </div>

              {create.isError && (
                <p className="text-red-400 text-sm">Не удалось создать продукт</p>
              )}

              <button
                type="submit"
                disabled={create.isPending || !valid}
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
// External search section (Stage 2 — Open Food Facts)
// ---------------------------------------------------------------------------

interface ExternalSearchSectionProps {
  /** Pre-fills the search field with the current local search query. */
  initialQuery: string;
}

function ExternalSearchSection({ initialQuery }: ExternalSearchSectionProps) {
  const [input, setInput] = useState(initialQuery);
  // Only fires a query when the user submits the form.
  const [committed, setCommitted] = useState("");

  const {
    data: results = [],
    isLoading,
    isError,
    isFetching,
  } = useSearchExternal(committed, committed.length > 0);

  const importMutation = useImportExternal();
  const [importedIds, setImportedIds] = useState<Set<string>>(new Set());

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const q = input.trim();
    if (q) setCommitted(q);
  }

  function handleImport(product: ExternalProductPreview) {
    importMutation.mutate(product.external_id, {
      onSuccess: () =>
        setImportedIds((prev) => new Set([...prev, product.external_id])),
    });
  }

  return (
    <div className="flex flex-col gap-3 pt-4 border-t border-white/8">
      <div className="flex items-center gap-1.5 px-1">
        <Globe size={13} className="text-white/40 shrink-0" />
        <span className="text-xs text-white/40 font-medium">Open Food Facts</span>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2 px-1">
        <input
          type="search"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Название или штрихкод…"
          className="flex-1 bg-brand-gray rounded-xl h-10 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20 text-sm"
        />
        <button
          type="submit"
          disabled={!input.trim() || isFetching}
          className="h-10 px-4 rounded-xl bg-white/10 text-white text-sm font-medium hover:bg-white/20 active:scale-[0.98] transition-all disabled:opacity-40 shrink-0"
        >
          {isFetching ? "…" : "Найти"}
        </button>
      </form>

      {isLoading && (
        <div className="flex justify-center py-4">
          <div className="h-5 w-5 rounded-full border-2 border-white/20 border-t-white animate-spin" />
        </div>
      )}

      {isError && (
        <p className="text-center text-white/40 text-sm px-1">
          Open Food Facts недоступен — попробуйте позже
        </p>
      )}

      {!isLoading && !isError && committed && results.length === 0 && (
        <p className="text-center text-white/40 text-sm px-1">Ничего не найдено</p>
      )}

      {results.length > 0 && (
        <motion.div
          className="flex flex-col gap-2"
          variants={listVariants}
          initial="hidden"
          animate="visible"
        >
          {results.map((p) => (
            <motion.div
              key={p.external_id}
              variants={itemVariants}
              className="bg-brand-gray rounded-3xl px-5 py-4 flex items-center gap-3"
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">
                  {p.name || "(без названия)"}
                </p>
                <p className="text-xs text-white/40 mt-0.5">
                  {p.kcal_per_100g} ккал · Б {p.protein_g_per_100g} · Ж{" "}
                  {p.fat_g_per_100g} · У {p.carbs_g_per_100g}
                </p>
              </div>
              <button
                onClick={() => handleImport(p)}
                disabled={
                  importMutation.isPending || importedIds.has(p.external_id)
                }
                className="shrink-0 h-8 px-3 rounded-xl text-xs font-medium bg-white/10 text-white hover:bg-white/20 active:scale-[0.98] transition-all disabled:opacity-40 whitespace-nowrap"
              >
                {importedIds.has(p.external_id) ? "✓ Добавлен" : "Добавить"}
              </button>
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Products tab
// ---------------------------------------------------------------------------

export default function ProductsTab() {
  const [addOpen, setAddOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [offOpen, setOffOpen] = useState(false);

  const { data: products = [], isLoading, isError } = useProducts(search || undefined);

  const emptyWithSearch = !isLoading && !isError && products.length === 0 && search.length > 0;

  return (
    <>
      {/* Search bar + add button */}
      <div className="flex items-center gap-2 px-1">
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Поиск продукта…"
          className="flex-1 bg-brand-gray rounded-xl h-10 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20 text-sm"
        />
        <button
          onClick={() => setAddOpen(true)}
          className="h-10 w-10 rounded-xl bg-white text-black flex items-center justify-center hover:bg-white/90 active:scale-[0.98] transition-transform shrink-0"
        >
          <Plus size={16} />
        </button>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex justify-center pt-12">
          <div className="h-6 w-6 rounded-full border-2 border-white/20 border-t-white animate-spin" />
        </div>
      )}

      {/* Error */}
      {isError && (
        <p className="text-center text-white/40 pt-12 text-sm">
          Не удалось загрузить продукты
        </p>
      )}

      {/* Empty state */}
      {!isLoading && !isError && products.length === 0 && (
        <div className="flex flex-col items-center gap-4 pt-16 text-center">
          <p className="text-white/40 text-sm">
            {search ? `Продукт «${search}» не найден` : "Продуктов ещё нет"}
          </p>
          {!search && (
            <button
              onClick={() => setAddOpen(true)}
              className="h-12 px-6 bg-white text-black font-semibold rounded-xl hover:bg-white/90 active:scale-[0.98] transition-transform"
            >
              Добавить продукт
            </button>
          )}
        </div>
      )}

      {/* Local product list */}
      {!isLoading && products.length > 0 && (
        <motion.div
          className="flex flex-col gap-2"
          variants={listVariants}
          initial="hidden"
          animate="visible"
        >
          {products.map((p) => (
            <motion.div
              key={p.id}
              variants={itemVariants}
              className="bg-brand-gray rounded-3xl px-5 py-4 flex items-center gap-3"
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{p.name}</p>
                <p className="text-xs text-white/40 mt-0.5">
                  {p.kcal_per_100g} ккал · Б {p.protein_g_per_100g} · Ж{" "}
                  {p.fat_g_per_100g} · У {p.carbs_g_per_100g}
                </p>
              </div>
              <span className="text-xs text-white/30 shrink-0">на 100 г</span>
            </motion.div>
          ))}
        </motion.div>
      )}

      {/* OFF toggle — more prominent when local search returned nothing */}
      {!isLoading && !isError && (
        <div className="px-1">
          <button
            onClick={() => setOffOpen((v) => !v)}
            className={`flex items-center gap-2 transition-colors ${
              emptyWithSearch
                ? "text-white/50 hover:text-white/70"
                : "text-white/30 hover:text-white/50"
            }`}
          >
            <Globe size={13} />
            <span className="text-xs">
              {offOpen ? "Скрыть поиск в Open Food Facts" : "Поиск в Open Food Facts"}
            </span>
          </button>
        </div>
      )}

      {/* OFF search section (animated) */}
      <AnimatePresence>
        {offOpen && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.2 }}
          >
            <ExternalSearchSection initialQuery={search} />
          </motion.div>
        )}
      </AnimatePresence>

      <AddProductModal open={addOpen} onClose={() => setAddOpen(false)} />
    </>
  );
}
