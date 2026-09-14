import { useState } from "react";
import { X } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import type { Task, TaskCreatePayload, TaskUpdatePayload, TaskPriority } from "../types";

const PRIORITIES: { value: TaskPriority; label: string }[] = [
  { value: "low", label: "Низкий" },
  { value: "medium", label: "Средний" },
  { value: "high", label: "Высокий" },
];

interface Props {
  open: boolean;
  onClose: () => void;
  onSubmit: (payload: TaskCreatePayload | TaskUpdatePayload) => void;
  initialData?: Task;
  loading?: boolean;
  error?: string;
}

export default function TaskFormModal({
  open,
  onClose,
  onSubmit,
  initialData,
  loading,
  error,
}: Props) {
  const [title, setTitle] = useState(initialData?.title ?? "");
  const [description, setDescription] = useState(initialData?.description ?? "");
  const [priority, setPriority] = useState<TaskPriority>(initialData?.priority ?? "medium");
  const [dueDate, setDueDate] = useState(initialData?.due_date ?? "");
  const [tag, setTag] = useState(initialData?.tag ?? "");

  const isEdit = !!initialData;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const payload: TaskCreatePayload | TaskUpdatePayload = {
      title: title.trim(),
      ...(description.trim() && { description: description.trim() }),
      priority,
      ...(dueDate && { due_date: dueDate }),
      ...(tag.trim() && { tag: tag.trim() }),
    };
    onSubmit(payload);
  }

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
                {isEdit ? "Редактировать задачу" : "Новая задача"}
              </h2>
              <button
                onClick={onClose}
                className="text-white/40 hover:text-white/70 transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              {/* Title */}
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">Заголовок</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Например: Купить билеты"
                  required
                  className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
                />
              </div>

              {/* Description */}
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">
                  Описание{" "}
                  <span className="text-white/40 font-normal">— необязательно</span>
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Детали задачи…"
                  rows={2}
                  className="bg-black/40 rounded-xl px-4 py-3 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20 resize-none"
                />
              </div>

              {/* Priority */}
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">Приоритет</label>
                <div className="flex gap-2">
                  {PRIORITIES.map(({ value, label }) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setPriority(value)}
                      className={`flex-1 h-10 rounded-xl text-sm font-medium transition-colors ${
                        priority === value
                          ? "bg-white text-black"
                          : "bg-black/40 text-white/60 hover:text-white/80"
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Due date */}
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">
                  Срок{" "}
                  <span className="text-white/40 font-normal">— необязательно</span>
                </label>
                <input
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="bg-black/40 rounded-xl h-11 px-4 text-white focus:outline-none focus:ring-2 focus:ring-white/20 [color-scheme:dark]"
                />
              </div>

              {/* Tag */}
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">
                  Тег{" "}
                  <span className="text-white/40 font-normal">— необязательно</span>
                </label>
                <input
                  type="text"
                  value={tag}
                  onChange={(e) => setTag(e.target.value)}
                  placeholder="Например: работа"
                  className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
                />
              </div>

              {error && <p className="text-red-400 text-sm">{error}</p>}

              <button
                type="submit"
                disabled={loading || !title.trim()}
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
