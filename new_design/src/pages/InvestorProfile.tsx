import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, MapPin, Globe, Landmark, TrendingUp, ChevronRight, Activity, PieChart as PieIcon, BarChart3 as BarIcon } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { FadeInImage } from '@/enhancements/FadeInImage';
import { Button } from '@/components/ui/button';
import MessageButton from '@/components/messaging/MessageButton';
import { Badge } from '@/components/ui/badge';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { useTheme } from '@/hooks/useTheme';
import { useLanguage } from '@/context/LanguageContext';
import { useInvestor } from '@/hooks/useInvestor';
import { useStartups } from '@/hooks/useStartups';
import { openExternal } from '@/lib/url';

export default function InvestorProfile() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { theme } = useTheme();
  // Matches the palette used by UserDashboard/Analytics; these were referenced
  // by the charts below but never defined, which broke the type build.
  const chartTextColor = theme === 'dark' ? '#a1a1aa' : '#52525b';
  const chartGridColor = theme === 'dark' ? '#27272a' : '#f4f4f5';
  const { t, language } = useLanguage();
  const { data: investor, isLoading: investorLoading } = useInvestor(id);
  const { data: startups = [] } = useStartups();

  if (investorLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-40 rounded-xl" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, idx) => (
            <Skeleton key={idx} className="h-24 rounded-xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-72 rounded-xl" />
          <Skeleton className="h-72 rounded-xl" />
        </div>
      </div>
    );
  }

  if (!investor) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-zinc-900 dark:text-white">{t('investorNotFound')}</h2>
        <Button onClick={() => navigate('/investors')} className="mt-4 bg-pulse-orange hover:bg-pulse-orange-hover text-white">
          {t('backToInvestors')}
        </Button>
      </div>
    );
  }

  // Portfolio is matched on the investor's declared focus sectors. Hardcoded
  // per-investor allowlists ("212-founders" -> woliz/chari/inyad) used to
  // override this with relationships that are not recorded anywhere.
  const portfolioStartups = startups.filter((s) =>
    s.sector.some((sec) => investor.focus.includes(sec)),
  );

  // Charts below are derived from that real portfolio rather than fixed figures.
  const CHART_COLORS = ['#d56426', '#3b82f6', '#10b981', '#a855f7', '#f59e0b', '#a855f7'];

  const sectorCounts = new Map<string, number>();
  portfolioStartups.forEach((s) =>
    s.sector.forEach((sec) => sectorCounts.set(sec, (sectorCounts.get(sec) ?? 0) + 1)),
  );
  const sectorData = [...sectorCounts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([name, value], index) => ({ name, value, color: CHART_COLORS[index % CHART_COLORS.length] }));

  const stageCounts = new Map<string, number>();
  portfolioStartups.forEach((s) => {
    const stage = s.stage?.trim();
    if (stage) stageCounts.set(stage, (stageCounts.get(stage) ?? 0) + 1);
  });
  const stageData = [...stageCounts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([stage, count]) => ({ stage, count }));

  return (
    <div className="space-y-6">
      {/* Back */}
      <button
        onClick={() => navigate('/investors')}
        className="inline-flex items-center gap-1.5 min-h-11 px-1 -ml-1 rounded text-sm text-zinc-500 hover:text-pulse-orange transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
      >
        <ArrowLeft className="w-4 h-4" />
        {t('backToInvestors')}
      </button>

      {/* Main Profile Info Card */}
      <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 p-6 transition-colors duration-200 ve-card-lift">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-xl overflow-hidden flex items-center justify-center flex-shrink-0 bg-white dark:bg-zinc-800 border border-zinc-150 dark:border-zinc-700/50">
              {investor.logo ? (
                <FadeInImage src={investor.logo} alt={investor.name} className="w-full h-full object-contain p-2" />
              ) : (
                <div className="w-full h-full bg-gradient-to-br from-emerald-50 to-emerald-100 dark:from-emerald-950/40 dark:to-emerald-900/10 flex items-center justify-center">
                  <Landmark className="w-8 h-8 text-emerald-600 dark:text-emerald-450" />
                </div>
              )}
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">{investor.name}</h1>
                <Badge className="bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-450 font-semibold border-none text-[10px]">
                  {investor.type}
                </Badge>
              </div>
              <div className="flex items-center gap-2 mt-1 text-sm text-zinc-500 dark:text-zinc-400">
                <MapPin className="w-4 h-4 text-zinc-400" />
                {investor.location}
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <MessageButton
              entityType="investor"
                showWhenUnavailable
              entityId={id}
              name={investor.name}
              className="h-9 px-4 text-xs dark:bg-zinc-800 dark:border-zinc-750 dark:hover:bg-zinc-700"
            />
            {investor.website && (
              <Button
                variant="outline"
                size="sm"
                className="h-9 px-4 text-xs dark:bg-zinc-800 dark:border-zinc-750 dark:hover:bg-zinc-700"
                onClick={() => openExternal(investor.website)}
              >
                <Globe className="w-3.5 h-3.5 mr-1.5" />
                {t('websiteButton')}
              </Button>
            )}
            <Button
              className="h-9 px-4 text-xs bg-pulse-orange hover:bg-pulse-orange-hover text-white rounded-lg"
              onClick={() => navigate(`/visualizer?highlight=${investor.id}`)}
            >
              {t('viewNetworkMap')}
            </Button>
          </div>
        </div>

        {/* Sectors Focus Badges */}
        <div className="border-t border-zinc-50 dark:border-zinc-800 pt-4">
          <span className="text-xs font-semibold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider block mb-2">
            {t('preferredSectors')}
          </span>
          <div className="flex flex-wrap gap-2">
            {investor.focus.map((sector) => (
              <Badge
                key={sector}
                variant="outline"
                className="text-xs font-medium border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-350"
              >
                {sector}
              </Badge>
            ))}
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-zinc-900 p-5 rounded-xl border border-zinc-100 dark:border-zinc-800 transition-colors duration-200 ve-card-lift">
          <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400 block mb-1">{language === 'en' ? 'Number of Deals' : 'Nombre de Deals'}</span>
          <span className="text-2xl font-bold text-zinc-900 dark:text-white">{investor.investments}</span>
        </div>
        <div className="bg-white dark:bg-zinc-900 p-5 rounded-xl border border-zinc-100 dark:border-zinc-800 transition-colors duration-200 ve-card-lift">
          <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400 block mb-1">{language === 'en' ? 'Active Startups' : 'Startups Actives'}</span>
          <span className="text-2xl font-bold text-zinc-900 dark:text-white">{investor.portfolio}</span>
        </div>
        <div className="bg-white dark:bg-zinc-900 p-5 rounded-xl border border-zinc-100 dark:border-zinc-800 transition-colors duration-200 ve-card-lift">
          <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400 block mb-1">{language === 'en' ? 'Average Ticket' : 'Ticket Moyen'}</span>
          <span className="text-2xl font-bold text-zinc-900 dark:text-white">$250k - $1.5M</span>
        </div>
        <div className="bg-white dark:bg-zinc-900 p-5 rounded-xl border border-zinc-100 dark:border-zinc-800 transition-colors duration-200 ve-card-lift">
          <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400 block mb-1">{language === 'en' ? 'Geo Focus' : 'Focus Géographique'}</span>
          <span className="text-2xl font-bold text-zinc-900 dark:text-white">Morocco & MENA</span>
        </div>
      </div>

      {/* Analytics Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sector Allocation */}
        <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 p-5 transition-colors duration-200">
          <h3 className="text-sm font-semibold text-zinc-900 dark:text-white mb-4 flex items-center gap-1.5">
            <PieIcon className="w-4 h-4 text-pulse-orange" />
            {language === 'en' ? 'Sector Breakdown (%)' : 'Répartition par Secteurs (%)'}
          </h3>
          <div className="h-60 flex items-center">
            <div className="w-[60%] h-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={sectorData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {sectorData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: theme === 'dark' ? '#18181b' : '#ffffff',
                      borderColor: theme === 'dark' ? '#27272a' : '#e4e4e7',
                      color: theme === 'dark' ? '#ffffff' : '#000000'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="w-[40%] space-y-2 text-xs">
              {sectorData.map((item, index) => (
                <div key={index} className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: item.color }} />
                  <span className="text-zinc-500 dark:text-zinc-400 truncate">{item.name}</span>
                  <span className="font-semibold text-zinc-900 dark:text-white ml-auto">{item.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Investment Stage Preferences */}
        <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 p-5 transition-colors duration-200">
          <h3 className="text-sm font-semibold text-zinc-900 dark:text-white mb-4 flex items-center gap-1.5">
            <BarIcon className="w-4 h-4 text-pulse-orange" />
            {language === 'en' ? 'Investments by Stage' : "Nombre d'investissements par Stage"}
          </h3>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stageData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={chartGridColor} vertical={false} />
                <XAxis dataKey="stage" stroke={chartTextColor} fontSize={11} tickLine={false} />
                <YAxis stroke={chartTextColor} fontSize={11} tickLine={false} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: theme === 'dark' ? '#18181b' : '#ffffff',
                    borderColor: theme === 'dark' ? '#27272a' : '#e4e4e7',
                    color: theme === 'dark' ? '#ffffff' : '#000000'
                  }}
                />
                <Bar dataKey="count" fill="#d56426" radius={[4, 4, 0, 0]} maxBarSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Portfolio Companies & Recent Investments */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Active Portfolio (2 Cols) */}
        <div className="lg:col-span-2 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 p-5 transition-colors duration-200">
          <h3 className="text-base font-semibold text-zinc-900 dark:text-white mb-4 flex items-center gap-1.5">
            <TrendingUp className="w-4.5 h-4.5 text-pulse-orange" />
            {t('portfolioStartupsTitle')} ({portfolioStartups.length})
          </h3>
          {portfolioStartups.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {portfolioStartups.map((s) => (
                <div
                  key={s.id}
                  onClick={() => navigate(`/startups/${s.id}`)}
                  className="flex items-center gap-3 p-3 bg-zinc-50 dark:bg-zinc-800/40 hover:bg-zinc-100 dark:hover:bg-zinc-800/80 border border-zinc-100 dark:border-zinc-800 rounded-lg cursor-pointer transition-colors group"
                >
                  <div className="w-8 h-8 rounded-lg overflow-hidden flex items-center justify-center flex-shrink-0 bg-white dark:bg-zinc-800 border border-zinc-150 dark:border-zinc-700/50">
                    {s.logo ? (
                      <FadeInImage src={s.logo} alt={s.name} className="w-full h-full object-contain p-1" />
                    ) : (
                      <div className="w-full h-full bg-gradient-to-br from-pulse-orange-50 to-orange-100 dark:from-orange-950/40 dark:to-orange-900/10 flex items-center justify-center font-bold text-pulse-orange text-xs">
                        {s.name[0]}
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="text-xs font-bold text-zinc-900 dark:text-white group-hover:text-pulse-orange transition-colors truncate">
                      {s.name}
                    </h4>
                    <p className="text-[10px] text-zinc-500 dark:text-zinc-400 truncate">
                      {s.sector.join(', ')}
                    </p>
                  </div>
                  <ChevronRight className="w-3.5 h-3.5 text-zinc-400 group-hover:text-pulse-orange transition-colors" />
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-xs text-zinc-500 dark:text-zinc-455">
              {language === 'en' ? 'No portfolio startups listed yet.' : 'Aucune startup du portefeuille référencée pour le moment.'}
            </div>
          )}
        </div>

        {/* A "recent investments" timeline was rendered here from hardcoded
            rounds (woliZ 2.2M$, KoolSkools 1.5M$, ...) attributed to this
            investor. Per-investor deal history is not recorded, so the panel now
            summarises the real matched portfolio instead. */}
        <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 p-5 transition-colors duration-200">
          <h3 className="text-sm font-semibold text-zinc-900 dark:text-white mb-4 flex items-center gap-1.5">
            <Activity className="w-4 h-4 text-pulse-orange" />
            {language === 'en' ? 'Focus sectors' : 'Secteurs de focus'}
          </h3>
          {investor.focus.length === 0 ? (
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              {language === 'en' ? 'No focus sectors recorded.' : 'Aucun secteur renseigné.'}
            </p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {investor.focus.map((sector) => (
                <span
                  key={sector}
                  className="text-[10px] px-2 py-1 bg-zinc-50 dark:bg-zinc-800/40 border border-zinc-100 dark:border-zinc-800 rounded text-zinc-700 dark:text-zinc-300"
                >
                  {sector}
                </span>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
