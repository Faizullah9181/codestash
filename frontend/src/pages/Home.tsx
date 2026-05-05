/**
 * Home page — dashboard overview with quick stats + recent items.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, Database, Plus, Server } from "lucide-react";
import { healthApi } from "../lib/api";

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
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[var(--text)]">Dashboard</h1>
        <p className="text-[var(--text-secondary)] mt-1">
          Full-stack starter template — React + FastAPI + PostgreSQL
        </p>
      </div>

      {/* System status */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
            <Server className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <p className="text-xs text-[var(--text-secondary)]">API Status</p>
            <p className="font-semibold text-[var(--text)]">
              {error ? "Unreachable" : status?.status === "ok" ? "Healthy" : "Checking…"}
            </p>
          </div>
        </div>

        <div className="card p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
            <Database className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <p className="text-xs text-[var(--text-secondary)]">Database</p>
            <p className="font-semibold text-[var(--text)]">
              {error ? "—" : status?.database === "connected" ? "Connected" : "Disconnected"}
            </p>
          </div>
        </div>

        <div className="card p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center">
            <Activity className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <p className="text-xs text-[var(--text-secondary)]">Version</p>
            <p className="font-semibold text-[var(--text)]">{status?.version ?? "…"} </p>
          </div>
        </div>
      </div>

      {/* Quick links */}
      <div className="card p-6">
        <h2 className="text-lg font-semibold text-[var(--text)] mb-4">Quick Start</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Link to="/items" className="flex items-center gap-3 p-3 rounded-lg border border-[var(--border)] hover:bg-[var(--hover)] transition-colors">
            <Database className="w-4 h-4 text-[var(--accent)]" />
            <div>
              <p className="text-sm font-medium text-[var(--text)]">Items CRUD</p>
              <p className="text-xs text-[var(--text-secondary)]">Example create / read / update / delete</p>
            </div>
          </Link>
          <a
            href="/docs"
            target="_blank"
            rel="noopener"
            className="flex items-center gap-3 p-3 rounded-lg border border-[var(--border)] hover:bg-[var(--hover)] transition-colors"
          >
            <Plus className="w-4 h-4 text-emerald-400" />
            <div>
              <p className="text-sm font-medium text-[var(--text)]">API Docs</p>
              <p className="text-xs text-[var(--text-secondary)]">Swagger / OpenAPI reference</p>
            </div>
          </a>
        </div>
      </div>
    </div>
  );
}