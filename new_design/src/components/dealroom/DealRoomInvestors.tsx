import { useCallback, useEffect, useState } from 'react';
import { Ban, Loader2, RotateCcw, UserPlus, Users, XCircle } from 'lucide-react';
import { apiDelete, apiGet, apiPatch, apiPost } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import type { DealRoomPermission, DealRoomSummary, Participant } from '@/types/dealroom';
import {
  EmptyState,
  ErrorState,
  Panel,
  PermissionBadge,
  RowSkeleton,
  StatusPill,
  formatDateTime,
  permissionLabel,
} from './shared';

/** Permission levels an investor may hold; upload and manage are startup-side. */
const INVESTOR_PERMISSIONS: DealRoomPermission[] = [
  'none',
  'view',
  'view_watermark',
  'download',
  'download_watermark',
];

interface Props {
  room: DealRoomSummary;
  language: string;
  onChanged?: () => void;
}

export default function DealRoomInvestors({ room, language, onChanged }: Props) {
  const en = language === 'en';
  const [investors, setInvestors] = useState<Participant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [inviteOpen, setInviteOpen] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setInvestors(await apiGet<Participant[]>(`/deal-rooms/${room.id}/investors`));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load investors');
    } finally {
      setLoading(false);
    }
  }, [room.id]);

  useEffect(() => {
    void load();
  }, [load]);

  const update = async (participant: Participant, body: Record<string, unknown>, message: string) => {
    setBusyId(participant.id);
    try {
      await apiPatch(`/deal-rooms/${room.id}/investors/${participant.id}`, body);
      toast.success(message);
      await load();
      onChanged?.();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Update failed');
    } finally {
      setBusyId(null);
    }
  };

  const revoke = async (participant: Participant) => {
    const name = participant.full_name || participant.email;
    if (
      !window.confirm(
        en
          ? `Revoke ${name}'s access? They lose it immediately, including any open document links.`
          : `Révoquer l'accès de ${name} ? L'accès cesse immédiatement.`,
      )
    ) {
      return;
    }
    setBusyId(participant.id);
    try {
      await apiDelete(`/deal-rooms/${room.id}/investors/${participant.id}`);
      toast.success(en ? 'Access revoked' : 'Accès révoqué');
      await load();
      onChanged?.();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Revoke failed');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <Panel
      title={en ? 'Investors' : 'Investisseurs'}
      action={
        <Button
          size="sm"
          className="h-8 text-xs bg-pulse-orange hover:bg-pulse-orange-hover text-primary-foreground"
          onClick={() => setInviteOpen(true)}
        >
          <UserPlus className="w-3.5 h-3.5 mr-1.5" />
          {en ? 'Invite' : 'Inviter'}
        </Button>
      }
    >
      {loading ? (
        <RowSkeleton rows={3} />
      ) : error ? (
        <ErrorState message={error} onRetry={() => void load()} retryLabel={en ? 'Try again' : 'Réessayer'} />
      ) : investors.length === 0 ? (
        <EmptyState
          icon={Users}
          title={en ? 'No investors yet' : 'Aucun investisseur'}
          description={
            en
              ? 'Invite an investor by email. They must already have a Pulse account, so every action in this room is attributable.'
              : "Invitez un investisseur par e-mail. Il doit déjà avoir un compte Pulse, afin que chaque action soit attribuable."
          }
          action={
            <Button
              size="sm"
              className="h-8 text-xs bg-pulse-orange hover:bg-pulse-orange-hover text-primary-foreground"
              onClick={() => setInviteOpen(true)}
            >
              <UserPlus className="w-3.5 h-3.5 mr-1.5" />
              {en ? 'Invite an investor' : 'Inviter un investisseur'}
            </Button>
          }
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wide text-zinc-500 dark:text-zinc-400 border-b border-zinc-100 dark:border-zinc-800">
                <th className="font-semibold px-4 py-2">{en ? 'Investor' : 'Investisseur'}</th>
                <th className="font-semibold px-3 py-2">{en ? 'Status' : 'Statut'}</th>
                <th className="font-semibold px-3 py-2">{en ? 'Access' : 'Accès'}</th>
                <th className="font-semibold px-3 py-2 whitespace-nowrap">{en ? 'Activity' : 'Activité'}</th>
                <th className="font-semibold px-3 py-2 whitespace-nowrap">{en ? 'Last seen' : 'Vu le'}</th>
                <th className="px-4 py-2" />
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-50 dark:divide-zinc-800/60">
              {investors.map((investor) => (
                <tr key={investor.id} className="hover:bg-zinc-50/60 dark:hover:bg-zinc-800/30">
                  <td className="px-4 py-3">
                    <div className="min-w-0">
                      <p className="font-medium text-zinc-900 dark:text-white truncate text-[13px]">
                        {investor.full_name || investor.email}
                      </p>
                      <p className="text-[11px] text-zinc-600 dark:text-zinc-300 truncate">
                        {investor.email}
                      </p>
                    </div>
                  </td>
                  <td className="px-3 py-3">
                    <div className="flex flex-col gap-1 items-start">
                      <StatusPill status={investor.status} language={language} />
                      {room.nda_required && (
                        <span
                          className={`text-[11px] ${
                            investor.nda_accepted_at
                              ? 'text-emerald-700 dark:text-emerald-400'
                              : 'text-amber-600 dark:text-amber-400'
                          }`}
                        >
                          {investor.nda_accepted_at
                            ? en ? 'NDA signed' : 'NDA signé'
                            : en ? 'NDA pending' : 'NDA en attente'}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-3 py-3">
                    <Select
                      value={investor.permission}
                      onValueChange={(value) =>
                        void update(
                          investor,
                          { permission: value },
                          en
                            ? `Access set to ${permissionLabel(value as DealRoomPermission, language)}`
                            : `Accès : ${permissionLabel(value as DealRoomPermission, language)}`,
                        )
                      }
                      disabled={busyId === investor.id}
                    >
                      <SelectTrigger className="h-7 w-[168px] text-[11px] dark:bg-zinc-800">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {INVESTOR_PERMISSIONS.map((permission) => (
                          <SelectItem key={permission} value={permission}>
                            {permissionLabel(permission, language)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </td>
                  <td className="px-3 py-3 whitespace-nowrap">
                    <span className="text-[11px] text-zinc-600 dark:text-zinc-300">
                      {investor.documents_viewed} {en ? 'viewed' : 'vus'} · {investor.downloads}{' '}
                      {en ? 'downloads' : 'téléch.'}
                    </span>
                  </td>
                  <td className="px-3 py-3 whitespace-nowrap">
                    <span className="text-[11px] text-zinc-600 dark:text-zinc-300">
                      {formatDateTime(investor.last_activity_at, language)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1 justify-end">
                      {busyId === investor.id && (
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-zinc-500 dark:text-zinc-400" />
                      )}
                      {investor.status === 'active' ? (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 px-2 text-[11px] text-amber-600 hover:text-amber-700"
                          onClick={() =>
                            void update(
                              investor,
                              { status: 'suspended' },
                              en ? 'Access suspended' : 'Accès suspendu',
                            )
                          }
                          disabled={busyId === investor.id}
                        >
                          <Ban className="w-3 h-3 mr-1" />
                          {en ? 'Suspend' : 'Suspendre'}
                        </Button>
                      ) : investor.status !== 'revoked' ? (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 px-2 text-[11px] text-emerald-700 dark:text-emerald-400 hover:text-emerald-700"
                          onClick={() =>
                            void update(
                              investor,
                              { status: 'active' },
                              en ? 'Access restored' : 'Accès rétabli',
                            )
                          }
                          disabled={busyId === investor.id}
                        >
                          <RotateCcw className="w-3 h-3 mr-1" />
                          {en ? 'Restore' : 'Rétablir'}
                        </Button>
                      ) : null}
                      {investor.status !== 'revoked' && (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 w-7 p-0 text-red-500 hover:text-red-600"
                          onClick={() => void revoke(investor)}
                          disabled={busyId === investor.id}
                          aria-label={en ? 'Revoke access' : "Révoquer l'accès"}
                          title={en ? 'Revoke access' : "Révoquer l'accès"}
                        >
                          <XCircle className="w-3.5 h-3.5" />
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {inviteOpen && (
        <InviteDialog
          roomId={room.id}
          language={language}
          defaultPermission={room.default_permission}
          onClose={() => setInviteOpen(false)}
          onInvited={() => {
            setInviteOpen(false);
            void load();
            onChanged?.();
          }}
        />
      )}
    </Panel>
  );
}

function InviteDialog({
  roomId,
  language,
  defaultPermission,
  onClose,
  onInvited,
}: {
  roomId: number;
  language: string;
  defaultPermission: DealRoomPermission;
  onClose: () => void;
  onInvited: () => void;
}) {
  const en = language === 'en';
  const [email, setEmail] = useState('');
  const [permission, setPermission] = useState<DealRoomPermission>(
    INVESTOR_PERMISSIONS.includes(defaultPermission) ? defaultPermission : 'view_watermark',
  );
  const [expiresAt, setExpiresAt] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    try {
      await apiPost(`/deal-rooms/${roomId}/investors`, {
        email: email.trim().toLowerCase(),
        permission,
        // A date input yields YYYY-MM-DD; expire at end of that day.
        expires_at: expiresAt ? new Date(`${expiresAt}T23:59:59`).toISOString() : null,
      });
      toast.success(en ? 'Investor invited' : 'Investisseur invité');
      onInvited();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Invite failed');
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="text-base">{en ? 'Invite an investor' : 'Inviter un investisseur'}</DialogTitle>
          <DialogDescription className="text-xs">
            {en
              ? 'They must already have a Pulse account. Access can be narrowed per folder or document afterwards.'
              : "Il doit déjà avoir un compte Pulse. L'accès peut ensuite être affiné par dossier ou document."}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="dr-invite-email" className="text-xs">{en ? 'Email' : 'E-mail'}</Label>
            <Input
              id="dr-invite-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="investor@fund.com"
              className="h-9 text-sm dark:bg-zinc-900"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">{en ? 'Access level' : "Niveau d'accès"}</Label>
            <Select value={permission} onValueChange={(v) => setPermission(v as DealRoomPermission)}>
              <SelectTrigger className="h-9 text-xs dark:bg-zinc-900">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {INVESTOR_PERMISSIONS.map((p) => (
                  <SelectItem key={p} value={p}>
                    {permissionLabel(p, language)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-[11px] text-zinc-600 dark:text-zinc-300">
              {en
                ? 'Watermarked renditions carry the viewer’s email, making leaks traceable.'
                : "Les versions filigranées portent l'e-mail du lecteur, rendant les fuites traçables."}
            </p>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="dr-invite-exp" className="text-xs">
              {en ? 'Access expires (optional)' : "Expiration de l'accès (facultatif)"}
            </Label>
            <Input
              id="dr-invite-exp"
              type="date"
              value={expiresAt}
              onChange={(e) => setExpiresAt(e.target.value)}
              className="h-9 text-sm dark:bg-zinc-900"
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" size="sm" className="h-9 text-xs" onClick={onClose}>
              {en ? 'Cancel' : 'Annuler'}
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={busy || !email.trim()}
              className="h-9 text-xs bg-pulse-orange hover:bg-pulse-orange-hover text-primary-foreground"
            >
              {busy && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
              {en ? 'Send invite' : "Envoyer l'invitation"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export { PermissionBadge };
