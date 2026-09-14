import { useState } from "react";
import { Plus } from "lucide-react";
import { motion } from "motion/react";
import { useTasks, type TaskFilter } from "../hooks";
import type { Task, TaskCreatePayload, TaskUpdatePayload } from "../types";
import { useCreateTask } from "../hooks";
import TaskCard from "./TaskCard";
import TaskFormModal from "./TaskFormModal";

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

const FILTERS: { value: TaskFilter; label: string }[] = [
  { value: "all", label: "Все" },
  { value: "active", label: "Активные" },
  { value: "done", label: "Выполнено" },
];

// Assumption: overdue first → future due_date ascending → no due_date → done last
function sortTasks(tasks: Task[]): Task[] {
  return [...tasks].sort((a, b) => {
    const aDone = a.status === "done";
    const bDone = b.status === "done";
    if (aDone !== bDone) return aDone ? 1 : -1;

    if (a.is_overdue !== b.is_overdue) return a.is_overdue ? -1 : 1;

    if (a.due_date && b.due_date) return a.due_date.localeCompare(b.due_date);
    if (a.due_date && !b.due_date) return -1;
    if (!a.due_date && b.due_date) return 1;

    return a.title.localeCompare(b.title, "ru");
  });
}

export default function TasksPage() {
  const [filter, setFilter] = useState<TaskFilter>("all");
  const [createOpen, setCreateOpen] = useState(false);

  const { data: tasks = [], isLoading, isError } = useTasks(filter);
  const createTask = useCreateTask();

  const sorted = sortTasks(tasks);

  function handleCreate(payload: TaskCreatePayload | TaskUpdatePayload) {
    createTask.mutate(payload as TaskCreatePayload, {
      onSuccess: () => setCreateOpen(false),
    });
  }

  return (
    <div className="max-w-lg mx-auto py-4 px-2 flex flex-col gap-4">
      {/* Page header */}
      <div className="flex items-center justify-between px-1">
        <h1 className="text-xl font-semibold">Задачи</h1>
        <button
          onClick={() => setCreateOpen(true)}
          className="h-8 w-8 rounded-xl bg-white text-black flex items-center justify-center hover:bg-white/90 active:scale-[0.98] transition-transform"
        >
          <Plus size={16} />
        </button>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 px-1">
        {FILTERS.map(({ value, label }) => (
          <button
            key={value}
            onClick={() => setFilter(value)}
            className={`px-3 h-8 rounded-xl text-xs font-medium transition-colors ${
              filter === value
                ? "bg-white/15 text-white"
                : "text-white/40 hover:text-white/60"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* States */}
      {isLoading && (
        <div className="flex justify-center pt-12">
          <div className="h-6 w-6 rounded-full border-2 border-white/20 border-t-white animate-spin" />
        </div>
      )}

      {isError && (
        <p className="text-center text-white/40 pt-12 text-sm">
          Не удалось загрузить задачи
        </p>
      )}

      {!isLoading && !isError && sorted.length === 0 && (
        <div className="flex flex-col items-center gap-4 pt-16 text-center">
          <p className="text-white/40 text-sm">
            {filter === "done"
              ? "Выполненных задач нет"
              : filter === "active"
              ? "Активных задач нет"
              : "Задач пока нет — добавь первую"}
          </p>
          {filter !== "done" && (
            <button
              onClick={() => setCreateOpen(true)}
              className="h-12 px-6 bg-white text-black font-semibold rounded-xl hover:bg-white/90 active:scale-[0.98] transition-transform"
            >
              Добавить задачу
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
          {sorted.map((task) => (
            <motion.div key={task.id} variants={itemVariants}>
              <TaskCard task={task} />
            </motion.div>
          ))}
        </motion.div>
      )}

      <TaskFormModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onSubmit={handleCreate}
        loading={createTask.isPending}
        error={createTask.isError ? "Не удалось создать задачу" : undefined}
      />
    </div>
  );
}
