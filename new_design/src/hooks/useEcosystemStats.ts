import { apiGet } from '@/lib/api';
import type { EcosystemStat } from '@/types';
import { useApiListState } from './useApiState';

export function useEcosystemStats() {
  return useApiListState<EcosystemStat>(() => apiGet<EcosystemStat[]>('/stats/ecosystem'), []);
}
