import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ChevronDown, Sparkles, Building, X } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { FadeInImage } from '@/enhancements/FadeInImage';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/context/LanguageContext';
import { useStartups } from '@/hooks/useStartups';
import { useStartupFilters } from '@/hooks/useStartupFilters';
import { useInvestors, useVentureStudios } from '@/hooks/useInvestors';
import { useStats } from '@/hooks/useStats';
import { formatCount } from '@/lib/utils';

const stages: Record<string, string> = {
  SCALING: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400',
  AMORCAGE: 'bg-blue-100 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400',
  AMORÇAGE: 'bg-blue-100 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400',
  IDEATION: 'bg-purple-100 text-purple-700 dark:bg-purple-950/40 dark:text-purple-400',
  SEED: 'bg-purple-100 text-purple-700 dark:bg-purple-950/40 dark:text-purple-400',
  'PRE-SEED': 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300',
  INTERNATIONALISATION: 'bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400',
  ACQUIRED: 'bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400',
};

interface FilterDef {
  /** Translation key for the visible label. */
  labelKey: string;
  /** Resolved label in the active language. */
  label: string;
  /** Stable query-string key; used as the filter's identity. */
  param: string;
  options: string[];
}

const staticFilters: { labelKey: string; param: string }[] = [
  { labelKey: 'filterCity', param: 'location' },
  { labelKey: 'filterSector', param: 'sector' },
  { labelKey: 'filterLegalForm', param: 'legal_form' },
  { labelKey: 'filterStage', param: 'stage' },
  { labelKey: 'filterStatus', param: 'status' },
];

export default function Startups() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeFilter, setActiveFilter] = useState<string | null>(null);
  const { t, language } = useLanguage();
  const { data: startups = [], total, isLoading: startupsLoading } = useStartups();
  const { data: filterOptions, isLoading: filtersLoading } = useStartupFilters();
  const { data: investors = [], isLoading: investorsLoading } = useInvestors();
  const { data: ventureStudios = [], isLoading: studiosLoading } = useVentureStudios();
  const { data: ecosystemStats } = useStats();

  const getFilterOptions = (param: string): string[] => {
    if (!filterOptions) return [];
    switch (param) {
      case 'location':
        return filterOptions.locations;
      case 'sector':
        return filterOptions.sectors;
      case 'stage':
        return filterOptions.stages;
      case 'status':
        return filterOptions.statuses;
      case 'legal_form':
        return filterOptions.legal_forms;
      default:
        return [];
    }
  };

  const filterDefs: FilterDef[] = staticFilters.map((f) => ({
    ...f,
    label: t(f.labelKey as Parameters<typeof t>[0]),
    options: getFilterOptions(f.param),
  }));

  // Tracked by `param`, which is stable across languages. Tracking the visible
  // label meant the open filter was lost whenever the label text changed.
  const activeFilterParam = activeFilter;

  const activeFilterValue = (param: string) => searchParams.get(param) || '';

  const setFilter = (param: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) {
      next.set(param, value);
    } else {
      next.delete(param);
    }
    setSearchParams(next, { replace: true });
  };

  const clearFilters = () => {
    const next = new URLSearchParams();
    const type = searchParams.get('type');
    if (type) next.set('type', type);
    setActiveFilter(null);
    setSearchParams(next, { replace: true });
  };

  const hasActiveFilters = staticFilters.some((f) => searchParams.get(f.param));

  const typeFilter = searchParams.get('type'); // 'incubateur' or 'venture-studio'

  // If filtering for Incubateurs, display them from investors list
  if (typeFilter === 'incubateur') {
    if (investorsLoading) {
      return (
        <div className="space-y-6 animate-fade-in">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-72" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {Array.from({ length: 4 }).map((_, idx) => (
              <Skeleton key={idx} className="h-32 rounded-xl" />
            ))}
          </div>
        </div>
      );
    }
    const incubatorList = investors.filter(i => i.type.includes('Incubateur') || i.type.includes('Accélérateur'));
    return (
      <div className="space-y-6 animate-fade-in">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-1">
            {t('incubatorsTitle')}
          </h1>
          <p className="text-sm text-zinc-600 dark:text-zinc-300">
            {t('incubatorsSubtitle')}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {incubatorList.map((inc) => (
            <div
              key={inc.id}
              onClick={() => navigate(`/investors/${inc.id}`)}
              className="p-5 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 hover:border-zinc-200 dark:hover:border-zinc-700 hover:shadow-md transition-all cursor-pointer group ve-card-lift"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg overflow-hidden flex items-center justify-center flex-shrink-0 bg-white dark:bg-zinc-800 border border-zinc-150 dark:border-zinc-700/50">
                    {inc.logo ? (
                      <FadeInImage src={inc.logo} alt={inc.name} className="w-full h-full object-contain p-1" />
                    ) : (
                      <div className="w-full h-full bg-purple-50 dark:bg-zinc-800 flex items-center justify-center text-purple-650">
                        <Sparkles className="w-5 h-5" />
                      </div>
                    )}
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-zinc-900 dark:text-white group-hover:text-pulse-orange transition-colors">
                      {inc.name}
                    </h3>
                    <span className="text-[11px] text-zinc-600 dark:text-zinc-300">
                      {inc.location}
                    </span>
                  </div>
                </div>
                <Badge className="bg-purple-50 dark:bg-zinc-800 text-purple-600 dark:text-purple-400 font-semibold border-none text-[11px]">
                  {inc.type}
                </Badge>
              </div>

              <div className="border-t border-zinc-50 dark:border-zinc-800/80 pt-3 mt-3 flex items-center justify-between text-xs text-zinc-550 dark:text-zinc-400">
                <span>Focus: {inc.focus.slice(0, 3).join(', ')}</span>
                <span className="font-semibold text-purple-650 dark:text-purple-400">{inc.portfolio} startups {language === 'en' ? 'tracked' : 'suivies'}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // If filtering for Venture Studios
  if (typeFilter === 'venture-studio') {
    if (studiosLoading) {
      return (
        <div className="space-y-6 animate-fade-in">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-72" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {Array.from({ length: 4 }).map((_, idx) => (
              <Skeleton key={idx} className="h-32 rounded-xl" />
            ))}
          </div>
        </div>
      );
    }
    // Filtered server-side by PrimaryInvestorType. This used to be a
    // client-side guess — `type.includes('corporate')` plus hardcoded UM6P/CDG
    // name matches — which never matched a real venture studio, because no row
    // in the table is typed 'corporate'.
    const studioList = ventureStudios;
    return (
      <div className="space-y-6 animate-fade-in">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-1">
            {t('ventureStudiosTitle')}
          </h1>
          <p className="text-sm text-zinc-600 dark:text-zinc-300">
            {t('ventureStudiosSubtitle')}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {studioList.map((studio) => (
            <div
              key={studio.id}
              onClick={() => navigate(`/investors/${studio.id}`)}
              className="p-5 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 hover:border-zinc-200 dark:hover:border-zinc-700 hover:shadow-md transition-all cursor-pointer group ve-card-lift"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg overflow-hidden flex items-center justify-center flex-shrink-0 bg-white dark:bg-zinc-800 border border-zinc-150 dark:border-zinc-700/50">
                    {studio.logo ? (
                      <FadeInImage src={studio.logo} alt={studio.name} className="w-full h-full object-contain p-1" />
                    ) : (
                      <div className="w-full h-full bg-orange-50 dark:bg-zinc-800 flex items-center justify-center text-pulse-orange">
                        <Building className="w-5 h-5" />
                      </div>
                    )}
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-zinc-900 dark:text-white group-hover:text-pulse-orange transition-colors">
                      {studio.name}
                    </h3>
                    <span className="text-[11px] text-zinc-600 dark:text-zinc-300">
                      {studio.location}
                    </span>
                  </div>
                </div>
                <Badge className="bg-orange-50 dark:bg-zinc-800 text-pulse-orange font-semibold border-none text-[11px]">
                  Venture Builder
                </Badge>
              </div>

              <div className="border-t border-zinc-50 dark:border-zinc-800/80 pt-3 mt-3 flex items-center justify-between text-xs text-zinc-550 dark:text-zinc-400">
                <span>Focus: {studio.focus.slice(0, 3).join(', ')}</span>
                {/* Studios seeded from the ecosystem directory have no investment
                    count, which would otherwise render a bare unit label. */}
                {studio.investments != null && (
                  <span className="font-semibold text-pulse-orange">
                    {studio.investments} {t('investmentsLabel')}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>

        {studioList.length === 0 && (
          <div className="p-8 text-center bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800">
            <Building className="w-8 h-8 mx-auto mb-3 text-zinc-300 dark:text-zinc-600" />
            <p className="text-sm text-zinc-600 dark:text-zinc-300">
              {t('ventureStudiosEmpty')}
            </p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-1">
          {t('startupsTitle')}
        </h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-300">
          {t('startupsSubtitle')}
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: t('totalStartupsLabel'), value: ecosystemStats ? formatCount(ecosystemStats.startups, language) : '' },
          { label: t('sectorsLabel'), value: ecosystemStats?.sectors.toString() ?? '' },
          { label: t('totalRaisedLabel'), value: ecosystemStats?.totalFunding ?? '' },
          { label: t('citiesLabel'), value: ecosystemStats?.cities.toString() ?? '' },
        ].map((stat) => (
          <div
            key={stat.label}
            className="p-4 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 transition-colors"
          >
            <div className="text-2xl font-bold text-zinc-900 dark:text-white">
              {stat.value || <Skeleton className="h-8 w-16" />}
            </div>
            <div className="text-xs text-zinc-500 dark:text-zinc-450 mt-0.5">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-3">
        <div className="flex flex-col sm:flex-row flex-wrap items-start sm:items-center gap-2">
          <div className="flex flex-wrap items-center gap-2">
            {filterDefs.map((filter) => {
              const isActive = activeFilter === filter.param;
              const selected = activeFilterValue(filter.param);
              return (
                <button
                  key={filter.param}
                  aria-pressed={isActive}
                  onClick={() => setActiveFilter(isActive ? null : filter.param)}
                  className={`inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg border transition-colors ${
                    isActive || selected
                      ? 'bg-pulse-orange-50 border-pulse-orange text-pulse-orange dark:bg-pulse-orange/10'
                      : 'bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-50 dark:bg-zinc-900 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-800'
                  }`}
                >
                  {filter.label}
                  {selected && <span className="w-1.5 h-1.5 rounded-full bg-current" />}
                  <ChevronDown className={`w-3 h-3 transition-transform ${isActive ? 'rotate-180' : ''}`} />
                </button>
              );
            })}
            {hasActiveFilters && (
              <Button
                variant="outline"
                size="sm"
                onClick={clearFilters}
                className="h-8 text-xs border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-300 dark:bg-zinc-900 dark:hover:bg-zinc-800"
              >
                <X className="w-3 h-3 mr-1" />
                {language === 'fr' ? 'Réinitialiser' : 'Reset'}
              </Button>
            )}
          </div>
          <div className="flex items-center gap-2 sm:ml-auto">
            <span className="text-xs text-zinc-500 dark:text-zinc-400">{t('sortBy')}</span>
            <select
              aria-label={t('sortBy')}
              value={`${searchParams.get('sort_by') || 'startup_name'}:${searchParams.get('order') || 'asc'}`}
              onChange={(e) => {
                const [column, dir] = e.target.value.split(':');
                const next = new URLSearchParams(searchParams);
                next.set('sort_by', column);
                next.set('order', dir);
                setSearchParams(next, { replace: true });
              }}
              className="px-3 py-1.5 text-xs font-medium bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg text-zinc-650 dark:text-zinc-300 focus:outline-none focus:ring-2 focus:ring-pulse-orange/20 focus:border-pulse-orange cursor-pointer"
            >
              <option value="startup_name:asc">{t('sortNameAsc')}</option>
              <option value="startup_name:desc">{t('sortNameDesc')}</option>
              <option value="total_funding_usd:desc">{t('amountRaised')} ↓</option>
              <option value="total_funding_usd:asc">{t('amountRaised')} ↑</option>
            </select>
          </div>
        </div>

        {activeFilter && activeFilterParam && (
          <div className="flex items-center gap-2 animate-fade-in">
            <select
              value={searchParams.get(activeFilterParam) || ''}
              onChange={(e) => setFilter(activeFilterParam, e.target.value)}
              disabled={filtersLoading}
              className="min-w-[12rem] px-3 py-2 text-xs bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg text-zinc-700 dark:text-zinc-300 focus:outline-none focus:ring-2 focus:ring-pulse-orange/20 focus:border-pulse-orange"
            >
              <option value="">
                {language === 'fr' ? 'Toutes les valeurs' : 'All values'}
              </option>
              {filterDefs
                .find((f) => f.param === activeFilter)
                ?.options?.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
            </select>
            {filtersLoading && <Skeleton className="h-8 w-24" />}
          </div>
        )}

        {hasActiveFilters && (
          <div className="flex flex-wrap items-center gap-2">
            {filterDefs.map(
              (filter) =>
                searchParams.get(filter.param) && (
                  <Badge
                    key={filter.param}
                    onClick={() => setFilter(filter.param, '')}
                    className="cursor-pointer inline-flex items-center gap-1 bg-pulse-orange-50 text-pulse-orange border-pulse-orange/30 hover:bg-pulse-orange-100 dark:bg-pulse-orange/10 dark:text-pulse-orange dark:border-pulse-orange/30"
                  >
                    {filter.label}: {searchParams.get(filter.param)}
                    <X className="w-3 h-3" />
                  </Badge>
                )
            )}
            <span className="text-xs text-zinc-600 dark:text-zinc-300 ml-2">
              {total} {language === 'fr' ? 'résultat(s)' : 'result(s)'}
            </span>
          </div>
        )}
      </div>

      {/* Startup Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {startupsLoading ? (
          Array.from({ length: 6 }).map((_, idx) => (
            <Skeleton key={idx} className="h-48 rounded-xl" />
          ))
        ) : (
          startups.map((startup) => (
            <div
              key={startup.id}
              onClick={() => navigate(`/startups/${startup.id}`)}
              className="p-5 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 hover:border-zinc-200 dark:hover:border-zinc-700 hover:shadow-md transition-all cursor-pointer ve-card-lift"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg overflow-hidden flex items-center justify-center flex-shrink-0 bg-white dark:bg-zinc-800 border border-zinc-150 dark:border-zinc-700/50">
                    {startup.logo ? (
                      <FadeInImage src={startup.logo} alt={startup.name} className="w-full h-full object-contain p-1" />
                    ) : (
                      <div className="w-full h-full bg-gradient-to-br from-pulse-orange-50 to-orange-100 dark:from-orange-950/40 dark:to-orange-900/10 flex items-center justify-center font-bold text-pulse-orange">
                        {startup.name[0]}
                      </div>
                    )}
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-zinc-900 dark:text-white">
                      {startup.name}
                    </h3>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      {startup.sector.slice(0, 2).map((s) => (
                        <span key={s} className="text-[11px] text-zinc-600 dark:text-zinc-300">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge
                    className={`text-[11px] font-semibold ${stages[startup.stage] || 'bg-zinc-100 text-zinc-700'}`}
                  >
                    {startup.stage}
                  </Badge>
                  <Badge
                    variant="outline"
                    className="text-[11px] font-semibold border-emerald-200 text-emerald-700 dark:text-emerald-400 dark:border-emerald-900 dark:text-emerald-400 bg-emerald-50/50 dark:bg-emerald-950/20"
                  >
                    {startup.status}
                  </Badge>
                </div>
              </div>

              <p className="text-xs text-zinc-600 dark:text-zinc-300 leading-relaxed mb-3 line-clamp-2">
                {startup.description}
              </p>

              <div className="flex items-center justify-between text-xs text-zinc-600 dark:text-zinc-300">
                <span>{startup.location}</span>
                {startup.funding > 0 && (
                  <span className="font-semibold text-zinc-700 dark:text-zinc-300">
                    {startup.fundingCurrency}
                    {(startup.funding / 1000000).toFixed(1)}M
                  </span>
                )}
              </div>

              <div className="flex items-center gap-3 mt-2 pt-2 border-t border-zinc-50 dark:border-zinc-800/80 text-[11px] text-zinc-600 dark:text-zinc-300">
                <span>{startup.teamSize} {t('employeesLabel')}</span>
                <span>•</span>
                <span>{t('foundedInLabel')} {startup.yearFounded}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
