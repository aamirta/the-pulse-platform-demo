import { useNavigate, useSearchParams } from 'react-router-dom';
import { MapPin, Filter, ChevronDown, Building2, Globe } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/context/LanguageContext';
import { LoadMore } from '@/components/LoadMore';
import { useInvestors } from '@/hooks/useInvestors';
import { ImageWithFallback } from '@/components/ImageWithFallback';
import { openExternal } from '@/lib/url';

const filters = ['Type d\'investisseur', 'Localisation'];

export default function Investors() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { t } = useLanguage();
  const { data: investors = [], isLoading, total, hasMore, isLoadingMore, loadMore } =
    useInvestors();
  
  const typeFilter = searchParams.get('type'); // 'vc', 'ba', 'public'

  const filteredInvestors = investors.filter(investor => {
    if (typeFilter === 'vc') {
      return investor.type.toLowerCase().includes('capital') || investor.type.toLowerCase().includes('vc');
    }
    if (typeFilter === 'ba') {
      return investor.type.toLowerCase().includes('angel') || investor.type.toLowerCase().includes('business angel');
    }
    if (typeFilter === 'public') {
      return investor.name.toLowerCase().includes('um6p') || investor.name.toLowerCase().includes('cdg') || investor.name.toLowerCase().includes('tamwilcom');
    }
    return true;
  });

  if (isLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-72" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, idx) => (
            <Skeleton key={idx} className="h-24 rounded-xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {Array.from({ length: 6 }).map((_, idx) => (
            <Skeleton key={idx} className="h-40 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-1">
          {typeFilter === 'vc' ? t('vcTitle') :
           typeFilter === 'ba' ? t('baTitle') :
           typeFilter === 'public' ? t('publicTitle') :
           t('investorsTitle')}
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          {typeFilter === 'vc' ? t('vcSubtitle') :
           typeFilter === 'ba' ? t('baSubtitle') :
           typeFilter === 'public' ? t('publicSubtitle') :
           t('investorsSubtitle')}
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: t('totalInvestorsLabel'), value: filteredInvestors.length.toString() },
          { label: t('locationsLabel'), value: '14' },
          { label: t('typesLabel'), value: '7' },
          { label: t('totalInvestedLabel'), value: '--' },
        ].map((stat) => (
          <div key={stat.label} className="p-4 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 transition-colors">
            <div className="text-2xl font-bold text-zinc-900 dark:text-white">{stat.value}</div>
            <div className="text-xs text-zinc-500 dark:text-zinc-455 mt-0.5">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        {filters.map((filter) => (
          <button
            key={filter}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg border border-zinc-200 bg-white text-zinc-650 hover:bg-zinc-50 dark:bg-zinc-900 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-800 transition-colors"
          >
            {filter}
            <ChevronDown className="w-3 h-3" />
          </button>
        ))}
        <Button 
          variant="outline" 
          size="sm" 
          className="h-8 text-xs border-zinc-200 dark:border-zinc-800 dark:bg-zinc-900 dark:hover:bg-zinc-800 dark:text-zinc-300"
        >
          <Filter className="w-3 h-3 mr-1" />
          {t('filter')}
        </Button>
      </div>

      {/* Investor Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {filteredInvestors.map((investor) => (
          <div
            key={investor.id}
            className="p-5 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 hover:border-zinc-200 dark:hover:border-zinc-700 hover:shadow-md transition-all cursor-pointer group ve-card-lift"
            onClick={() => navigate(`/investors/${investor.id}`)}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg overflow-hidden flex items-center justify-center flex-shrink-0 bg-white dark:bg-zinc-800 border border-zinc-150 dark:border-zinc-700/50">
                  {investor.logo ? (
                    <ImageWithFallback src={investor.logo} alt={investor.name} className="w-full h-full object-contain p-1" />
                  ) : (
                    <div className="w-full h-full bg-gradient-to-br from-emerald-50 to-emerald-100 dark:from-emerald-950/40 dark:to-emerald-950/20 flex items-center justify-center">
                      <Building2 className="w-5 h-5 text-emerald-600 dark:text-emerald-450" />
                    </div>
                  )}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-zinc-900 dark:text-white group-hover:text-pulse-orange transition-colors">
                    {investor.name}
                  </h3>
                  <div className="flex items-center gap-2 mt-0.5">
                    <Badge
                      variant="outline"
                      className="text-[10px] font-medium border-zinc-200 dark:border-zinc-800 text-zinc-500 dark:text-zinc-400"
                    >
                      {investor.type}
                    </Badge>
                    <span className="flex items-center gap-1 text-xs text-zinc-500 dark:text-zinc-400">
                      <MapPin className="w-3 h-3" />
                      {investor.location}
                    </span>
                  </div>
                </div>
              </div>
              
              {investor.website && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    openExternal(investor.website);
                  }}
                  className="p-2 text-zinc-400 hover:text-pulse-orange hover:bg-orange-50 dark:hover:bg-zinc-800 rounded-lg transition-colors"
                  title={t('visitWebsite')}
                >
                  <Globe className="w-4 h-4" />
                </button>
              )}
            </div>

            <div className="flex flex-wrap gap-1.5 mb-3">
              {investor.focus.slice(0, 4).map((f) => (
                <span
                  key={f}
                  className="px-2 py-0.5 bg-zinc-100 dark:bg-zinc-800 text-zinc-650 dark:text-zinc-300 text-[11px] rounded-md"
                >
                  {f}
                </span>
              ))}
            </div>

            <div className="flex items-center gap-4 pt-3 border-t border-zinc-50 dark:border-zinc-800/80 text-xs text-zinc-500 dark:text-zinc-400">
              <span>
                <strong className="text-zinc-700 dark:text-zinc-200">{investor.investments}</strong>{' '}
                {t('investmentsLabel')}
              </span>
              <span>
                <strong className="text-zinc-700 dark:text-zinc-200">{investor.portfolio}</strong>{' '}
                {t('portfolioCountLabel')}
              </span>
            </div>
          </div>
        ))}
      </div>

      <LoadMore
        loaded={investors.length}
        total={total}
        hasMore={hasMore}
        isLoading={isLoadingMore}
        onLoadMore={loadMore}
      />
    </div>
  );
}
