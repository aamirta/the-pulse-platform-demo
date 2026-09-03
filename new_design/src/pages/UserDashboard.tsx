import { useState, useEffect, useCallback } from 'react';
import {
  Building2, Users, Shield, CheckCircle2, AlertCircle, TrendingUp,
  MessageSquare, BarChart2, Star, RefreshCw,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
} from 'recharts';
import { useTheme } from '@/hooks/useTheme';
import { useLanguage } from '@/context/LanguageContext';
import { useAuth } from '@/context/AuthContext';
import { apiGet, apiPost, apiDelete } from '@/lib/api';
import { toast } from 'sonner';

interface DashboardStat {
  key: string;
  label: string;
  value: string;
  hint: string | null;
}

interface ModerationItem {
  id: number;
  full_name: string;
  email: string;
  role: string;
  created_at: string | null;
}

interface RecentPost {
  post_id: number;
  author_name: string | null;
  content: string;
  created_at: string | null;
}

interface DashboardResponse {
  role: 'startup' | 'investor' | 'partner' | 'admin';
  stats: DashboardStat[];
  funding_by_year: { labels: string[]; values: number[] };
  moderation_queue: ModerationItem[];
  recent_posts: RecentPost[];
}

/** Icon per stat key, so the cards keep their visual rhythm as the data changes. */
const STAT_ICONS: Record<string, typeof Building2> = {
  startups: Building2,
  members: Users,
  pending_members: AlertCircle,
  posts: MessageSquare,
  profile_completeness: CheckCircle2,
  unread_messages: MessageSquare,
  my_posts: MessageSquare,
  directory: Star,
};

const ROLE_ACCENT: Record<string, string> = {
  startup: 'text-pulse-orange',
  investor: 'text-emerald-700 dark:text-emerald-400 dark:text-emerald-450',
  partner: 'text-purple-600 dark:text-purple-400',
  admin: 'text-blue-600 dark:text-blue-400',
};

export default function UserDashboard() {
  const { theme } = useTheme();
  const { t, language } = useLanguage();
  const { role: sessionRole } = useAuth();

  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<number | null>(null);

  const chartTextColor = theme === 'dark' ? '#a1a1aa' : '#52525b';
  const chartGridColor = theme === 'dark' ? '#27272a' : '#f4f4f5';

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await apiGet<DashboardResponse>('/dashboard/'));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  // Moderation actions hit the real admin endpoints, then reload from the server
  // so the queue reflects persisted state rather than an optimistic local guess.
  const moderate = async (member: ModerationItem, action: 'confirm' | 'reject') => {
    setPendingAction(member.id);
    try {
      if (action === 'confirm') {
        await apiPost(`/admin/members/${member.id}/confirm`, {});
        toast.success(`${member.full_name} ${language === 'en' ? 'confirmed' : 'confirmé'}`);
      } else {
        await apiDelete(`/admin/members/${member.id}`);
        toast.success(`${member.full_name} ${language === 'en' ? 'removed' : 'supprimé'}`);
      }
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Action failed');
    } finally {
      setPendingAction(null);
    }
  };

  const role = data?.role ?? sessionRole ?? 'startup';
  const accent = ROLE_ACCENT[role] ?? ROLE_ACCENT.startup;
  const roleLabel = {
    startup: t('roleStartupTab'),
    investor: t('roleInvestorTab'),
    partner: t('rolePartnerTab'),
    admin: t('roleAdminTab'),
  }[role];

  const fundingSeries = (data?.funding_by_year.labels ?? []).map((label, index) => ({
    year: label,
    total: data?.funding_by_year.values[index] ?? 0,
  }));

  return (
    <div className="space-y-6">

      {/* Header & server-derived role indicator */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-150 dark:border-zinc-800">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-white flex items-center gap-2">
            {t('dashboardTitle')}
          </h1>
          <p className="text-sm text-zinc-600 dark:text-zinc-300">
            {t('dashboardSubtitle')}
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-center">
          {/* The role comes from the authenticated session, so it is shown rather
              than chosen — selecting it client-side previously exposed the
              administrator view to any signed-in user. */}
          <div className="flex items-center gap-1.5 p-1 bg-zinc-100 dark:bg-zinc-800 rounded-lg">
            <span className={`px-3 py-1.5 text-xs font-semibold rounded-md bg-white dark:bg-zinc-950 shadow-sm ${accent}`}>
              {roleLabel}
            </span>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => void load()}
            disabled={loading}
            aria-label={language === 'en' ? 'Refresh dashboard' : 'Actualiser le tableau de bord'}
            className="h-8 text-xs dark:bg-zinc-800 dark:border-zinc-700"
          >
            <RefreshCw className={`w-3 h-3 mr-1 ${loading ? 'animate-spin' : ''}`} />
            {language === 'en' ? 'Refresh' : 'Actualiser'}
          </Button>
        </div>
      </div>

      {/* Error state */}
      {error && !loading && (
        <div className="bg-white dark:bg-zinc-900 border border-red-200 dark:border-red-900/50 rounded-xl p-6 text-center">
          <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
          <p className="text-sm text-zinc-700 dark:text-zinc-300 mb-3">{error}</p>
          <Button size="sm" onClick={() => void load()} className="h-8 text-xs">
            {language === 'en' ? 'Try again' : 'Réessayer'}
          </Button>
        </div>
      )}

      {/* Loading skeleton — mirrors the real card grid so the layout does not jump */}
      {loading && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[0, 1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-white dark:bg-zinc-900 p-5 rounded-xl border border-zinc-100 dark:border-zinc-800 animate-pulse"
            >
              <div className="h-3 w-24 bg-zinc-100 dark:bg-zinc-800 rounded mb-3" />
              <div className="h-6 w-16 bg-zinc-100 dark:bg-zinc-800 rounded" />
            </div>
          ))}
        </div>
      )}

      {!loading && !error && data && (
        <div className="space-y-6 animate-fade-in">

          {/* Quick stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {data.stats.map((stat) => {
              const Icon = STAT_ICONS[stat.key] ?? TrendingUp;
              const isPercent = stat.value.endsWith('%');
              return (
                <div
                  key={stat.key}
                   className="bg-white dark:bg-zinc-900 p-5 rounded-xl border border-zinc-100 dark:border-zinc-800 transition-colors duration-200 flex items-center justify-between ve-card-lift"
                >
                  <div className="min-w-0">
                    <span className="text-xs text-zinc-600 dark:text-zinc-300 block mb-1">{stat.label}</span>
                    <span className="text-2xl font-bold text-zinc-900 dark:text-white">{stat.value}</span>
                    {stat.hint && (
                      <span className="text-[11px] text-zinc-600 dark:text-zinc-300 block mt-0.5 truncate">
                        {stat.hint}
                      </span>
                    )}
                    {isPercent && (
                      <Progress
                        value={Number.parseInt(stat.value, 10) || 0}
                        className="h-2 bg-zinc-100 dark:bg-zinc-800 mt-2"
                      />
                    )}
                  </div>
                  {!isPercent && <Icon className="w-8 h-8 text-zinc-300 dark:text-zinc-700 shrink-0" />}
                </div>
              );
            })}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* Ecosystem funding chart (2 cols) */}
            <div className="lg:col-span-2 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-150 dark:border-zinc-800 p-5 transition-colors duration-200">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-zinc-900 dark:text-white flex items-center gap-1.5">
                  <BarChart2 className="w-4 h-4 text-pulse-orange" />
                  {language === 'en' ? 'Ecosystem funding by year (M$)' : 'Financement par année (M$)'}
                </h3>
              </div>
              <div className="h-64">
                {fundingSeries.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-xs text-zinc-600 dark:text-zinc-300">
                    {language === 'en' ? 'No funding data yet' : 'Aucune donnée de financement'}
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={fundingSeries} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#d56426" stopOpacity={0.2} />
                          <stop offset="95%" stopColor="#d56426" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke={chartGridColor} vertical={false} />
                      <XAxis dataKey="year" stroke={chartTextColor} fontSize={11} tickLine={false} />
                      <YAxis stroke={chartTextColor} fontSize={11} tickLine={false} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: theme === 'dark' ? '#18181b' : '#ffffff',
                          borderColor: theme === 'dark' ? '#27272a' : '#e4e4e7',
                          color: theme === 'dark' ? '#ffffff' : '#000000',
                        }}
                      />
                      <Area type="monotone" dataKey="total" stroke="#d56426" strokeWidth={2} fillOpacity={1} fill="url(#colorRev)" />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>

            {/* Side panel: moderation queue for admins, community activity otherwise */}
            <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-150 dark:border-zinc-800 p-5 transition-colors duration-200">
              {role === 'admin' ? (
                <>
                  <h3 className="text-sm font-semibold text-zinc-900 dark:text-white mb-4 flex items-center gap-1.5">
                    <Shield className="w-4 h-4 text-blue-600" />
                    {t('moderationTitle')}
                  </h3>
                  {data.moderation_queue.length === 0 ? (
                    <div className="text-center py-8">
                      <CheckCircle2 className="w-7 h-7 text-emerald-700 dark:text-emerald-400/50 mx-auto mb-2" />
                      <p className="text-xs text-zinc-600 dark:text-zinc-300">
                        {language === 'en' ? 'Nothing awaiting review' : 'Rien à traiter'}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {data.moderation_queue.map((item) => (
                        <div
                          key={item.id}
                          className="p-3 bg-zinc-50 dark:bg-zinc-800/40 rounded-lg border border-zinc-100 dark:border-zinc-800 text-xs"
                        >
                          <div className="flex justify-between items-center mb-1 gap-2">
                            <span className="font-bold text-zinc-950 dark:text-zinc-200 truncate">{item.full_name}</span>
                            <Badge className="text-[11px] px-1 bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 border-none shrink-0">
                              {item.role}
                            </Badge>
                          </div>
                          <p className="text-[11px] text-zinc-600 dark:text-zinc-300 mb-3 truncate">{item.email}</p>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              disabled={pendingAction === item.id}
                              onClick={() => void moderate(item, 'confirm')}
                              className="h-6 text-[11px] flex-1 bg-blue-600 hover:bg-blue-750 text-white rounded"
                            >
                              {t('approveButton')}
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={pendingAction === item.id}
                              onClick={() => void moderate(item, 'reject')}
                              className="h-6 text-[11px] flex-1 border-zinc-250 dark:border-zinc-700 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-350 rounded"
                            >
                              {t('rejectButton')}
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <>
                  <h3 className="text-sm font-semibold text-zinc-900 dark:text-white mb-4 flex items-center gap-1.5">
                    <MessageSquare className={`w-4 h-4 ${accent}`} />
                    {language === 'en' ? 'Latest community posts' : 'Dernières publications'}
                  </h3>
                  {data.recent_posts.length === 0 ? (
                    <div className="text-center py-8">
                      <p className="text-xs text-zinc-600 dark:text-zinc-300">
                        {language === 'en' ? 'No posts yet' : 'Aucune publication'}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {data.recent_posts.map((post) => (
                        <div
                          key={post.post_id}
                          className="p-3 bg-zinc-50 dark:bg-zinc-800/40 rounded-lg border border-zinc-100 dark:border-zinc-800"
                        >
                          <p className="text-xs font-bold text-zinc-900 dark:text-white truncate">
                            {post.author_name || (language === 'en' ? 'Member' : 'Membre')}
                          </p>
                          <p className="text-[11px] text-zinc-600 dark:text-zinc-300 mt-1 line-clamp-2">
                            {post.content}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
