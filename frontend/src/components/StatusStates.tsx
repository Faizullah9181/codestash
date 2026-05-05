/**
 * StatusStates — reusable loading / error / empty / load-more components.
 * Mirrors F433's StatusStates pattern for consistent UX across pages.
 */

import { Loader2, AlertCircle, Inbox, ChevronDown } from "lucide-react";

export function LoadingSpinner({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-20 text-gray-400">
      <Loader2 className="w-5 h-5 animate-spin" />
      <span className="text-sm">{label}</span>
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
    <div className="card flex flex-col items-center gap-3 py-10 text-center">
      <AlertCircle className="w-8 h-8 text-red-400" />
      <p className="text-sm text-red-300">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary text-xs mt-2">
          Try Again
        </button>
      )}
    </div>
  );
}

export function EmptyState({
  message = "Nothing here yet",
  icon = <Inbox className="w-8 h-8" />,
}: {
  message?: string;
  icon?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-gray-500 gap-2">
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
      className="btn-secondary w-full flex items-center justify-center gap-2"
    >
      {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ChevronDown className="w-4 h-4" />}
      {loading ? "Loading…" : "Load more"}
    </button>
  );
}