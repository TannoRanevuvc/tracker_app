import { useState } from "react";
import { Flame, Check, Pencil, Archive } from "lucide-react";
import { motion } from "motion/react";
import type { Habit, HabitUpdatePayload } from "../types";
import { useCheckin, useDeleteCheckin, useArchiveHabit, useUpdateHabit } from "../hooks";
import HabitFormModal from "./HabitFormModal";

const DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

function getTodayAppTz(): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Tomsk" }).format(
    new Date()
  );
}

function frequencyLabel(habit: Habit): string {
  if (habit.frequency_type === "daily") return "Ежедневно";
  return (habit.weekly_days ?? [])
    .slice()
    .sort((a, b) => a - b)
    .map((d) => DAYS[d])
    .join(" ");
}

interface Props {
  habit: Habit;
}

export default function HabitCard({ habit }: Props) {
  const [editOpen, setEditOpen] = useState(false);

  const checkin = useCheckin();
  const deleteCheckin = useDeleteCheckin();
  const archive = useArchiveHabit();
  const update = useUpdateHabit(habit.id);

  function handleToggle() {
    if (habit.done_today) {
      deleteCheckin.mutate({ habitId: habit.id, date: getTodayAppTz() });
    } else {
      checkin.mutate({ habitId: habit.id });
    }
  }

  function handleEdit(payload: HabitUpdatePayload) {
    update.mutate(payload, { onSuccess: () => setEditOpen(false) });
  }

  const actionPending =
    checkin.isPending || deleteCheckin.isPending || archive.isPending;

  return (
    <>
      <motion.div
        className="bg-brand-gray rounded-3xl p-5 flex flex-col gap-4"
        layout
      >
        {/* Header row */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex flex-col gap-0.5 min-w-0">
            <span
              className={`font-semibold text-base truncate ${
                habit.archived_at ? "text-white/40" : "text-white"
              }`}
            >
              {habit.name}
            </span>
            <span className="text-xs text-white/40">
              {frequencyLabel(habit)}
              {habit.archived_at && " · архив"}
            </span>
          </div>

          {/* Streak */}
          <div className="flex items-center gap-1 shrink-0">
            <Flame
              size={16}
              className={
                habit.current_streak > 0
                  ? "text-orange-400"
                  : "text-white/20"
              }
            />
            <span
              className={`text-sm font-semibold tabular-nums ${
                habit.current_streak > 0 ? "text-white" : "text-white/30"
              }`}
            >
              {habit.current_streak}
            </span>
          </div>
        </div>

        {/* Actions row */}
        {!habit.archived_at && (
          <div className="flex gap-2">
            {/* Checkin toggle */}
            <button
              onClick={handleToggle}
              disabled={actionPending}
              className={`flex-1 h-10 rounded-xl text-sm font-medium flex items-center justify-center gap-2 transition-colors active:scale-[0.98] disabled:opacity-50 ${
                habit.done_today
                  ? "bg-white/10 text-white/60 hover:bg-white/15"
                  : "bg-white text-black hover:bg-white/90"
              }`}
            >
              {habit.done_today && <Check size={15} />}
              {habit.done_today ? "Выполнено" : "Отметить"}
            </button>

            {/* Edit */}
            <button
              onClick={() => setEditOpen(true)}
              className="h-10 w-10 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/40 hover:text-white/70 transition-colors"
            >
              <Pencil size={15} />
            </button>

            {/* Archive */}
            <button
              onClick={() => archive.mutate(habit.id)}
              disabled={actionPending}
              className="h-10 w-10 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/40 hover:text-white/70 transition-colors disabled:opacity-50"
            >
              <Archive size={15} />
            </button>
          </div>
        )}
      </motion.div>

      <HabitFormModal
        open={editOpen}
        onClose={() => setEditOpen(false)}
        onSubmit={handleEdit}
        initialData={habit}
        loading={update.isPending}
        error={update.isError ? "Не удалось сохранить" : undefined}
      />
    </>
  );
}
