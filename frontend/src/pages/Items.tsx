/**
 * Items page — full CRUD example with search, pagination, create/edit forms.
 * Demonstrates the useApi, usePaginatedApi hooks, and Form components.
 */

import { useState } from "react";
import { Pencil, Trash2, Plus, Search, Loader2, X, Package } from "lucide-react";
import { itemsApi, type Item, type ItemCreate } from "../lib/api";
import { usePaginatedApi } from "../hooks";
import { FormInput, FormSelect, FormTextarea } from "../components/Form";
import { LoadingSpinner, ErrorBox, EmptyState, LoadMoreButton } from "../components/StatusStates";

const STATUS_OPTIONS = [
  { value: "active", label: "Active" },
  { value: "inactive", label: "Inactive" },
  { value: "archived", label: "Archived" },
];

const STATUS_CLASS: Record<string, string> = {
  active: "badge badge-active",
  inactive: "badge badge-inactive",
  archived: "badge badge-archived",
};

export function Items() {
  const [search, setSearch] = useState("");
  const { items, loading, error, hasMore, loadMore, refetch } = usePaginatedApi<Item>(
    (page) => itemsApi.list(page, 20, search || undefined),
    [search],
  );

  const [showCreate, setShowCreate] = useState(false);
  const [editing, setEditing] = useState<Item | null>(null);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text)] tracking-tight">Items</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-0.5">Example CRUD resource</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="btn-primary flex items-center gap-2 self-start"
        >
          <Plus className="w-4 h-4" /> New Item
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-secondary)]" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search items by name or description…"
          className="form-input pl-10 w-full"
        />
      </div>

      {/* States */}
      {loading && <LoadingSpinner label="Loading items…" />}
      {error && <ErrorBox message={error} onRetry={refetch} />}

      {/* Empty state */}
      {!loading && !error && items.length === 0 && (
        <div className="card p-12 flex flex-col items-center gap-4 text-center">
          <div className="w-16 h-16 rounded-2xl bg-[var(--accent-dim)] flex items-center justify-center">
            <Package className="w-8 h-8 text-[var(--accent)]" />
          </div>
          <div>
            <p className="font-semibold text-[var(--text)]">No items yet</p>
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              {search ? "No results match your search." : "Create your first item to get started."}
            </p>
          </div>
          {!search && (
            <button onClick={() => setShowCreate(true)} className="btn-primary mt-2">
              <Plus className="w-4 h-4" /> Create Item
            </button>
          )}
        </div>
      )}

      {/* Item list */}
      {!loading && !error && items.length > 0 && (
        <div className="space-y-2">
          {items.map((item, i) => (
            <div
              key={item.id}
              className="card card-glow p-4 flex items-center justify-between gap-4 animate-fade-in group"
              style={{ animationDelay: `${i * 0.03}s` }}
            >
              <div className="min-w-0 flex-1 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-[var(--accent-dim)] flex items-center justify-center shrink-0">
                  <Package className="w-4 h-4 text-[var(--accent)]" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-[var(--text)] truncate">{item.name}</span>
                    <span className={STATUS_CLASS[item.status] ?? "badge badge-inactive"}>
                      {item.status}
                    </span>
                  </div>
                  {item.description && (
                    <p className="text-sm text-[var(--text-secondary)] truncate mt-0.5">
                      {item.description}
                    </p>
                  )}
                </div>
              </div>

              {/* Actions — show on hover */}
              <div className="flex items-center gap-0.5 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => setEditing(item)}
                  className="btn-icon"
                  title="Edit"
                >
                  <Pencil className="w-4 h-4" />
                </button>
                <button
                  onClick={async () => {
                    await itemsApi.delete(item.id);
                    refetch();
                  }}
                  className="btn-icon danger"
                  title="Delete"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
          {hasMore && (
            <div className="pt-2">
              <LoadMoreButton onClick={loadMore} />
            </div>
          )}
        </div>
      )}

      {/* Create modal */}
      {showCreate && (
        <ItemFormModal
          title="Create Item"
          onClose={() => setShowCreate(false)}
          onSave={async (data) => {
            await itemsApi.create(data);
            setShowCreate(false);
            refetch();
          }}
        />
      )}

      {/* Edit modal */}
      {editing && (
        <ItemFormModal
          title="Edit Item"
          initial={editing}
          onClose={() => setEditing(null)}
          onSave={async (data) => {
            await itemsApi.update(editing.id, data);
            setEditing(null);
            refetch();
          }}
        />
      )}
    </div>
  );
}

// ── Item Form Modal ────────────────────────────────────────────────

function ItemFormModal({
  title,
  initial,
  onClose,
  onSave,
}: {
  title: string;
  initial?: Item;
  onClose: () => void;
  onSave: (data: ItemCreate) => Promise<void>;
}) {
  const [name, setName] = useState(initial?.name ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [status, setStatus] = useState(initial?.status ?? "active");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await onSave({ name, description: description || null, status });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="modal-backdrop fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="modal-content card p-6 w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-bold text-[var(--text)]">{title}</h2>
          <button onClick={onClose} className="btn-icon">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <FormInput
            label="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Item name"
            required
            autoFocus
          />
          <FormTextarea
            label="Description"
            value={description ?? ""}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Optional description"
            hint="Optional"
          />
          <FormSelect
            label="Status"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            options={STATUS_OPTIONS}
          />
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-sm text-red-400">
              {error}
            </div>
          )}
          <div className="flex gap-3 pt-3">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !name.trim()}
              className="btn-primary flex-1"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Saving…
                </>
              ) : (
                "Save"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}