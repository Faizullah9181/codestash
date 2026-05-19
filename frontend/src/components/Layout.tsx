/**
 * Layout — sidebar + main content shell.
 * Mirrors F433's app layout pattern with responsive sidebar.
 */

import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  Home,
  Database,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
  Sparkles,
  Github,
  ExternalLink,
} from "lucide-react";

const NAV_ITEMS = [
  { to: "/", icon: Home, label: "Home", end: true },
  { to: "/items", icon: Database, label: "Items" },
];

export function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="app-shell flex min-h-screen bg-[var(--bg)]">
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`sidebar ${collapsed ? "w-[68px]" : "w-60"}
          fixed top-0 left-0 h-full z-50
          transition-all duration-300 ease-out
          max-lg:${mobileOpen ? "translate-x-0" : "-translate-x-full"}`}
      >
        {/* Logo area */}
        <div className="flex items-center gap-3 px-4 h-16 border-b border-[var(--border)]">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[var(--accent)] to-blue-500 flex items-center justify-center shadow-[var(--shadow-sm)]">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          {!collapsed && (
            <span className="font-bold text-[var(--text)] tracking-tight text-base">
              CodeStash
            </span>
          )}
        </div>

        {/* Nav */}
        <nav className="flex flex-col gap-1 p-3">
          {NAV_ITEMS.map(({ to, icon: Icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200
                ${
                  isActive
                    ? "bg-[var(--accent-dim)] text-[var(--accent)] shadow-[inset_0_0_0_1px_rgba(34,211,238,0.2)]"
                    : "text-[var(--text-secondary)] hover:bg-[var(--hover)] hover:text-[var(--text)]"
                }`
              }
            >
              <Icon className={`w-4 h-4 shrink-0 ${collapsed ? "mx-auto" : ""}`} />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Bottom actions */}
        <div className="absolute bottom-0 left-0 right-0 p-3 border-t border-[var(--border)]">
          {!collapsed && (
            <div className="text-[10px] text-[var(--text-secondary)] px-3 mb-2 uppercase tracking-widest">
              Powered by CodeStash
            </div>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="hidden lg:flex items-center justify-center w-full p-2 rounded-xl
              text-[var(--text-secondary)] hover:bg-[var(--hover)] hover:text-[var(--text)]
              transition-all duration-200"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main
        className={`flex-1 min-w-0 transition-all duration-300 ease-out
          ${collapsed ? "lg:ml-[68px]" : "lg:ml-60"}`}
      >
        {/* Mobile header */}
        <header className="lg:hidden flex items-center justify-between px-4 h-16 border-b border-[var(--border)] bg-[var(--bg)]/80 backdrop-blur sticky top-0 z-30">
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="btn-icon"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <span className="font-bold tracking-tight">CodeStash</span>
          <div className="w-8" />
        </header>

        <div className="content-frame w-full p-6 md:p-8 max-w-6xl mx-auto animate-fade-in">
          <Outlet />
        </div>
      </main>
    </div>
  );
}