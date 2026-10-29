import type { RouteObject } from "react-router-dom";
import NotesPage from "./components/NotesPage";

export const notesRoutes: RouteObject[] = [
  { path: "/notes", element: <NotesPage /> },
];
