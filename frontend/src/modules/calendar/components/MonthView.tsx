import { useMemo } from "react";
import type { CalendarItem } from "../types";

const WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

function startOfMonth(year: number, month: number): Date {
  return new Date(year, month, 1);
}

function buildCalendarDays(year: number, month: number): Date[] {
  const first = startOfMonth(year, month);
  // Monday=0, Sun=6 mapping (getDay returns Sun=0)
  const firstDow = (first.getDay() + 6) % 7;
  const days: Date[] = [];
  // Days from previous month
  for (let i = firstDow - 1; i >= 0; i--) {
    days.push(new Date(year, month, -i));
  }
  // Days of current month
  const lastDay = new Date(year, month + 1, 0).getDate();
  for (let d = 1; d <= lastDay; d++) {
    days.push(new Date(year, month, d));
  }
  // Fill to complete weeks
  while (days.length % 7 !== 0) {
    const next = days[days.length - 1];
    days.push(new Date(next.getFullYear(), next.getMonth(), next.getDate() + 1));
  }
  return days;
}

function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function dateKey(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

interface Props {
  year: number;
  month: number;
  items: CalendarItem[];
  selectedDay: Date | null;
  onDayClick: (day: Date) => void;
}

export default function MonthView({ year, month, items, selectedDay, onDayClick }: Props) {
  const today = new Date();
  const days = useMemo(() => buildCalendarDays(year, month), [year, month]);

  const itemsByDay = useMemo(() => {
    const map: Record<string, CalendarItem[]> = {};
    for (const item of items) {
      const d = new Date(item.start_at);
      const key = dateKey(d);
      if (!map[key]) map[key] = [];
      map[key].push(item);
    }
    return map;
  }, [items]);

  return (
    <div className="w-full">
      {/* Weekday headers */}
      <div className="grid grid-cols-7 mb-1">
        {WEEKDAYS.map((day) => (
          <div
            key={day}
            className="text-center text-xs text-white/40 font-medium py-2"
          >
            {day}
          </div>
        ))}
      </div>

      {/* Day grid */}
      <div className="grid grid-cols-7 gap-px bg-white/5 rounded-2xl overflow-hidden">
        {days.map((day, i) => {
          const isCurrentMonth = day.getMonth() === month;
          const isToday = isSameDay(day, today);
          const isSelected = selectedDay ? isSameDay(day, selectedDay) : false;
          const key = dateKey(day);
          const dayItems = itemsByDay[key] ?? [];
          const visible = dayItems.slice(0, 3);
          const overflow = dayItems.length - 3;

          return (
            <button
              key={i}
              onClick={() => onDayClick(day)}
              className={`bg-black min-h-[72px] p-1.5 flex flex-col items-start text-left transition-colors hover:bg-white/5 ${
                isSelected ? "bg-white/10" : ""
              }`}
            >
              {/* Day number */}
              <span
                className={`text-sm font-medium w-7 h-7 flex items-center justify-center rounded-full mb-1 ${
                  isToday
                    ? "bg-white text-black"
                    : isSelected
                    ? "bg-white/20 text-white"
                    : isCurrentMonth
                    ? "text-white"
                    : "text-white/25"
                }`}
              >
                {day.getDate()}
              </span>

              {/* Event pills */}
              <div className="flex flex-col gap-px w-full">
                {visible.map((item) => (
                  <div
                    key={item.id}
                    className="text-[10px] leading-tight rounded px-1 py-0.5 truncate font-medium"
                    style={
                      item.source === "task"
                        ? {
                            backgroundColor: "rgba(107,114,128,0.3)",
                            color: "#9ca3af",
                            border: "1px solid rgba(107,114,128,0.4)",
                          }
                        : item.source === "note"
                        ? {
                            backgroundColor: `${item.color ?? "#eab308"}30`,
                            color: item.color ?? "#eab308",
                            border: `1px dashed ${item.color ?? "#eab308"}80`,
                          }
                        : {
                            backgroundColor: `${item.color ?? "#3b82f6"}80`,
                            color: item.color ?? "#3b82f6",
                          }
                    }
                  >
                    {item.title}
                  </div>
                ))}
                {overflow > 0 && (
                  <span className="text-[10px] text-white/40 px-1">+{overflow} ещё</span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
