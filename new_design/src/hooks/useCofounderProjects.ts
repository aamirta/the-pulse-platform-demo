import type { CofounderProject } from '@/types';
import { useDirectoryList } from './useDirectoryList';

/**
 * Open co-founder searches, paginated server-side and newest first.
 *
 * The "Co-founders Needed" section used to filter the *founders* list against a
 * pair of hardcoded mock slugs (`sarah-bennani`, `mehdi-filali`) that no real API
 * id matches, so it always rendered empty. The postings live in their own table
 * and now have their own endpoint.
 */
export function useCofounderProjects() {
  return useDirectoryList<CofounderProject>('/cofounders/');
}
