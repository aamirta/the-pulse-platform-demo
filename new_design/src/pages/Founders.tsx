import { useNavigate, useSearchParams } from 'react-router-dom';
import { MapPin, Linkedin, Filter, ChevronDown, Users } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useLanguage } from '@/context/LanguageContext';
import { LoadMore } from '@/components/LoadMore';
import { useFounders } from '@/hooks/useFounders';
import { useExperts } from '@/hooks/useExperts';
import { useCofounderProjects } from '@/hooks/useCofounderProjects';
import { ImageWithFallback } from '@/components/ImageWithFallback';
import { openExternal } from '@/lib/url';

const filters = ['Ville', 'Secteur', 'Startup', 'Genre'];

export default function Founders() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { t, language } = useLanguage();
  const en = language === 'en';
  const typeFilter = searchParams.get('type'); // 'expert' or 'co-founder'
  // Which slice of the people directory to show. Separate from `?type=`, which
  // chooses the *view*: this narrows the founder list itself.
  const roleParam = searchParams.get('role');
  const roleFilter: 'founder' | 'cofounder' | undefined =
    roleParam === 'founder' || roleParam === 'cofounder' ? roleParam : undefined;

  const { data: founders = [], isLoading, total, hasMore, isLoadingMore, loadMore } =
    useFounders(roleFilter);

  // Experts and co-founder postings are separate resources with their own
  // tables and endpoints. They used to be approximated by filtering this
  // founders list against hardcoded mock slugs, which matched nothing.
  if (typeFilter === 'expert') {
    return <ExpertsSection />;
  }
  if (typeFilter === 'co-founder') {
    return <CofoundersSection />;
  }

  if (isLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-72" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 6 }).map((_, idx) => (
            <Skeleton key={idx} className="h-32 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-1">
          {en ? 'Founders & Co-Founders' : 'Fondateurs & Cofondateurs'}
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          {en
            ? 'Everyone who has founded a company in the Moroccan ecosystem. Open a profile to see their full details.'
            : "Toutes les personnes ayant fondé une entreprise dans l'écosystème marocain. Ouvrez un profil pour voir tous les détails."}
        </p>
      </div>

      {/* Founder / co-founder split. Server-derived, so the counts are real. */}
      <nav
        className="flex gap-1 border-b border-zinc-150 dark:border-zinc-800 -mb-px"
        role="tablist"
        aria-label={en ? 'Filter people' : 'Filtrer les personnes'}
      >
        {(
          [
            { key: undefined, label: en ? 'Everyone' : 'Tous' },
            { key: 'founder' as const, label: en ? 'Founders' : 'Fondateurs' },
            { key: 'cofounder' as const, label: en ? 'Co-Founders' : 'Cofondateurs' },
          ] as const
        ).map(({ key, label }) => (
          <button
            key={label}
            role="tab"
            aria-selected={roleFilter === key}
            onClick={() => {
              const params = new URLSearchParams(searchParams);
              if (key) params.set('role', key);
              else params.delete('role');
              setSearchParams(params);
            }}
            className={`px-3 py-2 text-xs font-medium whitespace-nowrap border-b-2 transition-colors ${
              roleFilter === key
                ? 'border-pulse-orange text-pulse-orange'
                : 'border-transparent text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-zinc-200'
            }`}
          >
            {label}
            {roleFilter === key && total > 0 && (
              <span className="ml-1.5 text-[10px] text-zinc-400 font-normal">{total}</span>
            )}
          </button>
        ))}
      </nav>

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
          {t('apply')}
        </Button>
      </div>

      {/* Founders Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {founders.map((founder) => (
          <div
            key={founder.id}
            className="flex items-start gap-4 p-5 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 hover:border-zinc-200 dark:hover:border-zinc-700 hover:shadow-md transition-all cursor-pointer group ve-card-lift"
            onClick={() => navigate(`/founders/${founder.id}`)}
          >
            <div className="w-12 h-12 rounded-full overflow-hidden flex items-center justify-center flex-shrink-0 bg-white dark:bg-zinc-800 border border-zinc-150 dark:border-zinc-700/50">
              {founder.avatar ? (
                <ImageWithFallback src={founder.avatar} alt={founder.name} className="w-full h-full object-cover" />
              ) : (
                <span className="text-base font-bold text-blue-650 dark:text-blue-400">
                  {founder.name.split(' ').map((n) => n[0]).join('')}
                </span>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-sm font-semibold text-zinc-900 dark:text-white group-hover:text-pulse-orange transition-colors">
                  {founder.name}
                </h2>
                {/* Whether they founded alone or alongside others. Derived by
                    the API from the startup-founder join, not guessed here. */}
                <Badge
                  variant="outline"
                  className={`text-[10px] px-1.5 py-0 font-medium ${
                    founder.founder_type === 'cofounder'
                      ? 'border-violet-500/30 text-violet-700 dark:text-violet-400 bg-violet-500/10'
                      : 'border-pulse-orange/30 text-pulse-orange bg-pulse-orange/10'
                  }`}
                >
                  {founder.founder_type === 'cofounder'
                    ? en
                      ? 'Co-Founder'
                      : 'Cofondateur'
                    : en
                      ? 'Founder'
                      : 'Fondateur'}
                </Badge>
                {/* A "hiring" badge used to be awarded here to two hardcoded
                    founder ids left over from mock data. There is no hiring flag
                    on the record, so no badge is rendered rather than granting
                    one arbitrarily. */}
              </div>
              <p className="text-xs text-pulse-orange dark:text-orange-400 font-medium mt-0.5">
                {founder.role}
              </p>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">{founder.startup}</p>
              <div className="flex items-center gap-3 mt-2">
                <span className="flex items-center gap-1 text-xs text-zinc-500 dark:text-zinc-400">
                  <MapPin className="w-3 h-3" />
                  {founder.location}
                </span>
                {founder.experience && (
                  <span className="text-xs text-zinc-500 dark:text-zinc-400">
                    {founder.experience}
                  </span>
                )}
              </div>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-2 line-clamp-2 leading-relaxed">
                {founder.bio}
              </p>
            </div>
            {founder.linkedin && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  openExternal(founder.linkedin);
                }}
                aria-label={`LinkedIn profile of ${founder.name}`}
                title={`LinkedIn profile of ${founder.name}`}
                className="p-2 text-zinc-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-zinc-800 rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/50"
              >
                <Linkedin className="w-4 h-4" aria-hidden="true" />
              </button>
            )}
          </div>
        ))}
      </div>

      <LoadMore
        loaded={founders.length}
        total={total}
        hasMore={hasMore}
        isLoading={isLoadingMore}
        onLoadMore={loadMore}
      />
    </div>
  );
}

/** Shared skeleton for the two subsections below. */
function SectionSkeleton() {
  return (
    <div className="space-y-6 animate-fade-in">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-4 w-72" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Array.from({ length: 6 }).map((_, idx) => (
          <Skeleton key={idx} className="h-32 rounded-xl" />
        ))}
      </div>
    </div>
  );
}

function SectionEmpty({ message }: { message: string }) {
  return (
    <div className="p-8 text-center bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800">
      <Users className="w-8 h-8 mx-auto mb-3 text-zinc-300 dark:text-zinc-600" />
      <p className="text-sm text-zinc-500 dark:text-zinc-400">{message}</p>
    </div>
  );
}

/** "Experts & Mentors" — reads the dedicated `/experts/` directory. */
function ExpertsSection() {
  const { t, language } = useLanguage();
  const { data: experts = [], total, hasMore, isLoading, isLoadingMore, loadMore } = useExperts();

  if (isLoading) return <SectionSkeleton />;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-1">
          {t('expertsTitle')}
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">{t('expertsSubtitle')}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {experts.map((expert) => (
          <div
            key={expert.id}
            className="flex items-start gap-4 p-5 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 hover:border-zinc-200 dark:hover:border-zinc-700 hover:shadow-md transition-all group"
          >
            <div className="w-12 h-12 rounded-full overflow-hidden flex items-center justify-center flex-shrink-0 bg-white dark:bg-zinc-800 border border-zinc-150 dark:border-zinc-700/50">
              {expert.profilePic ? (
                <ImageWithFallback
                  src={expert.profilePic}
                  alt={expert.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <span className="text-base font-bold text-pulse-orange">
                  {expert.name.split(' ').map((n) => n[0]).join('')}
                </span>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-sm font-semibold text-zinc-900 dark:text-white">
                  {expert.name}
                </h2>
                {expert.availability && (
                  <Badge className="bg-orange-50 dark:bg-zinc-800 text-pulse-orange border-none text-[8px] px-1 font-bold">
                    {expert.availability}
                  </Badge>
                )}
              </div>
              {expert.title && (
                <p className="text-xs text-pulse-orange dark:text-orange-400 font-medium mt-0.5">
                  {expert.title}
                </p>
              )}
              {expert.organization && (
                <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                  {expert.organization}
                </p>
              )}
              <div className="flex items-center gap-3 mt-2">
                {expert.location && (
                  <span className="flex items-center gap-1 text-xs text-zinc-500 dark:text-zinc-400">
                    <MapPin className="w-3 h-3" />
                    {expert.location}
                  </span>
                )}
                {expert.yearsExperience && (
                  <span className="text-xs text-zinc-500 dark:text-zinc-400">
                    {expert.yearsExperience}
                  </span>
                )}
              </div>
              {expert.skills.length > 0 && (
                <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-2 line-clamp-2 leading-relaxed">
                  {expert.skills.slice(0, 5).join(' · ')}
                </p>
              )}
            </div>
            {expert.linkedin && (
              <button
                onClick={() => openExternal(expert.linkedin ?? undefined)}
                aria-label={`LinkedIn profile of ${expert.name}`}
                title={`LinkedIn profile of ${expert.name}`}
                className="p-2 text-zinc-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-zinc-800 rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/50"
              >
                <Linkedin className="w-4 h-4" aria-hidden="true" />
              </button>
            )}
          </div>
        ))}
      </div>

      {experts.length === 0 && (
        <SectionEmpty
          message={
            language === 'en'
              ? 'No experts or mentors are listed yet.'
              : "Aucun expert ou mentor n'est encore répertorié."
          }
        />
      )}

      <LoadMore
        loaded={experts.length}
        total={total}
        hasMore={hasMore}
        isLoading={isLoadingMore}
        onLoadMore={loadMore}
      />
    </div>
  );
}

/**
 * "Co-founders Needed" — reads the dedicated `/cofounders/` directory.
 *
 * These rows are project postings rather than people, so they render as
 * opportunity cards: what is being built, and which roles are open.
 */
function CofoundersSection() {
  const { t, language } = useLanguage();
  const { data: projects = [], total, hasMore, isLoading, isLoadingMore, loadMore } =
    useCofounderProjects();

  if (isLoading) return <SectionSkeleton />;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-1">
          {t('cofoundersTitle')}
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">{t('cofoundersSubtitle')}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {projects.map((project) => (
          <div
            key={project.id}
            className="p-5 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 hover:border-zinc-200 dark:hover:border-zinc-700 hover:shadow-md transition-all group"
          >
            <div className="flex items-start justify-between gap-3 mb-2">
              <h2 className="text-sm font-semibold text-zinc-900 dark:text-white leading-snug">
                {project.title}
              </h2>
              {project.stage && (
                <Badge className="bg-orange-50 dark:bg-zinc-800 text-pulse-orange border-none text-[10px] font-semibold flex-shrink-0">
                  {project.stage}
                </Badge>
              )}
            </div>

            {project.domain && (
              <p className="text-xs text-pulse-orange dark:text-orange-400 font-medium">
                {project.domain}
              </p>
            )}

            {project.description && (
              <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-2 line-clamp-2 leading-relaxed">
                {project.description}
              </p>
            )}

            {project.rolesNeeded.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-3">
                {project.rolesNeeded.slice(0, 4).map((role) => (
                  <span
                    key={role}
                    className="px-2 py-0.5 text-[10px] font-medium rounded-md bg-zinc-100 text-zinc-650 dark:bg-zinc-800 dark:text-zinc-300"
                  >
                    {role}
                  </span>
                ))}
              </div>
            )}

            <div className="border-t border-zinc-50 dark:border-zinc-800/80 pt-3 mt-3 flex items-center justify-between text-xs text-zinc-500 dark:text-zinc-400">
              <span className="truncate">{project.authorName}</span>
              <div className="flex items-center gap-2 flex-shrink-0">
                {project.equityOffered && (
                  <span className="font-semibold text-pulse-orange">{project.equityOffered}</span>
                )}
                {project.authorLinkedin && (
                  <button
                    onClick={() => openExternal(project.authorLinkedin ?? undefined)}
                    aria-label={`LinkedIn profile of ${project.authorName ?? 'author'}`}
                    title={`LinkedIn profile of ${project.authorName ?? 'author'}`}
                    className="p-1 text-zinc-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-zinc-800 rounded transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/50"
                  >
                    <Linkedin className="w-3.5 h-3.5" aria-hidden="true" />
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {projects.length === 0 && (
        <SectionEmpty
          message={
            language === 'en'
              ? 'No co-founder searches are open right now.'
              : "Aucune recherche de co-fondateur n'est ouverte actuellement."
          }
        />
      )}

      <LoadMore
        loaded={projects.length}
        total={total}
        hasMore={hasMore}
        isLoading={isLoadingMore}
        onLoadMore={loadMore}
      />
    </div>
  );
}
