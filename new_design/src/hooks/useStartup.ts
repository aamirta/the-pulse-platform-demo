import { apiGet } from '@/lib/api';
import type { Startup } from '@/types';
import { useApiState } from './useApiState';

export function useStartup(id: string | undefined) {
  return useApiState<Startup>(() => (id ? apiGet<Startup>(`/startups/${id}`) : Promise.reject(new Error('Missing startup id'))), [id]);
}
