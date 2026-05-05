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
        <div className="fixed inset-0 z-40 bg-black/60" onClick={() => setMobileOpen(false)} />
      )}

      {/* Sidebar */}
      <aside
        className={`sidebar ${collapsed ? "w-16" : "w-56"} 
          fixed top-0 left-0 h-full border-r border-[var(--border)]
          bg-[var(--card)] transition-all duration-200 z-50
          max-lg:translate-x-0 max-lg:${mobileOpen ? "translate-x-0" : "-translate-x-full"}`}
      >
        {/* Logo area */}
        <div className="flex items-center gap-3 px-4 h-16 border-b border-[var(--border)]">
          <div className="w-8 h-8 rounded-lg bg-[var(--accent)] flex items-center justify-center text-white font-bold text-sm">
            CS
          </div>
          {!collapsed && <span className="font-semibold text-[var(--text)]">CodeStash</span>}
        </div>

        {/* Nav */}
        <nav className="flex flex-col gap-1 p-2">
          {NAV_ITEMS.map(({ to, icon: Icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors
                ${isActive ? "bg-[var(--accent)]/10 text-[var(--accent)]" : "text-[var(--text-secondary)] hover:bg-[var(--hover)]"}`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Collapse toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="hidden lg:flex items-center justify-center p-2 mx-2 mt-4 rounded-lg text-[var(--text-secondary)] hover:bg-[var(--hover)] transition-colors"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </aside>

      {/* Main content */}
      <main className="flex-1 min-w-0 lg:ml-56 transition-all duration-200">
        {/* Mobile header */}
        <header className="lg:hidden flex items-center gap-3 px-4 h-16 border-b border-[var(--border)]">
          <button onClick={() => setMobileOpen(!mobileOpen)}>
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <span className="font-semibold">CodeStash</span>
        </header>

        <div className="content-frame w-full p-6 max-w-5xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}