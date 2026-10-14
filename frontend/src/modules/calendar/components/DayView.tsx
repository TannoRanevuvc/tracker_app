import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { CalendarItem } from "../types";

const HOUR_HEIGHT = 64;
const HOURS = Array.from({ length: 24 }, (_, i) => i);

function pad(n: number) {
  return String(n).padStart(2, "0");
}

function timeToMinutes(iso: string): number {
  const d = new Date(iso);
  return d.getHours() * 60 + d.getMinutes();
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function getNowTop(day: Date): number | null {
  const now = new Date();
  const isToday =
    day.getFullYear() === now.getFullYear() &&
    day.getMonth() === now.getMonth() &&
    day.getDate() === now.getDate();
  if (!isToday) return null;
  return ((now.getHours() * 60 + now.getMinutes()) / 60) * HOUR_HEIGHT;
}

interface PositionedItem {
  item: CalendarItem;
  top: number;
  height: number;
  column: number;
  totalColumns: number;
}

function layoutItems(items: CalendarItem[]): PositionedItem[] {
  const timed = items.filter((i) => !i.all_day && i.start_at);
  timed.sort((a, b) => timeToMinutes(a.start_at) - timeToMinutes(b.start_at));

  const positioned: PositionedItem[] = [];
  const groups: CalendarItem[][] = [];

  for (const item of timed) {
    const startMin = timeToMinutes(item.start_at);
    const endMin = item.end_at ? timeToMinutes(item.end_at) : startMin + 60;

    let placed = false;
    for (const group of groups) {
      const lastEnd = Math.max(
        ...group.map((gi) =>
          gi.end_at ? timeToMinutes(gi.end_at) : timeToMinutes(gi.start_at) + 60
        )
      );
      if (startMin >= lastEnd) {
        group.push(item);
        placed = true;
        break;
      }
    }
    if (!placed) groups.push([item]);

    const top = (startMin / 60) * HOUR_HEIGHT;
    const height = Math.max(((endMin - startMin) / 60) * HOUR_HEIGHT, 24);
    positioned.push({ item, top, height, column: 0, totalColumns: 1 });
  }

  for (const p of positioned) {
    const startMin = timeToMinutes(p.item.start_at);
    const endMin = p.item.end_at ? timeToMinutes(p.item.end_at) : startMin + 60;
    const overlapping = positioned.filter((q) => {
      const qStart = timeToMinutes(q.item.start_at);
      const qEnd = q.item.end_at ? timeToMinutes(q.item.end_at) : qStart + 60;
      return q !== p && qStart < endMin && qEnd > startMin;
    });
    if (overlapping.length > 0) {
      p.totalColumns = overlapping.length + 1;
      const usedColumns = overlapping.map((q) => q.column);
      let col = 0;
      while (usedColumns.includes(col)) col++;
      p.column = col;
    }
  }

  return positioned;
}

interface Props {
  day: Date;
  items: CalendarItem[];
  onSlotClick: (time: string) => void;
  onEventClick: (item: CalendarItem) => void;
}

export default function DayView({ day, items, onSlotClick, onEventClick }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [nowTop, setNowTop] = useState<number | null>(() => getNowTop(day));

  // Update time indicator every minute
  useEffect(() => {
    setNowTop(getNowTop(day));
    const id = setInterval(() => setNowTop(getNowTop(day)), 60_000);
    return () => clearInterval(id);
  }, [day.toDateString()]);

  // useLayoutEffect runs after React commits the DOM but before the browser paints,
  // so the flex layout is already calculated and scrollTop sticks immediately.
  // We avoid reading clientHeight entirely — fixed 2.5h offset above current time
  // (same visual as Google Calendar) removes any dependency on container height.
  useLayoutEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const now = new Date();
    if (day.toDateString() === now.toDateString()) {
      const minutes = now.getHours() * 60 + now.getMinutes();
      el.scrollTop = Math.max(0, (minutes / 60 - 2.5) * HOUR_HEIGHT);
    } else {
      el.scrollTop = 8 * HOUR_HEIGHT;
    }
  }, [day.toDateString()]);

  const allDayItems = items.filter((i) => i.all_day);
  const positioned = layoutItems(items);

  // Current time label
  const now = new Date();
  const nowLabel = `${pad(now.getHours())}:${pad(now.getMinutes())}`;

  function handleHourClick(hour: number) {
    onSlotClick(`${pad(hour)}:00`);
  }

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* All-day strip */}
      {allDayItems.length > 0 && (
        <div className="px-4 py-2 border-b border-white/10 flex flex-col gap-1">
          <span className="text-xs text-white/40 mb-1">Весь день</span>
          {allDayItems.map((item) => (
            <button
              key={item.id}
              onClick={() => onEventClick(item)}
              className="text-xs rounded-lg px-3 py-1.5 text-left font-medium transition-opacity hover:opacity-80"
              style={{
                backgroundColor:
                  item.source === "task"
                    ? "rgba(107,114,128,0.2)"
                    : `${item.color ?? "#3b82f6"}30`,
                color: item.source === "task" ? "#9ca3af" : (item.color ?? "#3b82f6"),
                border:
                  item.source === "task"
                    ? "1px dashed rgba(107,114,128,0.5)"
                    : `1px solid ${item.color ?? "#3b82f6"}60`,
              }}
            >
              {item.title}
              {item.source === "task" && (
                <span className="ml-1 text-white/30">· задача</span>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Time grid */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        <div className="relative" style={{ height: HOUR_HEIGHT * 24 }}>
          {/* Hour rows */}
          {HOURS.map((hour) => (
            <div
              key={hour}
              className="absolute w-full flex items-start"
              style={{ top: hour * HOUR_HEIGHT, height: HOUR_HEIGHT }}
            >
              <span className="w-14 text-right pr-3 text-xs text-white/30 select-none pt-0.5 shrink-0">
                {pad(hour)}:00
              </span>
              <button
                className="flex-1 border-t border-white/5 hover:bg-white/5 transition-colors h-full"
                onClick={() => handleHourClick(hour)}
              />
            </div>
          ))}

          {/* Current time indicator */}
          {nowTop !== null && (
            <div
              className="absolute inset-x-0 flex items-center z-10 pointer-events-none"
              style={{ top: nowTop }}
            >
              {/* Time label */}
              <span className="w-14 text-right pr-2 text-[10px] font-semibold text-red-400 select-none shrink-0 leading-none">
                {nowLabel}
              </span>
              {/* Dot */}
              <div className="w-2.5 h-2.5 rounded-full bg-red-400 shrink-0 -ml-1.5" />
              {/* Line */}
              <div className="flex-1 h-px bg-red-400" />
            </div>
          )}

          {/* Event blocks */}
          {positioned.map(({ item, top, height, column, totalColumns }) => {
            const isTask = item.source === "task";
            const colWidth = `calc((100% - 56px) / ${totalColumns})`;
            const left = `calc(56px + ${column} * (100% - 56px) / ${totalColumns})`;

            return (
              <button
                key={item.id}
                onClick={() => !isTask && onEventClick(item)}
                className={`absolute rounded-lg px-2 py-1 text-left overflow-hidden transition-opacity ${
                  isTask ? "cursor-default" : "hover:opacity-80 cursor-pointer"
                }`}
                style={{
                  top: top + 1,
                  height: height - 2,
                  left,
                  width: colWidth,
                  backgroundColor: isTask
                    ? "rgba(107,114,128,0.15)"
                    : `${item.color ?? "#3b82f6"}25`,
                  border: isTask
                    ? "1px dashed rgba(107,114,128,0.4)"
                    : `1px solid ${item.color ?? "#3b82f6"}60`,
                  color: isTask ? "#9ca3af" : (item.color ?? "#3b82f6"),
                }}
              >
                <p className="text-xs font-semibold leading-tight truncate">{item.title}</p>
                {height > 32 && (
                  <p className="text-[10px] opacity-70 leading-tight">
                    {formatTime(item.start_at)}
                    {item.end_at ? ` – ${formatTime(item.end_at)}` : ""}
                    {isTask ? " · задача" : ""}
                  </p>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
