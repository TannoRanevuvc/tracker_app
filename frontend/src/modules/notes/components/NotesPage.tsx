import { useState } from "react";
import { Plus } from "lucide-react";
import NoteCard from "./NoteCard";
import NoteFormModal from "./NoteFormModal";
import { useNotes, useCreateNote, useUpdateNote, useDeleteNote } from "../hooks";
import type { Note, NoteCreatePayload, NoteUpdatePayload } from "../types";

export default function NotesPage() {
  const [modalOpen, setModalOpen] = useState(false);
  const [editingNote, setEditingNote] = useState<Note | null>(null);
  const [filter, setFilter] = useState<"all" | "pinned">("all");

  const hasPin = filter === "pinned" ? true : undefined;
  const { data: notes = [], isLoading } = useNotes(false, hasPin);

  const createNote = useCreateNote();
  const updateNote = useUpdateNote(editingNote?.id ?? "");
  const deleteNote = useDeleteNote();

  function openNew() {
    setEditingNote(null);
    setModalOpen(true);
  }

  function openEdit(note: Note) {
    setEditingNote(note);
    setModalOpen(true);
  }

  async function handleSubmit(payload: NoteCreatePayload | NoteUpdatePayload) {
    if (editingNote) {
      await updateNote.mutateAsync(payload as NoteUpdatePayload);
    } else {
      await createNote.mutateAsync(payload as NoteCreatePayload);
    }
    setModalOpen(false);
  }

  async function handleDelete() {
    if (!editingNote) return;
    await deleteNote.mutateAsync(editingNote.id);
    setModalOpen(false);
  }

  const mutationError =
    createNote.error?.message ?? updateNote.error?.message ?? undefined;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 pt-4 pb-3 shrink-0">
        <h1 className="text-lg font-semibold">Заметки</h1>
        <button
          onClick={openNew}
          className="w-8 h-8 flex items-center justify-center rounded-full bg-white text-black hover:bg-white/90 transition-colors"
        >
          <Plus size={18} />
        </button>
      </div>

      {/* Filter tabs */}
      <div className="px-4 pb-3 shrink-0">
        <div className="flex bg-white/10 rounded-xl p-0.5 text-sm w-fit">
          {(["all", "pinned"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded-lg transition-colors font-medium ${
                filter === f ? "bg-white text-black" : "text-white/60 hover:text-white"
              }`}
            >
              {f === "all" ? "Все" : "С датой"}
            </button>
          ))}
        </div>
      </div>

      {/* Notes list */}
      <div className="flex-1 min-h-0 overflow-y-auto px-4 pb-4">
        {isLoading ? (
          <div className="text-white/40 text-sm py-8 text-center">Загружаем…</div>
        ) : notes.length === 0 ? (
          <div className="text-white/30 text-sm py-12 text-center">
            {filter === "pinned" ? "Нет заметок с привязкой к дате" : "Заметок пока нет"}
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {notes.map((note) => (
              <NoteCard key={note.id} note={note} onClick={() => openEdit(note)} />
            ))}
          </div>
        )}
      </div>

      <NoteFormModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSubmit={handleSubmit}
        onDelete={editingNote ? handleDelete : undefined}
        initialData={editingNote ?? undefined}
        loading={createNote.isPending || updateNote.isPending || deleteNote.isPending}
        error={mutationError}
      />
    </div>
  );
}
