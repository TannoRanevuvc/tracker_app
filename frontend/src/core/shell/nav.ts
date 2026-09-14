export interface NavItem {
  label: string;
  path: string;
  moduleId: string;
}

export const navItems: NavItem[] = [
  { label: "Привычки", path: "/habits", moduleId: "habits" },
  { label: "Задачи", path: "/tasks", moduleId: "tasks" },
  { label: "Финансы", path: "/finance", moduleId: "finance" },
  { label: "Питание", path: "/food", moduleId: "food" },
  { label: "Мотивация", path: "/motivation", moduleId: "motivation" },
];
