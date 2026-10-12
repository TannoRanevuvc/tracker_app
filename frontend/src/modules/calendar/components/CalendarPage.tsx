import { useState, useMemo } from "react";
import { ChevronLeft, ChevronRight, Plus } from "lucide-react";
import MonthView from "./MonthView";
import DayView from "./DayView";
import EventFormModal from "./EventFormModal";
import {
  useCalendarEvents,
  useTasksForCalendar,
  useCreateEvent,
  useUpdateEvent,
  useDeleteEvent,
} from "../hooks";
import type { CalendarEvent, CalendarItem, EventCreatePayload, EventUpdatePayload } from "../types";

const MONTHS_RU = [
  "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
  "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
];
const DAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

function pad(n: number) {
  return String(n).padStart(2, "0");
}

function monthRangeISO(year: number, month: number): { start: string; end: string } {
  const start = `${year}-${pad(month + 1)}-01T00:00:00`;
  const nextMonth = month === 11 ? 0 : month + 1;
  const nextYear = month === 11 ? year + 1 : year;
  const end = `${nextYear}-${pad(nextMonth + 1)}-01T00:00:00`;
  return { start, end };
}

function dayRangeISO(day: Date): { start: string; end: string } {
  const y = day.getFullYear();
  const m = pad(day.getMonth() + 1);
  const d = pad(day.getDate());
  const start = `${y}-${m}-${d}T00:00:00`;
  const tomorrow = new Date(y, day.getMonth(), day.getDate() + 1);
  const end = `${tomorrow.getFullYear()}-${pad(tomorrow.getMonth() + 1)}-${pad(tomorrow.getDate())}T00:00:00`;
  return { start, end };
}

function formatDayHeader(day: Date): string {
  const dow = DAYS_RU[(day.getDay() + 6) % 7];
  return `${dow}, ${day.getDate()} ${MONTHS_RU[day.getMonth()].toLowerCase()}`;
}

export default function CalendarPage() {
  const today = new Date();
  const [view, setView] = useState<"month" | "day">("month");
  const [currentDate, setCurrentDate] = useState(today);
  const [selectedDay, setSelectedDay] = useState<Date | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingEvent, setEditingEvent] = useState<CalendarEvent | null>(null);
  const [defaultDate, setDefaultDate] = useState<string | undefined>();
  const [defaultTime, setDefaultTime] = useState<string | undefined>();

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const monthRange = useMemo(() => monthRangeISO(year, month), [year, month]);
  const dayRange = useMemo(
    () => (selectedDay ? dayRangeISO(selectedDay) : null),
    [selectedDay?.toDateString()]
  );

  const eventsQuery = useCalendarEvents(monthRange.start, monthRange.end);
  const dayEventsQuery = useCalendarEvents(
    dayRange?.start ?? "",
    dayRange?.end ?? ""
  );
  const tasksQuery = useTasksForCalendar();

  const createEvent = useCreateEvent();
  const updateEvent = useUpdateEvent(editingEvent?.id ?? "");
  const deleteEvent = useDeleteEvent();

  const monthItems: CalendarItem[] = useMemo(() => {
    const calItems: CalendarItem[] =
      eventsQuery.data?.map((e) => ({
        id: e.id,
        title: e.title,
        start_at: e.start_at,
        end_at: e.end_at,
        all_day: e.all_day,
        color: e.color,
        source: "calendar" as const,
      })) ?? [];
    return [...calItems, ...(tasksQuery.data ?? [])];
  }, [eventsQuery.data, tasksQuery.data]);

  const dayItems: CalendarItem[] = useMemo(() => {
    if (!selectedDay) return [];
    const calItems: CalendarItem[] =
      dayEventsQuery.data?.map((e) => ({
        id: e.id,
        title: e.title,
        start_at: e.start_at,
        end_at: e.end_at,
        all_day: e.all_day,
        color: e.color,
        source: "calendar" as const,
      })) ?? [];
    const dayStr = `${selectedDay.getFullYear()}-${pad(selectedDay.getMonth() + 1)}-${pad(selectedDay.getDate())}`;
    const taskItems = (tasksQuery.data ?? []).filter((t) =>
      t.start_at.startsWith(dayStr)
    );
    return [...calItems, ...taskItems];
  }, [dayEventsQuery.data, tasksQuery.data, selectedDay?.toDateString()]);

  function prevPeriod() {
    if (view === "month") {
      setCurrentDate(new Date(year, month - 1, 1));
    } else if (selectedDay) {
      const prev = new Date(selectedDay);
      prev.setDate(prev.getDate() - 1);
      setSelectedDay(prev);
    }
  }

  function nextPeriod() {
    if (view === "month") {
      setCurrentDate(new Date(year, month + 1, 1));
    } else if (selectedDay) {
      const next = new Date(selectedDay);
      next.setDate(next.getDate() + 1);
      setSelectedDay(next);
    }
  }

  function goToToday() {
    setCurrentDate(today);
    if (view === "day") {
      setSelectedDay(today);
    }
  }

  function handleDayClick(day: Date) {
    setSelectedDay(day);
    setView("day");
  }

  function handleSlotClick(time: string) {
    if (!selectedDay) return;
    const d = selectedDay;
    setDefaultDate(
      `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
    );
    setDefaultTime(time);
    setEditingEvent(null);
    setModalOpen(true);
  }

  function handleEventClick(item: CalendarItem) {
    if (item.source !== "calendar") return;
    const event = eventsQuery.data?.find((e) => e.id === item.id) ??
      dayEventsQuery.data?.find((e) => e.id === item.id);
    if (event) {
      setEditingEvent(event);
      setDefaultDate(undefined);
      setDefaultTime(undefined);
      setModalOpen(true);
    }
  }

  function openNewEvent() {
    setEditingEvent(null);
    if (view === "day" && selectedDay) {
      setDefaultDate(
        `${selectedDay.getFullYear()}-${pad(selectedDay.getMonth() + 1)}-${pad(selectedDay.getDate())}`
      );
      setDefaultTime("09:00");
    } else {
      setDefaultDate(undefined);
      setDefaultTime(undefined);
    }
    setModalOpen(true);
  }

  async function handleModalSubmit(payload: EventCreatePayload | EventUpdatePayload) {
    if (editingEvent) {
      await updateEvent.mutateAsync(payload as EventUpdatePayload);
    } else {
      await createEvent.mutateAsync(payload as EventCreatePayload);
    }
    setModalOpen(false);
  }

  async function handleDelete() {
    if (!editingEvent) return;
    await deleteEvent.mutateAsync(editingEvent.id);
    setModalOpen(false);
  }

  const mutationError =
    createEvent.error?.message ?? updateEvent.error?.message ?? undefined;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 pt-4 pb-2 shrink-0">
        <div className="flex items-center gap-2">
          <button
            onClick={prevPeriod}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-white/10 transition-colors text-white/70"
          >
            <ChevronLeft size={18} />
          </button>
          <button
            onClick={nextPeriod}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-white/10 transition-colors text-white/70"
          >
            <ChevronRight size={18} />
          </button>
          <h1 className="text-lg font-semibold ml-1">
            {view === "month"
              ? `${MONTHS_RU[month]} ${year}`
              : selectedDay
              ? formatDayHeader(selectedDay)
              : ""}
          </h1>
        </div>

        <div className="flex items-center gap-2">
          {/* View toggle */}
          <div className="flex bg-white/10 rounded-xl p-0.5 text-sm">
            <button
              onClick={() => setView("month")}
              className={`px-3 py-1 rounded-lg transition-colors font-medium ${
                view === "month" ? "bg-white text-black" : "text-white/60 hover:text-white"
              }`}
            >
              Месяц
            </button>
            <button
              onClick={() => {
                setView("day");
                if (!selectedDay) setSelectedDay(today);
              }}
              className={`px-3 py-1 rounded-lg transition-colors font-medium ${
                view === "day" ? "bg-white text-black" : "text-white/60 hover:text-white"
              }`}
            >
              День
            </button>
          </div>

          <button
            onClick={openNewEvent}
            className="w-8 h-8 flex items-center justify-center rounded-full bg-white text-black hover:bg-white/90 transition-colors"
          >
            <Plus size={18} />
          </button>
        </div>
      </div>

      {/* Today button */}
      <div className="px-4 pb-2 shrink-0">
        <button
          onClick={goToToday}
          className="text-xs text-white/50 hover:text-white/80 transition-colors"
        >
          Сегодня
        </button>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-hidden flex flex-col px-4 pb-4">
        {view === "month" ? (
          <MonthView
            year={year}
            month={month}
            items={monthItems}
            selectedDay={selectedDay}
            onDayClick={handleDayClick}
          />
        ) : (
          selectedDay && (
            <DayView
              day={selectedDay}
              items={dayItems}
              onSlotClick={handleSlotClick}
              onEventClick={handleEventClick}
            />
          )
        )}
      </div>

      {/* Event form modal */}
      <EventFormModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSubmit={handleModalSubmit}
        onDelete={editingEvent ? handleDelete : undefined}
        initialData={editingEvent ?? undefined}
        defaultDate={defaultDate}
        defaultTime={defaultTime}
        loading={createEvent.isPending || updateEvent.isPending || deleteEvent.isPending}
        error={mutationError}
      />
    </div>
  );
}
