import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/core/api-client";
import type { Note, NoteCreatePayload, NoteUpdatePayload } from "./types";

export function useNotes(archived = false, hasPin?: boolean) {
  const params = new URLSearchParams({ archived: String(archived) });
  if (hasPin !== undefined) params.set("has_pin", String(hasPin));
  return useQuery<Note[]>({
    queryKey: ["notes", { archived, hasPin }],
    queryFn: () => apiClient.get<Note[]>(`/notes?${params}`),
  });
}

export function useCreateNote() {
  const qc = useQueryClient();
  return useMutation<Note, Error, NoteCreatePayload>({
    mutationFn: (payload) => apiClient.post<Note>("/notes", payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notes"] }),
  });
}

export function useUpdateNote(noteId: string) {
  const qc = useQueryClient();
  return useMutation<Note, Error, NoteUpdatePayload>({
    mutationFn: (payload) => apiClient.patch<Note>(`/notes/${noteId}`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notes"] }),
  });
}

export function useDeleteNote() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (noteId) =>
      apiClient.delete(`/notes/${noteId}`).then(() => undefined),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notes"] }),
  });
}
