import { apiGet } from '@/lib/api';
import { useApiListState } from './useApiState';
import type { PaginatedResponse } from './useStartups';
import type { LatestFundingRound } from './useSidebarData';

/**
 * Real funding rounds recorded for a startup.
 *
 * The profile page previously rendered an invented two-round history (a "Série A"
 * derived from the total plus a fixed "1.2M$ Seed" credited to named investors).
 */
export function useStartupFunding(startupName: string | undefined) {
  return useApiListState<LatestFundingRound>(
    () =>
      startupName
        ? apiGet<PaginatedResponse<LatestFundingRound>>(
            `/funding-rounds/?startup=${encodeURIComponent(startupName)}&page_size=50`,
          ).then((res) => res.items ?? [])
        : Promise.resolve([]),
    [startupName],
  );
}
