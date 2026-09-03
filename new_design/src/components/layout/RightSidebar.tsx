import { useNavigate } from 'react-router-dom';
import { ArrowUpRight, Sparkles, Send } from 'lucide-react';
import { useTrends, useLatestFunding } from '@/hooks/useSidebarData';
import { useLanguage } from '@/context/LanguageContext';

export default function RightSidebar() {
  const navigate = useNavigate();
  const { t, language } = useLanguage();
  // Real ecosystem data; these two lists were previously static fixtures.
  const { data: trends = [] } = useTrends();
  const { data: fundingRounds = [] } = useLatestFunding();

  const samplePrompts = language === 'fr' 
    ? [
        'Quelles sont les startups fintech au Maroc ?',
        'Qui lève des fonds en ce moment ?',
        'Montre-moi les incubateurs à Casablanca',
      ]
    : [
        'Which startups are in fintech in Morocco?',
        'Who is raising funds right now?',
        'Show me incubators in Casablanca',
      ];

  return (
    <div className="space-y-6">
      {/* Trends */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-base font-semibold text-foreground">{t('trendsTitle')}</h3>
          <button
            onClick={() => navigate('/search')}
            className="inline-flex items-center min-h-11 px-1 text-xs text-muted-foreground hover:text-pulse-orange transition-all duration-200 ease-in-out rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
          >
            {language === 'fr' ? 'Voir tout' : 'View all'}
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {trends.map((trend) => (
            <button
              key={trend.tag}
              onClick={() => navigate(`/search?q=${trend.tag}`)}
              className="inline-flex items-center gap-1 px-3.5 py-1.5 bg-secondary/70 hover:bg-secondary border border-border/40 rounded-full text-xs font-medium text-foreground/90 shadow-soft-sm transition-all duration-200 ease-in-out"
            >
              #{trend.tag}
              <ArrowUpRight className="w-3 h-3 text-muted-foreground" />
            </button>
          ))}
        </div>
      </div>

      {/* Latest Funding */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-base font-semibold text-foreground">
            {t('latestFundraises')}
          </h3>
          <button
            onClick={() => navigate('/startups')}
            className="inline-flex items-center min-h-11 px-1 text-xs text-muted-foreground hover:text-pulse-orange transition-all duration-200 ease-in-out rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
          >
            {language === 'fr' ? 'Voir tout' : 'View all'}
          </button>
        </div>
        <div className="space-y-3">
          {fundingRounds.map((round) => (
            <div
              key={round.id}
              className="flex items-start gap-3 p-3 bg-card/90 rounded-xl border border-border/40 shadow-soft-sm hover:shadow-soft-md hover:border-border/70 transition-all duration-200 ease-in-out cursor-pointer"
              onClick={() => navigate(`/search?q=${encodeURIComponent(round.startup)}`)}
            >
              <div className="w-10 h-10 rounded-full bg-pulse-orange/15 text-pulse-orange flex items-center justify-center flex-shrink-0 font-bold text-sm">
                {round.startup?.[0] ?? '?'}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-semibold text-foreground truncate">
                    {round.startup}
                  </span>
                  <span className="text-sm font-bold text-foreground">
                    {round.amount}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="text-[11px] text-muted-foreground">{round.round}</span>
                  {/* Decorative separator: hidden from assistive tech, and at
                      full token opacity so it stays legible (it read 2.2:1). */}
                  <span className="text-[11px] text-muted-foreground" aria-hidden="true">•</span>
                  <span className="text-[11px] text-muted-foreground truncate">
                    {round.investor}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* PulseGPT */}
      <div className="p-4 bg-card/80 border border-border/40 rounded-xl space-y-3 shadow-soft-sm">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-pulse-orange" />
          <h3 className="text-sm font-semibold text-foreground">{t('pulseGptTitle')}</h3>
          <span className="px-1.5 py-0.5 text-[11px] font-semibold text-pulse-orange border border-pulse-orange/30 rounded">
            BETA
          </span>
        </div>
        <p className="text-xs text-muted-foreground">
          {t('pulseGptSub')}
        </p>
        <div className="space-y-2">
          {samplePrompts.map((prompt) => (
            <button
              key={prompt}
              onClick={() => navigate('/ai-assistant')}
              className="w-full text-left px-3 py-2 text-xs text-foreground/90 bg-secondary/40 border border-border/50 rounded-lg hover:border-pulse-orange/40 shadow-soft-sm transition-all duration-200 ease-in-out"
            >
              {prompt}
            </button>
          ))}
        </div>
        <div className="relative">
          <input
            type="text"
            placeholder={t('pulseGptPlaceholder')}
            aria-label={t('pulseGptPlaceholder')}
            className="w-full h-9 pl-3 pr-9 text-xs bg-secondary/40 border border-border/50 rounded-lg placeholder:text-muted-foreground focus:outline-none focus:border-pulse-orange/40 shadow-soft-sm transition-all duration-200 ease-in-out text-foreground cursor-pointer"
            onClick={() => navigate('/ai-assistant')}
            // Enter opens the assistant. Navigating on focus instead would hijack
            // Tab and make the sidebar impossible to move through by keyboard.
            onKeyDown={(event) => {
              if (event.key === 'Enter') navigate('/ai-assistant');
            }}
            readOnly
          />
          <button
            onClick={() => navigate('/ai-assistant')}
            aria-label={t('pulseGptTitle')}
            className="absolute right-1.5 top-1/2 -translate-y-1/2 inline-flex items-center justify-center min-w-6 min-h-6 p-1 rounded text-muted-foreground hover:text-pulse-orange transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
          >
            <Send className="w-3.5 h-3.5" aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  );
}
