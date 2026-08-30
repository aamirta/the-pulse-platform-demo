import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  AlertCircle,
  ChevronLeft,
  Clock,
  Filter,
  Loader2,
  Mail,
  MailOpen,
  MessageSquare,
  PenSquare,
  RotateCw,
  Search,
  Send,
  ShieldCheck,
  User,
  X,
} from 'lucide-react';
import { apiGet, apiPost } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useAuth } from '@/context/AuthContext';
import { useLanguage } from '@/context/LanguageContext';
import { notifyInboxChanged } from '@/hooks/useUnreadMessages';
import { toast } from 'sonner';
import { FadeInImage } from '@/enhancements/FadeInImage';

interface ConversationPartner {
  email: string;
  name: string | null;
  unread_count: number;
  last_message_at: string | null;
  last_message_preview: string | null;
  profile_pic: string | null;
  member_id: number | null;
  expert_id: number | null;
  role: string | null;
  message_count: number;
}

interface DirectMessage {
  id: number;
  post_id: number | null;
  from_email: string | null;
  to_email: string | null;
  from_name: string | null;
  to_name: string | null;
  message: string;
  is_read: boolean;
  created_at: string | null;
}

interface ThreadResponse {
  partner_email: string;
  messages: DirectMessage[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
  partner: ConversationPartner | null;
}

interface MessageSearchHit {
  id: number;
  partner_email: string;
  partner_name: string | null;
  partner_pic: string | null;
  outgoing: boolean;
  message: string;
  is_read: boolean;
  created_at: string | null;
}

interface Paged<T> {
  items: T[];
  total: number;
}

/** A row from the public community directory, which never carries an address. */
interface DirectoryMember {
  id: number;
  full_name: string;
  role: string;
  profile_pic: string | null;
}

/** What the id-addressed send endpoint returns once the thread exists. */
interface StartedConversation {
  partner_email: string;
  partner_name: string | null;
}

/**
 * A message the composer has accepted but the server has not yet confirmed.
 *
 * Held separately from `thread.messages` so reloading the thread cannot silently
 * drop something the user believes they sent: a failed send stays on screen,
 * with its text intact, until it is retried or dismissed.
 */
interface PendingMessage {
  localId: string;
  body: string;
  status: 'sending' | 'failed';
  error?: string;
}

/** Partner shape the header and context panel can render, however it was resolved. */
type PartnerLike = Partial<ConversationPartner> & { email: string };

const PAGE_SIZE = 30;
/** Mirrors `backend/schemas.py::MAX_MESSAGE_LENGTH`. */
const MAX_MESSAGE_LENGTH = 5000;
/** How often an open inbox re-reads the thread and the conversation list. */
const POLL_INTERVAL_MS = 20_000;

/** Initials fallback when a partner has no avatar, matching the directory cards. */
function Avatar({ partner, size = 40 }: { partner: PartnerLike; size?: number }) {
  const label = (partner.name || partner.email || '?').trim();
  const initials = label
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('');

  if (partner.profile_pic) {
    return (
      <FadeInImage
        src={partner.profile_pic}
        alt=""
        style={{ width: size, height: size }}
        className="rounded-full object-cover flex-shrink-0 bg-zinc-100 dark:bg-zinc-800"
      />
    );
  }
  return (
    <div
      style={{ width: size, height: size }}
      className="rounded-full flex-shrink-0 bg-pulse-orange-50 dark:bg-zinc-800 text-pulse-orange font-semibold flex items-center justify-center text-xs"
      aria-hidden
    >
      {initials || '?'}
    </div>
  );
}

/** Localised short timestamp; falls back to a date for anything older than a day. */
function formatTime(value: string | null | undefined, locale: string): string {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const diffMinutes = Math.floor((Date.now() - date.getTime()) / 60000);
  if (diffMinutes < 1) return locale === 'fr' ? "à l'instant" : 'just now';
  if (diffMinutes < 60) return `${diffMinutes}m`;
  if (diffMinutes < 60 * 24) return `${Math.floor(diffMinutes / 60)}h`;
  return date.toLocaleDateString(locale === 'fr' ? 'fr-FR' : 'en-GB', {
    day: '2-digit',
    month: 'short',
  });
}

/** Heading for a day separator in the timeline. */
function formatDay(value: string | null, locale: string): string {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  const sameDay = (a: Date, b: Date) => a.toDateString() === b.toDateString();
  if (sameDay(date, today)) return locale === 'fr' ? "Aujourd'hui" : 'Today';
  if (sameDay(date, yesterday)) return locale === 'fr' ? 'Hier' : 'Yesterday';
  return date.toLocaleDateString(locale === 'fr' ? 'fr-FR' : 'en-GB', {
    day: '2-digit',
    month: 'long',
    year: date.getFullYear() === today.getFullYear() ? undefined : 'numeric',
  });
}

/**
 * Render a message body, turning bare links into anchors.
 *
 * Built from React elements rather than injected HTML. The body is whatever
 * another member typed, so it only ever reaches the DOM as a text node, and a
 * candidate link becomes an `href` only once it parses as http(s) — which is
 * what keeps a `javascript:` payload inert.
 */
function MessageBody({ text }: { text: string }) {
  const parts = useMemo(() => text.split(/(https?:\/\/[^\s<>"']+)/g), [text]);
  return (
    <>
      {parts.map((part, index) => {
        let href: string | null = null;
        try {
          const parsed = new URL(part);
          if (parsed.protocol === 'http:' || parsed.protocol === 'https:') href = part;
        } catch {
          href = null;
        }
        if (!href) return <span key={index}>{part}</span>;
        return (
          <a
            key={index}
            href={href}
            target="_blank"
            rel="noopener noreferrer nofollow ugc"
            className="underline underline-offset-2 break-all hover:opacity-80"
          >
            {part}
          </a>
        );
      })}
    </>
  );
}

/**
 * Pick someone from the community directory and open a conversation with them.
 *
 * The directory deliberately publishes no email addresses, so the recipient is
 * named by id and the server resolves the address. Without this the inbox could
 * only ever continue conversations that already existed — there was no way to
 * start one from anywhere in the product.
 */
function NewConversationDialog({
  open,
  onOpenChange,
  language,
  selfMemberId,
  onStarted,
}: {
  open: boolean;
  onOpenChange: (next: boolean) => void;
  language: string;
  /** Filtered out of the picker: the server refuses a message to yourself. */
  selfMemberId: number | null;
  onStarted: (partnerEmail: string) => void;
}) {
  const en = language === 'en';
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<DirectoryMember[]>([]);
  const [searching, setSearching] = useState(false);
  const [recipient, setRecipient] = useState<DirectoryMember | null>(null);
  const [body, setBody] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset every time the dialog opens so it never reappears mid-draft.
  useEffect(() => {
    if (!open) return;
    setQuery('');
    setResults([]);
    setRecipient(null);
    setBody('');
    setError(null);
  }, [open]);

  useEffect(() => {
    if (!open || recipient) return;
    let cancelled = false;
    setSearching(true);
    const timer = setTimeout(async () => {
      try {
        const params = new URLSearchParams({ page_size: '8' });
        if (query.trim()) params.set('search', query.trim());
        const page = await apiGet<Paged<DirectoryMember>>(`/members/?${params}`);
        if (!cancelled) setResults(page.items.filter((person) => person.id !== selfMemberId));
      } catch {
        if (!cancelled) setResults([]);
      } finally {
        if (!cancelled) setSearching(false);
      }
    }, 250);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query, open, recipient, selfMemberId]);

  const send = async (event: React.FormEvent) => {
    event.preventDefault();
    const text = body.trim();
    if (!recipient || !text || sending) return;
    setSending(true);
    setError(null);
    try {
      const started = await apiPost<StartedConversation>(`/members/${recipient.id}/messages`, {
        message: text,
      });
      notifyInboxChanged();
      onOpenChange(false);
      onStarted(started.partner_email);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send');
    } finally {
      setSending(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-base">
            {en ? 'New message' : 'Nouveau message'}
          </DialogTitle>
          <DialogDescription className="text-xs">
            {en
              ? 'Choose someone from the community directory.'
              : 'Choisissez un membre de l’annuaire de la communauté.'}
          </DialogDescription>
        </DialogHeader>

        {!recipient ? (
          <div className="space-y-3">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
              <Input
                autoFocus
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={en ? 'Search by name or role' : 'Rechercher par nom ou rôle'}
                className="h-9 pl-8 text-sm"
                aria-label={en ? 'Search the directory' : 'Rechercher dans l’annuaire'}
              />
            </div>
            <div className="max-h-64 overflow-y-auto -mx-1">
              {searching && results.length === 0 ? (
                <div className="py-6 flex justify-center" role="status">
                  <Loader2 className="w-4 h-4 animate-spin text-zinc-400" />
                </div>
              ) : results.length === 0 ? (
                <p className="text-xs text-zinc-500 dark:text-zinc-400 text-center py-6">
                  {en ? 'No member matches this search.' : 'Aucun membre ne correspond.'}
                </p>
              ) : (
                results.map((person) => (
                  <button
                    key={person.id}
                    type="button"
                    onClick={() => setRecipient(person)}
                    className="w-full text-left px-3 py-2 flex items-center gap-3 rounded-lg hover:bg-zinc-50 dark:hover:bg-zinc-800/60"
                  >
                    <Avatar
                      partner={{
                        email: String(person.id),
                        name: person.full_name,
                        profile_pic: person.profile_pic,
                      }}
                      size={32}
                    />
                    <span className="min-w-0">
                      <span className="block text-sm font-medium text-zinc-900 dark:text-white truncate">
                        {person.full_name}
                      </span>
                      <span className="block text-[11px] text-zinc-500 dark:text-zinc-400 capitalize truncate">
                        {person.role}
                      </span>
                    </span>
                  </button>
                ))
              )}
            </div>
          </div>
        ) : (
          <form onSubmit={send} className="space-y-3">
            <div className="flex items-center gap-3 rounded-lg border border-zinc-100 dark:border-zinc-800 px-3 py-2">
              <Avatar
                partner={{
                  email: String(recipient.id),
                  name: recipient.full_name,
                  profile_pic: recipient.profile_pic,
                }}
                size={32}
              />
              <span className="min-w-0 flex-1">
                <span className="block text-sm font-medium text-zinc-900 dark:text-white truncate">
                  {recipient.full_name}
                </span>
                <span className="block text-[11px] text-zinc-500 dark:text-zinc-400 capitalize">
                  {recipient.role}
                </span>
              </span>
              <button
                type="button"
                onClick={() => setRecipient(null)}
                className="text-[11px] text-zinc-400 hover:underline"
              >
                {en ? 'Change' : 'Changer'}
              </button>
            </div>
            <textarea
              autoFocus
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={4}
              maxLength={MAX_MESSAGE_LENGTH}
              placeholder={en ? 'Write your message…' : 'Écrivez votre message…'}
              aria-label="Message"
              className="w-full resize-none rounded-md border border-input bg-transparent dark:bg-zinc-950 px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] placeholder:text-muted-foreground"
            />
            {error && (
              <p className="text-[11px] text-red-600 dark:text-red-400 flex items-center gap-1.5">
                <AlertCircle className="w-3 h-3" />
                {error}
              </p>
            )}
            <div className="flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-8 text-xs"
                onClick={() => onOpenChange(false)}
              >
                {en ? 'Cancel' : 'Annuler'}
              </Button>
              <Button
                type="submit"
                size="sm"
                disabled={!body.trim() || sending}
                className="h-8 text-xs bg-pulse-orange hover:bg-pulse-orange-hover text-white"
              >
                {sending ? (
                  <Loader2 className="w-3 h-3 mr-1.5 animate-spin" />
                ) : (
                  <Send className="w-3 h-3 mr-1.5" />
                )}
                {en ? 'Send' : 'Envoyer'}
              </Button>
            </div>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default function Inbox() {
  const { member, user, isBootstrapping } = useAuth();
  const { language } = useLanguage();
  const en = language === 'en';
  // The access token lives in memory only, so on a reload it is restored by the
  // bootstrap refresh. Requesting before that lands answers 401, logs an error
  // in the console and only succeeds on the automatic retry.
  const sessionReady = !isBootstrapping && (!!member || !!user);

  // The open conversation lives in the URL, so a refresh, a shared link and the
  // browser's back button all land on the same thread. It used to be local
  // state, and reloading the page dropped the reader back to an empty pane.
  const [searchParams, setSearchParams] = useSearchParams();
  const activeEmail = searchParams.get('to');

  const [partners, setPartners] = useState<ConversationPartner[]>([]);
  const [thread, setThread] = useState<ThreadResponse | null>(null);
  const [hits, setHits] = useState<MessageSearchHit[] | null>(null);
  const [reply, setReply] = useState('');
  const [pending, setPending] = useState<PendingMessage[]>([]);
  const [search, setSearch] = useState('');
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingThread, setLoadingThread] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [listError, setListError] = useState<string | null>(null);
  const [threadError, setThreadError] = useState<string | null>(null);
  const [composeOpen, setComposeOpen] = useState(false);

  const timelineRef = useRef<HTMLDivElement>(null);
  const composerRef = useRef<HTMLTextAreaElement>(null);
  // Checked synchronously: two fast Enter presses both read the same `sending`
  // state before React re-renders, which used to send the message twice.
  const sendingRef = useRef(false);

  const selectConversation = useCallback(
    (email: string | null) => {
      const params = new URLSearchParams(searchParams);
      if (email) params.set('to', email);
      else params.delete('to');
      setSearchParams(params);
    },
    [searchParams, setSearchParams],
  );

  const loadPartners = useCallback(
    async (options: { quiet?: boolean } = {}) => {
      if (!sessionReady) return;
      if (!options.quiet) setLoadingList(true);
      setListError(null);
      try {
        const params = new URLSearchParams();
        if (search.trim()) params.set('q', search.trim());
        if (unreadOnly) params.set('unread_only', 'true');
        const query = params.toString();
        setPartners(
          await apiGet<ConversationPartner[]>(`/members/conversations${query ? `?${query}` : ''}`),
        );
      } catch (err) {
        setListError(err instanceof Error ? err.message : 'Failed to load conversations');
      } finally {
        if (!options.quiet) setLoadingList(false);
      }
    },
    [search, unreadOnly, sessionReady],
  );

  // Debounced so typing in the search box does not fire a request per keystroke.
  useEffect(() => {
    const timer = setTimeout(() => void loadPartners(), 250);
    return () => clearTimeout(timer);
  }, [loadPartners]);

  // Message-text search runs alongside the conversation filter, so a term can
  // surface the exact message it matched rather than only the thread it is in.
  useEffect(() => {
    const term = search.trim();
    if (term.length < 2 || !sessionReady) {
      setHits(null);
      return;
    }
    let cancelled = false;
    const timer = setTimeout(async () => {
      try {
        const found = await apiGet<Paged<MessageSearchHit>>(
          `/members/messages/search?q=${encodeURIComponent(term)}&page_size=20`,
        );
        if (!cancelled) setHits(found.items);
      } catch {
        if (!cancelled) setHits(null);
      }
    }, 300);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [search, sessionReady]);

  const loadThread = useCallback(async (email: string, options: { quiet?: boolean } = {}) => {
    if (!sessionReady) return;
    if (!options.quiet) {
      setLoadingThread(true);
      setThreadError(null);
    }
    try {
      const data = await apiGet<ThreadResponse>(
        `/members/conversations/${encodeURIComponent(email)}?page=1&page_size=${PAGE_SIZE}`,
      );
      // A poll that resolves after the reader has moved on must not overwrite
      // the thread now on screen.
      setThread((current) =>
        current &&
        options.quiet &&
        current.partner_email.toLowerCase() !== data.partner_email.toLowerCase()
          ? current
          : data,
      );

      const hasUnread = data.messages.some(
        (m) => !m.is_read && (m.from_email ?? '').toLowerCase() === data.partner_email.toLowerCase(),
      );
      if (hasUnread) {
        await apiPost(`/members/conversations/${encodeURIComponent(email)}/read`, {});
        setPartners((prev) => prev.map((p) => (p.email === email ? { ...p, unread_count: 0 } : p)));
        notifyInboxChanged();
      }
    } catch (err) {
      if (!options.quiet) {
        setThreadError(err instanceof Error ? err.message : 'Failed to load messages');
        setThread(null);
      }
    } finally {
      if (!options.quiet) setLoadingThread(false);
    }
  }, [sessionReady]);

  // Open whichever conversation the URL names, including on a cold load.
  useEffect(() => {
    setPending([]);
    if (!activeEmail) {
      setThread(null);
      return;
    }
    void loadThread(activeEmail);
  }, [activeEmail, loadThread]);

  // Keep an open inbox current. Paused while the tab is hidden, so a
  // backgrounded window is not polling the API all afternoon.
  useEffect(() => {
    const tick = () => {
      if (document.visibilityState !== 'visible') return;
      void loadPartners({ quiet: true });
      if (activeEmail) void loadThread(activeEmail, { quiet: true });
    };
    const timer = setInterval(tick, POLL_INTERVAL_MS);
    document.addEventListener('visibilitychange', tick);
    return () => {
      clearInterval(timer);
      document.removeEventListener('visibilitychange', tick);
    };
  }, [activeEmail, loadPartners, loadThread]);

  /** Fetch the next older page and prepend it, keeping the scroll position stable. */
  const loadOlder = async () => {
    if (!thread || !activeEmail || thread.page >= thread.pages) return;
    setLoadingMore(true);
    const container = timelineRef.current;
    const previousHeight = container?.scrollHeight ?? 0;
    try {
      const older = await apiGet<ThreadResponse>(
        `/members/conversations/${encodeURIComponent(activeEmail)}?page=${thread.page + 1}&page_size=${PAGE_SIZE}`,
      );
      setThread({ ...older, messages: [...older.messages, ...thread.messages] });
      requestAnimationFrame(() => {
        if (container) container.scrollTop = container.scrollHeight - previousHeight;
      });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to load older messages');
    } finally {
      setLoadingMore(false);
    }
  };

  /**
   * Send one message.
   *
   * The body appears in the timeline immediately and is reconciled against the
   * server afterwards. A failure leaves the bubble in place, marked as failed,
   * rather than discarding what was typed.
   */
  const deliver = useCallback(
    async (body: string, localId: string, email: string) => {
      try {
        await apiPost(`/members/conversations/${encodeURIComponent(email)}/reply`, {
          message: body,
        });
        setPending((prev) => prev.filter((p) => p.localId !== localId));
        await loadThread(email, { quiet: true });
        void loadPartners({ quiet: true });
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to send';
        setPending((prev) =>
          prev.map((p) => (p.localId === localId ? { ...p, status: 'failed', error: message } : p)),
        );
      }
    },
    [loadThread, loadPartners],
  );

  const sendReply = async (event?: React.FormEvent) => {
    event?.preventDefault();
    const body = reply.trim();
    if (!activeEmail || !body || sendingRef.current) return;
    if (body.length > MAX_MESSAGE_LENGTH) return;

    sendingRef.current = true;
    const localId = `local-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    setPending((prev) => [...prev, { localId, body, status: 'sending' }]);
    setReply('');
    if (composerRef.current) composerRef.current.style.height = 'auto';
    try {
      await deliver(body, localId, activeEmail);
    } finally {
      sendingRef.current = false;
    }
  };

  const retry = (item: PendingMessage) => {
    if (!activeEmail) return;
    setPending((prev) =>
      prev.map((p) =>
        p.localId === item.localId ? { ...p, status: 'sending', error: undefined } : p,
      ),
    );
    void deliver(item.body, item.localId, activeEmail);
  };

  const discard = (localId: string) =>
    setPending((prev) => prev.filter((p) => p.localId !== localId));

  // Keep the newest message in view when a thread opens or a reply lands.
  useEffect(() => {
    const container = timelineRef.current;
    if (container && !loadingMore) container.scrollTop = container.scrollHeight;
  }, [thread?.partner_email, thread?.messages.length, pending.length, loadingMore]);

  const totalUnread = useMemo(
    () => partners.reduce((sum, p) => sum + p.unread_count, 0),
    [partners],
  );

  const partnerInfo: PartnerLike | null =
    thread?.partner ??
    partners.find((p) => p.email === activeEmail) ??
    (activeEmail ? { email: activeEmail, name: activeEmail } : null);

  const composerTooLong = reply.length > MAX_MESSAGE_LENGTH;
  const showCounter = reply.length > MAX_MESSAGE_LENGTH * 0.8;

  // Until the stored session has been checked, "signed out" is not yet a fact —
  // rendering the sign-in panel here flashed it at every member on every reload.
  if (isBootstrapping) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center" role="status" aria-live="polite">
        <Loader2 className="w-6 h-6 animate-spin text-zinc-400" />
        <span className="sr-only">{en ? 'Loading your messages' : 'Chargement de vos messages'}</span>
      </div>
    );
  }

  if (!member && !user) {
    return (
      <div className="space-y-6">
        <div className="pb-4 border-b border-zinc-150 dark:border-zinc-800">
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">
            {en ? 'Messages' : 'Messagerie'}
          </h1>
        </div>
        <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 p-10 text-center">
          <Mail className="w-8 h-8 text-zinc-300 dark:text-zinc-600 mx-auto mb-3" />
          <p className="text-sm text-zinc-600 dark:text-zinc-300 mb-4">
            {en
              ? 'Sign in to read and send messages.'
              : 'Connectez-vous pour lire et envoyer des messages.'}
          </p>
          <Button asChild className="bg-pulse-orange hover:bg-pulse-orange-hover text-white h-9 text-xs">
            <Link to="/login">{en ? 'Sign in' : 'Se connecter'}</Link>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-150 dark:border-zinc-800">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-white flex items-center gap-2">
            {en ? 'Messages' : 'Messagerie'}
            {totalUnread > 0 && (
              <Badge className="bg-pulse-orange hover:bg-pulse-orange text-white text-[10px] px-2 ve-badge-pop">
                {totalUnread}
              </Badge>
            )}
          </h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            {en
              ? 'Your private conversations with the ecosystem.'
              : "Vos échanges privés avec l'écosystème."}
          </p>
        </div>
        <Button
          onClick={() => setComposeOpen(true)}
          className="bg-pulse-orange hover:bg-pulse-orange-hover text-white h-9 text-xs self-start sm:self-auto"
        >
          <PenSquare className="w-3.5 h-3.5 mr-1.5" />
          {en ? 'New message' : 'Nouveau message'}
        </Button>
      </div>

      <NewConversationDialog
        open={composeOpen}
        onOpenChange={setComposeOpen}
        language={language}
        selfMemberId={member?.member_id ?? null}
        onStarted={(partnerEmail) => {
          selectConversation(partnerEmail);
          void loadPartners({ quiet: true });
        }}
      />

      <div className="grid grid-cols-1 lg:grid-cols-[320px_minmax(0,1fr)] xl:grid-cols-[320px_minmax(0,1fr)_260px] gap-4 h-[calc(100vh-15rem)] min-h-[520px]">

        {/* Conversations */}
        <aside
          className={`bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 flex flex-col overflow-hidden ${
            activeEmail ? 'hidden lg:flex' : 'flex'
          }`}
          aria-label="Conversations"
        >
          <div className="p-3 border-b border-zinc-100 dark:border-zinc-800 space-y-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={en ? 'Search people and messages' : 'Rechercher personnes et messages'}
                className="h-9 pl-8 pr-8 text-sm dark:bg-zinc-950"
                aria-label={
                  en ? 'Search conversations and messages' : 'Rechercher conversations et messages'
                }
              />
              {search && (
                <button
                  type="button"
                  onClick={() => setSearch('')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-zinc-100 dark:hover:bg-zinc-800"
                  aria-label={en ? 'Clear search' : 'Effacer la recherche'}
                >
                  <X className="w-3 h-3 text-zinc-400" />
                </button>
              )}
            </div>
            <Button
              size="sm"
              variant={unreadOnly ? 'default' : 'outline'}
              onClick={() => setUnreadOnly((v) => !v)}
              className={`h-7 text-[11px] w-full ${
                unreadOnly
                  ? 'bg-pulse-orange hover:bg-pulse-orange-hover text-white'
                  : 'dark:bg-zinc-800 dark:border-zinc-700'
              }`}
              aria-pressed={unreadOnly}
            >
              <Filter className="w-3 h-3 mr-1.5" />
              {en ? 'Unread only' : 'Non lus'}
            </Button>
          </div>

          <div className="flex-1 overflow-y-auto">
            {loadingList ? (
              <div className="p-3 space-y-2" role="status" aria-live="polite">
                <span className="sr-only">{en ? 'Loading conversations' : 'Chargement'}</span>
                {[0, 1, 2, 3].map((i) => (
                  <div key={i} className="flex gap-3 p-2 animate-pulse">
                    <div className="w-10 h-10 rounded-full bg-zinc-100 dark:bg-zinc-800" />
                    <div className="flex-1 space-y-2 py-1">
                      <div className="h-3 w-24 bg-zinc-100 dark:bg-zinc-800 rounded" />
                      <div className="h-2 w-36 bg-zinc-100 dark:bg-zinc-800 rounded" />
                    </div>
                  </div>
                ))}
              </div>
            ) : listError ? (
              <div className="p-6 text-center">
                <AlertCircle className="w-6 h-6 text-amber-500 mx-auto mb-2" />
                <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-3">{listError}</p>
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 text-[11px]"
                  onClick={() => void loadPartners()}
                >
                  <RotateCw className="w-3 h-3 mr-1.5" />
                  {en ? 'Try again' : 'Réessayer'}
                </Button>
              </div>
            ) : partners.length === 0 && !hits?.length ? (
              <div className="p-8 text-center">
                <MessageSquare className="w-7 h-7 text-zinc-300 dark:text-zinc-600 mx-auto mb-2" />
                <p className="text-xs text-zinc-500 dark:text-zinc-400">
                  {search || unreadOnly
                    ? en
                      ? 'Nothing matches this search.'
                      : 'Aucun résultat pour cette recherche.'
                    : en
                      ? 'No conversations yet. Open a founder, expert or investor profile and use “Send a message” to start one.'
                      : "Aucune conversation. Ouvrez un profil de fondateur, d'expert ou d'investisseur et utilisez « Envoyer un message »."}
                </p>
              </div>
            ) : (
              <>
                {partners.map((partner) => (
                  <button
                    key={partner.email}
                    onClick={() => selectConversation(partner.email)}
                    className={`w-full text-left px-3 py-3 flex gap-3 items-start border-b border-zinc-50 dark:border-zinc-800/60 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors ${
                      activeEmail === partner.email ? 'bg-pulse-orange-50 dark:bg-zinc-800' : ''
                    }`}
                    aria-current={activeEmail === partner.email ? 'true' : undefined}
                  >
                    <Avatar partner={partner} />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-baseline justify-between gap-2">
                        <span className="font-semibold text-sm text-zinc-900 dark:text-white truncate">
                          {partner.name || partner.email}
                        </span>
                        <span className="text-[10px] text-zinc-400 flex-shrink-0">
                          {formatTime(partner.last_message_at, language)}
                        </span>
                      </div>
                      <p
                        className={`text-xs truncate mt-0.5 ${
                          partner.unread_count > 0
                            ? 'text-zinc-800 dark:text-zinc-100 font-medium'
                            : 'text-zinc-500 dark:text-zinc-400'
                        }`}
                      >
                        {partner.last_message_preview || (en ? 'No messages' : 'Aucun message')}
                      </p>
                    </div>
                    {partner.unread_count > 0 && (
                      <span
                        className="mt-1 flex-shrink-0 bg-pulse-orange text-white text-[10px] font-bold min-w-[18px] h-[18px] px-1 rounded-full grid place-items-center ve-badge-pop"
                        aria-label={`${partner.unread_count} ${en ? 'unread' : 'non lus'}`}
                      >
                        {partner.unread_count}
                      </span>
                    )}
                  </button>
                ))}

                {hits && hits.length > 0 && (
                  <div>
                    <p className="px-3 pt-3 pb-1 text-[10px] font-semibold text-zinc-400 uppercase tracking-wide">
                      {en ? 'Matching messages' : 'Messages correspondants'}
                    </p>
                    {hits.map((hit) => (
                      <button
                        key={hit.id}
                        onClick={() => selectConversation(hit.partner_email)}
                        className="w-full text-left px-3 py-2.5 flex gap-3 items-start border-b border-zinc-50 dark:border-zinc-800/60 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors"
                      >
                        <Avatar
                          partner={{
                            name: hit.partner_name,
                            email: hit.partner_email,
                            profile_pic: hit.partner_pic,
                          }}
                          size={28}
                        />
                        <div className="min-w-0 flex-1">
                          <div className="flex items-baseline justify-between gap-2">
                            <span className="text-xs font-medium text-zinc-800 dark:text-zinc-100 truncate">
                              {hit.outgoing
                                ? `${en ? 'To' : 'À'} ${hit.partner_name || hit.partner_email}`
                                : hit.partner_name || hit.partner_email}
                            </span>
                            <span className="text-[10px] text-zinc-400 flex-shrink-0">
                              {formatTime(hit.created_at, language)}
                            </span>
                          </div>
                          <p className="text-[11px] text-zinc-500 dark:text-zinc-400 line-clamp-2 mt-0.5">
                            {hit.message}
                          </p>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </aside>

        {/* Thread */}
        <section
          className={`bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 flex flex-col overflow-hidden ${
            activeEmail ? 'flex' : 'hidden lg:flex'
          }`}
        >
          {!activeEmail || !partnerInfo ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
              <MessageSquare className="w-10 h-10 text-zinc-200 dark:text-zinc-700 mb-3 ve-float" />
              <p className="text-sm font-medium text-zinc-700 dark:text-zinc-200">
                {en ? 'Select a conversation' : 'Sélectionnez une conversation'}
              </p>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 max-w-xs">
                {en
                  ? 'Choose someone on the left to read your message history.'
                  : "Choisissez un contact à gauche pour lire l'historique."}
              </p>
            </div>
          ) : (
            <>
              <header className="px-4 py-3 border-b border-zinc-100 dark:border-zinc-800 flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => selectConversation(null)}
                  className="lg:hidden p-1 -ml-1 rounded hover:bg-zinc-100 dark:hover:bg-zinc-800"
                  aria-label={en ? 'Back to conversations' : 'Retour aux conversations'}
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <Avatar partner={partnerInfo} size={36} />
                <div className="min-w-0">
                  <p className="font-semibold text-sm text-zinc-900 dark:text-white truncate">
                    {partnerInfo.name || partnerInfo.email}
                  </p>
                  <p className="text-[11px] text-zinc-500 dark:text-zinc-400 truncate">
                    {partnerInfo.email}
                  </p>
                </div>
              </header>

              <div
                key={activeEmail}
                ref={timelineRef}
                className="flex-1 overflow-y-auto px-4 py-4 space-y-3 ve-view-enter"
                role="log"
                aria-label={en ? 'Message history' : 'Historique des messages'}
              >
                {loadingThread ? (
                  <div className="flex justify-center py-6" role="status">
                    <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
                    <span className="sr-only">{en ? 'Loading messages' : 'Chargement'}</span>
                  </div>
                ) : threadError ? (
                  <div className="flex flex-col items-center justify-center py-10 text-center">
                    <AlertCircle className="w-6 h-6 text-amber-500 mb-2" />
                    <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-3">{threadError}</p>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-7 text-[11px]"
                      onClick={() => void loadThread(activeEmail)}
                    >
                      <RotateCw className="w-3 h-3 mr-1.5" />
                      {en ? 'Try again' : 'Réessayer'}
                    </Button>
                  </div>
                ) : (
                  <>
                    {thread && thread.page < thread.pages && (
                      <div className="flex justify-center pb-2">
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 text-[11px] dark:bg-zinc-800 dark:border-zinc-700"
                          onClick={() => void loadOlder()}
                          disabled={loadingMore}
                        >
                          {loadingMore && <Loader2 className="w-3 h-3 mr-1.5 animate-spin" />}
                          {en ? 'Load earlier messages' : 'Charger les messages précédents'}
                        </Button>
                      </div>
                    )}

                    {thread?.messages.length === 0 && pending.length === 0 && (
                      <p className="text-center text-xs text-zinc-500 dark:text-zinc-400 py-8">
                        {en ? 'No messages yet. Say hello.' : 'Aucun message. Lancez la conversation.'}
                      </p>
                    )}

                    {thread?.messages.map((message, index) => {
                      // Within a thread there are exactly two ends, so "mine" is
                      // simply "not the partner". Comparing against the signed-in
                      // address instead broke administrator sessions, whose
                      // username is not an email at all.
                      const mine =
                        (message.from_email ?? '').toLowerCase() !==
                        thread.partner_email.toLowerCase();
                      const previous = index > 0 ? thread.messages[index - 1] : null;
                      const showDay =
                        !previous ||
                        new Date(message.created_at ?? 0).toDateString() !==
                          new Date(previous.created_at ?? 0).toDateString();

                      return (
                        <div key={message.id}>
                          {showDay && (
                            <div className="flex justify-center my-3">
                              <span className="text-[10px] font-medium text-zinc-400 bg-zinc-50 dark:bg-zinc-800 px-2.5 py-1 rounded-full">
                                {formatDay(message.created_at, language)}
                              </span>
                            </div>
                          )}
                          <div className={`flex gap-2 ve-msg-in ${mine ? 'justify-end' : 'justify-start'}`}>
                            {!mine && <Avatar partner={partnerInfo} size={28} />}
                            <div
                              className={`max-w-[75%] ${mine ? 'items-end' : 'items-start'} flex flex-col`}
                            >
                              <div
                                className={`px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap [overflow-wrap:anywhere] ${
                                  mine
                                    ? 'bg-pulse-orange text-white rounded-br-sm'
                                    : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-800 dark:text-zinc-100 rounded-bl-sm'
                                }`}
                              >
                                <MessageBody text={message.message} />
                              </div>
                              <div className="flex items-center gap-1.5 mt-1 px-1">
                                <span className="text-[10px] text-zinc-400">
                                  {message.created_at
                                    ? new Date(message.created_at).toLocaleTimeString(
                                        en ? 'en-GB' : 'fr-FR',
                                        { hour: '2-digit', minute: '2-digit' },
                                      )
                                    : ''}
                                </span>
                                {mine &&
                                  (message.is_read ? (
                                    <MailOpen
                                      className="w-3 h-3 text-zinc-400"
                                      aria-label={en ? 'Read' : 'Lu'}
                                    />
                                  ) : (
                                    <Mail
                                      className="w-3 h-3 text-zinc-300"
                                      aria-label={en ? 'Sent' : 'Envoyé'}
                                    />
                                  ))}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}

                    {/* Messages the composer accepted but the server has not confirmed. */}
                    {pending.map((item) => (
                      <div key={item.localId} className="flex justify-end ve-msg-in">
                        <div className="max-w-[75%] flex flex-col items-end">
                          <div
                            className={`px-3.5 py-2.5 rounded-2xl rounded-br-sm text-sm leading-relaxed whitespace-pre-wrap [overflow-wrap:anywhere] ${
                              item.status === 'failed'
                                ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 border border-red-200 dark:border-red-900/60'
                                : 'bg-pulse-orange/70 text-white'
                            }`}
                          >
                            <MessageBody text={item.body} />
                          </div>
                          {item.status === 'sending' ? (
                            <span className="text-[10px] text-zinc-400 mt-1 px-1 flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {en ? 'Sending…' : 'Envoi…'}
                            </span>
                          ) : (
                            <div className="flex items-center gap-2 mt-1 px-1">
                              <span className="text-[10px] text-red-600 dark:text-red-400">
                                {item.error || (en ? 'Not sent' : 'Non envoyé')}
                              </span>
                              <button
                                type="button"
                                onClick={() => retry(item)}
                                className="text-[10px] font-medium text-pulse-orange hover:underline"
                              >
                                {en ? 'Retry' : 'Réessayer'}
                              </button>
                              <button
                                type="button"
                                onClick={() => discard(item.localId)}
                                className="text-[10px] text-zinc-400 hover:underline"
                              >
                                {en ? 'Discard' : 'Supprimer'}
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </>
                )}
              </div>

              <form
                onSubmit={sendReply}
                className="p-3 border-t border-zinc-100 dark:border-zinc-800 space-y-1.5"
              >
                <div className="flex gap-2 items-end">
                  {/* A native textarea so it can be measured and grown as the
                      message gets longer; the previous one-row box made a
                      multi-paragraph message impossible to read before sending. */}
                  <textarea
                    ref={composerRef}
                    value={reply}
                    onChange={(e) => {
                      setReply(e.target.value);
                      e.target.style.height = 'auto';
                      e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
                    }}
                    onKeyDown={(e) => {
                      // Enter sends; Shift+Enter inserts a newline.
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        void sendReply();
                      }
                    }}
                    rows={1}
                    maxLength={MAX_MESSAGE_LENGTH + 1}
                    placeholder={en ? 'Write a message…' : 'Écrire un message…'}
                    aria-label="Message"
                    aria-invalid={composerTooLong}
                    className="flex-1 min-h-[40px] max-h-40 resize-none rounded-md border border-input bg-transparent dark:bg-zinc-950 px-3 py-2 text-sm shadow-xs outline-none transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] placeholder:text-muted-foreground"
                  />
                  <Button
                    type="submit"
                    disabled={!reply.trim() || composerTooLong}
                    className="bg-pulse-orange hover:bg-pulse-orange-hover text-white h-10 w-10 p-0 flex-shrink-0"
                    aria-label={en ? 'Send' : 'Envoyer'}
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
                <div className="flex items-center justify-between px-1 min-h-[14px]">
                  <span className="text-[10px] text-zinc-400">
                    {en
                      ? 'Enter to send · Shift+Enter for a new line'
                      : 'Entrée pour envoyer · Maj+Entrée pour une nouvelle ligne'}
                  </span>
                  {showCounter && (
                    <span
                      className={`text-[10px] ${composerTooLong ? 'text-red-600 dark:text-red-400 font-medium' : 'text-zinc-400'}`}
                    >
                      {reply.length} / {MAX_MESSAGE_LENGTH}
                    </span>
                  )}
                </div>
              </form>
            </>
          )}
        </section>

        {/* Context panel */}
        <aside className="hidden xl:flex flex-col gap-4 overflow-y-auto">
          {partnerInfo ? (
            <>
              <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 p-4 text-center">
                <div className="flex justify-center mb-3">
                  <Avatar partner={partnerInfo} size={56} />
                </div>
                <p className="font-semibold text-sm text-zinc-900 dark:text-white">
                  {partnerInfo.name || partnerInfo.email}
                </p>
                <p className="text-[11px] text-zinc-500 dark:text-zinc-400 break-all mt-0.5">
                  {partnerInfo.email}
                </p>
                {partnerInfo.role && (
                  <Badge variant="secondary" className="mt-2 text-[10px] capitalize">
                    {partnerInfo.role}
                  </Badge>
                )}
              </div>

              <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 p-4 space-y-3">
                <h2 className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wide">
                  Conversation
                </h2>
                <div className="flex justify-between text-xs">
                  <span className="text-zinc-500 dark:text-zinc-400">Messages</span>
                  <span className="font-semibold text-zinc-900 dark:text-white">
                    {thread?.total ?? partnerInfo.message_count ?? 0}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-zinc-500 dark:text-zinc-400">
                    {en ? 'Last activity' : 'Dernière activité'}
                  </span>
                  <span className="font-semibold text-zinc-900 dark:text-white">
                    {formatTime(partnerInfo.last_message_at, language) || '—'}
                  </span>
                </div>
              </div>

              <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 p-4">
                <p className="text-[11px] text-zinc-500 dark:text-zinc-400 flex items-start gap-2 leading-relaxed">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" />
                  {en
                    ? 'Only you and this contact can read these messages.'
                    : 'Vous seul et ce contact pouvez lire ces messages.'}
                </p>
              </div>
            </>
          ) : (
            <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 p-6 text-center">
              <User className="w-6 h-6 text-zinc-200 dark:text-zinc-700 mx-auto mb-2" />
              <p className="text-[11px] text-zinc-500 dark:text-zinc-400">
                {en ? 'Contact details appear here.' : 'Les détails du contact apparaissent ici.'}
              </p>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
