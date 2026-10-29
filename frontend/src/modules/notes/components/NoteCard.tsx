import { Calendar } from "lucide-react";
import type { Note } from "../types";
import { NOTE_DEFAULT_COLOR } from "../types";

interface Props {
  note: Note;
  onClick: () => void;
}

function formatPinnedAt(iso: string): string {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  const day = pad(d.getDate());
  const month = pad(d.getMonth() + 1);
  const h = d.getHours();
  const m = d.getMinutes();
  if (h === 0 && m === 0) return `${day}.${month}`;
  return `${day}.${month} ${pad(h)}:${pad(m)}`;
}

export default function NoteCard({ note, onClick }: Props) {
  const accent = note.color ?? NOTE_DEFAULT_COLOR;

  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-white/5 hover:bg-white/10 rounded-2xl p-4 transition-colors flex gap-3"
    >
      {/* Color stripe */}
      <div
        className="w-1 rounded-full shrink-0 self-stretch"
        style={{ backgroundColor: accent }}
      />

      <div className="flex-1 min-w-0">
        <p className="font-semibold text-white leading-tight truncate">{note.title}</p>
        {note.body && (
          <p className="text-sm text-white/50 mt-1 line-clamp-2 whitespace-pre-wrap">
            {note.body}
          </p>
        )}
        {note.pinned_at && (
          <div className="flex items-center gap-1 mt-2">
            <Calendar size={11} className="shrink-0" style={{ color: accent }} />
            <span className="text-[11px] font-medium" style={{ color: accent }}>
              {formatPinnedAt(note.pinned_at)}
            </span>
          </div>
        )}
      </div>
    </button>
  );
}
