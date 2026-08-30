import type { Investor } from '@/types';
import { useDirectoryList } from './useDirectoryList';

/**
 * Investor directory, filtered and paginated server-side.
 *
 * Forwards the URL query string so search and filters apply to all investors,
 * not just the first page.
 */
export function useInvestors() {
  return useDirectoryList<Investor>('/investors/');
}

/**
 * The `PrimaryInvestorType` venture studios carry in the Investors table.
 *
 * Kept in sync with `VENTURE_STUDIO_TYPE` in scripts/add_venture_studios.py,
 * which seeds the rows.
 */
export const VENTURE_STUDIO_TYPE = 'Venture Studio';

/**
 * Venture studios and builders, filtered server-side.
 *
 * The section is reached via `/startups?type=venture-studio`, and that `type`
 * param used to be forwarded verbatim to the API — which matched
 * `PrimaryInvestorType ILIKE '%venture-studio%'` and returned zero rows, so the
 * section always rendered empty. The hyphenated slug is a route selector, not a
 * database value, so the real type is substituted here.
 */
export function useVentureStudios() {
  return useDirectoryList<Investor>('/investors/', { type: VENTURE_STUDIO_TYPE });
}
