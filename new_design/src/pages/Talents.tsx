import { useMemo, useState } from 'react';
import { Search, MapPin, Briefcase, AlertTriangle, Users } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useLanguage } from '@/context/LanguageContext';
import { useTalents } from '@/hooks/useTalents';
import { describeError } from '@/lib/errors';

/**
 * Talent marketplace.
 *
 * Previously the sidebar pointed "Talent Marketplace" at
 * `/opportunities?type=talent`, so the entry opened the Opportunities page.
 * This renders the `talents` table instead.
 *
 * A note on the wording: the review proposed "Offres d'emploi et missions",
 * i.e. job adverts. The table holds the other side of that market -- profiles
 * of people available to join a startup (title, skills, availability, what
 * they are looking for). The copy below describes what the page actually
 * shows rather than promising adverts the data does not contain.
 */
export default function Talents() {
  const { language } = useLanguage();
  const isFr = language === 'fr';
  const { data: talents, total, isLoading, error, refetch } = useTalents();

  const [search, setSearch] = useState('');
  const [activeFormat, setActiveFormat] = useState<string>('all');

  const formats = useMemo(() => {
    const seen = new Set<string>();
    for (const item of talents) if (item.workFormat) seen.add(item.workFormat);
    return ['all', ...Array.from(seen).sort()];
  }, [talents]);

  const visible = useMemo(() => {
    const query = search.trim().toLowerCase();
    return talents.filter((item) => {
      if (activeFormat !== 'all' && item.workFormat !== activeFormat) return false;
      if (!query) return true;
      return (
        item.name.toLowerCase().includes(query) ||
        (item.title ?? '').toLowerCase().includes(query) ||
        (item.location ?? '').toLowerCase().includes(query) ||
        item.skills.some((s) => s.toLowerCase().includes(query))
      );
    });
  }, [talents, search, activeFormat]);

  return (
    <div className="space-y-6 pb-8">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="p-2 rounded-xl bg-pulse-orange/10 text-pulse-orange">
            <Users className="w-5 h-5" />
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-zinc-900 dark:text-white tracking-tight">
          {isFr ? 'Talents' : 'Talent'}
        </h1>
        <p className="text-xs sm:text-sm text-zinc-600 dark:text-zinc-300 mt-1">
          {isLoading || error
            ? isFr
              ? 'Profils disponibles pour rejoindre les startups marocaines.'
              : 'People available to join Moroccan startups.'
            : isFr
              ? `${total} profils disponibles pour rejoindre les startups marocaines.`
              : `${total} people available to join Moroccan startups.`}
        </p>
      </div>

      {(talents.length > 0 || isLoading) && (
        <div className="bg-white dark:bg-zinc-900 p-4 rounded-2xl border border-zinc-200 dark:border-zinc-800 space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 dark:text-zinc-400" />
            <Input
              placeholder={
                isFr ? 'Rechercher un profil, une compétence...' : 'Search a profile, a skill...'
              }
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label={isFr ? 'Rechercher un talent' : 'Search talent'}
              className="pl-9 dark:bg-zinc-950 dark:border-zinc-800 dark:text-white text-sm h-10 rounded-xl"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            {formats.map((format) => (
              <button
                key={format}
                onClick={() => setActiveFormat(format)}
                aria-pressed={activeFormat === format}
                className={`px-3 py-1.5 text-xs font-bold rounded-xl transition-all ${
                  activeFormat === format
                    ? 'bg-pulse-orange text-primary-foreground shadow-sm'
                    : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700'
                }`}
              >
                {format === 'all' ? (isFr ? 'Tous' : 'All') : format}
              </button>
            ))}
          </div>
        </div>
      )}

      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-44 rounded-2xl" />
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

      {!isLoading && !error && visible.length === 0 && (
        <div className="flex flex-col items-center gap-2 py-16 text-center">
          <Users className="w-8 h-8 text-zinc-500 dark:text-zinc-400" />
          <p className="text-sm text-zinc-600 dark:text-zinc-300 max-w-sm">
            {talents.length === 0
              ? isFr
                ? "Aucun profil publié pour l'instant."
                : 'No profiles published yet.'
              : isFr
                ? 'Aucun profil ne correspond à votre recherche.'
                : 'No profile matches your search.'}
          </p>
        </div>
      )}

      {!isLoading && !error && visible.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {visible.map((talent) => (
            <article
              key={talent.id}
              className="bg-white dark:bg-zinc-900 p-4 rounded-2xl border border-zinc-200 dark:border-zinc-800 flex flex-col gap-3"
            >
              <div>
                <h2 className="text-sm font-bold text-zinc-900 dark:text-white">{talent.name}</h2>
                {talent.title && (
                  <p className="text-xs text-zinc-600 dark:text-zinc-300 mt-0.5">{talent.title}</p>
                )}
              </div>

              <div className="flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-zinc-600 dark:text-zinc-300">
                {talent.location && (
                  <span className="inline-flex items-center gap-1">
                    <MapPin className="w-3 h-3" aria-hidden="true" />
                    {talent.location}
                  </span>
                )}
                {talent.yearsExperience && (
                  <span className="inline-flex items-center gap-1">
                    <Briefcase className="w-3 h-3" aria-hidden="true" />
                    {isFr
                      ? `${talent.yearsExperience} ans d'expérience`
                      : `${talent.yearsExperience} years of experience`}
                  </span>
                )}
              </div>

              {talent.skills.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {talent.skills.slice(0, 5).map((skill) => (
                    <Badge
                      key={skill}
                      variant="secondary"
                      className="text-[11px] font-medium bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300"
                    >
                      {skill}
                    </Badge>
                  ))}
                </div>
              )}

              {talent.availability && (
                <p className="text-[11px] text-zinc-600 dark:text-zinc-300 mt-auto">
                  <span className="font-semibold text-zinc-700 dark:text-zinc-200">
                    {isFr ? 'Disponibilité : ' : 'Availability: '}
                  </span>
                  {talent.availability}
                </p>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
