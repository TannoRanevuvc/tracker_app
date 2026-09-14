import { useState } from "react";
import { Plus, X } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { useProducts, useCreateProduct } from "../hooks";
import type { ProductCreatePayload } from "../types";

const listVariants = {
  visible: { opacity: 1, transition: { staggerChildren: 0.04, delayChildren: 0.05 } },
  hidden: { opacity: 0 },
};
const itemVariants = {
  hidden: { opacity: 0, y: 6 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.25 } },
};

// ---------------------------------------------------------------------------
// Add product modal
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

  const validNum = (s: string) => /^\d+([.,]\d{0,2})?$/.test(s.trim()) && parseFloat(s.replace(",", ".")) >= 0;
  const valid = name.trim().length > 0 && validNum(kcal) && validNum(protein) && validNum(fat) && validNum(carbs);

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
                  placeholder="Гречка"
                  required
                  className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
                />
              </div>

              <p className="text-xs text-white/40 -mb-1">На 100 г продукта</p>

              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-2">
                  <label className="text-sm font-medium text-white">Ккал</label>
                  <input
                    type="text"
                    inputMode="decimal"
                    value={kcal}
                    onChange={(e) => setKcal(e.target.value)}
                    placeholder="110"
                    required
                    className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label className="text-sm font-medium text-white">Белки, г</label>
                  <input
                    type="text"
                    inputMode="decimal"
                    value={protein}
                    onChange={(e) => setProtein(e.target.value)}
                    placeholder="4"
                    required
                    className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label className="text-sm font-medium text-white">Жиры, г</label>
                  <input
                    type="text"
                    inputMode="decimal"
                    value={fat}
                    onChange={(e) => setFat(e.target.value)}
                    placeholder="1"
                    required
                    className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label className="text-sm font-medium text-white">Углев., г</label>
                  <input
                    type="text"
                    inputMode="decimal"
                    value={carbs}
                    onChange={(e) => setCarbs(e.target.value)}
                    placeholder="23"
                    required
                    className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
                  />
                </div>
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
// Products tab
// ---------------------------------------------------------------------------

export default function ProductsTab() {
  const [addOpen, setAddOpen] = useState(false);
  const [search, setSearch] = useState("");
  const { data: products = [], isLoading, isError } = useProducts(search || undefined);

  return (
    <>
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

      {isLoading && (
        <div className="flex justify-center pt-12">
          <div className="h-6 w-6 rounded-full border-2 border-white/20 border-t-white animate-spin" />
        </div>
      )}

      {isError && (
        <p className="text-center text-white/40 pt-12 text-sm">Не удалось загрузить продукты</p>
      )}

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
                  {p.kcal_per_100g} ккал · Б {p.protein_g_per_100g} · Ж {p.fat_g_per_100g} · У {p.carbs_g_per_100g}
                </p>
              </div>
              <span className="text-xs text-white/30 shrink-0">на 100 г</span>
            </motion.div>
          ))}
        </motion.div>
      )}

      <AddProductModal open={addOpen} onClose={() => setAddOpen(false)} />
    </>
  );
}
