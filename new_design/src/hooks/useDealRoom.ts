import { useCallback, useEffect, useState } from 'react';
import { apiGet, apiPost, API_BASE_URL, getAccessToken } from '@/lib/api';
import type {
  DealRoomSummary,
  DocumentLink,
} from '@/types/dealroom';

/**
 * Load the deal rooms the signed-in actor can open.
 *
 * The list is whatever the server says it is: rooms owned through an approved
 * entity claim, plus rooms the actor has been admitted to as an investor.
 */
export function useMyDealRooms() {
  const [rooms, setRooms] = useState<DealRoomSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setRooms(await apiGet<DealRoomSummary[]>('/deal-rooms/mine'));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load deal rooms');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return { rooms, loading, error, reload: load };
}

/** Generic loader for one deal room resource, with a manual reload hook. */
export function useDealRoomResource<T>(path: string | null, enabled = true) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(enabled && path !== null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!path || !enabled) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setData(await apiGet<T>(path));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [path, enabled]);

  useEffect(() => {
    void load();
  }, [load]);

  return { data, loading, error, reload: load };
}

/**
 * Open a document through the signed-link pipeline.
 *
 * Two steps on purpose. The first asks the API to mint a short-lived link bound
 * to this viewer, this version and this intent; the second fetches the bytes,
 * which the server re-authorizes before sending. The raw file is never
 * addressable, and the watermark is applied server-side, so nothing here can
 * weaken either guarantee.
 */
export async function openDealRoomDocument(
  roomId: number,
  documentId: number,
  intent: 'preview' | 'download',
): Promise<{ blobUrl: string; link: DocumentLink }> {
  const link = await apiPost<DocumentLink>(
    `/deal-rooms/${roomId}/documents/${documentId}/link?intent=${intent}`,
    {},
  );

  // `link.url` is absolute from the API root; API_BASE_URL already ends in /api/v1.
  const target = link.url.replace(/^\/api\/v1/, '');
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}${target}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }

  const blob = await response.blob();
  return { blobUrl: URL.createObjectURL(blob), link };
}

/** Trigger a browser save for an already-fetched document blob. */
export function saveBlob(blobUrl: string, filename: string) {
  const anchor = document.createElement('a');
  anchor.href = blobUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
}
