import type { RouteObject } from "react-router-dom";
import CalendarPage from "./components/CalendarPage";

export const calendarRoutes: RouteObject[] = [
  { path: "/calendar", element: <CalendarPage /> },
];
