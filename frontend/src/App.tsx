import { createBrowserRouter, RouterProvider, Navigate } from "react-router-dom";
import ProtectedRoute from "@/core/auth/ProtectedRoute";
import LoginPage from "@/core/auth/LoginPage";
import Shell from "@/core/shell/Shell";
import { habitsRoutes } from "@/modules/habits/routes";
import { tasksRoutes } from "@/modules/tasks/routes";

const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    path: "/",
    element: <ProtectedRoute />,
    children: [
      {
        element: <Shell />,
        children: [
          { index: true, element: <Navigate to="/habits" replace /> },
          ...habitsRoutes,
          ...tasksRoutes,
        ],
      },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
