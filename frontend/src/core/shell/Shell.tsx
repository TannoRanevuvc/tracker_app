import { NavLink, Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Sun, Moon } from "lucide-react";
import { apiClient } from "@/core/api-client";
import { navItems } from "./nav";
import { useTheme } from "./ThemeProvider";

interface ModuleInfo {
  name: string;
  enabled: boolean;
}

export default function Shell() {
  const { theme, toggleTheme } = useTheme();

  const { data: modules = [] } = useQuery<ModuleInfo[]>({
    queryKey: ["core", "modules"],
    queryFn: () => apiClient.get<ModuleInfo[]>("/core/modules"),
    staleTime: 60 * 1000,
  });

  const enabledModuleIds = new Set(
    modules.filter((m) => m.enabled).map((m) => m.name)
  );
  const visibleItems = navItems.filter((item) =>
    enabledModuleIds.has(item.moduleId)
  );

  const ThemeIcon = theme === "dark" ? Sun : Moon;

  return (
    <div className="flex flex-col min-h-screen bg-black text-white antialiased font-sans selection:bg-white/20">
      {/* Desktop header */}
      <header className="hidden lg:flex bg-brand-gray px-4 py-3 items-center gap-6 shrink-0">
        <span className="font-semibold text-white">Tracker</span>
        <nav className="flex gap-4 flex-1">
          {visibleItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                isActive
                  ? "text-white font-medium text-sm"
                  : "text-white/60 hover:text-white/80 text-sm transition-colors"
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <button
          onClick={toggleTheme}
          aria-label="Toggle theme"
          className="p-1.5 rounded-lg text-white/60 hover:text-white/90 hover:bg-white/8 transition-colors"
        >
          <ThemeIcon size={18} strokeWidth={1.75} />
        </button>
      </header>

      {/* Mobile header */}
      <header className="lg:hidden bg-brand-gray px-4 py-3 flex items-center justify-between shrink-0">
        <span className="font-semibold text-white">Tracker</span>
        <button
          onClick={toggleTheme}
          aria-label="Toggle theme"
          className="p-1.5 rounded-lg text-white/60 hover:text-white/90 hover:bg-white/8 transition-colors"
        >
          <ThemeIcon size={18} strokeWidth={1.75} />
        </button>
      </header>

      {/* Content */}
      <main className="flex-1 p-2 lg:p-4 pb-24 lg:pb-4">
        <Outlet />
      </main>

      {/* Mobile bottom tab bar */}
      <nav className="lg:hidden fixed bottom-0 inset-x-0 bg-brand-gray border-t border-white/8 flex items-stretch z-40">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex flex-1 flex-col items-center justify-center gap-1 py-2 text-[10px] font-medium transition-colors ${
                  isActive ? "text-white" : "text-white/40"
                }`
              }
            >
              <Icon size={22} strokeWidth={1.75} />
              {item.label}
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
}
