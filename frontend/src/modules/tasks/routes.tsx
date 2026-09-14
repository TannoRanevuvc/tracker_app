import { RouteObject } from "react-router-dom";
import TasksPage from "./components/TasksPage";

export const tasksRoutes: RouteObject[] = [
  { path: "/tasks", element: <TasksPage /> },
];
