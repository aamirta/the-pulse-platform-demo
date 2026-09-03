import { useCallback, useEffect, useState } from 'react';
import {
  Activity,
  BarChart3,
  Download,
  Eye,
  EyeOff,
  FileWarning,
  ScrollText,
  Users,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { apiGet, API_BASE_URL, getAccessToken } from '@/lib/api';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useTheme } from '@/hooks/useTheme';
import { toast } from 'sonner';
import type { DealRoomAnalytics, DealRoomSummary, PagedAudit } from '@/types/dealroom';
import {
  EmptyState,
  ErrorState,
  Panel,
  RowSkeleton,
  StatCard,
  auditActionLabel,
  auditActionTone,
  categoryLabel,
  formatDateTime,
} from './shared';

/** Audit actions offered as filters, mirroring `services/dealroom.py`. */
const AUDIT_ACTIONS = [
  'deal_room.opened',
  'document.previewed',
  'document.downloaded',
  'document.uploaded',
  'document.deleted',
  'permission.changed',
  'investor.invited',
  'investor.approved',
  'access.revoked',
  'access.denied',
  'nda.accepted',
  'question.created',
  'answer.created',
];

interface Props {
  room: DealRoomSummary;
  language: string;
}

/**
 * Engagement analytics and the audit trail.
 *
 * Both are startup-side only; the API refuses these routes for investors, so
 * one investor's reading history is never visible to another.
 */
export default function DealRoomInsights({ room, language }: Props) {
  const en = language === 'en';
  const { theme } = useTheme();

  const [analytics, setAnalytics] = useState<DealRoomAnalytics | null>(null);
  const [audit, setAudit] = useState<PagedAudit | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [action, setAction] = useState('all');
  const [page, setPage] = useState(1);
  const [exporting, setExporting] = useState(false);

  const axisColor = theme === 'dark' ? '#a1a1aa' : '#52525b';
  const gridColor = theme === 'dark' ? '#27272a' : '#f4f4f5';

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: '25' });
      if (action !== 'all') params.set('action', action);
      const [stats, trail] = await Promise.all([
        apiGet<DealRoomAnalytics>(`/deal-rooms/${room.id}/analytics`),
        apiGet<PagedAudit>(`/deal-rooms/${room.id}/audit?${params}`),
      ]);
      setAnalytics(stats);
      setAudit(trail);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load insights');
    } finally {
      setLoading(false);
    }
  }, [room.id, action, page]);

  useEffect(() => {
    void load();
  }, [load]);

  /**
   * Download the audit CSV.
   *
   * Fetched with the bearer token rather than linked directly, because the
   * export endpoint is authorized like every other route and a plain anchor
   * would arrive unauthenticated.
   */
  const exportAudit = async () => {
    setExporting(true);
    try {
      const token = getAccessToken();
      const response = await fetch(`${API_BASE_URL}/deal-rooms/${room.id}/audit/export`, {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `deal-room-${room.id}-audit.csv`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setExporting(false);
    }
  };

  if (loading && !analytics) return <RowSkeleton rows={6} />;
  if (error) {
    return (
      <Panel>
        <ErrorState message={error} onRetry={() => void load()} retryLabel={en ? 'Try again' : 'Réessayer'} />
      </Panel>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label={en ? 'Total views' : 'Vues totales'}
          value={analytics?.total_views ?? 0}
          icon={Eye}
        />
        <StatCard
          label={en ? 'Downloads' : 'Téléchargements'}
          value={analytics?.total_downloads ?? 0}
          icon={Download}
        />
        <StatCard
          label={en ? 'Active investors' : 'Investisseurs actifs'}
          value={analytics?.active_investors ?? 0}
          icon={Users}
        />
        <StatCard
          label={en ? 'Never opened' : 'Jamais ouverts'}
          value={analytics?.never_viewed.length ?? 0}
          hint={en ? 'Documents with no views' : 'Documents sans vue'}
          icon={FileWarning}
          tone={analytics?.never_viewed.length ? 'warning' : 'default'}
        />
      </div>

      {analytics && analytics.timeline.length > 0 && (
        <Panel title={en ? 'Engagement over time' : 'Engagement dans le temps'}>
          <div className="p-4 h-56">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={analytics.timeline}>
                <defs>
                  <linearGradient id="drViews" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#D56426" stopOpacity={0.28} />
                    <stop offset="100%" stopColor="#D56426" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: axisColor }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 11, fill: axisColor }} tickLine={false} axisLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    fontSize: 12,
                    borderRadius: 12,
                    border: 'none',
                    background: theme === 'dark' ? '#27272a' : '#ffffff',
                    color: theme === 'dark' ? '#e4e4e7' : '#18181b',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="views"
                  stroke="#D56426"
                  strokeWidth={2}
                  fill="url(#drViews)"
                  name={en ? 'Views' : 'Vues'}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Panel title={en ? 'Most viewed documents' : 'Documents les plus consultés'}>
          {!analytics || analytics.documents.length === 0 ? (
            <EmptyState
              icon={BarChart3}
              title={en ? 'No views yet' : 'Aucune vue'}
              description={
                en
                  ? 'Once investors start opening documents, interest shows up here.'
                  : "Dès que les investisseurs consulteront les documents, l'intérêt apparaîtra ici."
              }
            />
          ) : (
            <ul className="divide-y divide-zinc-50 dark:divide-zinc-800/60">
              {analytics.documents.slice(0, 8).map((doc) => (
                <li key={doc.document_id} className="px-4 py-2.5 flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-[13px] text-zinc-900 dark:text-white truncate">{doc.title}</p>
                    <p className="text-[11px] text-zinc-600 dark:text-zinc-300">
                      {categoryLabel(doc.category, language)} · {doc.unique_investors}{' '}
                      {en ? 'investors' : 'investisseurs'}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 text-[11px] text-zinc-600 dark:text-zinc-300 flex-shrink-0">
                    <span className="flex items-center gap-1">
                      <Eye className="w-3 h-3" /> {doc.views}
                    </span>
                    <span className="flex items-center gap-1">
                      <Download className="w-3 h-3" /> {doc.downloads}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel title={en ? 'Investor engagement' : 'Engagement des investisseurs'}>
          {!analytics || analytics.investors.length === 0 ? (
            <EmptyState
              icon={Users}
              title={en ? 'No investors yet' : 'Aucun investisseur'}
              description={en ? 'Invite investors to start tracking interest.' : 'Invitez des investisseurs pour suivre leur intérêt.'}
            />
          ) : (
            <ul className="divide-y divide-zinc-50 dark:divide-zinc-800/60">
              {analytics.investors.map((investor) => (
                <li key={investor.participant_id} className="px-4 py-2.5">
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-[13px] text-zinc-900 dark:text-white truncate">
                        {investor.full_name || investor.email}
                      </p>
                      <p className="text-[11px] text-zinc-600 dark:text-zinc-300">
                        {investor.documents_viewed} {en ? 'viewed' : 'vus'} · {investor.downloads}{' '}
                        {en ? 'downloads' : 'téléch.'} · {investor.questions_asked}{' '}
                        {en ? 'questions' : 'questions'}
                      </p>
                    </div>
                    <span className="text-xs font-semibold text-pulse-orange flex-shrink-0">
                      {investor.engagement_score}%
                    </span>
                  </div>
                  <div className="mt-1.5 h-1 rounded-full bg-zinc-100 dark:bg-zinc-800 overflow-hidden">
                    <div
                      className="h-full bg-pulse-orange rounded-full transition-all"
                      style={{ width: `${investor.engagement_score}%` }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>

      {analytics && analytics.never_viewed.length > 0 && (
        <Panel title={en ? 'Never opened' : 'Jamais ouverts'}>
          <ul className="px-4 py-3 flex flex-wrap gap-2">
            {analytics.never_viewed.map((doc) => (
              <li
                key={doc.document_id}
                className="inline-flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded-lg bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400"
              >
                <EyeOff className="w-3 h-3" />
                {doc.title}
              </li>
            ))}
          </ul>
        </Panel>
      )}

      <Panel
        title={en ? 'Audit trail' : "Journal d'audit"}
        action={
          <div className="flex items-center gap-2">
            <Select
              value={action}
              onValueChange={(value) => {
                setAction(value);
                setPage(1);
              }}
            >
              <SelectTrigger className="h-8 w-[180px] text-[11px] dark:bg-zinc-800">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{en ? 'All actions' : 'Toutes les actions'}</SelectItem>
                {AUDIT_ACTIONS.map((value) => (
                  <SelectItem key={value} value={value}>
                    {auditActionLabel(value, language)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              size="sm"
              variant="outline"
              className="h-8 text-[11px] dark:bg-zinc-800 dark:border-zinc-700"
              onClick={() => void exportAudit()}
              disabled={exporting}
            >
              <Download className="w-3 h-3 mr-1.5" />
              {en ? 'Export CSV' : 'Exporter CSV'}
            </Button>
          </div>
        }
      >
        {!audit || audit.items.length === 0 ? (
          <EmptyState
            icon={ScrollText}
            title={en ? 'No activity recorded' : 'Aucune activité enregistrée'}
            description={
              en
                ? 'Every document open, permission change and access decision is logged here.'
                : "Chaque ouverture de document, changement de droit et décision d'accès est journalisé ici."
            }
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[11px] uppercase tracking-wide text-zinc-500 dark:text-zinc-400 border-b border-zinc-100 dark:border-zinc-800">
                    <th className="font-semibold px-4 py-2 whitespace-nowrap">{en ? 'When' : 'Quand'}</th>
                    <th className="font-semibold px-3 py-2">{en ? 'Who' : 'Qui'}</th>
                    <th className="font-semibold px-3 py-2">{en ? 'Action' : 'Action'}</th>
                    <th className="font-semibold px-3 py-2">{en ? 'Resource' : 'Ressource'}</th>
                    <th className="font-semibold px-4 py-2">IP</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-50 dark:divide-zinc-800/60">
                  {audit.items.map((event) => (
                    <tr key={event.id} className="hover:bg-zinc-50/60 dark:hover:bg-zinc-800/30">
                      <td className="px-4 py-2 text-[11px] text-zinc-600 dark:text-zinc-300 whitespace-nowrap">
                        {formatDateTime(event.created_at, language)}
                      </td>
                      <td className="px-3 py-2 text-[11px] text-zinc-700 dark:text-zinc-200">
                        <span className="block truncate max-w-[180px]">{event.actor_email || '—'}</span>
                        <span className="text-[11px] text-zinc-500 dark:text-zinc-400 capitalize">{event.actor_role}</span>
                      </td>
                      <td className="px-3 py-2">
                        {/* The raw identifier is kept in `title` and in the CSV
                            export, where it is the stable contract; the table
                            itself is read by founders, not by engineers. */}
                        <span
                          title={event.action}
                          className={`text-[11px] font-medium ${
                            auditActionTone(event.action) === 'danger'
                              ? 'text-red-600 dark:text-red-400'
                              : auditActionTone(event.action) === 'warning'
                                ? 'text-amber-600 dark:text-amber-400'
                                : 'text-zinc-700 dark:text-zinc-200'
                          }`}
                        >
                          {auditActionLabel(event.action, language)}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-[11px] text-zinc-600 dark:text-zinc-300">
                        {event.resource_type ? `${event.resource_type} #${event.resource_id}` : '—'}
                      </td>
                      <td className="px-4 py-2 text-[11px] text-zinc-500 dark:text-zinc-400 whitespace-nowrap">
                        {event.ip || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {audit.pages > 1 && (
              <footer className="px-4 py-3 border-t border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
                <span className="text-[11px] text-zinc-600 dark:text-zinc-300">
                  <Activity className="w-3 h-3 inline mr-1" />
                  {audit.total} {en ? 'events' : 'événements'}
                </span>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 text-[11px] dark:bg-zinc-800 dark:border-zinc-700"
                    disabled={audit.page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    {en ? 'Previous' : 'Précédent'}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 text-[11px] dark:bg-zinc-800 dark:border-zinc-700"
                    disabled={audit.page >= audit.pages}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    {en ? 'Next' : 'Suivant'}
                  </Button>
                </div>
              </footer>
            )}
          </>
        )}
      </Panel>
    </div>
  );
}
