import { apiGet } from '@/lib/api';
import type { Investor } from '@/types';
import { useApiState } from './useApiState';

export function useInvestor(id: string | undefined) {
  return useApiState<Investor>(() => (id ? apiGet<Investor>(`/investors/${id}`) : Promise.reject(new Error('Missing investor id'))), [id]);
}
