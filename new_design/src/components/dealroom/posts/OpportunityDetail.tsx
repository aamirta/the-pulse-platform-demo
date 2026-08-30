/**
 * One opportunity, opened.
 *
 * Everything the card could not fit, plus the three actions a reader can take:
 * respond, report, or — if it is theirs — manage it. Which of those appear is
 * driven by `can_manage` and `responded_by_me` as resolved by the API; the
 * client never decides a permission for itself, and every button behind them is
 * re-authorized server-side anyway.
 *
 * Responding writes a message into the author's inbox, so the confirmation
 * offers a link straight to that thread rather than leaving the reader to go
 * find it.
 */

import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  Check,
  Eye,
  FileLock2,
  Flag,
  Loader2,
  MessagesSquare,
  PencilLine,
  Target,
  Trash2,
  Users,
  X,
} from 'lucide-react';
import { toast } from 'sonner';
import { FadeInImage } from '@/enhancements/FadeInImage';
import { apiDelete, apiGet, apiPost, type ApiError } from '@/lib/api';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAuth } from '@/context/AuthContext';
import { notifyInboxChanged } from '@/hooks/useUnreadMessages';
import type {
  DealRoomPostDetail as PostDetail,
  PostMeta,
  PostResponseCreated,
  PostResponseItem,
} from '@/types/dealroomPosts';
import {
  Chip,
  PostTypeIcon,
  commitmentLabel,
  counterpartyLabel,
  daysUntil,
  formatAmountRange,
  initials,
  postStatusLabel,
  postTypeLabel,
  postTypeTone,
  relativeTime,
  reportReasonLabel,
  stageLabel,
  statusTone,
} from './shared';

interface OpportunityDetailProps {
  postId: number;
  meta: PostMeta | null;
  language: string;
  onClose: () => void;
  /** Called after any change that should refresh the list behind the sheet. */
  onChanged: () => void;
  onEdit: (post: PostDetail) => void;
}

export default function OpportunityDetail({
  postId,
  meta,
  language,
  onClose,
  onChanged,
  onEdit,
}: OpportunityDetailProps) {
  const en = language === 'en';
  const navigate = useNavigate();
  const { member, user, isBootstrapping } = useAuth();
  const signedIn = !isBootstrapping && (!!member || !!user);

  const [post, setPost] = useState<PostDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [responseOpen, setResponseOpen] = useState(false);
  const [responseBody, setResponseBody] = useState('');
  const [sending, setSending] = useState(false);

  const [reportOpen, setReportOpen] = useState(false);
  const [reportReason, setReportReason] = useState('');
  const [reportDetail, setReportDetail] = useState('');
  const [reporting, setReporting] = useState(false);

  const [responses, setResponses] = useState<PostResponseItem[] | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet<PostDetail>(`/deal-room-posts/${postId}`);
      setPost(data);
      // The author's own view needs the responder list; nobody else may read it.
      if (data.can_manage) {
        setResponses(await apiGet<PostResponseItem[]>(`/deal-room-posts/${postId}/responses`));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load this opportunity');
    } finally {
      setLoading(false);
    }
  }, [postId]);

  useEffect(() => {
    void load();
  }, [load]);

  const respond = async (event: React.FormEvent) => {
    event.preventDefault();
    const text = responseBody.trim();
    if (text.length < 10 || sending) return;
    setSending(true);
    try {
      const result = await apiPost<PostResponseCreated>(`/deal-room-posts/${postId}/respond`, {
        message: text,
      });
      notifyInboxChanged();
      setResponseOpen(false);
      setResponseBody('');
      toast.success(en ? 'Response sent' : 'Réponse envoyée', {
        description: en
          ? 'The conversation is in your inbox.'
          : 'La conversation est dans votre boîte de réception.',
        action: {
          label: en ? 'Open' : 'Ouvrir',
          onClick: () => navigate(`/inbox?to=${encodeURIComponent(result.partner_email)}`),
        },
      });
      await load();
      onChanged();
    } catch (err) {
      toast.error((err as ApiError).message || (en ? 'Could not respond' : 'Échec de la réponse'));
    } finally {
      setSending(false);
    }
  };

  const report = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!reportReason || reporting) return;
    setReporting(true);
    try {
      await apiPost(`/deal-room-posts/${postId}/report`, {
        reason: reportReason,
        detail: reportDetail.trim() || null,
      });
      setReportOpen(false);
      setReportReason('');
      setReportDetail('');
      toast.success(
        en ? 'Reported. A moderator will review it.' : 'Signalé. Un modérateur va examiner.',
      );
    } catch (err) {
      toast.error((err as ApiError).message || (en ? 'Could not report' : 'Échec du signalement'));
    } finally {
      setReporting(false);
    }
  };

  const changeStatus = async (status: 'published' | 'closed' | 'archived') => {
    setBusy(true);
    try {
      await apiPost(`/deal-room-posts/${postId}/status`, { status });
      toast.success(en ? 'Updated' : 'Mis à jour');
      await load();
      onChanged();
    } catch (err) {
      toast.error((err as ApiError).message || (en ? 'Could not update' : 'Échec'));
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    if (!post) return;
    const willArchive = post.status !== 'draft' || post.response_count > 0;
    const confirmed = window.confirm(
      willArchive
        ? en
          ? 'This post has been seen by others, so it will be archived rather than deleted. Continue?'
          : "Ce post a été vu par d'autres : il sera archivé plutôt que supprimé. Continuer ?"
        : en
          ? 'Delete this draft permanently?'
          : 'Supprimer définitivement ce brouillon ?',
    );
    if (!confirmed) return;

    setBusy(true);
    try {
      await apiDelete(`/deal-room-posts/${postId}`);
      toast.success(willArchive ? (en ? 'Archived' : 'Archivé') : en ? 'Deleted' : 'Supprimé');
      onChanged();
      onClose();
    } catch (err) {
      toast.error((err as ApiError).message || (en ? 'Could not delete' : 'Échec'));
    } finally {
      setBusy(false);
    }
  };

  const decideResponse = async (responseId: number, status: 'accepted' | 'declined') => {
    try {
      await apiPost(`/deal-room-posts/${postId}/responses/${responseId}/decision`, { status });
      setResponses(await apiGet<PostResponseItem[]>(`/deal-room-posts/${postId}/responses`));
    } catch (err) {
      toast.error((err as ApiError).message || (en ? 'Could not update' : 'Échec'));
    }
  };

  if (loading) {
    return (
      <div className="grid place-items-center py-20">
        <Loader2 className="w-5 h-5 animate-spin text-pulse-orange" />
      </div>
    );
  }

  if (error || !post) {
    return (
      <div className="text-center py-16">
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          {error || (en ? 'Opportunity not found' : 'Opportunité introuvable')}
        </p>
        <Button variant="outline" size="sm" className="mt-4" onClick={onClose}>
          {en ? 'Back to the board' : 'Retour au tableau'}
        </Button>
      </div>
    );
  }

  const author = post.author;
  const displayName = author.entity_name || author.full_name || (en ? 'Member' : 'Membre');
  const amount = formatAmountRange(post.amount_min, post.amount_max, post.currency, language);
  const remaining = daysUntil(post.deadline);

  const facts = [
    { label: en ? 'Amount' : 'Montant', value: amount },
    { label: en ? 'Sector' : 'Secteur', value: post.sector },
    { label: en ? 'Stage' : 'Stade', value: post.stage ? stageLabel(post.stage, language) : null },
    { label: en ? 'Location' : 'Lieu', value: post.location },
    { label: en ? 'Equity' : 'Participation', value: post.equity_offered },
    {
      label: en ? 'Commitment' : 'Engagement',
      value: post.commitment ? commitmentLabel(post.commitment, language) : null,
    },
    {
      label: en ? 'Deadline' : 'Échéance',
      value:
        remaining === null
          ? null
          : remaining < 0
            ? en
              ? 'Passed'
              : 'Dépassée'
            : en
              ? `${remaining} days`
              : `${remaining} jours`,
    },
    {
      label: en ? 'Open to' : 'Ouvert à',
      value: counterpartyLabel(post.counterparty_type, language),
    },
  ].filter((fact) => fact.value);

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 p-5">
        <div className="flex items-center gap-2 flex-wrap mb-3">
          <Chip
            icon={<PostTypeIcon type={post.post_type} className="w-3 h-3" />}
            className={postTypeTone(post.post_type)}
          >
            {postTypeLabel(post.post_type, language)}
          </Chip>
          {post.status !== 'published' && (
            <Chip className={statusTone(post.status)}>{postStatusLabel(post.status, language)}</Chip>
          )}
          {post.moderation_status === 'flagged' && (
            <Chip className="bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20">
              {en ? 'Under review' : 'En examen'}
            </Chip>
          )}
          <span className="ml-auto text-[11px] text-zinc-400">
            {relativeTime(post.published_at ?? post.created_at, language)}
          </span>
        </div>

        <h2 className="text-lg font-semibold text-zinc-900 dark:text-white leading-snug">
          {post.title}
        </h2>
        <p className="text-sm text-zinc-600 dark:text-zinc-300 mt-2 leading-relaxed">
          {post.summary}
        </p>

        {/* Author */}
        <div className="flex items-center gap-2.5 mt-4 pt-4 border-t border-zinc-50 dark:border-zinc-800">
          {author.profile_pic ? (
            <FadeInImage src={author.profile_pic} alt="" className="w-9 h-9 rounded-full object-cover" />
          ) : (
            <span className="w-9 h-9 rounded-full bg-pulse-orange/10 text-pulse-orange text-xs font-bold grid place-items-center">
              {initials(displayName)}
            </span>
          )}
          <div className="min-w-0">
            <p className="text-sm font-medium text-zinc-900 dark:text-white truncate">
              {displayName}
            </p>
            <p className="text-[11px] text-zinc-400 truncate">
              {author.entity_name && author.full_name
                ? `${author.full_name}${author.role ? ` · ${author.role}` : ''}`
                : author.role || ''}
            </p>
          </div>
          {post.has_deal_room && (
            <Chip
              icon={<FileLock2 className="w-3 h-3" />}
              className="ml-auto bg-zinc-500/10 text-zinc-600 dark:text-zinc-300 border-zinc-500/20"
            >
              {en ? 'Has a data room' : 'Data room disponible'}
            </Chip>
          )}
        </div>
      </div>

      {/* Deal facts */}
      {facts.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {facts.map((fact) => (
            <div
              key={fact.label}
              className="bg-white dark:bg-zinc-900 rounded-lg border border-zinc-100 dark:border-zinc-800 px-3 py-2"
            >
              <p className="text-[10px] uppercase tracking-wide text-zinc-400">{fact.label}</p>
              <p className="text-xs font-semibold text-zinc-900 dark:text-white mt-0.5 truncate">
                {fact.value}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* The full ask */}
      <section className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 p-5">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-400 mb-2.5">
          {en ? 'About this opportunity' : 'À propos de cette opportunité'}
        </h3>
        <p className="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed whitespace-pre-wrap">
          {post.details}
        </p>
      </section>

      {/* Who they want */}
      {post.looking_for && (
        <section className="bg-pulse-orange/[0.04] dark:bg-pulse-orange/[0.07] rounded-xl border border-pulse-orange/20 p-5">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-pulse-orange mb-2.5 flex items-center gap-1.5">
            <Target className="w-3.5 h-3.5" />
            {en ? 'Who they are looking for' : 'Profil recherché'}
          </h3>
          <p className="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed whitespace-pre-wrap">
            {post.looking_for}
          </p>
        </section>
      )}

      {post.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {post.tags.map((tag) => (
            <Chip
              key={tag}
              className="bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 border-transparent"
            >
              {tag}
            </Chip>
          ))}
        </div>
      )}

      {/* Reader actions */}
      {!post.can_manage && (
        <div className="flex items-center gap-2 flex-wrap">
          {post.responded_by_me ? (
            <div className="flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
              <Check className="w-4 h-4" />
              {en ? 'You have responded' : 'Vous avez répondu'}
            </div>
          ) : post.status === 'published' ? (
            <Button
              size="sm"
              className="bg-pulse-orange hover:bg-pulse-orange-hover text-white"
              onClick={() => {
                if (!signedIn) {
                  toast.info(en ? 'Sign in to respond' : 'Connectez-vous pour répondre');
                  navigate('/login');
                  return;
                }
                setResponseOpen(true);
              }}
            >
              <MessagesSquare className="w-3.5 h-3.5 mr-1.5" />
              {en ? 'Respond' : 'Répondre'}
            </Button>
          ) : (
            <p className="text-xs text-zinc-400">
              {en
                ? 'This opportunity is closed and is no longer taking responses.'
                : "Cette opportunité est clôturée et n'accepte plus de réponses."}
            </p>
          )}

          {signedIn && (
            <Button
              variant="ghost"
              size="sm"
              className="text-zinc-400 hover:text-red-600"
              onClick={() => setReportOpen(true)}
            >
              <Flag className="w-3.5 h-3.5 mr-1.5" />
              {en ? 'Report' : 'Signaler'}
            </Button>
          )}
        </div>
      )}

      {/* Author actions */}
      {post.can_manage && (
        <section className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 p-4 space-y-3">
          <div className="flex items-center gap-3 text-[11px] text-zinc-400">
            <span className="inline-flex items-center gap-1">
              <Eye className="w-3.5 h-3.5" />
              {post.view_count} {en ? 'views' : 'vues'}
            </span>
            <span className="inline-flex items-center gap-1">
              <Users className="w-3.5 h-3.5" />
              {post.response_count} {en ? 'responses' : 'réponses'}
            </span>
            {(post.open_report_count ?? 0) > 0 && (
              <span className="inline-flex items-center gap-1 text-amber-600 dark:text-amber-400">
                <AlertTriangle className="w-3.5 h-3.5" />
                {post.open_report_count} {en ? 'open reports' : 'signalements'}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {post.status !== 'archived' && (
              <Button variant="outline" size="sm" onClick={() => onEdit(post)} disabled={busy}>
                <PencilLine className="w-3.5 h-3.5 mr-1.5" />
                {en ? 'Edit' : 'Modifier'}
              </Button>
            )}
            {post.status === 'draft' && (
              <Button
                size="sm"
                className="bg-pulse-orange hover:bg-pulse-orange-hover text-white"
                onClick={() => changeStatus('published')}
                disabled={busy}
              >
                {en ? 'Publish' : 'Publier'}
              </Button>
            )}
            {post.status === 'published' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => changeStatus('closed')}
                disabled={busy}
              >
                {en ? 'Close' : 'Clôturer'}
              </Button>
            )}
            {post.status === 'closed' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => changeStatus('published')}
                disabled={busy}
              >
                {en ? 'Reopen' : 'Rouvrir'}
              </Button>
            )}
            {post.status !== 'archived' && (
              <Button
                variant="ghost"
                size="sm"
                className="text-zinc-400 hover:text-red-600 ml-auto"
                onClick={remove}
                disabled={busy}
              >
                <Trash2 className="w-3.5 h-3.5 mr-1.5" />
                {post.status === 'draft' && post.response_count === 0
                  ? en
                    ? 'Delete'
                    : 'Supprimer'
                  : en
                    ? 'Archive'
                    : 'Archiver'}
              </Button>
            )}
          </div>

          {post.moderation_note && (
            <p className="text-[11px] text-amber-700 dark:text-amber-400 bg-amber-500/10 rounded-md px-2.5 py-1.5">
              {en ? 'Moderator note: ' : 'Note du modérateur : '}
              {post.moderation_note}
            </p>
          )}
        </section>
      )}

      {/* Responders — author only */}
      {post.can_manage && responses !== null && (
        <section className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-400 mb-3">
            {en ? 'Who responded' : 'Qui a répondu'} ({responses.length})
          </h3>
          {responses.length === 0 ? (
            <p className="text-xs text-zinc-400 py-2">
              {en
                ? 'Nobody has responded yet. Responses arrive here and in your inbox.'
                : "Personne n'a encore répondu. Les réponses arrivent ici et dans votre boîte."}
            </p>
          ) : (
            <ul className="space-y-2.5">
              {responses.map((response) => (
                <li
                  key={response.id}
                  className="flex items-start gap-2.5 p-2.5 rounded-lg bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-100 dark:border-zinc-800"
                >
                  <span className="w-7 h-7 rounded-full bg-pulse-orange/10 text-pulse-orange text-[9px] font-bold grid place-items-center flex-shrink-0 mt-0.5">
                    {initials(response.responder.full_name)}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-xs font-medium text-zinc-900 dark:text-white">
                        {response.responder.full_name || (en ? 'Member' : 'Membre')}
                      </p>
                      {response.status !== 'pending' && (
                        <Chip
                          className={
                            response.status === 'accepted'
                              ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20'
                              : 'bg-zinc-500/10 text-zinc-500 border-zinc-500/20'
                          }
                        >
                          {response.status === 'accepted'
                            ? en
                              ? 'Accepted'
                              : 'Accepté'
                            : en
                              ? 'Declined'
                              : 'Décliné'}
                        </Chip>
                      )}
                      <span className="text-[10px] text-zinc-400 ml-auto">
                        {relativeTime(response.created_at, language)}
                      </span>
                    </div>
                    <p className="text-[11px] text-zinc-600 dark:text-zinc-400 mt-1 line-clamp-3 leading-relaxed">
                      {response.message}
                    </p>
                    <div className="flex items-center gap-1.5 mt-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 px-2 text-[10px]"
                        onClick={() => navigate('/inbox')}
                      >
                        <MessagesSquare className="w-3 h-3 mr-1" />
                        {en ? 'Open in inbox' : 'Ouvrir dans la boîte'}
                      </Button>
                      {response.status === 'pending' && (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 px-2 text-[10px] text-emerald-600"
                            onClick={() => decideResponse(response.id, 'accepted')}
                          >
                            <Check className="w-3 h-3 mr-1" />
                            {en ? 'Accept' : 'Accepter'}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 px-2 text-[10px] text-zinc-400"
                            onClick={() => decideResponse(response.id, 'declined')}
                          >
                            <X className="w-3 h-3 mr-1" />
                            {en ? 'Decline' : 'Décliner'}
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {/* Respond dialog */}
      <Dialog open={responseOpen} onOpenChange={(next) => !next && setResponseOpen(false)}>
        <DialogContent className="max-w-md">
          <form onSubmit={respond}>
            <DialogHeader>
              <DialogTitle className="text-base">
                {en ? 'Respond to this opportunity' : 'Répondre à cette opportunité'}
              </DialogTitle>
              <DialogDescription className="text-xs">
                {en
                  ? 'This starts a conversation in your inbox with the author. Say who you are and why this fits.'
                  : "Ceci démarre une conversation avec l'auteur dans votre boîte. Dites qui vous êtes et pourquoi cela correspond."}
              </DialogDescription>
            </DialogHeader>
            <div className="py-3">
              <Textarea
                value={responseBody}
                onChange={(event) => setResponseBody(event.target.value)}
                rows={6}
                maxLength={2000}
                autoFocus
                placeholder={
                  en
                    ? 'Introduce yourself, and be specific about what you bring…'
                    : 'Présentez-vous et soyez précis sur ce que vous apportez…'
                }
                className="text-sm resize-none"
              />
              <p className="text-[11px] text-zinc-400 mt-1 text-right">
                {responseBody.trim().length}/2000
                {responseBody.trim().length < 10 && responseBody.length > 0 && (
                  <span className="text-amber-600 ml-2">
                    {en ? 'At least 10 characters' : 'Au moins 10 caractères'}
                  </span>
                )}
              </p>
            </div>
            <DialogFooter className="gap-2">
              <Button type="button" variant="ghost" size="sm" onClick={() => setResponseOpen(false)}>
                {en ? 'Cancel' : 'Annuler'}
              </Button>
              <Button
                type="submit"
                size="sm"
                disabled={responseBody.trim().length < 10 || sending}
                className="bg-pulse-orange hover:bg-pulse-orange-hover text-white"
              >
                {sending && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
                {en ? 'Send response' : 'Envoyer'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Report dialog */}
      <Dialog open={reportOpen} onOpenChange={(next) => !next && setReportOpen(false)}>
        <DialogContent className="max-w-md">
          <form onSubmit={report}>
            <DialogHeader>
              <DialogTitle className="text-base">
                {en ? 'Report this opportunity' : 'Signaler cette opportunité'}
              </DialogTitle>
              <DialogDescription className="text-xs">
                {en
                  ? 'A moderator will review it. The post stays visible until they decide.'
                  : "Un modérateur l'examinera. Le post reste visible jusqu'à sa décision."}
              </DialogDescription>
            </DialogHeader>
            <div className="py-3 space-y-3">
              <Select value={reportReason} onValueChange={setReportReason}>
                <SelectTrigger className="text-sm">
                  <SelectValue placeholder={en ? 'Choose a reason' : 'Choisir une raison'} />
                </SelectTrigger>
                <SelectContent>
                  {(meta?.report_reasons ?? []).map((reason) => (
                    <SelectItem key={reason} value={reason} className="text-sm">
                      {reportReasonLabel(reason, language)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Textarea
                value={reportDetail}
                onChange={(event) => setReportDetail(event.target.value)}
                rows={3}
                maxLength={1000}
                placeholder={en ? 'Anything else? (optional)' : 'Autre chose ? (facultatif)'}
                className="text-sm resize-none"
              />
            </div>
            <DialogFooter className="gap-2">
              <Button type="button" variant="ghost" size="sm" onClick={() => setReportOpen(false)}>
                {en ? 'Cancel' : 'Annuler'}
              </Button>
              <Button
                type="submit"
                size="sm"
                variant="destructive"
                disabled={!reportReason || reporting}
              >
                {reporting && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
                {en ? 'Submit report' : 'Signaler'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
