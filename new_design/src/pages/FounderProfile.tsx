import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, MapPin, Building, Globe, Linkedin, Sparkles } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { FadeInImage } from '@/enhancements/FadeInImage';
import { Button } from '@/components/ui/button';
import MessageButton from '@/components/messaging/MessageButton';
import { Badge } from '@/components/ui/badge';
import { useLanguage } from '@/context/LanguageContext';
import { useFounder } from '@/hooks/useFounder';
import { openExternal } from '@/lib/url';

export default function FounderProfile() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t, language } = useLanguage();
  const { data: founder, isLoading } = useFounder(id);

  if (isLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-48 rounded-xl" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <Skeleton className="h-32 rounded-xl" />
          </div>
          <Skeleton className="h-64 rounded-xl" />
        </div>
      </div>
    );
  }

  if (!founder) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-zinc-900 dark:text-white">{t('founderNotFound')}</h2>
        <Button onClick={() => navigate('/founders')} className="mt-4 bg-pulse-orange hover:bg-pulse-orange-hover text-primary-foreground">
          {t('backToFounders')}
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back */}
      <button
        onClick={() => navigate('/founders')}
        className="inline-flex items-center gap-1.5 min-h-11 px-1 -ml-1 rounded text-sm text-zinc-500 hover:text-pulse-orange transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
      >
        <ArrowLeft className="w-4 h-4" />
        {t('backToFounders')}
      </button>

      {/* Main Profile Info Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left 2 Cols: Details */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 p-6 transition-colors duration-200 ve-card-lift">
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 mb-4">
              <div className="w-20 h-20 rounded-full overflow-hidden flex items-center justify-center flex-shrink-0 border-2 border-white dark:border-zinc-800 shadow-md bg-white dark:bg-zinc-850">
                {founder.avatar ? (
                  <FadeInImage src={founder.avatar} alt={founder.name} className="w-full h-full object-cover" />
                ) : (
                  <span className="text-2xl font-bold text-blue-700 dark:text-blue-400">
                    {founder.name.split(' ').map((n) => n[0]).join('')}
                  </span>
                )}
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">{founder.name}</h1>
                  <Badge className="bg-pulse-orange/15 dark:bg-pulse-orange/20 text-pulse-orange dark:text-orange-400 font-semibold border-none text-[11px]">
                    Top Founder
                  </Badge>
                </div>
                <p className="text-sm font-medium text-pulse-orange dark:text-orange-400 flex items-center gap-1">
                  {founder.role} {language === 'en' ? 'at' : 'chez'}{' '}
                  <button 
                    onClick={() => navigate(`/startups/${founder.startupId}`)}
                    className="underline hover:text-pulse-orange-hover flex items-center gap-0.5 inline-flex align-baseline font-bold"
                  >
                    <Building className="w-3.5 h-3.5 inline" /> {founder.startup}
                  </button>
                </p>
                <div className="flex items-center gap-3 text-xs text-zinc-600 dark:text-zinc-300 pt-1">
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5" />
                    {founder.location || 'Casablanca, Morocco'}
                  </span>
                  {founder.experience && (
                    <>
                      <span>•</span>
                      <span>{founder.experience}</span>
                    </>
                  )}
                </div>
              </div>
            </div>

            <p className="text-sm text-zinc-600 dark:text-zinc-350 leading-relaxed mb-6 whitespace-pre-line">
              {founder.bio || (language === 'en'
                ? "Passionate entrepreneur building innovative technology solutions to boost the local and regional economy. Actively engaged in mentorship and expanding the startup ecosystem in Morocco."
                : "Entrepreneur passionné développant des solutions technologiques innovantes pour dynamiser l'économie locale et régionale. Engagé activement dans le mentorat et l'expansion de l'écosystème startup au Maroc.")}
            </p>

            <div className="flex items-center gap-2 pt-2">
              <MessageButton
                entityType="founder"
                showWhenUnavailable
                entityId={id}
                name={founder.name}
                className="h-8 text-xs dark:bg-zinc-800 dark:border-zinc-750 dark:hover:bg-zinc-700"
              />
              {founder.linkedin && (
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 text-xs dark:bg-zinc-800 dark:border-zinc-750 dark:hover:bg-zinc-700"
                  onClick={() => openExternal(founder.linkedin)}
                >
                  <Linkedin className="w-3.5 h-3.5 mr-1.5 text-blue-600 dark:text-blue-400" />
                  {t('linkedinProfile')}
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                className="h-8 text-xs dark:bg-zinc-800 dark:border-zinc-750 dark:hover:bg-zinc-700"
                onClick={() => navigate(`/visualizer?highlight=${founder.id}`)}
              >
                <Globe className="w-3.5 h-3.5 mr-1.5 text-pulse-orange" />
                {t('relationalNetwork')}
              </Button>
            </div>
          </div>

          {/* A speaking-engagements list was rendered here from hardcoded
              talks attributed to this founder. It is removed rather than
              fabricated; there is no speaking data in the backend. */}
        </div>

        {/* Right 1 Col: Influence score + Mentoring */}
        <div className="space-y-6">
          {/* An "influence score" gauge, a mentorship list and a publications
              list were rendered here from hardcoded values attributed to real,
              named founders. None of it is backed by data, so this column now
              shows only fields the record actually contains. */}
          <div className="bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 p-6 transition-colors duration-200">
            <h3 className="text-sm font-semibold text-zinc-900 dark:text-white mb-4 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-pulse-orange" />
              {language === 'en' ? 'Expertise' : 'Expertise'}
            </h3>
            {founder.skills ? (
              <div className="flex flex-wrap gap-2">
                {founder.skills
                  .split(/[,\n]/)
                  .map((skill) => skill.trim())
                  .filter(Boolean)
                  .map((skill) => (
                    <span
                      key={skill}
                      className="text-[11px] px-2 py-1 bg-zinc-50 dark:bg-zinc-800/40 border border-zinc-100 dark:border-zinc-800 rounded text-zinc-700 dark:text-zinc-300"
                    >
                      {skill}
                    </span>
                  ))}
              </div>
            ) : (
              <p className="text-xs text-zinc-600 dark:text-zinc-300">
                {language === 'en' ? 'No expertise listed yet.' : 'Aucune expertise renseignée.'}
              </p>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
