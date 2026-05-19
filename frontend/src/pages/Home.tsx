/**
 * Home page — dashboard overview with quick stats + recent items.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, Database, Plus, Server, ArrowRight, Sparkles, ExternalLink, Zap, Box } from "lucide-react";
import { healthApi } from "../lib/api";

const STAT_CARDS = [
  {
    key: "api",
    label: "API Status",
    icon: Server,
    color: "emerald",
    value: (s: any, err: string | null) =>
      err ? "Unreachable" : s?.status === "ok" ? "Healthy" : "Checking…",
    ok: (s: any) => s?.status === "ok",
    err: (err: string | null) => !!err,
  },
  {
    key: "db",
    label: "Database",
    icon: Database,
    color: "blue",
    value: (s: any, err: string | null) =>
      err ? "—" : s?.database === "connected" ? "Connected" : "Disconnected",
    ok: (s: any) => s?.database === "connected",
  },
  {
    key: "version",
    label: "Version",
    icon: Activity,
    color: "purple",
    value: (s: any) => s?.version ?? "…",
    ok: () => true,
  },
];

const QUICK_LINKS = [
  {
    to: "/items",
    icon: Box,
    title: "Items CRUD",
    desc: "Create, read, update & delete example resources",
    color: "text-cyan-400",
    bg: "bg-cyan-500/10",
  },
  {
    href: "/docs",
    icon: ExternalLink,
    title: "API Docs",
    desc: "Swagger / OpenAPI interactive reference",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
  },
];

export function Home() {
  const [status, setStatus] = useState<{ status: string; version: string; database: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    healthApi
      .status()
      .then(setStatus)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="space-y-10">
      {/* Hero */}
      <div className="animate-fade-in">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[var(--accent)] to-blue-600 flex items-center justify-center shadow-[0_4px_16px_rgba(34,211,238,0.25)]">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-[var(--text)] tracking-tight">Dashboard</h1>
        </div>
        <p className="text-[var(--text-secondary)] text-lg ml-[52px]">
          Full-stack starter — React + FastAPI + PostgreSQL
        </p>
      </div>

      {/* System status */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4" style={{ animationDelay: "0.1s" }}>
        {STAT_CARDS.map(({ key, label, icon: Icon, color, value, ok, err }) => {
          const colorMap: Record<string, string> = {
            emerald: "shadow-emerald-500/10",
            blue: "shadow-blue-500/10",
            purple: "shadow-purple-500/10",
          };
          return (
            <div
              key={key}
              className="card card-glow p-5 flex items-center gap-4 animate-fade-in"
            >
              <div className={`w-11 h-11 rounded-xl bg-${color}-500/10 flex items-center justify-center shrink-0`}>
                <Icon className={`w-5 h-5 text-${color}-400`} />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
                  {label}
                </p>
                <p className="font-semibold text-[var(--text)] mt-0.5 truncate">
                  {value(status, error)}
                </p>
              </div>
              {/* Status dot */}
              <div className="ml-auto shrink-0">
                <div
                  className={`w-2 h-2 rounded-full ${
                    err?.(error)
                      ? "bg-red-400 shadow-[0_0_6px_rgba(248,113,113,0.6)]"
                      : ok(status)
                      ? "bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.6)]"
                      : "bg-amber-400 shadow-[0_0_6px_rgba(251,191,36,0.4)] animate-pulse"
                  }`}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick links */}
      <div className="card p-6 md:p-8 animate-fade-in" style={{ animationDelay: "0.2s" }}>
        <div className="flex items-center gap-2 mb-6">
          <Zap className="w-5 h-5 text-[var(--accent)]" />
          <h2 className="text-lg font-bold text-[var(--text)]">Quick Start</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {QUICK_LINKS.map(({ to, href, icon: Icon, title, desc, color, bg }) => {
            const Comp = to ? Link : "a";
            const extraProps = to ? { to } : { href, target: "_blank", rel: "noopener" };
            return (
              <Comp
                key={title}
                {...(extraProps as any)}
                className="group flex items-center gap-4 p-4 rounded-xl border border-[var(--border)]
                  hover:border-[rgba(255,255,255,0.15)] hover:bg-[var(--card-hover)]
                  transition-all duration-200"
              >
                <div className={`w-10 h-10 rounded-xl ${bg} flex items-center justify-center shrink-0`}>
                  <Icon className={`w-4 h-4 ${color}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-[var(--text)] group-hover:text-[var(--accent)] transition-colors">
                    {title}
                  </p>
                  <p className="text-xs text-[var(--text-secondary)] mt-0.5">{desc}</p>
                </div>
                <ArrowRight className="w-4 h-4 text-[var(--text-secondary)] opacity-0 group-hover:opacity-100 transition-all shrink-0" />
              </Comp>
            );
          })}
        </div>
      </div>
    </div>
  );
}