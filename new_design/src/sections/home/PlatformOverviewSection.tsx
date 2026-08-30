import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  Bot,
  Network,
  Briefcase,
  Sparkles,
  ArrowUpRight,
  Zap,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { ScrollReveal } from '@/components/ui/ScrollReveal';
import { GlowCard } from '@/components/ui/GlowCard';
import { Button } from '@/components/ui/button';
import { fadeUp } from '@/lib/motion';
import { useLanguage } from '@/context/LanguageContext';
import { useStats } from '@/hooks/useStats';

export default function PlatformOverviewSection() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  // Pillar figures are read from the ecosystem, not hard-coded: the old
  // literals understated startups (500+ vs 1109) and overstated programmes.
  const { data: stats } = useStats();
  const fmt = (n: number | undefined) => (n === undefined ? '—' : n.toLocaleString('fr-FR'));
  const [activePillar, setActivePillar] = useState<'dealflow' | 'ai' | 'visualizer' | 'opportunities'>('dealflow');

  const pillars = [
    {
      id: 'dealflow' as const,
      icon: <Building2 className="w-5 h-5" />,
      title: t('pillar1Title'),
      subtitle: t('pillar1Subtitle'),
      description: t('pillar1Desc'),
      actionText: t('pillar1Action'),
      route: '/startups',
      statLabel: t('pillar1StatLabel'),
      statValue: fmt(stats?.startups),
    },
    {
      id: 'ai' as const,
      icon: <Bot className="w-5 h-5" />,
      title: t('pillar2Title'),
      subtitle: t('pillar2Subtitle'),
      description: t('pillar2Desc'),
      actionText: t('pillar2Action'),
      route: '/ai-assistant',
      statLabel: t('pillar2StatLabel'),
      statValue: fmt(stats?.sectors),
    },
    {
      id: 'visualizer' as const,
      icon: <Network className="w-5 h-5" />,
      title: t('pillar3Title'),
      subtitle: t('pillar3Subtitle'),
      description: t('pillar3Desc'),
      actionText: t('pillar3Action'),
      route: '/visualizer',
      statLabel: t('pillar3StatLabel'),
      statValue: fmt(stats?.founders),
    },
    {
      id: 'opportunities' as const,
      icon: <Briefcase className="w-5 h-5" />,
      title: t('pillar4Title'),
      subtitle: t('pillar4Subtitle'),
      description: t('pillar4Desc'),
      actionText: t('pillar4Action'),
      route: '/opportunities',
      statLabel: t('pillar4StatLabel'),
      statValue: fmt(stats?.incubators),
    },
  ];

  const currentPillar = pillars.find((p) => p.id === activePillar)!;

  return (
    <ScrollReveal variants={fadeUp} className="w-full py-8 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2 max-w-3xl mx-auto">
        <span className="text-xs font-extrabold uppercase tracking-widest text-pulse-orange flex items-center justify-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5" />
          {t('overviewTag')}
        </span>
        <h2 className="text-2xl sm:text-4xl font-extrabold text-foreground tracking-tight">
          {t('overviewTitle')}
        </h2>
        <p className="text-xs sm:text-base text-muted-foreground">
          {t('overviewSubtitle')}
        </p>
      </div>

      {/* Pillar Tabs Bar */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {pillars.map((pillar) => {
          const isSelected = activePillar === pillar.id;
          return (
            <button
              key={pillar.id}
              onClick={() => setActivePillar(pillar.id)}
              className={`p-4 rounded-2xl border text-left transition-all duration-200 ease-in-out relative overflow-hidden flex flex-col justify-between ${
                isSelected
                  ? 'bg-card border-pulse-orange/70 shadow-soft-md scale-[1.01]'
                  : 'bg-secondary/40 border-border/40 hover:bg-secondary/70 shadow-soft-sm'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div
                    className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold transition-all duration-200 ease-in-out ${
                      isSelected
                        ? 'bg-pulse-orange text-primary-foreground shadow-soft-sm'
                        : 'bg-muted text-muted-foreground'
                    }`}
                  >
                    {pillar.icon}
                  </div>
                  {isSelected && (
                    <span className="w-2 h-2 rounded-full bg-pulse-orange animate-pulse" />
                  )}
                </div>
                <h3 className="text-sm font-extrabold text-foreground mb-1">
                  {pillar.title}
                </h3>
                <p className="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed">
                  {pillar.subtitle}
                </p>
              </div>

              <div className="mt-3 pt-2 border-t border-border/40 flex items-center justify-between text-[10px] font-bold text-muted-foreground">
                <span>{pillar.statLabel}</span>
                <span className="text-foreground font-black">{pillar.statValue}</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Active Tab Preview Showcase Box */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activePillar}
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -15 }}
          transition={{ duration: 0.2, ease: 'easeInOut' }}
        >
          <GlowCard className="p-6 sm:p-10 bg-card border border-border/50 shadow-soft-lg">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              
              {/* Pillar Text Description (Span 7) */}
              <div className="lg:col-span-7 space-y-4">
                <div className="flex items-center gap-2">
                  <span className="p-2 rounded-xl bg-pulse-orange/15 text-pulse-orange">
                    {currentPillar.icon}
                  </span>
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-pulse-orange">
                    {t('overviewModuleTag')}
                  </span>
                </div>

                <h3 className="text-2xl sm:text-3xl font-extrabold text-foreground tracking-tight">
                  {currentPillar.title}
                </h3>

                <p className="text-xs sm:text-base text-muted-foreground leading-relaxed">
                  {currentPillar.description}
                </p>

                <div className="pt-4">
                  <Button
                    onClick={() => navigate(currentPillar.route)}
                    className="h-11 px-6 bg-pulse-orange hover:bg-pulse-orange-hover text-primary-foreground font-bold text-xs rounded-xl shadow-soft-sm hover:shadow-soft-md transition-all duration-200 ease-in-out flex items-center gap-2"
                  >
                    {currentPillar.actionText}
                    <ArrowUpRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Interactive Visual Graphic Representation (Span 5) */}
              <div className="lg:col-span-5 p-6 rounded-2xl bg-secondary/60 text-foreground border border-border/50 space-y-4 relative overflow-hidden shadow-soft-md">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-mono text-muted-foreground uppercase">
                    {t('overviewComponentIndicator')}
                  </span>
                  <Zap className="w-4 h-4 text-pulse-orange" />
                </div>

                <div className="space-y-3">
                  <div className="p-3 rounded-xl bg-card/70 border border-border/40 flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">{t('overviewCoverageLabel')}</span>
                    <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">{t('overviewCoverageValue')}</span>
                  </div>
                  <div className="p-3 rounded-xl bg-card/70 border border-border/40 flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">{t('overviewApiLabel')}</span>
                    <span className="font-mono font-bold text-pulse-orange">{t('overviewApiValue')}</span>
                  </div>
                </div>

                <div className="pt-2 text-[10px] text-muted-foreground font-mono flex items-center gap-1">
                  <Sparkles className="w-3 h-3 text-pulse-orange" />
                  <span>{t('overviewSyncInfo')}</span>
                </div>
              </div>

            </div>
          </GlowCard>
        </motion.div>
      </AnimatePresence>
    </ScrollReveal>
  );
}
