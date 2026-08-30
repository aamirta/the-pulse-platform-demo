import { apiGet } from '@/lib/api';
import { useApiState } from './useApiState';

export interface HomeStats {
  startups: number;
  founders: number;
  investors: number;
  incubators: number;
  totalFunding: string;
  opportunities: number;
  sectors: number;
  cities: number;
  fundingRounds: number;
}

export function useStats() {
  return useApiState<HomeStats>(() => apiGet<HomeStats>('/stats/home'), []);
}
