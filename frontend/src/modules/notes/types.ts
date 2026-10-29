export interface Note {
  id: string;
  title: string;
  body?: string;
  pinned_at?: string;
  color?: string;
  archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface NoteCreatePayload {
  title: string;
  body?: string;
  color?: string;
  pinned_at?: string;
}

export interface NoteUpdatePayload {
  title?: string;
  body?: string;
  color?: string;
  pinned_at?: string | null;
  archived?: boolean;
}

export const NOTE_DEFAULT_COLOR = "#eab308";
