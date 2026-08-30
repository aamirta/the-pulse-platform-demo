import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Globe, Linkedin, MapPin, Users, Calendar, DollarSign, Award, ChevronRight } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import MessageButton from '@/components/messaging/MessageButton';
import { useLanguage } from '@/context/LanguageContext';
import { useStartupFunding } from '@/hooks/useStartupFunding';
import { useStartup } from '@/hooks/useStartup';
import { useFounders } from '@/hooks/useFounders';
import { ImageWithFallback } from '@/components/ImageWithFallback';
import { openExternal } from '@/lib/url';

const stages: Record<string, string> = {
  SCALING: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400',
  AMORÇAGE: 'bg-blue-100 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400',
  SEED: 'bg-purple-100 text-purple-700 dark:bg-purple-950/40 dark:text-purple-400',
  'PRE-SEED': 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300',
  ACQUIRED: 'bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400',
};

export default function StartupProfile() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t, language } = useLanguage();
  const { data: startup, isLoading } = useStartup(id);
  const { data: founders = [] } = useFounders();

  // Real rounds recorded for this startup. This list used to be fabricated: a
  // "Série A" inferred from the total plus a fixed 1.2M$ Seed credited to
  // investors that had never funded the company.
  // Called before the early returns below so hook order stays stable.
  const { data: fundingHistory = [] } = useStartupFunding(startup?.name);

  if (isLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-40 rounded-xl" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <Skeleton className="h-32 rounded-xl" />
          </div>
          <Skeleton className="h-64 rounded-xl" />
        </div>
      </div>
    );
  }

  if (!startup) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-zinc-900 dark:text-white">{t('startupNotFound')}</h2>
        <Button onClick={() => navigate('/startups')} className="mt-4 bg-pulse-orange hover:bg-pulse-orange-hover text-white">
          {t('backToStartups')}
        </Button>
      </div>
    );
  }

  const startupFounders = founders.filter((f) => f.startupId === startup.id);

  return (
    <div className="space-y-6">
      {/* Back */}
      <button
        onClick={() => navigate('/startups')}
        className="inline-flex items-center gap-1.5 min-h-11 px-1 -ml-1 rounded text-sm text-zinc-500 hover:text-pulse-orange transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
      >
        <ArrowLeft className="w-4 h-4" />
        {t('backToStartups')}
      </button>

      {/* Header Info Block */}
      <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 p-6 transition-colors duration-200 ve-card-lift">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-xl overflow-hidden flex items-center justify-center flex-shrink-0 bg-white dark:bg-zinc-800 border border-zinc-150 dark:border-zinc-700/50">
              {startup.logo ? (
                <ImageWithFallback src={startup.logo} alt={startup.name} className="w-full h-full object-contain p-2" />
              ) : (
                <div className="w-full h-full bg-gradient-to-br from-pulse-orange-50 to-orange-100 dark:from-orange-950/40 dark:to-orange-900/10 flex items-center justify-center font-bold text-pulse-orange text-2xl">
                  {startup.name[0]}
                </div>
              )}
            </div>
            <div>
              <h1 className="text-xl font-bold text-zinc-900 dark:text-white">{startup.name}</h1>
              <div className="flex flex-wrap items-center gap-1.5 mt-1.5">
                {startup.sector.map((s) => (
                  <Badge
                    key={s}
                    variant="outline"
                    className="text-[10px] font-medium border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-400"
                  >
                    {s}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge
              className={`text-xs font-semibold ${stages[startup.stage] || ''}`}
            >
              {startup.stage}
            </Badge>
            <Badge
              variant="outline"
              className="text-xs font-semibold border-emerald-200 text-emerald-700 dark:border-emerald-900 dark:text-emerald-400 bg-emerald-50/50 dark:bg-emerald-950/20"
            >
              {startup.status}
            </Badge>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4 text-xs text-zinc-500 dark:text-zinc-400 mb-4">
          <span className="flex items-center gap-1.5">
            <MapPin className="w-4 h-4 text-zinc-400" />
            {startup.location}
          </span>
          <span className="flex items-center gap-1.5">
            <Calendar className="w-4 h-4 text-zinc-400" />
            {t('foundedInLabel')} {startup.yearFounded}
          </span>
          <span className="flex items-center gap-1.5">
            <Users className="w-4 h-4 text-zinc-400" />
            {startup.teamSize} {t('employeesLabel')}
          </span>
          {startup.funding > 0 && (
            <span className="flex items-center gap-1.5">
              <DollarSign className="w-4 h-4 text-zinc-400" />
              {startup.fundingCurrency}{(startup.funding / 1000000).toFixed(1)}M {t('raisedLabel')}
            </span>
          )}
        </div>

        <p className="text-sm text-zinc-600 dark:text-zinc-350 leading-relaxed mb-5">
          {startup.description}
        </p>

        <div className="flex items-center gap-2 pt-2 border-t border-zinc-50 dark:border-zinc-800">
          <MessageButton
            entityType="startup"
                showWhenUnavailable
            entityId={id}
            name={startup.name}
            className="h-9 px-4 text-xs dark:bg-zinc-800 dark:border-zinc-750 dark:hover:bg-zinc-700"
          />
          {startup.website && (
            <Button
              variant="outline"
              size="sm"
              className="h-8 text-xs dark:bg-zinc-800 dark:border-zinc-750 dark:hover:bg-zinc-700"
              onClick={() => openExternal(startup.website)}
            >
              <Globe className="w-3.5 h-3.5 mr-1.5" />
              {t('websiteButton')}
            </Button>
          )}
          {startup.linkedin && (
            <Button
              variant="outline"
              size="sm"
              className="h-8 text-xs dark:bg-zinc-800 dark:border-zinc-750 dark:hover:bg-zinc-700"
              onClick={() => openExternal(startup.linkedin)}
            >
              <Linkedin className="w-3.5 h-3.5 mr-1.5 text-blue-600 dark:text-blue-400" />
              LinkedIn
            </Button>
          )}
          <Button
            className="h-8 text-xs bg-pulse-orange hover:bg-pulse-orange-hover text-white rounded-lg ml-auto border-none"
            onClick={() => navigate(`/visualizer?highlight=${startup.id}`)}
          >
            {t('viewNetworkMap')}
          </Button>
        </div>
      </div>

      {/* Grid: Founders & Funding Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Founders Column (2 Cols) */}
        <div className="lg:col-span-2 space-y-4">
          {startupFounders.length > 0 && (
            <div>
              <h2 className="text-base font-semibold text-zinc-900 dark:text-white mb-3">{t('tabFounders')}</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {startupFounders.map((founder) => (
                  <div
                    key={founder.id}
                    onClick={() => navigate(`/founders/${founder.id}`)}
                    className="flex items-start gap-3 p-4 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 hover:border-zinc-200 dark:hover:border-zinc-700 hover:shadow-sm cursor-pointer transition-all group ve-card-lift"
                  >
                    <div className="w-10 h-10 rounded-full overflow-hidden flex items-center justify-center flex-shrink-0 bg-white dark:bg-zinc-800 border border-zinc-150 dark:border-zinc-700/50">
                      {founder.avatar ? (
                        <ImageWithFallback src={founder.avatar} alt={founder.name} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center font-bold text-blue-600 dark:text-blue-400 bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-950/40 dark:to-purple-950/20">
                          {founder.name.split(' ').map((n) => n[0]).join('')}
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-xs font-bold text-zinc-900 dark:text-white group-hover:text-pulse-orange transition-colors flex items-center justify-between">
                        {founder.name}
                        <ChevronRight className="w-3 h-3 text-zinc-400 group-hover:text-pulse-orange transition-colors" />
                      </h4>
                      <p className="text-[10px] text-pulse-orange dark:text-orange-400 font-medium">
                        {founder.role}
                      </p>
                      <p className="text-[10px] text-zinc-500 dark:text-zinc-400 mt-1 line-clamp-2 leading-relaxed">
                        {founder.bio}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Funding History Timeline (1 Col) */}
        <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 p-5 transition-colors">
          <h3 className="text-sm font-semibold text-zinc-900 dark:text-white mb-4 flex items-center gap-1.5">
            <Award className="w-4.5 h-4.5 text-pulse-orange" />
            {t('fundingHistoryTitle')}
          </h3>
          
          {fundingHistory.length > 0 ? (
            <div className="space-y-4 relative before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-zinc-100 dark:before:bg-zinc-800">
              {fundingHistory.map((hist, index) => (
                <div key={index} className="flex gap-4 relative pl-7 last:pb-0">
                  <div className="absolute left-1.5 top-1.5 w-3 h-3 rounded-full bg-pulse-orange border-2 border-white dark:border-zinc-900" />
                  <div className="space-y-0.5">
                    <span className="text-[9px] text-zinc-400 dark:text-zinc-400 block font-semibold">{hist.date}</span>
                    <h4 className="text-xs font-bold text-zinc-900 dark:text-white">
                      {hist.round}{hist.amount ? ` — ${hist.amount}` : ''}
                    </h4>
                    {hist.investor && (
                      <p className="text-[10px] text-zinc-500 dark:text-zinc-400 leading-relaxed">
                        {language === 'en' ? 'Investors' : 'Investisseurs'}: {hist.investor}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6 text-xs text-zinc-500 dark:text-zinc-500">
              {language === 'en' ? 'No funding rounds recorded (Bootstrapped).' : 'Aucune levée de fonds enregistrée (Bootstrapped).'}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
