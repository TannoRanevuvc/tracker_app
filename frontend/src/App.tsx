import { RouterProvider, createRouter } from "@tanstack/react-router";
import { habitsRoutes } from "@/modules/habits/routes";
import { tasksRoutes } from "@/modules/tasks/routes";
import { financeRoutes } from "@/modules/finance/routes";
import { foodRoutes } from "@/modules/food/routes";

// TODO: wire up TanStack Router with module routes
export default function App() {
  return (
    <div className="min-h-screen bg-background">
      <p>Tracker App — skeleton</p>
    </div>
  );
}
