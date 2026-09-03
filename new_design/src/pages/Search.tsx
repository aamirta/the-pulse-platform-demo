import { useState } from 'react';
import { Search as SearchIcon, Building2, Users, Landmark } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Skeleton } from '@/components/ui/skeleton';
import { useLanguage } from '@/context/LanguageContext';
import { useSearch } from '@/hooks/useSearch';

export default function Search() {
  const [query, setQuery] = useState('');
  const [activeTab, setActiveTab] = useState('all');
  const navigate = useNavigate();
  const { t } = useLanguage();
  const { data: searchResults = [], isLoading } = useSearch(query);

  const tabs = [
    { key: 'all', label: t('tabAll'), icon: SearchIcon },
    { key: 'startup', label: t('tabStartups'), icon: Building2 },
    { key: 'founder', label: t('tabFounders'), icon: Users },
    { key: 'investor', label: t('tabInvestors'), icon: Landmark },
  ];

  const filteredResults = searchResults.filter((r) => activeTab === 'all' || r.type === activeTab);

  const groupedResults = {
    startup: filteredResults.filter((r) => r.type === 'startup'),
    founder: filteredResults.filter((r) => r.type === 'founder'),
    investor: filteredResults.filter((r) => r.type === 'investor'),
  };

  const showStartups = activeTab === 'all' || activeTab === 'startup';
  const showFounders = activeTab === 'all' || activeTab === 'founder';
  const showInvestors = activeTab === 'all' || activeTab === 'investor';

  const totalResults = filteredResults.length;

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-4">{t('searchTitle')}</h1>
        <div className="relative max-w-2xl">
          <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500 dark:text-zinc-400" />
          <input
            type="text"
            placeholder={t('searchBoxPlaceholder')}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full h-12 pl-12 pr-4 bg-white dark:bg-zinc-900 border border-zinc-250 dark:border-zinc-800 rounded-xl text-base text-zinc-900 dark:text-white placeholder:text-zinc-500 dark:text-zinc-400 focus:outline-none focus:border-pulse-orange/40 dark:focus:border-pulse-orange/40 focus:ring-2 focus:ring-pulse-orange/10 transition-all"
            autoFocus
          />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-zinc-200 dark:border-zinc-800 pb-1">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === tab.key
                ? 'text-pulse-orange border-b-2 border-pulse-orange dark:text-orange-400 dark:border-orange-400'
                : 'text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Results */}
      {query && !isLoading && (
        <p className="text-sm text-zinc-600 dark:text-zinc-300">
          {totalResults} {t('resultsFor')} "{query}"
        </p>
      )}

      <div className="space-y-6">
        {isLoading && query ? (
          Array.from({ length: 4 }).map((_, idx) => (
            <Skeleton key={idx} className="h-16 rounded-xl" />
          ))
        ) : (
          <>
            {/* Startups */}
            {showStartups && groupedResults.startup.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-300 mb-3 flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-zinc-500 dark:text-zinc-400" />
                  {t('tabStartups')} ({groupedResults.startup.length})
                </h3>
                <div className="space-y-2">
                  {groupedResults.startup.map((s) => (
                    <div
                      key={s.id}
                      onClick={() => navigate(s.url)}
                      className="flex items-center gap-4 p-4 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 hover:border-zinc-200 dark:hover:border-zinc-700 hover:shadow-sm transition-all cursor-pointer group ve-card-lift"
                    >
                      <div className="w-10 h-10 rounded-lg overflow-hidden flex items-center justify-center flex-shrink-0 bg-white dark:bg-zinc-800 border border-zinc-150 dark:border-zinc-700/50">
                        <div className="w-full h-full bg-gradient-to-br from-pulse-orange-50 to-orange-100 dark:from-orange-950/40 dark:to-orange-900/10 flex items-center justify-center font-bold text-pulse-orange">
                          {s.title[0]}
                        </div>
                      </div>
                      <div className="flex-1">
                        <h4 className="text-sm font-semibold text-zinc-900 dark:text-white group-hover:text-pulse-orange transition-colors">{s.title}</h4>
                        <p className="text-xs text-zinc-600 dark:text-zinc-300 mt-0.5">
                          {s.subtitle}
                        </p>
                      </div>
                      <span className="text-xs text-zinc-600 dark:text-zinc-300">{t('tabStartups')}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Founders */}
            {showFounders && groupedResults.founder.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-300 mb-3 flex items-center gap-2">
                  <Users className="w-4 h-4 text-zinc-500 dark:text-zinc-400" />
                  {t('tabFounders')} ({groupedResults.founder.length})
                </h3>
                <div className="space-y-2">
                  {groupedResults.founder.map((f) => (
                    <div
                      key={f.id}
                      onClick={() => navigate(f.url)}
                      className="flex items-center gap-4 p-4 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 hover:border-zinc-200 dark:hover:border-zinc-700 hover:shadow-sm transition-all cursor-pointer group ve-card-lift"
                    >
                      <div className="w-10 h-10 rounded-full overflow-hidden flex items-center justify-center flex-shrink-0 bg-white dark:bg-zinc-800 border border-zinc-150 dark:border-zinc-700/50">
                        <div className="w-full h-full flex items-center justify-center font-bold text-blue-600 dark:text-blue-400 bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-950/40 dark:to-purple-950/20">
                          {f.title.split(' ').map((n) => n[0]).join('')}
                        </div>
                      </div>
                      <div className="flex-1">
                        <h4 className="text-sm font-semibold text-zinc-900 dark:text-white group-hover:text-pulse-orange transition-colors">{f.title}</h4>
                        <p className="text-xs text-zinc-600 dark:text-zinc-300 mt-0.5">
                          {f.subtitle}
                        </p>
                      </div>
                      <span className="text-xs text-zinc-600 dark:text-zinc-300">{t('tabFounders')}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Investors */}
            {showInvestors && groupedResults.investor.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-300 mb-3 flex items-center gap-2">
                  <Landmark className="w-4 h-4 text-zinc-500 dark:text-zinc-400" />
                  {t('tabInvestors')} ({groupedResults.investor.length})
                </h3>
                <div className="space-y-2">
                  {groupedResults.investor.map((i) => (
                    <div
                      key={i.id}
                      onClick={() => navigate(i.url)}
                      className="flex items-center gap-4 p-4 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 hover:border-zinc-200 dark:hover:border-zinc-700 hover:shadow-sm transition-all cursor-pointer group ve-card-lift"
                    >
                      <div className="w-10 h-10 rounded-lg overflow-hidden flex items-center justify-center flex-shrink-0 bg-white dark:bg-zinc-800 border border-zinc-150 dark:border-zinc-700/50">
                        <div className="w-full h-full bg-gradient-to-br from-emerald-100 to-emerald-100 dark:from-emerald-950/40 dark:to-emerald-950/20 flex items-center justify-center">
                          <Landmark className="w-5 h-5 text-emerald-700 dark:text-emerald-400 dark:text-emerald-450" />
                        </div>
                      </div>
                      <div className="flex-1">
                        <h4 className="text-sm font-semibold text-zinc-900 dark:text-white group-hover:text-pulse-orange transition-colors">{i.title}</h4>
                        <p className="text-xs text-zinc-600 dark:text-zinc-300 mt-0.5">
                          {i.subtitle}
                        </p>
                      </div>
                      <span className="text-xs text-zinc-600 dark:text-zinc-300">{t('tabInvestors')}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {query && totalResults === 0 && !isLoading && (
              <div className="text-center py-12">
                <SearchIcon className="w-12 h-12 text-zinc-300 dark:text-zinc-750 mx-auto mb-3" />
                <p className="text-zinc-600 dark:text-zinc-300">{t('noResults')} "{query}"</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
