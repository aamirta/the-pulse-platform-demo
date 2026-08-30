import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { apiGet } from '@/lib/api';
import type { Startup } from '@/types';

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface StartupListState {
  data: Startup[];
  total: number;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

export function useStartups(): StartupListState {
  const [searchParams] = useSearchParams();
  const query = searchParams.toString();

  const [data, setData] = useState<Startup[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const refetch = useCallback(() => setRefreshKey((k) => k + 1), []);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    const path = query ? `/startups/?${query}` : '/startups/';
    apiGet<PaginatedResponse<Startup>>(path)
      .then((result) => {
        if (!cancelled) {
          setData(result.items ?? []);
          setTotal(result.total ?? 0);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : 'Une erreur est survenue';
          setError(new Error(message));
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [query, refreshKey]);

  return { data, total, isLoading, error, refetch };
}
