import { useEffect, useMemo, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
} from 'recharts';
import { TrendingUp, TrendingDown, Loader2, AlertCircle } from 'lucide-react';
import { useTheme } from '@/hooks/useTheme';
import { useLanguage } from '@/context/LanguageContext';
import { apiGet } from '@/lib/api';

interface ChartSeries {
  labels: string[];
  values: (number | string)[];
}

interface HomeStats {
  startups: number;
  founders: number;
  investors: number;
  incubators: number;
  totalFunding: string;
  opportunities: number;
  sectors: number;
  cities: number;
  fundingRounds: number;
}

interface TrendItem {
  tag: string;
  count: number;
}

interface StatsResponse {
  counts: HomeStats;
  trends: TrendItem[];
  fundingByStage: ChartSeries;
  fundingByYear: ChartSeries;
  topSectors: ChartSeries;
  topFundedStartups: ChartSeries | null;
  fundingBySector: ChartSeries | null;
}

const COLORS = ['#b8521c', '#d56426', '#e07b43', '#f0a878', '#fde4cf', '#f59e0b', '#a855f7', '#3b82f6', '#10b981', '#a855f7'];

export default function Analytics() {
  const { theme } = useTheme();
  const { t, language } = useLanguage();
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiGet<StatsResponse>('/stats/charts')
      .then((data) => {
        if (!cancelled) {
          setStats(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || t('errorLoading'));
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [t]);

  const chartTextColor = theme === 'dark' ? '#a1a1aa' : '#52525b';
  const chartGridColor = theme === 'dark' ? '#27272a' : '#f4f4f5';

  const sectorData = useMemo(() => {
    if (!stats) return [];
    return stats.topSectors.labels.map((label, i) => ({
      name: label,
      value: Number(stats.topSectors.values[i] || 0),
      color: COLORS[i % COLORS.length],
    }));
  }, [stats]);

  const fundingByStage = useMemo(() => {
    if (!stats) return [];
    return stats.fundingByStage.labels.map((label, i) => ({
      stage: label,
      amount: Number(stats.fundingByStage.values[i] || 0) / 1_000_000,
    }));
  }, [stats]);

  const fundingByYear = useMemo(() => {
    if (!stats) return [];
    return stats.fundingByYear.labels.map((label, i) => ({
      year: label,
      amount: Number(stats.fundingByYear.values[i] || 0) / 1_000_000,
    }));
  }, [stats]);

  const topFundedStartups = useMemo(() => {
    if (!stats || !stats.topFundedStartups) return [];
    return stats.topFundedStartups.labels.map((label, i) => ({
      name: label,
      amount: Number(stats.topFundedStartups!.values[i] || 0),
    }));
  }, [stats]);

  const fundingBySector = useMemo(() => {
    if (!stats || !stats.fundingBySector) return [];
    return stats.fundingBySector.labels.map((label, i) => ({
      name: label,
      amount: Number(stats.fundingBySector!.values[i] || 0),
    }));
  }, [stats]);

  const kpiCards = useMemo(() => {
    if (!stats) return [];
    const c = stats.counts;
    return [
      { label: t('activeStartupsKpi'), value: c.startups.toLocaleString(), change: '+12%', up: true },
      { label: t('fundraisingKpi'), value: c.totalFunding, change: '+28%', up: true },
      { label: t('newFoundersKpi'), value: c.founders.toLocaleString(), change: '+8%', up: true },
      { label: t('growthRateKpi'), value: '18%', change: '-2%', up: false },
    ];
  }, [stats, t]);

  const cityData = useMemo(() => {
    const others = language === 'en' ? 'Others' : 'Autres';
    return [
      { city: 'Casablanca', count: 892 },
      { city: 'Rabat', count: 312 },
      { city: 'Marrakech', count: 187 },
      { city: 'Tanger', count: 156 },
      { city: 'Agadir', count: 98 },
      { city: others, count: 306 },
    ];
  }, [language]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-orange-600" />
        <span className="ml-3 text-zinc-600 dark:text-zinc-400">{t('loading')}</span>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] text-red-500">
        <AlertCircle className="w-6 h-6 mr-2" />
        {error || t('errorLoading')}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-1 font-serif">
          {t('analyticsTitle')}
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          {t('analyticsSubtitle')}
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiCards.map((kpi) => (
          <div
            key={kpi.label}
            className="p-4 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 transition-colors"
          >
            <div className="text-xs text-zinc-500 dark:text-zinc-400 mb-1">{kpi.label}</div>
            <div className="text-2xl font-bold text-zinc-900 dark:text-white">{kpi.value}</div>
            <div
              className={`inline-flex items-center gap-0.5 text-xs font-semibold mt-1 ${
                kpi.up ? 'text-emerald-600 dark:text-emerald-455' : 'text-red-500 dark:text-red-400'
              }`}
            >
              {kpi.up ? (
                <TrendingUp className="w-3 h-3" />
              ) : (
                <TrendingDown className="w-3 h-3" />
              )}
              {kpi.change} {t('vsLastMonth')}
            </div>
          </div>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Sector Distribution */}
        <div className="p-5 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 transition-colors">
          <h3 className="text-sm font-semibold text-zinc-900 dark:text-white mb-4">
            {t('sectorDistribution')}
          </h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={sectorData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={95}
                paddingAngle={2}
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
              <Legend
                verticalAlign="bottom"
                height={40}
                iconType="circle"
                iconSize={8}
                formatter={(value: string) => (
                  <span className="text-xs text-zinc-650 dark:text-zinc-400">{value}</span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Funding by Stage */}
        <div className="p-5 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 transition-colors">
          <h3 className="text-sm font-semibold text-zinc-900 dark:text-white mb-4">
            {t('startupsByStage')}
          </h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={fundingByStage} margin={{ left: -20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={chartGridColor} vertical={false} />
              <XAxis dataKey="stage" stroke={chartTextColor} tick={{ fontSize: 11, fill: chartTextColor }} tickLine={false} />
              <YAxis stroke={chartTextColor} tick={{ fontSize: 11, fill: chartTextColor }} tickLine={false} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: theme === 'dark' ? '#18181b' : '#ffffff',
                  borderColor: theme === 'dark' ? '#27272a' : '#e4e4e7',
                  color: theme === 'dark' ? '#ffffff' : '#000000'
                }}
              />
              <Bar dataKey="amount" fill="#b8521c" radius={[6, 6, 0, 0]} maxBarSize={45} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Funding by Year */}
        <div className="p-5 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 transition-colors">
          <h3 className="text-sm font-semibold text-zinc-900 dark:text-white mb-4">
            {t('fundingActivity')}
          </h3>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={fundingByYear} margin={{ left: -20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={chartGridColor} vertical={false} />
              <XAxis dataKey="year" stroke={chartTextColor} tick={{ fontSize: 11, fill: chartTextColor }} tickLine={false} />
              <YAxis stroke={chartTextColor} tick={{ fontSize: 11, fill: chartTextColor }} tickLine={false} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: theme === 'dark' ? '#18181b' : '#ffffff',
                  borderColor: theme === 'dark' ? '#27272a' : '#e4e4e7',
                  color: theme === 'dark' ? '#ffffff' : '#000000'
                }}
              />
              <Line
                type="monotone"
                dataKey="amount"
                stroke="#b8521c"
                strokeWidth={2.5}
                dot={{ fill: '#b8521c', r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* City Distribution */}
        <div className="p-5 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 transition-colors">
          <h3 className="text-sm font-semibold text-zinc-900 dark:text-white mb-4">
            {t('startupsByCity')}
          </h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={cityData} layout="vertical" margin={{ left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={chartGridColor} horizontal={false} />
              <XAxis type="number" stroke={chartTextColor} tick={{ fontSize: 11, fill: chartTextColor }} tickLine={false} />
              <YAxis
                dataKey="city"
                type="category"
                stroke={chartTextColor}
                tick={{ fontSize: 11, fill: chartTextColor }}
                width={80}
                tickLine={false}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: theme === 'dark' ? '#18181b' : '#ffffff',
                  borderColor: theme === 'dark' ? '#27272a' : '#e4e4e7',
                  color: theme === 'dark' ? '#ffffff' : '#000000'
                }}
              />
              <Bar dataKey="count" fill="#d56426" radius={[0, 6, 6, 0]} maxBarSize={20} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Top funded startups */}
        <div className="p-5 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 transition-colors">
          <h3 className="text-sm font-semibold text-zinc-900 dark:text-white mb-4">
            {t('topFundedStartups')}
          </h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={topFundedStartups} margin={{ left: -20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={chartGridColor} vertical={false} />
              <XAxis dataKey="name" stroke={chartTextColor} tick={{ fontSize: 11, fill: chartTextColor }} tickLine={false} />
              <YAxis stroke={chartTextColor} tick={{ fontSize: 11, fill: chartTextColor }} tickLine={false} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: theme === 'dark' ? '#18181b' : '#ffffff',
                  borderColor: theme === 'dark' ? '#27272a' : '#e4e4e7',
                  color: theme === 'dark' ? '#ffffff' : '#000000'
                }}
              />
              <Bar dataKey="amount" fill="#3b82f6" radius={[6, 6, 0, 0]} maxBarSize={45} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Funding by sector */}
        <div className="p-5 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 transition-colors">
          <h3 className="text-sm font-semibold text-zinc-900 dark:text-white mb-4">
            {t('fundingBySector')}
          </h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={fundingBySector} margin={{ left: -20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={chartGridColor} vertical={false} />
              <XAxis dataKey="name" stroke={chartTextColor} tick={{ fontSize: 11, fill: chartTextColor }} tickLine={false} />
              <YAxis stroke={chartTextColor} tick={{ fontSize: 11, fill: chartTextColor }} tickLine={false} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: theme === 'dark' ? '#18181b' : '#ffffff',
                  borderColor: theme === 'dark' ? '#27272a' : '#e4e4e7',
                  color: theme === 'dark' ? '#ffffff' : '#000000'
                }}
              />
              <Bar dataKey="amount" fill="#a855f7" radius={[6, 6, 0, 0]} maxBarSize={45} />
            </BarChart>
          </ResponsiveContainer>
        </div>

      </div>
    </div>
  );
}
