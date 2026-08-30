import type { Expert } from '@/types';
import { useDirectoryList } from './useDirectoryList';

/**
 * Ecosystem experts and mentors, paginated server-side.
 *
 * The "Experts & Mentors" section used to filter the *founders* list against a
 * pair of hardcoded mock slugs (`youssef-chari`, `driss-spore`) that no real API
 * id matches, so it always rendered empty. Experts have their own table and now
 * their own endpoint.
 */
export function useExperts() {
  return useDirectoryList<Expert>('/experts/');
}
