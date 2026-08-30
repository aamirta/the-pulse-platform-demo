import { apiGet } from '@/lib/api';
import { useApiListState } from './useApiState';

export interface SearchResult {
  id: string;
  type: 'startup' | 'founder' | 'investor';
  title: string;
  subtitle: string;
  url: string;
}

interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
}

export function useSearch(q: string) {
  return useApiListState<SearchResult>(
    () => (q.trim() ? apiGet<SearchResponse>(`/search/?q=${encodeURIComponent(q.trim())}`).then((res) => res.results) : Promise.resolve([])),
    [q]
  );
}
