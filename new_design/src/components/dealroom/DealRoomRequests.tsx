import { useCallback, useEffect, useState } from 'react';
import { Check, Inbox, Loader2, MessageCircleQuestion, X } from 'lucide-react';
import { apiGet, apiPost } from '@/lib/api';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import type { AccessRequest, DealRoomPermission, DealRoomSummary } from '@/types/dealroom';
import {
  EmptyState,
  ErrorState,
  Panel,
  RowSkeleton,
  StatusPill,
  formatDateTime,
  permissionLabel,
} from './shared';

const GRANTABLE: DealRoomPermission[] = ['view', 'view_watermark', 'download', 'download_watermark'];

interface Props {
  room: DealRoomSummary;
  language: string;
  onChanged?: () => void;
}

/** Access requests: approve with a chosen permission, reject, or ask for more. */
export default function DealRoomRequests({ room, language, onChanged }: Props) {
  const en = language === 'en';
  const [requests, setRequests] = useState<AccessRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [permissions, setPermissions] = useState<Record<number, DealRoomPermission>>({});

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setRequests(await apiGet<AccessRequest[]>(`/deal-rooms/${room.id}/access-requests`));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load access requests');
    } finally {
      setLoading(false);
    }
  }, [room.id]);

  useEffect(() => {
    void load();
  }, [load]);

  const decide = async (
    request: AccessRequest,
    decision: 'approve' | 'reject' | 'request_info',
  ) => {
    setBusyId(request.id);
    try {
      await apiPost(`/deal-rooms/${room.id}/access-requests/${request.id}/decision`, {
        decision,
        permission: permissions[request.id] ?? room.default_permission ?? 'view_watermark',
      });
      toast.success(
        decision === 'approve'
          ? en ? 'Investor admitted' : 'Investisseur admis'
          : decision === 'reject'
            ? en ? 'Request rejected' : 'Demande refusée'
            : en ? 'More information requested' : 'Informations demandées',
      );
      await load();
      onChanged?.();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Decision failed');
    } finally {
      setBusyId(null);
    }
  };

  const pending = requests.filter((r) => r.status === 'pending' || r.status === 'info_requested');
  const decided = requests.filter((r) => r.status !== 'pending' && r.status !== 'info_requested');

  return (
    <div className="space-y-4">
      <Panel title={en ? 'Pending requests' : 'Demandes en attente'}>
        {loading ? (
          <RowSkeleton rows={2} />
        ) : error ? (
          <ErrorState message={error} onRetry={() => void load()} retryLabel={en ? 'Try again' : 'Réessayer'} />
        ) : pending.length === 0 ? (
          <EmptyState
            icon={Inbox}
            title={en ? 'Nothing to review' : 'Rien à examiner'}
            description={
              en
                ? 'Access requests from investors will appear here for approval.'
                : "Les demandes d'accès des investisseurs apparaîtront ici."
            }
          />
        ) : (
          <ul className="divide-y divide-zinc-50 dark:divide-zinc-800/60">
            {pending.map((request) => (
              <li key={request.id} className="px-4 py-4">
                <div className="flex flex-col lg:flex-row lg:items-start gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium text-zinc-900 dark:text-white">
                        {request.full_name || request.email}
                      </span>
                      <StatusPill status={request.status} language={language} />
                    </div>
                    <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5">
                      {request.email} · {formatDateTime(request.created_at, language)}
                    </p>
                    {request.message && (
                      <p className="text-xs text-zinc-600 dark:text-zinc-300 mt-2 bg-zinc-50 dark:bg-zinc-800/50 rounded-lg p-3 leading-relaxed">
                        “{request.message}”
                      </p>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center gap-2 lg:justify-end">
                    <Select
                      value={permissions[request.id] ?? 'view_watermark'}
                      onValueChange={(value) =>
                        setPermissions((prev) => ({
                          ...prev,
                          [request.id]: value as DealRoomPermission,
                        }))
                      }
                    >
                      <SelectTrigger className="h-8 w-[168px] text-[11px] dark:bg-zinc-800">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {GRANTABLE.map((permission) => (
                          <SelectItem key={permission} value={permission}>
                            {permissionLabel(permission, language)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>

                    <Button
                      size="sm"
                      className="h-8 text-[11px] bg-pulse-orange hover:bg-pulse-orange-hover text-white"
                      onClick={() => void decide(request, 'approve')}
                      disabled={busyId === request.id}
                    >
                      {busyId === request.id ? (
                        <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                      ) : (
                        <Check className="w-3 h-3 mr-1" />
                      )}
                      {en ? 'Approve' : 'Approuver'}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-8 text-[11px] dark:bg-zinc-800 dark:border-zinc-700"
                      onClick={() => void decide(request, 'request_info')}
                      disabled={busyId === request.id}
                    >
                      <MessageCircleQuestion className="w-3 h-3 mr-1" />
                      {en ? 'Ask for more' : 'Demander plus'}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 text-[11px] text-red-500 hover:text-red-600"
                      onClick={() => void decide(request, 'reject')}
                      disabled={busyId === request.id}
                    >
                      <X className="w-3 h-3 mr-1" />
                      {en ? 'Reject' : 'Refuser'}
                    </Button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Panel>

      {decided.length > 0 && (
        <Panel title={en ? 'Decided' : 'Traitées'}>
          <ul className="divide-y divide-zinc-50 dark:divide-zinc-800/60">
            {decided.map((request) => (
              <li key={request.id} className="px-4 py-3 flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-[13px] text-zinc-900 dark:text-white truncate">
                    {request.full_name || request.email}
                  </p>
                  <p className="text-[11px] text-zinc-500 dark:text-zinc-400">
                    {formatDateTime(request.decided_at, language)}
                  </p>
                </div>
                <StatusPill status={request.status} language={language} />
              </li>
            ))}
          </ul>
        </Panel>
      )}
    </div>
  );
}
