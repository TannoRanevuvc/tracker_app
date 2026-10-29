import { createBrowserRouter, RouterProvider, Navigate } from "react-router-dom";
import ProtectedRoute from "@/core/auth/ProtectedRoute";
import LoginPage from "@/core/auth/LoginPage";
import RegisterPage from "@/core/auth/RegisterPage";
import Shell from "@/core/shell/Shell";
import SettingsPage from "@/core/settings/SettingsPage";
import { habitsRoutes } from "@/modules/habits/routes";
import { tasksRoutes } from "@/modules/tasks/routes";
import { motivationRoutes } from "@/modules/motivation/routes";
import { financeRoutes } from "@/modules/finance/routes";
import { foodRoutes } from "@/modules/food/routes";
import { calendarRoutes } from "@/modules/calendar/routes";
import { notesRoutes } from "@/modules/notes/routes";

const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },
  {
    path: "/",
    element: <ProtectedRoute />,
    children: [
      {
        element: <Shell />,
        children: [
          { index: true, element: <Navigate to="/calendar" replace /> },
          { path: "settings", element: <SettingsPage /> },
          ...habitsRoutes,
          ...tasksRoutes,
          ...motivationRoutes,
          ...financeRoutes,
          ...foodRoutes,
          ...calendarRoutes,
          ...notesRoutes,
        ],
      },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
