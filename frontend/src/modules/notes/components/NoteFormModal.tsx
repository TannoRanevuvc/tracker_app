import { useState, useEffect } from "react";
import { X, Calendar } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import type { Note, NoteCreatePayload, NoteUpdatePayload } from "../types";
import { NOTE_DEFAULT_COLOR } from "../types";
import { COLOR_PRESETS } from "@/modules/calendar/types";

const PAD = (n: number) => String(n).padStart(2, "0");

function toLocalDatetimeValue(iso: string): { date: string; time: string } {
  const d = new Date(iso);
  return {
    date: `${d.getFullYear()}-${PAD(d.getMonth() + 1)}-${PAD(d.getDate())}`,
    time: `${PAD(d.getHours())}:${PAD(d.getMinutes())}`,
  };
}

function toISOString(date: string, time: string): string {
  return new Date(`${date}T${time}:00`).toISOString();
}

function previewParsedDate(title: string): string | null {
  const dateMatch = title.match(/(\d{1,2})\.(\d{1,2})(?:\.(\d{2,4}))?/);
  if (!dateMatch) return null;
  const day = parseInt(dateMatch[1]);
  const month = parseInt(dateMatch[2]);
  const yearRaw = dateMatch[3];
  let year = yearRaw ? parseInt(yearRaw) : new Date().getFullYear();
  if (year < 100) year += 2000;
  const remaining = title.slice((dateMatch.index ?? 0) + dateMatch[0].length);
  const timeMatch = remaining.match(/(?:в\s+)?(\d{1,2}):(\d{2})/);
  const h = timeMatch ? parseInt(timeMatch[1]) : 0;
  const m = timeMatch ? parseInt(timeMatch[2]) : 0;
  if (month < 1 || month > 12 || day < 1 || day > 31) return null;
  const label = `${PAD(day)}.${PAD(month)}.${year}${timeMatch ? ` в ${PAD(h)}:${PAD(m)}` : ""}`;
  return label;
}

interface Props {
  open: boolean;
  onClose: () => void;
  onSubmit: (payload: NoteCreatePayload | NoteUpdatePayload) => void;
  onDelete?: () => void;
  initialData?: Note;
  loading?: boolean;
  error?: string;
}

export default function NoteFormModal({
  open,
  onClose,
  onSubmit,
  onDelete,
  initialData,
  loading,
  error,
}: Props) {
  const isEdit = !!initialData;

  const [title, setTitle] = useState(initialData?.title ?? "");
  const [body, setBody] = useState(initialData?.body ?? "");
  const [color, setColor] = useState(initialData?.color ?? NOTE_DEFAULT_COLOR);
  const [useExplicitDate, setUseExplicitDate] = useState(false);
  const [date, setDate] = useState("");
  const [time, setTime] = useState("00:00");

  useEffect(() => {
    if (open) {
      setTitle(initialData?.title ?? "");
      setBody(initialData?.body ?? "");
      setColor(initialData?.color ?? NOTE_DEFAULT_COLOR);
      if (initialData?.pinned_at) {
        const { date: d, time: t } = toLocalDatetimeValue(initialData.pinned_at);
        setDate(d);
        setTime(t);
        setUseExplicitDate(true);
      } else {
        setDate("");
        setTime("00:00");
        setUseExplicitDate(false);
      }
    }
  }, [open, initialData]);

  const parsedPreview = !useExplicitDate ? previewParsedDate(title) : null;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const payload: NoteCreatePayload | NoteUpdatePayload = {
      title: title.trim(),
      body: body.trim() || undefined,
      color,
      ...(useExplicitDate && date
        ? { pinned_at: toISOString(date, time) }
        : {}),
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
          <motion.div className="absolute inset-0 bg-neutral-950/60" onClick={onClose} />
          <motion.div
            className="relative w-full max-w-md bg-brand-gray rounded-3xl p-6 flex flex-col gap-5 max-h-[90vh] overflow-y-auto"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 20, opacity: 0 }}
            transition={{ duration: 0.25 }}
          >
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">
                {isEdit ? "Редактировать заметку" : "Новая заметка"}
              </h2>
              <button onClick={onClose} className="text-white/40 hover:text-white/70 transition-colors">
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
                  placeholder="Военка 05.10 в 13:00"
                  required
                  className="bg-black/40 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20"
                />
                {parsedPreview && (
                  <div className="flex items-center gap-1.5 text-[12px] text-yellow-400/80">
                    <Calendar size={11} />
                    <span>Привязка к {parsedPreview}</span>
                  </div>
                )}
              </div>

              {/* Body */}
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-white">
                  Текст <span className="text-white/40 font-normal">— необязательно</span>
                </label>
                <textarea
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  placeholder="Детали заметки…"
                  rows={4}
                  className="bg-black/40 rounded-xl px-4 py-3 text-white placeholder:text-white/20 focus:outline-none focus:ring-2 focus:ring-white/20 resize-none"
                />
              </div>

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
                        color === c
                          ? "scale-125 ring-2 ring-white ring-offset-2 ring-offset-brand-gray"
                          : "hover:scale-110"
                      }`}
                      style={{ backgroundColor: c }}
                    />
                  ))}
                </div>
              </div>

              {/* Explicit date toggle */}
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-white">Указать дату вручную</span>
                <button
                  type="button"
                  onClick={() => setUseExplicitDate((v) => !v)}
                  className={`w-11 h-6 rounded-full transition-colors relative ${
                    useExplicitDate ? "bg-white" : "bg-white/20"
                  }`}
                >
                  <span
                    className={`absolute top-1 w-4 h-4 rounded-full transition-transform ${
                      useExplicitDate ? "left-6 bg-black" : "left-1 bg-white"
                    }`}
                  />
                </button>
              </div>

              {useExplicitDate && (
                <div className="flex gap-3">
                  <div className="flex flex-col gap-2 flex-1">
                    <label className="text-sm font-medium text-white">Дата</label>
                    <input
                      type="date"
                      value={date}
                      onChange={(e) => setDate(e.target.value)}
                      className="bg-black/40 rounded-xl h-11 px-4 text-white focus:outline-none focus:ring-2 focus:ring-white/20"
                    />
                  </div>
                  <div className="flex flex-col gap-2 flex-1">
                    <label className="text-sm font-medium text-white">Время</label>
                    <input
                      type="time"
                      value={time}
                      onChange={(e) => setTime(e.target.value)}
                      className="bg-black/40 rounded-xl h-11 px-4 text-white focus:outline-none focus:ring-2 focus:ring-white/20"
                    />
                  </div>
                </div>
              )}

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
                  Удалить заметку
                </button>
              )}
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
