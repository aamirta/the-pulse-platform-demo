import { apiGet } from '@/lib/api';
import type { EcosystemGraphData } from '@/types';
import { useApiState } from './useApiState';

/**
 * Fetch the real ecosystem relationship graph.
 *
 * Every edge is backed by a join record (StartupFounders, Investements ->
 * FundingRounds, StartupIncubators), so the returned graph reflects the
 * database rather than any client-side inference.
 */
export function useEcosystemGraph(limit = 140) {
  return useApiState<EcosystemGraphData>(
    () => apiGet<EcosystemGraphData>(`/graph/ecosystem?limit=${limit}`),
    [limit]
  );
}
