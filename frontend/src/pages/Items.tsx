/**
 * Items page — full CRUD example with search, pagination, create/edit forms.
 * Demonstrates the useApi, usePaginatedApi hooks, and Form components.
 */

import { useState } from "react";
import { Pencil, Trash2, Plus, Search,Loader2 } from "lucide-react";
import { itemsApi, type Item, type ItemCreate } from "../lib/api";
import { usePaginatedApi } from "../hooks";
import { FormInput, FormSelect, FormTextarea } from "../components/Form";
import { LoadingSpinner, ErrorBox, EmptyState, LoadMoreButton } from "../components/StatusStates";

const STATUS_OPTIONS = [
  { value: "active", label: "Active" },
  { value: "inactive", label: "Inactive" },
  { value: "archived", label: "Archived" },
];

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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text)]">Items</h1>
          <p className="text-sm text-[var(--text-secondary)]">Example CRUD resource</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> New Item
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-secondary)]" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search items…"
          className="form-input pl-10 w-full"
        />
      </div>

      {/* Item list */}
      {loading && <LoadingSpinner label="Loading items…" />}
      {error && <ErrorBox message={error} onRetry={refetch} />}
      {!loading && !error && items.length === 0 && (
        <EmptyState message="No items yet. Create your first item!" />
      )}
      {!loading && !error && items.length > 0 && (
        <div className="space-y-2">
          {items.map((item) => (
            <div
              key={item.id}
              className="card p-4 flex items-center justify-between gap-4"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-[var(--text)]">{item.name}</span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-[var(--accent)]/10 text-[var(--accent)]">
                    {item.status}
                  </span>
                </div>
                {item.description && (
                  <p className="text-sm text-[var(--text-secondary)] truncate mt-0.5">
                    {item.description}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <button
                  onClick={() => setEditing(item)}
                  className="p-2 rounded-lg hover:bg-[var(--hover)] text-[var(--text-secondary)] transition-colors"
                >
                  <Pencil className="w-4 h-4" />
                </button>
                <button
                  onClick={async () => {
                    await itemsApi.delete(item.id);
                    refetch();
                  }}
                  className="p-2 rounded-lg hover:bg-red-500/10 text-red-400 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
          {hasMore && <LoadMoreButton onClick={loadMore} />}
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div className="card p-6 w-full max-w-md mx-4" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-lg font-semibold text-[var(--text)] mb-4">{title}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <FormInput label="Name" value={name} onChange={(e) => setName(e.target.value)} required />
          <FormTextarea
            label="Description"
            value={description ?? ""}
            onChange={(e) => setDescription(e.target.value)}
            hint="Optional"
          />
          <FormSelect
            label="Status"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            options={STATUS_OPTIONS}
          />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">
              Cancel
            </button>
            <button type="submit" disabled={submitting} className="btn-primary flex-1 flex items-center justify-center gap-2">
              {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
              {submitting ? "Saving…" : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}