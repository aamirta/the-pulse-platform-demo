import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  Sparkles,
  Network,
  ShieldCheck,
  Zap,
  ArrowUpRight,
  BarChart,
  Bot,
  Search,
} from 'lucide-react';
import { ScrollReveal } from '@/components/ui/ScrollReveal';
import { GlowCard } from '@/components/ui/GlowCard';
import { fadeUp, staggerContainer } from '@/lib/motion';
import { motion } from 'framer-motion';
import { useLanguage } from '@/context/LanguageContext';
import { useFundingBySector } from '@/hooks/useFundingBySector';

export default function FeaturesBentoSection() {
  const navigate = useNavigate();
  // Measured split, replacing the invented "Fintech & Payments 32%" figures.
  const { data: sectors } = useFundingBySector();
  const topSectors = (() => {
    if (!sectors?.values?.length) return [];
    const total = sectors.values.reduce((a, b) => a + b, 0);
    if (!total) return [];
    return sectors.labels.slice(0, 2).map((label, i) => ({
      label,
      share: Math.round((sectors.values[i] / total) * 100),
    }));
  })();
  const { t } = useLanguage();

  return (
    <ScrollReveal variants={fadeUp} className="w-full py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <span className="text-xs font-extrabold tracking-wide text-pulse-orange flex items-center gap-1.5 mb-1">
            <Zap className="w-3.5 h-3.5" />
            {t('bentoTag')}
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-foreground tracking-tight">
            {t('bentoTitle')}
          </h2>
        </div>
        <p className="text-xs sm:text-sm text-muted-foreground max-w-md">
          {t('bentoSubtitle')}
        </p>
      </div>

      {/* Bento Grid */}
      <motion.div
        variants={staggerContainer(0.08)}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.15 }}
        className="grid grid-cols-1 md:grid-cols-12 gap-4"
      >
        {/* 1. Large Card: Real-time Analytics (Span 7) */}
        <motion.div variants={fadeUp} className="md:col-span-7">
          <GlowCard
            onClick={() => navigate('/analytics')}
            className="p-6 sm:p-8 flex flex-col justify-between h-full bg-card border border-border/40 shadow-soft-sm hover:shadow-soft-md transition-all duration-200 ease-in-out"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="w-10 h-10 rounded-xl bg-pulse-orange/15 text-pulse-orange flex items-center justify-center font-bold">
                  <BarChart className="w-5 h-5" />
                </div>
                <span className="inline-flex items-center gap-1 text-[11px] font-extrabold tracking-wide text-pulse-orange bg-pulse-orange/10 px-2.5 py-1 rounded-full">
                  {t('bentoLiveBadge')}
                </span>
              </div>
              <h3 className="text-xl font-extrabold text-foreground mb-2">
                {t('bento1Title')}
              </h3>
              <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed mb-6">
                {t('bento1Desc')}
              </p>
            </div>

            {/* Visual Mini Chart Representation */}
            <div className="p-4 rounded-2xl bg-secondary/40 border border-border/40 shadow-soft-sm space-y-3">
              <div className="flex items-center justify-between text-xs font-bold text-foreground">
                <span>{t('bentoChartTitle')}</span>
                <TrendingUp className="w-3.5 h-3.5 text-emerald-700 dark:text-emerald-400" aria-hidden="true" />
              </div>
              <div className="space-y-2">
                {topSectors.map((s, i) => (
                  <div key={s.label}>
                    <div className="flex justify-between text-[11px] text-muted-foreground mb-1">
                      <span>{s.label}</span>
                      <span>{s.share} %</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
                      <div
                        className={i === 0 ? 'h-full bg-pulse-orange' : 'h-full bg-muted-foreground/60'}
                        style={{ width: `${s.share}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </GlowCard>
        </motion.div>

        {/* 2. Medium Card: AI Matchmaking (Span 5) */}
        <motion.div variants={fadeUp} className="md:col-span-5">
          <GlowCard
            onClick={() => navigate('/ai-assistant')}
            className="p-6 sm:p-8 flex flex-col justify-between h-full bg-card border border-border/40 shadow-soft-sm hover:shadow-soft-md transition-all duration-200 ease-in-out"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="w-10 h-10 rounded-xl bg-pulse-orange/15 text-pulse-orange flex items-center justify-center font-bold">
                  <Bot className="w-5 h-5" />
                </div>
                <ArrowUpRight className="w-5 h-5 text-muted-foreground" />
              </div>
              <h3 className="text-xl font-extrabold text-foreground mb-2">
                {t('bento2Title')}
              </h3>
              <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed mb-4">
                {t('bento2Desc')}
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-secondary/40 border border-border/40 shadow-soft-sm flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-pulse-orange flex-shrink-0" />
              <span className="text-xs text-muted-foreground truncate font-mono">
                {t('bentoAiPrompt')}
              </span>
            </div>
          </GlowCard>
        </motion.div>

        {/* 3. Medium Card: Visualizer (Span 4) */}
        <motion.div variants={fadeUp} className="md:col-span-4">
          <GlowCard
            onClick={() => navigate('/visualizer')}
            className="p-6 flex flex-col justify-between h-full bg-card border border-border/40 shadow-soft-sm hover:shadow-soft-md transition-all duration-200 ease-in-out"
          >
            <div>
              <div className="w-10 h-10 rounded-xl bg-pulse-orange/15 text-pulse-orange flex items-center justify-center font-bold mb-4">
                <Network className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-foreground mb-1">
                {t('bento3Title')}
              </h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {t('bento3Desc')}
              </p>
            </div>
            <span className="text-xs font-bold text-pulse-orange flex items-center gap-1 mt-4">
              {t('bento3Action')} <ArrowUpRight className="w-3.5 h-3.5" />
            </span>
          </GlowCard>
        </motion.div>

        {/* 4. Medium Card: Verified Dealflow (Span 4) */}
        <motion.div variants={fadeUp} className="md:col-span-4">
          <GlowCard
            onClick={() => navigate('/investors')}
            className="p-6 flex flex-col justify-between h-full bg-card border border-border/40 shadow-soft-sm hover:shadow-soft-md transition-all duration-200 ease-in-out"
          >
            <div>
              <div className="w-10 h-10 rounded-xl bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 flex items-center justify-center font-bold mb-4">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-foreground mb-1">
                {t('bento4Title')}
              </h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {t('bento4Desc')}
              </p>
            </div>
            <span className="text-xs font-bold text-emerald-700 dark:text-emerald-400 flex items-center gap-1 mt-4">
              {t('bento4Action')} <ArrowUpRight className="w-3.5 h-3.5" />
            </span>
          </GlowCard>
        </motion.div>

        {/* 5. Medium Card: Open Search (Span 4) */}
        <motion.div variants={fadeUp} className="md:col-span-4">
          <GlowCard
            onClick={() => navigate('/search')}
            className="p-6 flex flex-col justify-between h-full bg-card border border-border/40 shadow-soft-sm hover:shadow-soft-md transition-all duration-200 ease-in-out"
          >
            <div>
              <div className="w-10 h-10 rounded-xl bg-secondary text-foreground flex items-center justify-center font-bold mb-4">
                <Search className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-foreground mb-1">
                {t('bento5Title')}
              </h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {t('bento5Desc')}
              </p>
            </div>
            <span className="text-xs font-bold text-foreground flex items-center gap-1 mt-4">
              {t('bento5Action')} <ArrowUpRight className="w-3.5 h-3.5" />
            </span>
          </GlowCard>
        </motion.div>
      </motion.div>
    </ScrollReveal>
  );
}
