import type { Founder } from '@/types';
import { useDirectoryList } from './useDirectoryList';

/**
 * Founder directory, filtered and paginated server-side.
 *
 * Forwards the URL query string so search and filters apply to all founders,
 * not just the first page.
 *
 * `founderType` narrows to sole founders or to people who founded alongside
 * others. It is passed as an override rather than read from the URL because the
 * page's own `?type=` param selects *which view* to render — experts, co-founder
 * postings, or this directory — and the API knows it by a different name.
 */
export function useFounders(founderType?: 'founder' | 'cofounder') {
  return useDirectoryList<Founder>(
    '/founders/',
    founderType ? { founder_type: founderType } : undefined,
  );
}
