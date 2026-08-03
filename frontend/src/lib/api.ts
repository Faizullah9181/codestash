/**
 * Typed API client for the FastAPI backend.
 *
 * Provides:
 * - `apiGet<T>`, `apiPost<T>`, `apiPut<T>`, `apiPatch<T>`, `apiDelete<T>`
 * - Automatic prefix handling (dev proxy vs prod VITE_API_URL)
 * - JSON handling + error normalization
 */

const BASE_URL =
  import.meta.env.PROD && import.meta.env.VITE_API_URL
    ? `${import.meta.env.VITE_API_URL}`
    : "";

async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    const body = await res.text().catch(() => res.statusText);
    throw new Error(body || `Request failed: ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ── Convenience methods ──────────────────────────────────────────

export function apiGet<T>(path: string): Promise<T> {
  return apiFetch<T>(path);
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return apiFetch<T>(path, {
    method: "POST",
    body: body ? JSON.stringify(body) : undefined,
  });
}

export function apiPut<T>(path: string, body?: unknown): Promise<T> {
  return apiFetch<T>(path, {
    method: "PUT",
    body: body ? JSON.stringify(body) : undefined,
  });
}

export function apiPatch<T>(path: string, body?: unknown): Promise<T> {
  return apiFetch<T>(path, {
    method: "PATCH",
    body: body ? JSON.stringify(body) : undefined,
  });
}

export function apiDelete<T = void>(path: string): Promise<T> {
  return apiFetch<T>(path, { method: "DELETE" });
}

// ── Shared types ─────────────────────────────────────────────────

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}

// ── Domain endpoints ────────────────────────────────────────────

export const healthApi = {
  status: () => apiGet<{ status: string; version: string; database: string }>("/api/status"),
};

export interface AgentInfo {
  name: string;
  provider: { type: string; model: string; base_url: string; configured: boolean };
  orchestration: { framework: string };
  pattern: { type: string };
  memory: { backend: string };
  telemetry: { enabled: boolean; langfuse_public_key: boolean; langfuse_secret_key: boolean; langfuse_host: string };
  agentops: {
    enabled: boolean;
    configured: boolean;
    capture_content: boolean;
    default_tags: string[];
    environment: string;
    error?: string | null;
  };
  probe?: { ok: boolean; reply?: string; error?: string } | null;
}

export const agentApi = {
  info: (probe = false) => apiGet<AgentInfo>(`/api/agent${probe ? "?probe=true" : ""}`),
};

export const itemsApi = {
  list: (page = 1, limit = 20, status?: string) => {
    const params = new URLSearchParams({ page: String(page), limit: String(limit) });
    if (status) params.set("status", status);
    return apiGet<Paginated<Item>>(`/api/items?${params}`);
  },
  get: (id: number) => apiGet<Item>(`/api/items/${id}`),
  create: (data: ItemCreate) => apiPost<Item>("/api/items", data),
  update: (id: number, data: Partial<ItemCreate>) => apiPatch<Item>(`/api/items/${id}`, data),
  delete: (id: number) => apiDelete(`/api/items/${id}`),
};

// ── Domain types ────────────────────────────────────────────────

export interface Item {
  id: number;
  name: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ItemCreate {
  name: string;
  description?: string | null;
  status?: string;
}
