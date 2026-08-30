import type { NewsItem } from '@/types';
import { useDirectoryList } from './useDirectoryList';

/**
 * News/article feed, filtered and paginated server-side.
 *
 * Forwards the URL query string so category filters and search apply to all
 * articles, not just the first page.
 */
export function useNews() {
  return useDirectoryList<NewsItem>('/articles/');
}
