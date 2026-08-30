import { apiGet } from '@/lib/api';
import { useApiListState } from './useApiState';
import type { PaginatedResponse } from './useStartups';

export interface Trend {
  tag: string;
  count: number;
}

export interface LatestFundingRound {
  id: string;
  startup: string;
  startupLogo?: string;
  amount: string;
  round: string;
  investor: string;
  date: string;
}

/** Trending sectors, ranked by how many startups reference them. */
export function useTrends(limit = 8) {
  return useApiListState<Trend>(
    () => apiGet<Trend[]>('/stats/trends').then((items) => items.slice(0, limit)),
    [limit],
  );
}

/**
 * The most recent funding rounds.
 *
 * Rows with no recorded amount are filtered out so the sidebar does not render
 * blank figures — the previous implementation read from a static fixture.
 */
export function useLatestFunding(limit = 4) {
  return useApiListState<LatestFundingRound>(
    () =>
      apiGet<PaginatedResponse<LatestFundingRound>>('/funding-rounds/?page_size=50').then((res) =>
        (res.items ?? []).filter((round) => round.amount?.trim()).slice(0, limit),
      ),
    [limit],
  );
}
