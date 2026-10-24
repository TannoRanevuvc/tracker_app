import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Sun, Moon, Settings, Grid3x3 } from "lucide-react";
import { apiClient } from "@/core/api-client";
import { primaryNavItems, secondaryNavItems, navItems } from "./nav";
import { useTheme } from "./ThemeProvider";

interface ModuleInfo {
  name: string;
  enabled: boolean;
}

export default function Shell() {
  const { theme, toggleTheme } = useTheme();
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();

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
  const visiblePrimary = primaryNavItems.filter((item) =>
    enabledModuleIds.has(item.moduleId)
  );
  const visibleSecondary = secondaryNavItems.filter((item) =>
    enabledModuleIds.has(item.moduleId)
  );

  const ThemeIcon = theme === "dark" ? Sun : Moon;

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-black text-white antialiased font-sans selection:bg-white/20">
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
        <div className="flex items-center gap-1">
          <NavLink
            to="/settings"
            aria-label="Настройки"
            className={({ isActive }) =>
              `p-1.5 rounded-lg transition-colors ${isActive ? "text-white" : "text-white/60 hover:text-white/90 hover:bg-white/8"}`
            }
          >
            <Settings size={18} strokeWidth={1.75} />
          </NavLink>
          <button
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="p-1.5 rounded-lg text-white/60 hover:text-white/90 hover:bg-white/8 transition-colors"
          >
            <ThemeIcon size={18} strokeWidth={1.75} />
          </button>
        </div>
      </header>

      {/* Mobile header */}
      <header className="lg:hidden bg-brand-gray px-4 py-3 flex items-center justify-between shrink-0">
        <span className="font-semibold text-white">Tracker</span>
        <div className="flex items-center gap-1">
          <NavLink
            to="/settings"
            aria-label="Настройки"
            className={({ isActive }) =>
              `p-1.5 rounded-lg transition-colors ${isActive ? "text-white" : "text-white/60 hover:text-white/90 hover:bg-white/8"}`
            }
          >
            <Settings size={18} strokeWidth={1.75} />
          </NavLink>
          <button
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="p-1.5 rounded-lg text-white/60 hover:text-white/90 hover:bg-white/8 transition-colors"
          >
            <ThemeIcon size={18} strokeWidth={1.75} />
          </button>
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 min-h-0 overflow-y-auto p-2 lg:p-4 pb-24 lg:pb-4">
        <Outlet />
      </main>

      {/* Mobile bottom tab bar */}
      <nav className="lg:hidden fixed bottom-0 inset-x-0 bg-brand-gray border-t border-white/8 flex items-stretch z-40">
        {visiblePrimary.map((item) => {
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
        {visibleSecondary.length > 0 && (
          <button
            onClick={() => setMenuOpen(true)}
            className="flex flex-1 flex-col items-center justify-center gap-1 py-2 text-[10px] font-medium text-white/40 transition-colors"
          >
            <Grid3x3 size={22} strokeWidth={1.75} />
            Ещё
          </button>
        )}
      </nav>

      {/* Secondary menu overlay */}
      {menuOpen && (
        <div
          className="lg:hidden fixed inset-0 z-50 flex items-end"
          onClick={() => setMenuOpen(false)}
        >
          <div
            className="absolute inset-0 bg-black/60"
            aria-hidden="true"
          />
          <div
            className="relative w-full bg-brand-gray border-t border-white/10 rounded-t-2xl px-4 pt-4 pb-8"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="w-10 h-1 bg-white/20 rounded-full mx-auto mb-6" />
            <div className="grid grid-cols-3 gap-4">
              {visibleSecondary.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.path}
                    onClick={() => {
                      navigate(item.path);
                      setMenuOpen(false);
                    }}
                    className="flex flex-col items-center justify-center gap-2 py-4 rounded-xl bg-white/5 active:bg-white/10 transition-colors text-white/70"
                  >
                    <Icon size={24} strokeWidth={1.75} />
                    <span className="text-xs font-medium">{item.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
