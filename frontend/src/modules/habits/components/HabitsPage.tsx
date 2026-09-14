import { useState } from "react";
import { Plus } from "lucide-react";
import { motion } from "motion/react";
import { useHabits, useCreateHabit } from "../hooks";
import type { HabitCreatePayload, HabitUpdatePayload } from "../types";
import HabitCard from "./HabitCard";
import HabitFormModal from "./HabitFormModal";

const listVariants = {
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.07, delayChildren: 0.1 },
  },
  hidden: { opacity: 0 },
};

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35 } },
};

export default function HabitsPage() {
  const [showArchived, setShowArchived] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);

  const { data: habits = [], isLoading, isError } = useHabits(showArchived);
  const createHabit = useCreateHabit();

  // Sort: undone first, then alphabetically
  const sorted = [...habits].sort((a, b) => {
    if (a.done_today !== b.done_today) return a.done_today ? 1 : -1;
    return a.name.localeCompare(b.name, "ru");
  });

  function handleCreate(payload: HabitCreatePayload | HabitUpdatePayload) {
    createHabit.mutate(payload as HabitCreatePayload, {
      onSuccess: () => setCreateOpen(false),
    });
  }

  return (
    <div className="max-w-lg mx-auto py-4 px-2 flex flex-col gap-4">
      {/* Page header */}
      <div className="flex items-center justify-between px-1">
        <h1 className="text-xl font-semibold">Привычки</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowArchived((v) => !v)}
            className={`text-xs px-3 h-8 rounded-xl transition-colors ${
              showArchived
                ? "bg-white/15 text-white/80"
                : "text-white/40 hover:text-white/60"
            }`}
          >
            Архив
          </button>
          <button
            onClick={() => setCreateOpen(true)}
            className="h-8 w-8 rounded-xl bg-white text-black flex items-center justify-center hover:bg-white/90 active:scale-[0.98] transition-transform"
          >
            <Plus size={16} />
          </button>
        </div>
      </div>

      {/* Content */}
      {isLoading && (
        <div className="flex justify-center pt-12">
          <div className="h-6 w-6 rounded-full border-2 border-white/20 border-t-white animate-spin" />
        </div>
      )}

      {isError && (
        <p className="text-center text-white/40 pt-12 text-sm">
          Не удалось загрузить привычки
        </p>
      )}

      {!isLoading && !isError && sorted.length === 0 && (
        <div className="flex flex-col items-center gap-4 pt-16 text-center">
          <p className="text-white/40 text-sm">
            {showArchived
              ? "Архивных привычек нет"
              : "Привычек пока нет — добавь первую"}
          </p>
          {!showArchived && (
            <button
              onClick={() => setCreateOpen(true)}
              className="h-12 px-6 bg-white text-black font-semibold rounded-xl hover:bg-white/90 active:scale-[0.98] transition-transform"
            >
              Добавить привычку
            </button>
          )}
        </div>
      )}

      {!isLoading && sorted.length > 0 && (
        <motion.div
          className="flex flex-col gap-3"
          variants={listVariants}
          initial="hidden"
          animate="visible"
        >
          {sorted.map((habit) => (
            <motion.div key={habit.id} variants={itemVariants}>
              <HabitCard habit={habit} />
            </motion.div>
          ))}
        </motion.div>
      )}

      <HabitFormModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onSubmit={handleCreate}
        loading={createHabit.isPending}
        error={createHabit.isError ? "Не удалось создать привычку" : undefined}
      />
    </div>
  );
}
