/**
 * Data access for the Deal Room marketplace.
 *
 * Three hooks, one per surface: the public board, the author's own posts, and
 * the filter vocabulary. Nothing here holds a hard-coded list — `usePostMeta`
 * fetches the vocabulary the server actually validates against, so a dropdown
 * can never offer a value the API would reject.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { apiGet } from '@/lib/api';
import type { BoardFilters, DealRoomPostListItem, PostMeta } from '@/types/dealroomPosts';

interface Paged<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

/** Build a query string, dropping empty values so they never reach the API. */
export function buildQuery(filters: Record<string, unknown>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === null || value === '') continue;
    params.set(key, String(value));
  }
  const query = params.toString();
  return query ? `?${query}` : '';
}

interface BoardState {
  posts: DealRoomPostListItem[];
  total: number;
  pages: number;
  page: number;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

/**
 * The public opportunity board.
 *
 * Filters are serialised into the request rather than applied client-side: the
 * board is paginated server-side, so filtering a single page in the browser
 * would silently hide matches that live on page two.
 *
 * A request that resolves after a newer one has been issued is discarded, so
 * typing quickly in the search box cannot leave a stale page on screen.
 */
export function useDealRoomPosts(filters: BoardFilters): BoardState {
  const [posts, setPosts] = useState<DealRoomPostListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [page, setPage] = useState(filters.page ?? 1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nonce, setNonce] = useState(0);

  const requestId = useRef(0);
  const query = buildQuery(filters as Record<string, unknown>);

  useEffect(() => {
    const id = ++requestId.current;
    setLoading(true);
    setError(null);

    apiGet<Paged<DealRoomPostListItem>>(`/deal-room-posts${query}`)
      .then((data) => {
        if (id !== requestId.current) return;
        setPosts(data.items);
        setTotal(data.total);
        setPages(data.pages);
        setPage(data.page);
      })
      .catch((err: unknown) => {
        if (id !== requestId.current) return;
        setError(err instanceof Error ? err.message : 'Could not load opportunities');
        setPosts([]);
        setTotal(0);
      })
      .finally(() => {
        if (id === requestId.current) setLoading(false);
      });
  }, [query, nonce]);

  const reload = useCallback(() => setNonce((n) => n + 1), []);
  return { posts, total, pages, page, loading, error, reload };
}

/** The caller's own posts, drafts included. */
export function useMyDealRoomPosts(statusFilter?: string): BoardState {
  const [posts, setPosts] = useState<DealRoomPostListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nonce, setNonce] = useState(0);

  const requestId = useRef(0);
  const query = buildQuery({ status: statusFilter, page_size: 50 });

  useEffect(() => {
    const id = ++requestId.current;
    setLoading(true);
    setError(null);

    apiGet<Paged<DealRoomPostListItem>>(`/deal-room-posts/mine${query}`)
      .then((data) => {
        if (id !== requestId.current) return;
        setPosts(data.items);
        setTotal(data.total);
        setPages(data.pages);
      })
      .catch((err: unknown) => {
        if (id !== requestId.current) return;
        setError(err instanceof Error ? err.message : 'Could not load your posts');
        setPosts([]);
      })
      .finally(() => {
        if (id === requestId.current) setLoading(false);
      });
  }, [query, nonce]);

  const reload = useCallback(() => setNonce((n) => n + 1), []);
  return { posts, total, pages, page: 1, loading, error, reload };
}

/**
 * The filter and composer vocabulary.
 *
 * Cached at module scope because every board mount needs it and it changes only
 * when someone posts. `reload` refetches after a create, so a brand new sector
 * appears in the filter bar without a page refresh.
 */
let metaCache: PostMeta | null = null;

export function usePostMeta(): { meta: PostMeta | null; loading: boolean; reload: () => void } {
  const [meta, setMeta] = useState<PostMeta | null>(metaCache);
  const [loading, setLoading] = useState(metaCache === null);

  const load = useCallback(() => {
    setLoading(true);
    apiGet<PostMeta>('/deal-room-posts/meta')
      .then((data) => {
        metaCache = data;
        setMeta(data);
      })
      .catch(() => {
        // The board still works without facet counts: the fixed vocabularies
        // are what the composer needs, and a failure here must not block it.
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (metaCache === null) load();
  }, [load]);

  const reload = useCallback(() => {
    metaCache = null;
    load();
  }, [load]);

  return { meta, loading, reload };
}
