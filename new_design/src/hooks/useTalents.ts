import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { apiGet } from '@/lib/api';
import type { PaginatedResponse } from './useStartups';

/** A person available to join a startup, as returned by `/talents/`. */
export interface Talent {
  id: string;
  name: string;
  title: string | null;
  location: string | null;
  yearsExperience: string | null;
  roleType: string | null;
  workFormat: string | null;
  availability: string | null;
  skills: string[];
  industries: string[];
  profilePic: string | null;
}

export interface TalentListState {
  data: Talent[];
  total: number;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

/**
 * Fetch the talent marketplace from `/talents/`.
 *
 * The sidebar used to route "Talent Marketplace" to `/opportunities?type=talent`,
 * which rendered the Opportunities page verbatim -- the routing bug the review
 * flagged. The listing has its own table and now its own endpoint.
 */
export function useTalents(): TalentListState {
  const [searchParams] = useSearchParams();
  const query = searchParams.toString();

  const [data, setData] = useState<Talent[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const refetch = useCallback(() => setRefreshKey((k) => k + 1), []);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    const path = query ? `/talents/?${query}` : '/talents/?page_size=100';
    apiGet<PaginatedResponse<Talent>>(path)
      .then((result) => {
        if (!cancelled) {
          setData(result.items ?? []);
          setTotal(result.total ?? 0);
        }
      })
      .catch((err) => {
        // Kept intact so the copy layer can read `kind`.
        if (!cancelled) setError(err instanceof Error ? err : new Error(String(err)));
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
