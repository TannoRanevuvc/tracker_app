import { useState, useEffect } from "react";
import { X } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import type { CalendarEvent, EventCreatePayload, EventUpdatePayload } from "../types";
import { COLOR_PRESETS, DEFAULT_EVENT_COLOR } from "../types";

interface Props {
  open: boolean;
  onClose: () => void;
  onSubmit: (payload: EventCreatePayload | EventUpdatePayload) => void;
  onDelete?: () => void;
  initialData?: CalendarEvent;
  defaultDate?: string;
  defaultTime?: string;
  loading?: boolean;
  error?: string;
}

function toLocalDatetimeValue(iso: string): { date: string; time: string } {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  const date = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const time = `${pad(d.getHours())}:${pad(d.getMinutes())}`;
  return { date, time };
}

function toISOString(date: string, time: string): string {
  return `${date}T${time}:00`;
}

export default function EventFormModal({
  open,
  onClose,
  onSubmit,
  onDelete,
  initialData,
  defaultDate,
  defaultTime,
  loading,
  error,
}: Props) {
  const isEdit = !!initialData;

  const initDate = initialData
    ? toLocalDatetimeValue(initialData.start_at).date
    : defaultDate ?? new Date().toISOString().slice(0, 10);

  const initStartTime = initialData
    ? toLocalDatetimeValue(initialData.start_at).time
    : defaultTime ?? "09:00";

  const initEndTime = initialData?.end_at
    ? toLocalDatetimeValue(initialData.end_at).time
    : "";

  const [title, setTitle] = useState(initialData?.title ?? "");
  const [description, setDescription] = useState(initialData?.description ?? "");
  const [date, setDate] = useState(initDate);
  const [startTime, setStartTime] = useState(initStartTime);
  const [endTime, setEndTime] = useState(initEndTime);
  const [allDay, setAllDay] = useState(initialData?.all_day ?? false);
  const [color, setColor] = useState(initialData?.color ?? DEFAULT_EVENT_COLOR);

  useEffect(() => {
    if (open) {
      setTitle(initialData?.title ?? "");
      setDescription(initialData?.description ?? "");
      setDate(
        initialData
          ? toLocalDatetimeValue(initialData.start_at).date
          : defaultDate ?? new Date().toISOString().slice(0, 10)
      );
      setStartTime(
        initialData ? toLocalDatetimeValue(initialData.start_at).time : defaultTime ?? "09:00"
      );
      setEndTime(initialData?.end_at ? toLocalDatetimeValue(initialData.end_at).time : "");
      setAllDay(initialData?.all_day ?? false);
      setColor(initialData?.color ?? DEFAULT_EVENT_COLOR);
    }
  }, [open, initialData, defaultDate, defaultTime]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const payload: EventCreatePayload | EventUpdatePayload = {
      title: title.trim(),
      start_at: allDay ? `${date}T00:00:00` : toISOString(date, startTime),
      ...(endTime && !allDay ? { end_at: toISOString(date, endTime) } : {}),
      all_day: allDay,
      color,
      ...(description.trim() ? { description: description.trim() } : {}),
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
          <motion.div className="absolute inset-0 bg-black/60" onClick={onClose} />
          <motion.div
            className="relative w-full max-w-md bg-brand-gray rounded-3xl p-6 flex flex-col gap-5 max-h-[90vh] overflow-y-auto"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 20, opacity: 0 }}
            transition={{ duration: 0.25 }}
          >
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">
                {isEdit ? "Редактировать событие" : "Новое событие"}
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
                <label className="text-sm font-medium text-white">Название</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Например: Встреча с врачом"
                  required
                  className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
                />
              </div>

              {/* All-day toggle */}
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-white">Весь день</span>
                <button
                  type="button"
                  onClick={() => setAllDay((v) => !v)}
                  className={`w-11 h-6 rounded-full transition-colors relative ${
                    allDay ? "bg-white" : "bg-white/20"
                  }`}
                >
                  <span
                    className={`absolute top-1 w-4 h-4 rounded-full transition-transform ${
                      allDay ? "left-6 bg-black" : "left-1 bg-white"
                    }`}
                  />
                </button>
              </div>

              {/* Date */}
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">Дата</label>
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  required
                  className="bg-black/40 rounded-xl h-11 px-4 text-white focus:outline-none focus:ring-2 focus:ring-white/20 [color-scheme:dark]"
                />
              </div>

              {/* Time (hidden when all-day) */}
              {!allDay && (
                <div className="flex gap-3">
                  <div className="flex flex-col gap-2 flex-1">
                    <label className="text-sm font-medium text-white">Начало</label>
                    <input
                      type="time"
                      value={startTime}
                      onChange={(e) => setStartTime(e.target.value)}
                      required
                      className="bg-black/40 rounded-xl h-11 px-4 text-white focus:outline-none focus:ring-2 focus:ring-white/20 [color-scheme:dark]"
                    />
                  </div>
                  <div className="flex flex-col gap-2 flex-1">
                    <label className="text-sm font-medium text-white">
                      Конец <span className="text-white/40 font-normal">— необяз.</span>
                    </label>
                    <input
                      type="time"
                      value={endTime}
                      onChange={(e) => setEndTime(e.target.value)}
                      className="bg-black/40 rounded-xl h-11 px-4 text-white focus:outline-none focus:ring-2 focus:ring-white/20 [color-scheme:dark]"
                    />
                  </div>
                </div>
              )}

              {/* Color */}
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">Цвет</label>
                <div className="flex gap-2 flex-wrap">
                  {COLOR_PRESETS.map((c) => (
                    <button
                      key={c}
                      type="button"
                      onClick={() => setColor(c)}
                      className={`w-8 h-8 rounded-full transition-transform ${
                        color === c ? "scale-125 ring-2 ring-white ring-offset-2 ring-offset-brand-gray" : "hover:scale-110"
                      }`}
                      style={{ backgroundColor: c }}
                    />
                  ))}
                </div>
              </div>

              {/* Description */}
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">
                  Описание <span className="text-white/40 font-normal">— необязательно</span>
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Детали события…"
                  rows={2}
                  className="bg-black/40 rounded-xl px-4 py-3 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20 resize-none"
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

              {isEdit && onDelete && (
                <button
                  type="button"
                  onClick={onDelete}
                  disabled={loading}
                  className="w-full h-11 text-red-400 hover:text-red-300 text-sm font-medium transition-colors disabled:opacity-40"
                >
                  Удалить событие
                </button>
              )}
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
