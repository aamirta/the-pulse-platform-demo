import { useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Activity,
  BarChart3,
  Building2,
  FileText,
  FolderLock,
  Globe,
  Inbox,
  Linkedin,
  Loader2,
  Lock,
  Megaphone,
  MessagesSquare,
  Settings2,
  ShieldCheck,
  Users,
} from 'lucide-react';
import { apiGet } from '@/lib/api';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAuth } from '@/context/AuthContext';
import { useLanguage } from '@/context/LanguageContext';
import { useMyDealRooms } from '@/hooks/useDealRoom';
import type {
  DealRoomDocument,
  DealRoomOverview,
  DealRoomSummary,
  PagedDocuments,
} from '@/types/dealroom';
import DealRoomDocuments from '@/components/dealroom/DealRoomDocuments';
import DealRoomInsights from '@/components/dealroom/DealRoomInsights';
import DealRoomInvestors from '@/components/dealroom/DealRoomInvestors';
import DealRoomQA from '@/components/dealroom/DealRoomQA';
import DealRoomRequests from '@/components/dealroom/DealRoomRequests';
import DealRoomSettings, { NdaGate } from '@/components/dealroom/DealRoomSettings';
import OpportunityBoard from '@/components/dealroom/posts/OpportunityBoard';
import {
  EmptyState,
  ErrorState,
  Panel,
  PermissionBadge,
  RowSkeleton,
  StatCard,
  StatusPill,
  auditActionLabel,
  auditActionTone,
  formatDateTime,
} from '@/components/dealroom/shared';

type Mode = 'opportunities' | 'rooms';
type TabKey = 'overview' | 'documents' | 'investors' | 'requests' | 'qa' | 'insights' | 'settings';

/**
 * The subset of the public startup record worth showing beside the documents.
 *
 * An investor opening a data room needs to know *which company* they are looking
 * at before they open a single file; the room previously showed counters and a
 * name and nothing else. Everything here already appears on the public startup
 * profile, so surfacing it discloses nothing new — contact details and registry
 * numbers are deliberately left out as noise rather than substance.
 */
interface StartupSnapshot {
  id: string;
  name: string;
  description: string | null;
  sector: string[] | null;
  stage: string | null;
  status: string | null;
  location: string | null;
  region: string | null;
  teamSize: string | null;
  yearFounded: number | string | null;
  website: string | null;
  linkedin: string | null;
  forme_juridique: string | null;
  total_funding_usd: number | null;
  valuation: number | null;
}

/**
 * Deal Room.
 *
 * One page for both sides of the table. Which tabs exist, and what each one
 * shows, follows `viewer_role` as resolved by the API — the client never picks
 * its own role, and hiding a tab is presentation only: every endpoint behind it
 * re-checks authorization independently.
 */
export default function DealRoom() {
  const { member, user, isBootstrapping } = useAuth();
  const { language } = useLanguage();
  const en = language === 'en';

  const [searchParams, setSearchParams] = useSearchParams();
  const { rooms, loading: loadingRooms, error: roomsError, reload: reloadRooms } = useMyDealRooms();

  const [roomId, setRoomId] = useState<number | null>(null);
  const [room, setRoom] = useState<DealRoomSummary | null>(null);
  const [overview, setOverview] = useState<DealRoomOverview | null>(null);
  const [documents, setDocuments] = useState<DealRoomDocument[]>([]);
  const [company, setCompany] = useState<StartupSnapshot | null>(null);
  const [loadingRoom, setLoadingRoom] = useState(false);
  const [roomError, setRoomError] = useState<string | null>(null);

  const tab = (searchParams.get('tab') as TabKey) || 'overview';
  const setTab = (next: TabKey) => {
    const params = new URLSearchParams(searchParams);
    params.set('tab', next);
    setSearchParams(params, { replace: true });
  };

  // Which half of the Deal Room is showing. The marketplace is the front door:
  // it is the only half a member without a room of their own can use, and
  // arriving at an empty private room was the old dead end.
  const mode: Mode = searchParams.get('view') === 'rooms' ? 'rooms' : 'opportunities';
  const setMode = (next: Mode) => {
    const params = new URLSearchParams(searchParams);
    if (next === 'rooms') params.set('view', 'rooms');
    else params.delete('view');
    setSearchParams(params, { replace: true });
  };

  // Pick the room from the URL when present, otherwise the first one available.
  useEffect(() => {
    if (roomId !== null || rooms.length === 0) return;
    const requested = Number(searchParams.get('room'));
    const match = rooms.find((r) => r.id === requested);
    setRoomId(match ? match.id : rooms[0].id);
  }, [rooms, roomId, searchParams]);

  const isManager = room?.viewer_role === 'startup' || room?.viewer_role === 'admin';

  const loadRoom = useCallback(async () => {
    if (roomId === null) return;
    setLoadingRoom(true);
    setRoomError(null);
    try {
      const summary = await apiGet<DealRoomSummary>(`/deal-rooms/${roomId}`);
      setRoom(summary);

      const manager = summary.viewer_role === 'startup' || summary.viewer_role === 'admin';
      // The overview endpoint is startup-side; asking for it as an investor
      // would be a guaranteed 403, so it is simply not requested.
      const [counters, docs, profile] = await Promise.all([
        manager
          ? apiGet<DealRoomOverview>(`/deal-rooms/${roomId}/overview`).catch(() => null)
          : Promise.resolve(null),
        apiGet<PagedDocuments>(`/deal-rooms/${roomId}/documents?page_size=100`).catch(() => null),
        // Public directory data; a room whose startup row is missing still opens.
        apiGet<StartupSnapshot>(`/startups/${summary.startup_id}`).catch(() => null),
      ]);
      setOverview(counters);
      setDocuments(docs?.items ?? []);
      setCompany(profile);
    } catch (err) {
      setRoomError(err instanceof Error ? err.message : 'Failed to load this deal room');
      setRoom(null);
    } finally {
      setLoadingRoom(false);
    }
  }, [roomId]);

  useEffect(() => {
    void loadRoom();
  }, [loadRoom]);

  const tabs = useMemo(() => {
    const base: { key: TabKey; label: string; icon: typeof FileText; badge?: number }[] = [
      { key: 'overview', label: en ? 'Overview' : 'Aperçu', icon: Activity },
      { key: 'documents', label: en ? 'Documents' : 'Documents', icon: FileText },
      { key: 'qa', label: en ? 'Q&A' : 'Questions', icon: MessagesSquare },
    ];
    if (isManager) {
      base.splice(2, 0, { key: 'investors', label: en ? 'Investors' : 'Investisseurs', icon: Users });
      base.splice(3, 0, {
        key: 'requests',
        label: en ? 'Requests' : 'Demandes',
        icon: Inbox,
        badge: overview?.pending_access_requests,
      });
      base.push({ key: 'insights', label: en ? 'Insights' : 'Analyses', icon: BarChart3 });
      base.push({ key: 'settings', label: en ? 'Settings' : 'Paramètres', icon: Settings2 });
    }
    return base;
  }, [isManager, en, overview?.pending_access_requests]);

  if (isBootstrapping) {
    return <RowSkeleton rows={4} />;
  }

  // The marketplace stands on its own: it needs no room, and it is what a
  // member without one comes here for. Rendered before every private-room
  // branch below so an empty room list never blocks it.
  if (mode === 'opportunities') {
    return (
      <PageShell language={language} mode={mode} onModeChange={setMode}>
        <OpportunityBoard language={language} />
      </PageShell>
    );
  }

  if (!member && !user) {
    return (
      <PageShell language={language} mode={mode} onModeChange={setMode}>
        <Panel>
          <EmptyState
            icon={Lock}
            title={en ? 'Sign in required' : 'Connexion requise'}
            description={
              en
                ? 'Deal Rooms are private. Sign in to open the ones shared with you.'
                : 'Les Deal Rooms sont privées. Connectez-vous pour accéder aux vôtres.'
            }
          />
        </Panel>
      </PageShell>
    );
  }

  if (loadingRooms) {
    return (
      <PageShell language={language} mode={mode} onModeChange={setMode}>
        <RowSkeleton rows={4} />
      </PageShell>
    );
  }

  if (roomsError) {
    return (
      <PageShell language={language} mode={mode} onModeChange={setMode}>
        <Panel>
          <ErrorState
            message={roomsError}
            onRetry={() => void reloadRooms()}
            retryLabel={en ? 'Try again' : 'Réessayer'}
          />
        </Panel>
      </PageShell>
    );
  }

  if (rooms.length === 0) {
    return (
      <PageShell language={language} mode={mode} onModeChange={setMode}>
        <Panel>
          <EmptyState
            icon={Building2}
            title={en ? 'No Deal Room yet' : 'Aucune Deal Room'}
            description={
              en
                ? 'A Deal Room is your private space for sharing fundraising materials with selected investors. Startups get one once their company profile is claimed and approved; investors see rooms they have been admitted to.'
                : "La Deal Room est votre espace privé pour partager vos documents de levée avec des investisseurs choisis. Les startups en obtiennent une après validation de leur profil ; les investisseurs voient celles auxquelles ils sont admis."
            }
          />
        </Panel>
      </PageShell>
    );
  }

  return (
    <PageShell
      language={language}
      mode={mode}
      onModeChange={setMode}
      right={
        rooms.length > 1 ? (
          <Select
            value={String(roomId ?? '')}
            onValueChange={(value) => {
              setRoomId(Number(value));
              const params = new URLSearchParams(searchParams);
              params.set('room', value);
              setSearchParams(params, { replace: true });
            }}
          >
            <SelectTrigger className="h-9 w-[240px] text-xs dark:bg-zinc-900">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {rooms.map((r) => (
                <SelectItem key={r.id} value={String(r.id)}>
                  {r.startup_name ?? r.name ?? `Deal Room #${r.id}`}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : undefined
      }
    >
      {loadingRoom && !room ? (
        <RowSkeleton rows={4} />
      ) : roomError || !room ? (
        <Panel>
          <ErrorState
            message={roomError ?? (en ? 'Deal room unavailable' : 'Deal Room indisponible')}
            onRetry={() => void loadRoom()}
            retryLabel={en ? 'Try again' : 'Réessayer'}
          />
        </Panel>
      ) : (
        <div className="space-y-4">
          {/* Room identity and security posture */}
          <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 p-4 flex flex-col sm:flex-row sm:items-center gap-3 justify-between">
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-base font-semibold text-zinc-900 dark:text-white truncate">
                  {room.startup_name ?? room.name}
                </h2>
                <StatusPill status={room.status} language={language} />
                {!isManager && (
                  <PermissionBadge permission={room.viewer_permission} language={language} />
                )}
              </div>
              <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-1 flex items-center gap-3 flex-wrap">
                {room.watermark_enabled && (
                  <span className="inline-flex items-center gap-1">
                    <ShieldCheck className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
                    {en ? 'Watermarking on' : 'Filigrane activé'}
                  </span>
                )}
                {room.nda_required && (
                  <span className="inline-flex items-center gap-1">
                    <Lock className="w-3 h-3 text-amber-600 dark:text-amber-400" />
                    {en ? 'NDA required' : 'NDA requis'}
                  </span>
                )}
                <span>
                  {room.allow_downloads
                    ? en ? 'Downloads allowed' : 'Téléchargements autorisés'
                    : en ? 'Downloads disabled' : 'Téléchargements désactivés'}
                </span>
              </p>
            </div>
          </div>

          {/* Tabs */}
          <nav
            className="flex gap-1 overflow-x-auto border-b border-zinc-150 dark:border-zinc-800 -mb-px"
            role="tablist"
            aria-label={en ? 'Deal Room sections' : 'Sections de la Deal Room'}
          >
            {tabs.map(({ key, label, icon: Icon, badge }) => (
              <button
                key={key}
                role="tab"
                aria-selected={tab === key}
                onClick={() => setTab(key)}
                className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium whitespace-nowrap border-b-2 transition-colors ${
                  tab === key
                    ? 'border-pulse-orange text-pulse-orange'
                    : 'border-transparent text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-zinc-200'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
                {badge ? (
                  <span className="ml-0.5 bg-pulse-orange text-white text-[9px] font-bold min-w-[16px] h-4 px-1 rounded-full grid place-items-center">
                    {badge}
                  </span>
                ) : null}
              </button>
            ))}
          </nav>

          {/* An investor who has not signed sees the agreement instead of content. */}
          {!isManager && room.nda_required && !room.nda_satisfied && tab !== 'overview' ? (
            <NdaGate room={room} language={language} onAccepted={() => void loadRoom()} />
          ) : (
            <div className="animate-fade-in ve-view-enter" key={tab}>
              {tab === 'overview' && (
                <OverviewTab
                  room={room}
                  overview={overview}
                  company={company}
                  documentCount={documents.length}
                  language={language}
                  onOpenDocuments={() => setTab('documents')}
                  onAcceptNda={() => void loadRoom()}
                />
              )}
              {tab === 'documents' && (
                <DealRoomDocuments room={room} language={language} onChanged={() => void loadRoom()} />
              )}
              {tab === 'investors' && isManager && (
                <DealRoomInvestors room={room} language={language} onChanged={() => void loadRoom()} />
              )}
              {tab === 'requests' && isManager && (
                <DealRoomRequests room={room} language={language} onChanged={() => void loadRoom()} />
              )}
              {tab === 'qa' && (
                <DealRoomQA
                  room={room}
                  language={language}
                  documents={documents}
                  onChanged={() => void loadRoom()}
                />
              )}
              {tab === 'insights' && isManager && (
                <DealRoomInsights room={room} language={language} />
              )}
              {tab === 'settings' && isManager && (
                <DealRoomSettings room={room} language={language} onChanged={() => void loadRoom()} />
              )}
            </div>
          )}
        </div>
      )}
    </PageShell>
  );
}

/** One label/value row in the company panel; renders nothing when empty. */
function Fact({ label, children }: { label: string; children: React.ReactNode }) {
  if (children === null || children === undefined || children === '') return null;
  return (
    <div className="min-w-0">
      <dt className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wide">{label}</dt>
      <dd className="text-[13px] text-zinc-800 dark:text-zinc-100 mt-0.5 truncate">{children}</dd>
    </div>
  );
}

/** Normalise the loose `www.example.com` values the directory stores. */
function externalHref(value: string | null): string | null {
  if (!value) return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  const candidate = /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
  try {
    const url = new URL(candidate);
    return url.protocol === 'http:' || url.protocol === 'https:' ? url.toString() : null;
  } catch {
    return null;
  }
}

/**
 * Who the deal is about.
 *
 * Sits above the documents on the Overview because "what is this company"
 * precedes "what did they send me" in every real diligence conversation.
 */
function CompanyPanel({ company, language }: { company: StartupSnapshot; language: string }) {
  const en = language === 'en';
  const site = externalHref(company.website);
  const linkedin = externalHref(company.linkedin);
  const sectors = (company.sector ?? []).filter(Boolean);

  return (
    <Panel title={en ? 'Company' : 'Entreprise'}>
      <div className="p-5 space-y-4">
        {company.description && (
          <p className="text-[13px] leading-relaxed text-zinc-600 dark:text-zinc-300">
            {company.description}
          </p>
        )}

        {sectors.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {sectors.map((sector) => (
              <span
                key={sector}
                className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-pulse-orange-50 dark:bg-zinc-800 text-pulse-orange"
              >
                {sector}
              </span>
            ))}
          </div>
        )}

        <dl className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-x-4 gap-y-3">
          <Fact label={en ? 'Stage' : 'Stade'}>{company.stage}</Fact>
          <Fact label={en ? 'Status' : 'Statut'}>{company.status}</Fact>
          <Fact label={en ? 'Location' : 'Localisation'}>
            {[company.location, company.region].filter(Boolean).join(' · ') || null}
          </Fact>
          <Fact label={en ? 'Team' : 'Équipe'}>{company.teamSize}</Fact>
          <Fact label={en ? 'Founded' : 'Créée en'}>{company.yearFounded}</Fact>
          <Fact label={en ? 'Legal form' : 'Forme juridique'}>{company.forme_juridique}</Fact>
          <Fact label={en ? 'Total raised' : 'Total levé'}>
            {company.total_funding_usd ? `$${company.total_funding_usd.toLocaleString()}` : null}
          </Fact>
          <Fact label={en ? 'Valuation' : 'Valorisation'}>
            {company.valuation ? `$${company.valuation.toLocaleString()}` : null}
          </Fact>
        </dl>

        {(site || linkedin) && (
          <div className="flex flex-wrap gap-2 pt-1">
            {site && (
              <Button asChild size="sm" variant="outline" className="h-8 text-[11px] dark:bg-zinc-800 dark:border-zinc-700">
                <a href={site} target="_blank" rel="noopener noreferrer">
                  <Globe className="w-3 h-3 mr-1.5" />
                  {en ? 'Website' : 'Site web'}
                </a>
              </Button>
            )}
            {linkedin && (
              <Button asChild size="sm" variant="outline" className="h-8 text-[11px] dark:bg-zinc-800 dark:border-zinc-700">
                <a href={linkedin} target="_blank" rel="noopener noreferrer">
                  <Linkedin className="w-3 h-3 mr-1.5" />
                  LinkedIn
                </a>
              </Button>
            )}
          </div>
        )}
      </div>
    </Panel>
  );
}

function PageShell({
  language,
  mode,
  onModeChange,
  right,
  children,
}: {
  language: string;
  mode: Mode;
  onModeChange: (next: Mode) => void;
  right?: React.ReactNode;
  children: React.ReactNode;
}) {
  const en = language === 'en';
  const marketplace = mode === 'opportunities';
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-150 dark:border-zinc-800">
        <div className="min-w-0">
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">Deal Room</h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            {marketplace
              ? en
                ? 'Find the people you need, and let them find you.'
                : 'Trouvez les personnes dont vous avez besoin, et laissez-les vous trouver.'
              : en
                ? 'Share fundraising materials with selected investors, under your control.'
                : 'Partagez vos documents de levée avec des investisseurs choisis, sous votre contrôle.'}
          </p>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          {/* The two halves: the open board, and the private rooms behind it. */}
          <div
            className="inline-flex p-0.5 rounded-lg bg-zinc-100 dark:bg-zinc-850 border border-zinc-150 dark:border-zinc-800"
            role="tablist"
            aria-label={en ? 'Deal Room view' : 'Vue Deal Room'}
          >
            {(
              [
                { key: 'opportunities' as Mode, label: en ? 'Opportunities' : 'Opportunités', icon: Megaphone },
                { key: 'rooms' as Mode, label: en ? 'Data rooms' : 'Data rooms', icon: FolderLock },
              ] as const
            ).map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                type="button"
                role="tab"
                aria-selected={mode === key}
                onClick={() => onModeChange(key)}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  mode === key
                    ? 'bg-white dark:bg-zinc-900 text-pulse-orange shadow-sm'
                    : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-zinc-200'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
              </button>
            ))}
          </div>
          {right}
        </div>
      </div>
      {children}
    </div>
  );
}

function OverviewTab({
  room,
  overview,
  company,
  documentCount,
  language,
  onOpenDocuments,
  onAcceptNda,
}: {
  room: DealRoomSummary;
  overview: DealRoomOverview | null;
  company: StartupSnapshot | null;
  documentCount: number;
  language: string;
  onOpenDocuments: () => void;
  onAcceptNda: () => void;
}) {
  const en = language === 'en';
  const isManager = room.viewer_role === 'startup' || room.viewer_role === 'admin';

  if (!isManager) {
    return (
      <div className="space-y-4">
        {room.nda_required && !room.nda_satisfied ? (
          <NdaGate room={room} language={language} onAccepted={onAcceptNda} />
        ) : (
          <>
            {company && <CompanyPanel company={company} language={language} />}
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
              <StatCard
                label={en ? 'Documents shared' : 'Documents partagés'}
                value={documentCount}
                icon={FileText}
              />
              <StatCard
                label={en ? 'Your access' : 'Votre accès'}
                value={room.allow_downloads ? (en ? 'Full' : 'Complet') : en ? 'View only' : 'Lecture'}
                hint={room.watermark_enabled ? (en ? 'Watermarked' : 'Filigrané') : undefined}
                icon={ShieldCheck}
              />
              <StatCard
                label={en ? 'NDA' : 'NDA'}
                value={
                  room.nda_required
                    ? room.nda_satisfied
                      ? en ? 'Signed' : 'Signé'
                      : en ? 'Pending' : 'En attente'
                    : en ? 'Not required' : 'Non requis'
                }
                icon={Lock}
                tone={room.nda_required && !room.nda_satisfied ? 'warning' : 'success'}
              />
            </div>
            <Panel>
              <div className="p-5 flex flex-col sm:flex-row sm:items-center gap-3 justify-between">
                <div>
                  <p className="text-sm font-medium text-zinc-900 dark:text-white">
                    {en ? 'Review the materials' : 'Consultez les documents'}
                  </p>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                    {en
                      ? 'Everything the startup has shared with you, in one place.'
                      : 'Tout ce que la startup a partagé avec vous, au même endroit.'}
                  </p>
                </div>
                <Button
                  size="sm"
                  className="h-9 text-xs bg-pulse-orange hover:bg-pulse-orange-hover text-white"
                  onClick={onOpenDocuments}
                >
                  <FileText className="w-3.5 h-3.5 mr-1.5" />
                  {en ? 'Open documents' : 'Voir les documents'}
                </Button>
              </div>
            </Panel>
          </>
        )}
      </div>
    );
  }

  if (!overview) {
    return (
      <Panel>
        <div className="p-6 flex justify-center">
          <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
        </div>
      </Panel>
    );
  }

  return (
    <div className="space-y-4">
      {company && <CompanyPanel company={company} language={language} />}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label={en ? 'Investors' : 'Investisseurs'}
          value={overview.investor_count}
          hint={`${overview.active_investor_count} ${en ? 'active' : 'actifs'}`}
          icon={Users}
        />
        <StatCard
          label={en ? 'Documents' : 'Documents'}
          value={overview.document_count}
          hint={`${overview.documents_viewed} ${en ? 'viewed' : 'consultés'}`}
          icon={FileText}
        />
        <StatCard
          label={en ? 'Pending requests' : 'Demandes en attente'}
          value={overview.pending_access_requests}
          icon={Inbox}
          tone={overview.pending_access_requests > 0 ? 'warning' : 'default'}
        />
        <StatCard
          label={en ? 'Engagement' : 'Engagement'}
          value={`${overview.engagement_score}%`}
          hint={
            overview.last_activity_at
              ? `${en ? 'Last activity' : 'Dernière activité'} ${formatDateTime(overview.last_activity_at, language)}`
              : en ? 'No activity yet' : 'Aucune activité'
          }
          icon={Activity}
        />
      </div>

      {overview.documents_never_viewed > 0 && (
        <div className="rounded-xl border border-amber-200 dark:border-amber-900/50 bg-amber-50/60 dark:bg-amber-950/30 px-4 py-3 flex items-center gap-2">
          <Activity className="w-4 h-4 text-amber-600 dark:text-amber-400 flex-shrink-0" />
          <p className="text-xs text-amber-800 dark:text-amber-300">
            {en
              ? `${overview.documents_never_viewed} document(s) have never been opened by any investor.`
              : `${overview.documents_never_viewed} document(s) n'ont jamais été ouverts.`}
          </p>
        </div>
      )}

      <Panel title={en ? 'Recent activity' : 'Activité récente'}>
        {overview.recent_activity.length === 0 ? (
          <EmptyState
            icon={Activity}
            title={en ? 'Nothing yet' : 'Rien pour le moment'}
            description={
              en
                ? 'Invite an investor and publish your first documents to get started.'
                : 'Invitez un investisseur et publiez vos premiers documents pour commencer.'
            }
          />
        ) : (
          <ul className="divide-y divide-zinc-50 dark:divide-zinc-800/60">
            {overview.recent_activity.map((event) => {
              const tone = auditActionTone(event.action);
              return (
                <li key={event.id} className="px-4 py-2.5 flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-[13px] text-zinc-800 dark:text-zinc-100 truncate">
                      <span
                        className={`font-medium ${
                          tone === 'danger'
                            ? 'text-red-600 dark:text-red-400'
                            : tone === 'warning'
                              ? 'text-amber-600 dark:text-amber-400'
                              : 'text-zinc-900 dark:text-white'
                        }`}
                      >
                        {auditActionLabel(event.action, language)}
                      </span>
                      <span className="text-zinc-400 mx-1.5">·</span>
                      <span className="text-zinc-500 dark:text-zinc-400">{event.actor_email}</span>
                    </p>
                  </div>
                  <span className="text-[11px] text-zinc-400 flex-shrink-0">
                    {formatDateTime(event.created_at, language)}
                  </span>
                </li>
              );
            })}
          </ul>
        )}
      </Panel>
    </div>
  );
}
