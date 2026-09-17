import { CheckSquare, ListTodo, Wallet, Salad, Flame } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface NavItem {
  label: string;
  path: string;
  moduleId: string;
  icon: LucideIcon;
}

export const navItems: NavItem[] = [
  { label: "Привычки",  path: "/habits",     moduleId: "habits",     icon: CheckSquare },
  { label: "Задачи",    path: "/tasks",      moduleId: "tasks",      icon: ListTodo },
  { label: "Финансы",   path: "/finance",    moduleId: "finance",    icon: Wallet },
  { label: "Питание",   path: "/food",       moduleId: "food",       icon: Salad },
  { label: "Мотивация", path: "/motivation", moduleId: "motivation", icon: Flame },
];
