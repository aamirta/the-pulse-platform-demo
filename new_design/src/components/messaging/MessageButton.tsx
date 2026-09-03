/**
 * "Message" button for profile pages.
 *
 * Restores the affordance the old design had: from anybody's profile you can
 * open a conversation with them without knowing their address.
 *
 * Two ways to name the recipient:
 *   `memberId`                 — a community member (founder, expert, member card)
 *   `entityType` + `entityId`  — a directory entity (startup, investor, incubator),
 *                                resolved to whoever holds the approved claim
 *
 * The second form is what makes this work on company profiles at all: those
 * pages render from the directory tables, which hold no account. The lookup runs
 * once on mount and the control renders nothing when nobody has claimed the
 * entity, rather than offering a button that cannot work.
 *
 * No email address ever reaches this component. Sending goes through
 * `POST /members/{id}/messages`, which resolves the address server-side; the
 * response hands back the thread key the inbox needs to open the conversation.
 */

import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, MessageSquare } from 'lucide-react';
import { toast } from 'sonner';
import { apiGet, apiPost, type ApiError } from '@/lib/api';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { useAuth } from '@/context/AuthContext';
import { useLanguage } from '@/context/LanguageContext';
import { notifyInboxChanged } from '@/hooks/useUnreadMessages';
import type { EntityContact } from '@/types/dealroomPosts';

/** What `POST /members/{id}/messages` returns. */
interface StartedConversation {
  partner_email: string;
  partner_name: string | null;
}

interface MessageButtonProps {
  /** Message a member directly, when the page already knows the member id. */
  memberId?: number | null;
  /** Or resolve the member behind a directory entity. */
  entityType?: 'startup' | 'investor' | 'incubator' | 'founder';
  /**
   * Always a string on the wire. Founder ids are not numeric — a scraped
   * profile carries a number, an onboarded one a random token — so this must
   * never be coerced.
   */
  entityId?: number | string;
  /** Display name used in the dialog copy. */
  name?: string | null;
  variant?: 'default' | 'outline' | 'secondary' | 'ghost';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  className?: string;
  /** Render icon-only, for tight card layouts. */
  iconOnly?: boolean;
  /**
   * Show a disabled button explaining *why* nobody can be messaged, instead of
   * rendering nothing.
   *
   * On a profile page this matters: most directory records are scraped
   * ecosystem data with no account behind them, and a button that simply
   * vanishes reads as a broken feature rather than as "this person has not
   * joined yet". Cards leave it off, where a dead control would be noise.
   */
  showWhenUnavailable?: boolean;
}

export default function MessageButton({
  memberId,
  entityType,
  entityId,
  name,
  variant = 'outline',
  size = 'sm',
  className,
  iconOnly = false,
  showWhenUnavailable = false,
}: MessageButtonProps) {
  const { member, user, isBootstrapping } = useAuth();
  const { language } = useLanguage();
  const navigate = useNavigate();
  const en = language === 'en';

  const [contact, setContact] = useState<EntityContact | null>(null);
  const [resolving, setResolving] = useState(false);
  const [open, setOpen] = useState(false);
  const [body, setBody] = useState('');
  const [sending, setSending] = useState(false);
  // Checked synchronously: two fast clicks both read the same `sending` state
  // before React re-renders, which would send the message twice.
  const sendingRef = useRef(false);

  const signedIn = !isBootstrapping && (!!member || !!user);
  // Kept as an opaque string: a founder id may be a token like "yX-8jCXs…",
  // and Number() would turn it into NaN and silently hide the button.
  const resolvedEntityId = entityId === undefined ? undefined : String(entityId).trim();
  const needsLookup = memberId == null && !!entityType && !!resolvedEntityId;

  // Resolve the entity to a member once. Not gated on being signed in: a
  // visitor should see the button and be sent to sign in, not see nothing.
  useEffect(() => {
    if (!needsLookup) return;
    let cancelled = false;
    setResolving(true);
    apiGet<EntityContact>(
      `/members/by-entity/${entityType}/${encodeURIComponent(resolvedEntityId as string)}`,
    )
      .then((data) => {
        if (!cancelled) setContact(data);
      })
      .catch(() => {
        // A failed lookup is indistinguishable from an unclaimed entity as far
        // as the UI is concerned: either way there is nobody to message.
        if (!cancelled) setContact(null);
      })
      .finally(() => {
        if (!cancelled) setResolving(false);
      });
    return () => {
      cancelled = true;
    };
  }, [needsLookup, entityType, resolvedEntityId]);

  const targetId = memberId ?? contact?.member_id ?? null;
  const targetName = name ?? contact?.full_name ?? null;
  const isSelf =
    contact?.is_self === true ||
    (member != null && targetId != null && member.member_id === targetId);

  // Your own profile — the button would only ever refuse.
  if (isSelf) return null;

  // Nobody to message: this directory record has no account behind it.
  const unavailable =
    (needsLookup && !resolving && !contact?.contactable) || (!needsLookup && targetId == null);

  if (unavailable) {
    if (!showWhenUnavailable) return null;
    const reason = en
      ? 'This person has not joined The Pulse yet, so there is no inbox to message.'
      : "Cette personne n'a pas encore rejoint The Pulse : aucune messagerie disponible.";
    return (
      <Button
        type="button"
        variant={variant}
        size={iconOnly ? 'icon' : size}
        className={className}
        disabled
        title={reason}
        aria-label={reason}
      >
        <MessageSquare className={iconOnly ? 'w-4 h-4' : 'w-4 h-4 mr-1.5'} />
        {!iconOnly && (en ? 'Not on The Pulse' : 'Pas sur The Pulse')}
      </Button>
    );
  }

  const label = 'Message';

  const openDialog = () => {
    if (!signedIn) {
      toast.info(en ? 'Sign in to send a message' : 'Connectez-vous pour envoyer un message');
      navigate('/login');
      return;
    }
    setOpen(true);
  };

  const send = async (event: React.FormEvent) => {
    event.preventDefault();
    const text = body.trim();
    if (!text || targetId == null || sendingRef.current) return;

    sendingRef.current = true;
    setSending(true);
    try {
      const started = await apiPost<StartedConversation>(`/members/${targetId}/messages`, {
        message: text,
      });
      // Refresh the badge before navigating, so the count is already right when
      // the inbox paints.
      notifyInboxChanged();
      setOpen(false);
      setBody('');
      toast.success(en ? 'Message sent' : 'Message envoyé');
      // The inbox keys the open thread off `?to=`, so this lands directly in the
      // conversation — existing or brand new, the same URL reaches both.
      navigate(`/inbox?to=${encodeURIComponent(started.partner_email)}`);
    } catch (err) {
      const apiError = err as ApiError;
      toast.error(apiError.message || (en ? 'Could not send message' : "Échec de l'envoi"));
    } finally {
      sendingRef.current = false;
      setSending(false);
    }
  };

  return (
    <>
      <Button
        type="button"
        variant={variant}
        size={iconOnly ? 'icon' : size}
        className={className}
        onClick={openDialog}
        disabled={resolving}
        aria-label={targetName ? `${label} ${targetName}` : label}
        title={targetName ? `${label} ${targetName}` : label}
      >
        {resolving ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <MessageSquare className={iconOnly ? 'w-4 h-4' : 'w-4 h-4 mr-1.5'} />
        )}
        {!iconOnly && label}
      </Button>

      <Dialog open={open} onOpenChange={(next) => !next && setOpen(false)}>
        <DialogContent className="max-w-md">
          <form onSubmit={send}>
            <DialogHeader>
              <DialogTitle className="text-base">
                {targetName
                  ? en
                    ? `Message ${targetName}`
                    : `Message à ${targetName}`
                  : en
                    ? 'Send a message'
                    : 'Envoyer un message'}
              </DialogTitle>
              <DialogDescription className="text-xs">
                {en
                  ? 'This opens a conversation in your inbox. If you have messaged before, it continues that thread.'
                  : "Ceci ouvre une conversation dans votre boîte de réception. Si vous vous êtes déjà écrit, le fil existant continue."}
              </DialogDescription>
            </DialogHeader>

            <div className="py-3">
              <Textarea
                value={body}
                onChange={(event) => setBody(event.target.value)}
                rows={5}
                maxLength={5000}
                autoFocus
                placeholder={
                  en
                    ? 'Introduce yourself and say what you are looking for…'
                    : 'Présentez-vous et expliquez ce que vous recherchez…'
                }
                className="text-sm resize-none"
              />
              <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1 text-right">{body.trim().length}/5000</p>
            </div>

            <DialogFooter className="gap-2">
              <Button type="button" variant="ghost" size="sm" onClick={() => setOpen(false)}>
                {en ? 'Cancel' : 'Annuler'}
              </Button>
              <Button type="submit" size="sm" disabled={!body.trim() || sending}>
                {sending && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
                {en ? 'Send' : 'Envoyer'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
