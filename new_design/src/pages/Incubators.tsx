import { useMemo, useState } from 'react';
import { FlaskConical, MapPin, Search, Linkedin, AlertTriangle } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useLanguage } from '@/context/LanguageContext';
import { useIncubators } from '@/hooks/useIncubators';
import { describeError } from '@/lib/errors';

export default function Incubators() {
  const { language } = useLanguage();
  const isFr = language === 'fr';
  const { data: incubators, total, isLoading, error, refetch } = useIncubators();

  const [search, setSearch] = useState('');
  const [activeType, setActiveType] = useState<string>('all');

  const types = useMemo(() => {
    const seen = new Set<string>();
    for (const item of incubators) if (item.type) seen.add(item.type);
    return ['all', ...Array.from(seen).sort()];
  }, [incubators]);

  const visible = useMemo(() => {
    const query = search.trim().toLowerCase();
    return incubators.filter((item) => {
      if (activeType !== 'all' && item.type !== activeType) return false;
      if (!query) return true;
      return (
        item.name.toLowerCase().includes(query) ||
        (item.city ?? '').toLowerCase().includes(query) ||
        item.sectors.some((s) => s.toLowerCase().includes(query))
      );
    });
  }, [incubators, search, activeType]);

  return (
    <div className="space-y-6 pb-8">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="p-2 rounded-xl bg-pulse-orange/10 text-pulse-orange">
            <FlaskConical className="w-5 h-5" />
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-zinc-900 dark:text-white tracking-tight">
          {isFr ? 'Incubateurs & accélérateurs' : 'Incubators & accelerators'}
        </h1>
        <p className="text-xs sm:text-sm text-zinc-600 dark:text-zinc-300 mt-1">
          {/* The count comes from the API. While it is still in flight it is
              left out entirely rather than rendered as a "0 structures"
              headline, which is what the review saw. */}
          {isLoading || error
            ? isFr
              ? "Structures d'accompagnement au Maroc."
              : 'Support organisations across Morocco.'
            : isFr
              ? `${total} structures d'accompagnement au Maroc.`
              : `${total} support organisations across Morocco.`}
        </p>
      </div>

      <div className="bg-white dark:bg-zinc-900 p-4 rounded-2xl border border-zinc-200 dark:border-zinc-800 space-y-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 dark:text-zinc-400" />
          <Input
            placeholder={isFr ? 'Rechercher un incubateur...' : 'Search an incubator...'}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 dark:bg-zinc-950 dark:border-zinc-800 dark:text-white text-sm h-10 rounded-xl"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {types.map((type) => (
            <button
              key={type}
              onClick={() => setActiveType(type)}
              className={`px-3 py-1.5 text-xs font-bold rounded-xl transition-all ${
                activeType === type
                  ? 'bg-pulse-orange text-primary-foreground shadow-sm'
                  : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700'
              }`}
            >
              {type === 'all' ? (isFr ? 'Tous' : 'All') : type}
            </button>
          ))}
        </div>
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-40 rounded-2xl" />
          ))}
        </div>
      )}

      {!isLoading && error && (
        <div className="flex flex-col items-center gap-3 py-16 text-center" role="alert">
          <AlertTriangle className="w-8 h-8 text-amber-500" />
          <span className="text-sm text-zinc-600 dark:text-zinc-300 max-w-sm">
            {describeError(error, language)}
          </span>
          <Button variant="outline" size="sm" onClick={refetch}>
            {isFr ? 'Réessayer' : 'Try again'}
          </Button>
        </div>
      )}

      {!isLoading && !error && (
        <>
          <span className="block text-xs text-zinc-600 dark:text-zinc-300">
            {visible.length} / {total}
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {visible.map((item) => (
              <div
                key={item.id}
                className="bg-white dark:bg-zinc-900 p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 hover:border-pulse-orange/40 transition-colors flex flex-col gap-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <h3 className="text-sm font-black text-zinc-900 dark:text-white leading-tight">
                    {item.name}
                  </h3>
                  {item.status && (
                    <Badge className="text-[11px] font-extrabold px-2 py-0.5 rounded-full border-none bg-pulse-orange/10 text-pulse-orange shrink-0">
                      {item.status}
                    </Badge>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-2 text-[11px] text-zinc-600 dark:text-zinc-300">
                  {item.type && <span className="font-semibold">{item.type}</span>}
                  {item.city && (
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      {item.city}
                    </span>
                  )}
                </div>

                {item.sectors.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {item.sectors.slice(0, 4).map((sector) => (
                      <span
                        key={sector}
                        className="text-[11px] px-2 py-0.5 rounded-full bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300"
                      >
                        {sector}
                      </span>
                    ))}
                    {item.sectors.length > 4 && (
                      <span className="text-[11px] px-2 py-0.5 text-zinc-500 dark:text-zinc-400">
                        +{item.sectors.length - 4}
                      </span>
                    )}
                  </div>
                )}

                {item.investmentPhases.length > 0 && (
                  <span className="text-[11px] text-zinc-600 dark:text-zinc-300">
                    {isFr ? 'Phases : ' : 'Phases: '}
                    {item.investmentPhases.join(', ')}
                  </span>
                )}

                {item.linkedin && (
                  <a
                    href={item.linkedin}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-auto inline-flex items-center gap-1.5 text-[11px] font-bold text-pulse-orange hover:underline"
                  >
                    <Linkedin className="w-3.5 h-3.5" />
                    LinkedIn
                  </a>
                )}
              </div>
            ))}
          </div>

          {visible.length === 0 && (
            <div className="py-16 text-center text-sm text-zinc-600 dark:text-zinc-300">
              {isFr ? 'Aucun incubateur ne correspond.' : 'No incubator matches.'}
            </div>
          )}
        </>
      )}
    </div>
  );
}
