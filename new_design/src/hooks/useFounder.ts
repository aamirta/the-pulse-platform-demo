import { apiGet } from '@/lib/api';
import type { Founder } from '@/types';
import { useApiState } from './useApiState';

export function useFounder(id: string | undefined) {
  return useApiState<Founder>(() => (id ? apiGet<Founder>(`/founders/${id}`) : Promise.reject(new Error('Missing founder id'))), [id]);
}
