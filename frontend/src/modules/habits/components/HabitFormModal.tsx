import { useState } from "react";
import { X } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import type { Habit, HabitCreatePayload, HabitUpdatePayload } from "../types";

const DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

interface Props {
  open: boolean;
  onClose: () => void;
  onSubmit: (payload: HabitCreatePayload | HabitUpdatePayload) => void;
  initialData?: Habit;
  loading?: boolean;
  error?: string;
}

export default function HabitFormModal({
  open,
  onClose,
  onSubmit,
  initialData,
  loading,
  error,
}: Props) {
  const [name, setName] = useState(initialData?.name ?? "");
  const [freqType, setFreqType] = useState<"daily" | "weekly_days">(
    initialData?.frequency_type ?? "daily"
  );
  const [selectedDays, setSelectedDays] = useState<number[]>(
    initialData?.weekly_days ?? []
  );

  function toggleDay(day: number) {
    setSelectedDays((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day]
    );
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (freqType === "weekly_days" && selectedDays.length === 0) return;
    const payload: HabitCreatePayload | HabitUpdatePayload =
      freqType === "daily"
        ? { name, frequency_type: "daily" }
        : { name, frequency_type: "weekly_days", weekly_days: selectedDays };
    onSubmit(payload);
  }

  const isEdit = !!initialData;

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
          <motion.div
            className="absolute inset-0 bg-black/60"
            onClick={onClose}
          />
          <motion.div
            className="relative w-full max-w-md bg-brand-gray rounded-3xl p-6 flex flex-col gap-5"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 20, opacity: 0 }}
            transition={{ duration: 0.25 }}
          >
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">
                {isEdit ? "Редактировать привычку" : "Новая привычка"}
              </h2>
              <button
                onClick={onClose}
                className="text-white/40 hover:text-white/70 transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">
                  Название
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Например: Бег"
                  required
                  className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20 border-none"
                />
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">
                  Частота
                </label>
                <div className="flex gap-2">
                  {(
                    [
                      ["daily", "Ежедневно"],
                      ["weekly_days", "По дням"],
                    ] as const
                  ).map(([val, label]) => (
                    <button
                      key={val}
                      type="button"
                      onClick={() => setFreqType(val)}
                      className={`flex-1 h-10 rounded-xl text-sm font-medium transition-colors ${
                        freqType === val
                          ? "bg-white text-black"
                          : "bg-black/40 text-white/60 hover:text-white/80"
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {freqType === "weekly_days" && (
                <div className="flex flex-col gap-2">
                  <label className="text-sm font-medium text-white">Дни</label>
                  <div className="flex gap-1.5">
                    {DAYS.map((label, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => toggleDay(idx)}
                        className={`flex-1 h-9 rounded-xl text-xs font-medium transition-colors ${
                          selectedDays.includes(idx)
                            ? "bg-white text-black"
                            : "bg-black/40 text-white/40 hover:text-white/70"
                        }`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                  {selectedDays.length === 0 && (
                    <p className="text-xs text-white/40">
                      Выберите хотя бы один день
                    </p>
                  )}
                </div>
              )}

              {error && <p className="text-red-400 text-sm">{error}</p>}

              <button
                type="submit"
                disabled={
                  loading ||
                  !name.trim() ||
                  (freqType === "weekly_days" && selectedDays.length === 0)
                }
                className="w-full h-12 bg-white text-black font-semibold rounded-xl hover:bg-white/90 active:scale-[0.98] transition-transform disabled:opacity-40 mt-1"
              >
                {loading ? "Сохраняем…" : isEdit ? "Сохранить" : "Создать"}
              </button>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
