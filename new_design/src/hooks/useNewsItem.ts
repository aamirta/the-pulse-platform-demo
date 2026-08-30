import { apiGet } from '@/lib/api';
import type { NewsItem } from '@/types';
import { useApiState } from './useApiState';

export function useNewsItem(id: string | undefined) {
  return useApiState<NewsItem>(() => (id ? apiGet<NewsItem>(`/articles/${id}`) : Promise.reject(new Error('Missing article id'))), [id]);
}
