/**
 * StatusStates — reusable loading / error / empty / load-more components.
 * Mirrors F433's StatusStates pattern for consistent UX across pages.
 */

import { Loader2, AlertCircle, ChevronDown, RefreshCw } from "lucide-react";

export function LoadingSpinner({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-20 text-[var(--text-secondary)]">
      <div className="w-12 h-12 rounded-2xl bg-[var(--accent-dim)] flex items-center justify-center">
        <Loader2 className="w-6 h-6 text-[var(--accent)] animate-spin" />
      </div>
      <span className="text-sm font-medium">{label}</span>
    </div>
  );
}

export function ErrorBox({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="card p-8 flex flex-col items-center gap-4 text-center">
      <div className="w-12 h-12 rounded-2xl bg-red-500/10 flex items-center justify-center">
        <AlertCircle className="w-6 h-6 text-red-400" />
      </div>
      <div>
        <p className="font-semibold text-[var(--text)]">Something went wrong</p>
        <p className="text-sm text-[var(--text-secondary)] mt-1">{message}</p>
      </div>
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary mt-2">
          <RefreshCw className="w-4 h-4" /> Try Again
        </button>
      )}
    </div>
  );
}

export function EmptyState({
  message = "Nothing here yet",
  icon,
}: {
  message?: string;
  icon?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-[var(--text-secondary)] gap-2">
      {icon}
      <p className="text-sm">{message}</p>
    </div>
  );
}

export function LoadMoreButton({
  onClick,
  loading,
}: {
  onClick: () => void;
  loading?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className="btn-secondary w-full flex items-center justify-center gap-2 py-3"
    >
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <ChevronDown className="w-4 h-4" />
      )}
      {loading ? "Loading…" : "Load more"}
    </button>
  );
}