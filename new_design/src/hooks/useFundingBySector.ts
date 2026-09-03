import { apiGet } from '@/lib/api';
import { useApiState } from './useApiState';

/** `{labels, values}` series returned by the stats endpoints. */
export interface SectorSeries {
  labels: string[];
  values: number[];
}

/**
 * Funding split by sector, from `/stats/funding-by-sector`.
 *
 * The home page's analytics preview used to render invented figures
 * ("Fintech & Payments 32%", "AgriTech & Climate 24%") that matched nothing in
 * the database. This supplies the measured split instead.
 */
export function useFundingBySector() {
  return useApiState<SectorSeries>(
    () => apiGet<SectorSeries>('/stats/funding-by-sector'),
    [],
  );
}
