import { useState } from "react";
import { Check, RotateCcw, Pencil, Trash2, AlertCircle } from "lucide-react";
import { motion } from "motion/react";
import type { Task, TaskUpdatePayload } from "../types";
import { useCompleteTask, useReopenTask, useDeleteTask, useUpdateTask } from "../hooks";
import TaskFormModal from "./TaskFormModal";

const PRIORITY_DOT: Record<string, string> = {
  high: "bg-red-400",
  medium: "bg-yellow-400",
  low: "bg-white/30",
};

const PRIORITY_LABEL: Record<string, string> = {
  high: "Высокий",
  medium: "Средний",
  low: "Низкий",
};

function formatDate(iso: string): string {
  return new Date(iso + "T00:00:00").toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "short",
  });
}

interface Props {
  task: Task;
}

export default function TaskCard({ task }: Props) {
  const [editOpen, setEditOpen] = useState(false);

  const complete = useCompleteTask();
  const reopen = useReopenTask();
  const remove = useDeleteTask();
  const update = useUpdateTask(task.id);

  const actionPending = complete.isPending || reopen.isPending || remove.isPending;
  const isDone = task.status === "done";

  function handleEdit(payload: TaskUpdatePayload) {
    update.mutate(payload, { onSuccess: () => setEditOpen(false) });
  }

  return (
    <>
      <motion.div
        className="bg-brand-gray rounded-3xl p-5 flex flex-col gap-4"
        layout
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex flex-col gap-1 min-w-0 flex-1">
            <span
              className={`font-semibold text-base leading-snug ${
                isDone ? "line-through text-white/40" : "text-white"
              }`}
            >
              {task.title}
            </span>

            {task.description && (
              <span className="text-sm text-white/50 line-clamp-2">
                {task.description}
              </span>
            )}

            {/* Meta row */}
            <div className="flex items-center flex-wrap gap-x-3 gap-y-1 mt-0.5">
              {/* Priority */}
              <div className="flex items-center gap-1.5">
                <span
                  className={`w-1.5 h-1.5 rounded-full shrink-0 ${PRIORITY_DOT[task.priority]}`}
                />
                <span className="text-xs text-white/40">
                  {PRIORITY_LABEL[task.priority]}
                </span>
              </div>

              {/* Due date */}
              {task.due_date && (
                <div className="flex items-center gap-1">
                  {task.is_overdue && (
                    <AlertCircle size={12} className="text-red-400 shrink-0" />
                  )}
                  <span
                    className={`text-xs ${
                      task.is_overdue ? "text-red-400" : "text-white/40"
                    }`}
                  >
                    {formatDate(task.due_date)}
                  </span>
                </div>
              )}

              {/* Tag */}
              {task.tag && (
                <span className="text-xs px-2 py-0.5 bg-white/8 rounded-full text-white/50">
                  {task.tag}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          {/* Complete / Reopen */}
          {!isDone ? (
            <button
              onClick={() => complete.mutate(task.id)}
              disabled={actionPending}
              className="flex-1 h-10 rounded-xl text-sm font-medium flex items-center justify-center gap-2 bg-white text-black hover:bg-white/90 active:scale-[0.98] transition-all disabled:opacity-50"
            >
              <Check size={15} />
              Выполнено
            </button>
          ) : (
            <button
              onClick={() => reopen.mutate(task.id)}
              disabled={actionPending}
              className="flex-1 h-10 rounded-xl text-sm font-medium flex items-center justify-center gap-2 bg-white/10 text-white/60 hover:bg-white/15 active:scale-[0.98] transition-all disabled:opacity-50"
            >
              <RotateCcw size={14} />
              Открыть снова
            </button>
          )}

          {/* Edit */}
          <button
            onClick={() => setEditOpen(true)}
            className="h-10 w-10 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/40 hover:text-white/70 transition-colors"
          >
            <Pencil size={15} />
          </button>

          {/* Delete */}
          <button
            onClick={() => remove.mutate(task.id)}
            disabled={actionPending}
            className="h-10 w-10 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/40 hover:text-red-400 transition-colors disabled:opacity-50"
          >
            <Trash2 size={15} />
          </button>
        </div>
      </motion.div>

      <TaskFormModal
        open={editOpen}
        onClose={() => setEditOpen(false)}
        onSubmit={handleEdit}
        initialData={task}
        loading={update.isPending}
        error={update.isError ? "Не удалось сохранить" : undefined}
      />
    </>
  );
}
