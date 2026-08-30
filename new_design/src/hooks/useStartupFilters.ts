import { apiGet } from '@/lib/api';
import { useApiState } from './useApiState';

export interface StartupFilters {
  sectors: string[];
  stages: string[];
  statuses: string[];
  locations: string[];
  legal_forms: string[];
}

export function useStartupFilters() {
  return useApiState<StartupFilters>(() => apiGet('/startups/filters'), []);
}
