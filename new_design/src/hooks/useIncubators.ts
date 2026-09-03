import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { apiGet } from '@/lib/api';
import type { Incubator } from '@/types';
import type { PaginatedResponse } from './useStartups';

export interface IncubatorListState {
  data: Incubator[];
  total: number;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

/**
 * Fetch the incubator directory from `/incubators/`.
 *
 * The sidebar used to route "Incubateurs" to `/startups?type=incubateur`, which
 * filtered the *investor* list and surfaced only the 3 investors whose type
 * mentioned an incubator. The real directory lives in its own table.
 */
export function useIncubators(): IncubatorListState {
  const [searchParams] = useSearchParams();
  const query = searchParams.toString();

  const [data, setData] = useState<Incubator[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const refetch = useCallback(() => setRefreshKey((k) => k + 1), []);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    const path = query ? `/incubators/?${query}` : '/incubators/?page_size=100';
    apiGet<PaginatedResponse<Incubator>>(path)
      .then((result) => {
        if (!cancelled) {
          setData(result.items ?? []);
          setTotal(result.total ?? 0);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          // Kept intact so the copy layer can read `kind`; re-wrapping lost it.
          setError(err instanceof Error ? err : new Error(String(err)));
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [query, refreshKey]);

  return { data, total, isLoading, error, refetch };
}
