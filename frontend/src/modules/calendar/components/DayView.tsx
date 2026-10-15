import { useEffect, useRef, useState, useCallback } from "react";
import type { CalendarItem } from "../types";

const HOUR_HEIGHT = 28;
const COL_W = 52;
const HOURS = Array.from({ length: 24 }, (_, i) => i);
const HALF_HOURS = Array.from({ length: 24 }, (_, i) => i);

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

function getNowMinutes(day: Date): number | null {
  const now = new Date();
  const isToday =
    day.getFullYear() === now.getFullYear() &&
    day.getMonth() === now.getMonth() &&
    day.getDate() === now.getDate();
  if (!isToday) return null;
  return now.getHours() * 60 + now.getMinutes();
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

  for (const item of timed) {
    const startMin = timeToMinutes(item.start_at);
    const endMin = item.end_at ? timeToMinutes(item.end_at) : startMin + 60;
    const top = (startMin / 60) * HOUR_HEIGHT;
    const height = Math.max(((endMin - startMin) / 60) * HOUR_HEIGHT, 22);
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
      const used = overlapping.map((q) => q.column);
      let col = 0;
      while (used.includes(col)) col++;
      p.column = col;
    }
  }

  return positioned;
}

interface Props {
  day: Date;
  items: CalendarItem[];
  onSlotClick: (startTime: string, endTime?: string) => void;
  onEventClick: (item: CalendarItem) => void;
}

export default function DayView({ day, items, onSlotClick, onEventClick }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [nowMinutes, setNowMinutes] = useState<number | null>(() => getNowMinutes(day));

  useEffect(() => {
    setNowMinutes(getNowMinutes(day));
    const id = setInterval(() => setNowMinutes(getNowMinutes(day)), 60_000);
    return () => clearInterval(id);
  }, [day.toDateString()]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    // Scroll to end of day on open
    const target = HOUR_HEIGHT * 24;
    let id = requestAnimationFrame(() => {
      id = requestAnimationFrame(() => {
        el.scrollTop = target;
      });
    });
    return () => cancelAnimationFrame(id);
  }, [day.toDateString()]);

  const [drag, setDrag] = useState<{ startMin: number; endMin: number } | null>(null);
  const dragRef = useRef(drag);
  useEffect(() => { dragRef.current = drag; }, [drag]);

  const minsFromClientY = useCallback((clientY: number): number => {
    const el = scrollRef.current;
    if (!el) return 0;
    const rect = el.getBoundingClientRect();
    const relY = clientY - rect.top + el.scrollTop;
    const raw = (relY / HOUR_HEIGHT) * 60;
    return Math.max(0, Math.min(24 * 60 - 15, Math.round(raw / 15) * 15));
  }, []);

  // touch-action:none blocks native scroll on mobile → implement manually
  // Long-press (200ms without significant movement) initiates drag on touch
  const gridRef = useRef<HTMLDivElement>(null);
  const onSlotClickRef = useRef(onSlotClick);
  useEffect(() => { onSlotClickRef.current = onSlotClick; }, [onSlotClick]);

  useEffect(() => {
    const grid = gridRef.current;
    const scroll = scrollRef.current;
    if (!grid || !scroll) return;

    let startY = 0;
    let lastY = 0;
    let longPressId: ReturnType<typeof setTimeout> | null = null;
    let touchMode: "pending" | "scrolling" | "dragging" = "pending";

    const minsFromY = (clientY: number) => {
      const rect = scroll.getBoundingClientRect();
      const relY = clientY - rect.top + scroll.scrollTop;
      const raw = (relY / HOUR_HEIGHT) * 60;
      return Math.max(0, Math.min(24 * 60 - 15, Math.round(raw / 15) * 15));
    };
    const fmt = (m: number) => `${pad(Math.floor(m / 60))}:${pad(m % 60)}`;

    const onTouchStart = (e: TouchEvent) => {
      if ((e.target as HTMLElement).closest("button")) return;
      e.preventDefault();
      const t = e.touches[0];
      startY = lastY = t.clientY;
      touchMode = "pending";
      longPressId = setTimeout(() => {
        touchMode = "dragging";
        const mins = minsFromY(startY);
        setDrag({ startMin: mins, endMin: mins + 15 });
      }, 200);
    };

    const onTouchMove = (e: TouchEvent) => {
      const y = e.touches[0].clientY;
      const dy = Math.abs(y - startY);
      if (touchMode === "pending") {
        if (dy > 8) {
          clearTimeout(longPressId!);
          touchMode = "scrolling";
        }
      }
      if (touchMode === "scrolling") {
        scroll.scrollTop -= y - lastY;
      } else if (touchMode === "dragging") {
        const mins = minsFromY(y);
        setDrag((d) => d && { ...d, endMin: Math.max(d.startMin + 15, mins) });
      }
      lastY = y;
    };

    const onTouchEnd = () => {
      clearTimeout(longPressId!);
      if (touchMode === "dragging") {
        setDrag((d) => {
          if (d) onSlotClickRef.current(fmt(d.startMin), fmt(d.endMin));
          return null;
        });
      }
      touchMode = "pending";
    };

    grid.addEventListener("touchstart", onTouchStart, { passive: false });
    grid.addEventListener("touchmove", onTouchMove, { passive: false });
    grid.addEventListener("touchend", onTouchEnd);
    grid.addEventListener("touchcancel", onTouchEnd);
    return () => {
      grid.removeEventListener("touchstart", onTouchStart);
      grid.removeEventListener("touchmove", onTouchMove);
      grid.removeEventListener("touchend", onTouchEnd);
      grid.removeEventListener("touchcancel", onTouchEnd);
    };
  }, []);

  // Mouse drag
  function handlePointerDown(e: React.PointerEvent<HTMLDivElement>) {
    if (e.pointerType !== "mouse") return;
    if ((e.target as HTMLElement).closest("button")) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    const mins = minsFromClientY(e.clientY);
    setDrag({ startMin: mins, endMin: mins + 15 });
  }

  function handlePointerMove(e: React.PointerEvent<HTMLDivElement>) {
    if (e.pointerType !== "mouse" || !drag) return;
    const mins = minsFromClientY(e.clientY);
    setDrag((d) => d && { ...d, endMin: Math.max(d.startMin + 15, mins) });
  }

  function handlePointerUp() {
    if (!drag) return;
    const { startMin, endMin } = drag;
    setDrag(null);
    const fmt = (m: number) => `${pad(Math.floor(m / 60))}:${pad(m % 60)}`;
    onSlotClick(fmt(startMin), fmt(endMin));
  }

  const allDayItems = items.filter((i) => i.all_day);
  const positioned = layoutItems(items);

  const nowTop = nowMinutes !== null ? (nowMinutes / 60) * HOUR_HEIGHT : null;
  const nowLabel =
    nowMinutes !== null
      ? `${pad(Math.floor(nowMinutes / 60))}:${pad(nowMinutes % 60)}`
      : null;

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
      {/* All-day strip */}
      {allDayItems.length > 0 && (
        <div className="px-3 py-2 border-b border-white/8 flex flex-col gap-1 shrink-0">
          <span className="text-[10px] text-white/30 mb-0.5 uppercase tracking-wide">
            Весь день
          </span>
          {allDayItems.map((item) => (
            <button
              key={item.id}
              onClick={() => onEventClick(item)}
              className="text-xs rounded-md px-2 py-1 text-left font-medium transition-opacity hover:opacity-80"
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
                <span className="ml-1 opacity-50">· задача</span>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Time grid */}
      <div ref={scrollRef} className="flex-1 min-h-0 overflow-y-auto">
        <div
          ref={gridRef}
          className="relative select-none"
          style={{ height: HOUR_HEIGHT * 24, touchAction: "none" }}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={() => setDrag(null)}
        >
          {/* Hour lines + labels */}
          {HOURS.map((hour) => (
            <div
              key={hour}
              className="absolute w-full pointer-events-none"
              style={{ top: hour * HOUR_HEIGHT }}
            >
              {/* Hour label — centered on the line via -translate-y-1/2 */}
              {hour > 0 && (
                <span
                  className="absolute text-[10px] text-white/35 leading-none"
                  style={{
                    right: `calc(100% - ${COL_W}px + 8px)`,
                    transform: "translateY(-50%)",
                    whiteSpace: "nowrap",
                  }}
                >
                  {pad(hour)}:00
                </span>
              )}
              {/* Hour line (starts after time column) */}
              <div
                className="absolute h-px bg-white/10"
                style={{ left: COL_W, right: 0 }}
              />
            </div>
          ))}

          {/* Half-hour lines */}
          {HALF_HOURS.map((hour) => (
            <div
              key={`h-${hour}`}
              className="absolute pointer-events-none"
              style={{
                top: hour * HOUR_HEIGHT + HOUR_HEIGHT / 2,
                left: COL_W,
                right: 0,
                height: 1,
                background: "rgba(255,255,255,0.04)",
              }}
            />
          ))}


          {/* Current time indicator */}
          {nowTop !== null && nowLabel !== null && (
            <div
              className="absolute inset-x-0 z-20 pointer-events-none flex items-center"
              style={{ top: nowTop }}
            >
              {/* Red time label in the column */}
              <span
                className="text-[10px] font-semibold text-red-400 leading-none shrink-0"
                style={{ width: COL_W - 4, textAlign: "right" }}
              >
                {nowLabel}
              </span>
              {/* Dot at column edge */}
              <div className="w-2.5 h-2.5 rounded-full bg-red-400 shrink-0 -ml-1.5 -mr-1" />
              {/* Line */}
              <div className="flex-1 h-px bg-red-400" />
            </div>
          )}

          {/* Drag selection */}
          {drag && (
            <div
              className="absolute rounded pointer-events-none z-10"
              style={{
                top: (drag.startMin / 60) * HOUR_HEIGHT,
                height: ((drag.endMin - drag.startMin) / 60) * HOUR_HEIGHT,
                left: COL_W,
                right: 0,
                backgroundColor: "rgba(59,130,246,0.25)",
                border: "1.5px solid rgba(59,130,246,0.7)",
              }}
            />
          )}

          {/* Event blocks */}
          {positioned.map(({ item, top, height, column, totalColumns }) => {
            const isTask = item.source === "task";
            const gridW = `calc(100% - ${COL_W}px)`;
            const colW = `calc(${gridW} / ${totalColumns} - 2px)`;
            const left = `calc(${COL_W}px + ${column} * ${gridW} / ${totalColumns} + 1px)`;

            return (
              <button
                key={item.id}
                onClick={(e) => {
                  e.stopPropagation();
                  if (!isTask) onEventClick(item);
                }}
                className={`absolute rounded px-2 py-1 text-left overflow-hidden transition-opacity ${
                  isTask ? "cursor-default" : "hover:opacity-80 cursor-pointer"
                }`}
                style={{
                  top: top + 1,
                  height: height - 2,
                  left,
                  width: colW,
                  backgroundColor: isTask
                    ? "rgba(107,114,128,0.15)"
                    : `${item.color ?? "#3b82f6"}25`,
                  borderLeft: `3px solid ${isTask ? "rgba(107,114,128,0.5)" : (item.color ?? "#3b82f6")}`,
                  color: isTask ? "#9ca3af" : (item.color ?? "#3b82f6"),
                }}
              >
                <p className="text-[11px] font-semibold leading-tight truncate">{item.title}</p>
                {height > 30 && (
                  <p className="text-[10px] opacity-70 leading-tight mt-0.5">
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
