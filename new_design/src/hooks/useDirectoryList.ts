import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { apiGet } from '@/lib/api';
import type { PaginatedResponse } from './useStartups';

/**
 * Page size requested for directory listings.
 *
 * Matches the backend's MAX_PAGE_SIZE. The previous hooks sent no pagination
 * parameters at all, so they silently received the API default of 20 rows and
 * then filtered that slice client-side — the Founders page showed 20 of 983
 * records and its search only ever looked at those 20.
 */
export const DIRECTORY_PAGE_SIZE = 100;

export interface DirectoryListState<T> {
  data: T[];
  /** Total matching rows on the server, which may exceed the loaded page. */
  total: number;
  /** True while more rows exist beyond what has been loaded. */
  hasMore: boolean;
  isLoading: boolean;
  /** True while an additional page is being appended. */
  isLoadingMore: boolean;
  error: Error | null;
  refetch: () => void;
  /** Append the next page to the current results. */
  loadMore: () => void;
}

/**
 * Fetch a paginated directory resource, forwarding the current URL query string
 * so filtering and search happen server-side across the whole dataset.
 *
 * `overrides` replaces individual query params before the request is sent. Some
 * URL params select *which view* to render rather than describing a server-side
 * filter — `/startups?type=venture-studio` is one — and forwarding those blindly
 * filters the result set down to nothing. Such views pass the real API value here.
 */
export function useDirectoryList<T>(
  resource: string,
  overrides?: Record<string, string>,
): DirectoryListState<T> {
  const [searchParams] = useSearchParams();

  const params = new URLSearchParams(searchParams);
  if (overrides) {
    for (const [key, value] of Object.entries(overrides)) {
      params.set(key, value);
    }
  }
  if (!params.has('page_size')) {
    params.set('page_size', String(DIRECTORY_PAGE_SIZE));
  }
  // Effects below key off this string, not the `overrides` object, so callers
  // can pass a fresh literal each render without retriggering fetches.
  const query = params.toString();

  const [data, setData] = useState<T[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [page, setPage] = useState(1);

  const refetch = useCallback(() => setRefreshKey((key) => key + 1), []);

  // Changing the filters restarts paging, otherwise page 3 of the old query
  // would be appended to page 1 of the new one.
  useEffect(() => {
    setPage(1);
  }, [query]);

  useEffect(() => {
    let cancelled = false;
    const isFirstPage = page === 1;
    if (isFirstPage) {
      setIsLoading(true);
    } else {
      setIsLoadingMore(true);
    }
    setError(null);

    apiGet<PaginatedResponse<T>>(`${resource}?${query}&page=${page}`)
      .then((result) => {
        if (cancelled) return;
        const items = result.items ?? [];
        setData((previous) => (isFirstPage ? items : [...previous, ...items]));
        setTotal(result.total ?? 0);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof Error ? err : new Error('Une erreur est survenue'));
      })
      .finally(() => {
        if (cancelled) return;
        setIsLoading(false);
        setIsLoadingMore(false);
      });

    return () => {
      cancelled = true;
    };
  }, [resource, query, refreshKey, page]);

  const loadMore = useCallback(() => {
    setPage((current) => current + 1);
  }, []);

  return {
    data,
    total,
    hasMore: total > data.length,
    isLoading,
    isLoadingMore,
    error,
    refetch,
    loadMore,
  };
}
