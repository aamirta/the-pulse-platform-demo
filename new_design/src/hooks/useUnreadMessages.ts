import { useCallback, useEffect, useState } from 'react';
import { apiGet } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

/** Counters behind the inbox badge, as returned by the API. */
export interface UnreadCounters {
  unread: number;
  conversations: number;
}

/** Cross-tab ping so reading a thread in one tab clears the badge in the others. */
const REFRESH_BROADCAST_KEY = 'pulse-inbox-read-at';

/**
 * One shared poller for every badge on the page.
 *
 * The counter is rendered in at least two places (the sidebar and the account
 * menu), and a per-component `setInterval` meant each of them fetched on its
 * own schedule — with React's development double-mount, a single page load
 * issued the request roughly a dozen times. State, the timer and the in-flight
 * request all live here instead, so N subscribers still cost one request.
 */
const listeners = new Set<(counters: UnreadCounters) => void>();
let counters: UnreadCounters = { unread: 0, conversations: 0 };
let inFlight: Promise<void> | null = null;
let timer: ReturnType<typeof setInterval> | null = null;
let pollIntervalMs = 60_000;

function publish(next: UnreadCounters) {
  counters = next;
  listeners.forEach((listener) => listener(next));
}

/** Fetch the counters, collapsing concurrent callers onto one request. */
function refresh(): Promise<void> {
  if (inFlight) return inFlight;
  inFlight = apiGet<UnreadCounters>('/members/conversations/unread-count')
    .then((next) => publish(next))
    .catch(() => {
      // A failed counter must never surface an error: it is decoration on the
      // navigation, not something the user asked for.
    })
    .finally(() => {
      inFlight = null;
    });
  return inFlight;
}

function startPolling() {
  if (timer) return;
  timer = setInterval(() => {
    // A hidden tab does not need a fresh badge, and polling one all afternoon
    // is pure waste.
    if (document.visibilityState === 'visible') void refresh();
  }, pollIntervalMs);
}

function stopPolling() {
  if (!timer) return;
  clearInterval(timer);
  timer = null;
}

/** Ask every mounted badge — in this tab and the others — to re-read the count. */
export function notifyInboxChanged() {
  void refresh();
  try {
    localStorage.setItem(REFRESH_BROADCAST_KEY, String(Date.now()));
  } catch {
    /* private browsing: in-tab subscribers are still updated */
  }
}

/**
 * Subscribe to the unread counter for the signed-in actor.
 *
 * Nothing is requested until the stored session has finished being restored:
 * firing during bootstrap sent an unauthenticated request that answered 401,
 * logged an error in the console, and only succeeded on the retry after the
 * token refresh landed.
 */
export function useUnreadMessages(intervalMs = 60_000): UnreadCounters & { reload: () => void } {
  const { member, user, isBootstrapping } = useAuth();
  const ready = (!!member || !!user) && !isBootstrapping;
  const [local, setLocal] = useState<UnreadCounters>(counters);

  pollIntervalMs = intervalMs;

  const reload = useCallback(() => {
    if (ready) void refresh();
  }, [ready]);

  useEffect(() => {
    if (!ready) {
      // Signed out: drop any count left over from the previous session.
      if (counters.unread || counters.conversations) publish({ unread: 0, conversations: 0 });
      setLocal({ unread: 0, conversations: 0 });
      return;
    }

    listeners.add(setLocal);
    setLocal(counters);
    void refresh();
    startPolling();

    const onStorage = (event: StorageEvent) => {
      if (event.key === REFRESH_BROADCAST_KEY) void refresh();
    };
    const onVisible = () => {
      if (document.visibilityState === 'visible') void refresh();
    };
    window.addEventListener('storage', onStorage);
    document.addEventListener('visibilitychange', onVisible);

    return () => {
      listeners.delete(setLocal);
      window.removeEventListener('storage', onStorage);
      document.removeEventListener('visibilitychange', onVisible);
      // The timer belongs to the page, not to any one badge, so it only stops
      // once the last subscriber has gone.
      if (listeners.size === 0) stopPolling();
    };
  }, [ready]);

  return { ...local, reload };
}
