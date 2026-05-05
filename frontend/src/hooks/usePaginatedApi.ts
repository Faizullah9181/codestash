/**
 * usePaginatedApi — auto-loading paginated list with "load more".
 *
 * Usage:
 *   const { items, loading, error, hasMore, loadMore, refetch, total } =
 *     usePaginatedApi((page) => itemsApi.list(page, 20), []);
 */

import { useState, useEffect, useCallback } from "react";

interface UsePaginatedApiState<T> {
  items: T[];
  total: number;
  loading: boolean;
  loadingMore: boolean;
  error: string | null;
  hasMore: boolean;
  loadMore: () => Promise<void>;
  refetch: () => Promise<void>;
}

export function usePaginatedApi<T>(
  fetcher: (page: number, limit?: number) => Promise<{
    items: T[];
    total: number;
    has_more: boolean;
  }>,
  deps: unknown[] = [],
  limit = 20,
): UsePaginatedApiState<T> {
  const [items, setItems] = useState<T[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPage = useCallback(
    async (p: number, append: boolean) => {
      if (append) setLoadingMore(true);
      else setLoading(true);
      setError(null);

      try {
        const result = await fetcher(p, limit);
        setItems((prev) => (append ? [...prev, ...result.items] : result.items));
        setTotal(result.total);
        setHasMore(result.has_more);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Unknown error");
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [...deps, limit],
  );

  useEffect(() => {
    loadPage(1, false);
  }, [loadPage]);

  const loadMore = useCallback(async () => {
    const next = page + 1;
    setPage(next);
    await loadPage(next, true);
  }, [page, loadPage]);

  const refetch = useCallback(async () => {
    setPage(1);
    setItems([]);
    await loadPage(1, false);
  }, [loadPage]);

  return { items, total, loading, loadingMore, error, hasMore, loadMore, refetch };
}