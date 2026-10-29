import { CheckSquare, ListTodo, Wallet, Salad, Flame, CalendarDays, StickyNote } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface NavItem {
  label: string;
  path: string;
  moduleId: string;
  icon: LucideIcon;
}

export const primaryNavItems: NavItem[] = [
  { label: "Календарь", path: "/calendar",   moduleId: "calendar",   icon: CalendarDays },
  { label: "Задачи",    path: "/tasks",      moduleId: "tasks",      icon: ListTodo },
  { label: "Привычки",  path: "/habits",     moduleId: "habits",     icon: CheckSquare },
];

export const secondaryNavItems: NavItem[] = [
  { label: "Финансы",   path: "/finance",    moduleId: "finance",    icon: Wallet },
  { label: "Питание",   path: "/food",       moduleId: "food",       icon: Salad },
  { label: "Мотивация", path: "/motivation", moduleId: "motivation", icon: Flame },
  { label: "Заметки",   path: "/notes",      moduleId: "notes",      icon: StickyNote },
];

export const navItems: NavItem[] = [...primaryNavItems, ...secondaryNavItems];
