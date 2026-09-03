import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  ArrowRight,
  TrendingUp,
  Building,
  Landmark,
  Bot,
  Zap,

} from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { GlowCard } from '@/components/ui/GlowCard';
import { FadeInImage } from '@/enhancements/FadeInImage';
import { useEnhancements } from '@/enhancements/useEnhancements';
import { useLanguage } from '@/context/LanguageContext';
import { formatAmount, formatCount } from '@/lib/utils';
import { useStats } from '@/hooks/useStats';
import { useNews } from '@/hooks/useNews';
import {
  fadeUp,
  staggerContainer,
  floatingVariant,
} from '@/lib/motion';

export default function HeroSection() {
  const navigate = useNavigate();
  const { t, language } = useLanguage();
  // This card is badged "Live", so every figure in it must come from the API.
  // It previously rendered hard-coded literals.
  const { data: stats } = useStats();
  const { data: news = [] } = useNews();
  const ticker = news.slice(0, 2);
  const enhanced = useEnhancements();

  return (
    <div className="relative overflow-hidden pt-4 pb-8 sm:py-12">
      {/* Subtle Background Glow - Controlled Muted Terracotta Warm Mesh */}
      <div className="absolute top-[-10%] left-1/2 -translate-x-1/2 w-[750px] h-[450px] bg-pulse-orange/10 blur-[140px] rounded-full pointer-events-none -z-10" />

      {/* Enhancement layer: low-opacity backdrop using the existing, previously
          unused brand illustration. Absolutely positioned inside the existing
          relative hero — zero layout impact, and only rendered when the
          enhancement flag is on. */}
      {enhanced && (
        <div className="ve-hero-backdrop -z-10" aria-hidden="true">
          <FadeInImage src="/hero-illustration.jpg" alt="" loading="eager" />
        </div>
      )}

      {/* Main Container */}
      <motion.div
        variants={staggerContainer(0.1, 0.05)}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center"
      >
        {/* Left Column: Headlines & CTAs (Span 7) */}
        <div className="lg:col-span-7 space-y-6 text-left">
          {/* Badge */}
          <motion.div variants={fadeUp} className="inline-block">
            <span className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-pulse-orange/10 border border-pulse-orange/25 text-pulse-orange text-xs font-bold tracking-wide shadow-soft-sm">
              {/* This badge used to redraw the wordmark from a text pair plus
                  an animated SVG pulse line -- a second lockup competing with
                  the official logo in the header. It now carries the tagline. */}
              <Sparkles className="w-3.5 h-3.5 animate-pulse" aria-hidden="true" />
              <span className="text-[11px] font-semibold tracking-normal text-foreground">
                {t('heroBadge')}
              </span>
            </span>
          </motion.div>

          {/* Main Title */}
          <motion.h1
            variants={fadeUp}
            /* Tailwind's text-* utilities set a line-height too, so the
               responsive `sm:`/`lg:` sizes were overriding `leading-[1.1]`
               from inside their media queries and setting the heading solid
               at 1.0. The leading is repeated per breakpoint so it survives. */
            className="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-foreground leading-[1.1] sm:leading-[1.1] lg:leading-[1.1]"
          >
            {t('heroTitlePrefix')}
            {t('heroTitleHighlight') && (
              <> <span className="text-pulse-orange">{t('heroTitleHighlight')}</span></>
            )}
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            variants={fadeUp}
            className="text-sm sm:text-lg text-muted-foreground max-w-2xl leading-relaxed font-normal"
          >
            {t('heroSubtitle')}
          </motion.p>

          {/* CTAs */}
          <motion.div
            variants={fadeUp}
            className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 pt-2"
          >
            <Button
              onClick={() => navigate('/startups')}
              className="h-12 px-6 bg-pulse-orange hover:bg-pulse-orange-hover text-primary-foreground font-bold text-sm rounded-xl shadow-soft-md hover:shadow-soft-lg transition-all duration-200 ease-in-out flex items-center justify-center gap-2 group"
            >
              {t('heroCtaPrimary')}
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Button>

            <Button
              onClick={() => navigate('/register')}
              variant="outline"
              className="h-12 px-6 border-border/50 hover:bg-secondary/70 text-foreground font-semibold text-sm rounded-xl transition-all duration-200 ease-in-out flex items-center justify-center gap-2 shadow-soft-sm"
            >
              <Zap className="w-4 h-4 text-pulse-orange" aria-hidden="true" />
              {t('heroCtaSecondary')}
            </Button>
          </motion.div>

          {/* Trust Highlights */}
          <motion.div
            variants={fadeUp}
            className="pt-4 flex flex-wrap items-center gap-4 text-xs font-semibold text-muted-foreground border-t border-border/40"
          >
            {/* Same figures as the KPI tiles below, from the same request.
                These were hard-coded ("1 900+ startups") against the live
                thepulse.ma numbers, so the trust line and the counters a
                screen apart disagreed. */}
            <div className="flex items-center gap-1.5">
              <Building className="w-4 h-4 text-pulse-orange" aria-hidden="true" />
              <span>
                {stats ? `${formatCount(stats.startups, language)} ` : ''}
                {t('heroStat1')}
              </span>
            </div>
            <span aria-hidden="true">•</span>
            <div className="flex items-center gap-1.5">
              <Landmark className="w-4 h-4 text-emerald-700 dark:text-emerald-400" aria-hidden="true" />
              <span>
                {stats ? `${formatCount(stats.founders, language)} ` : ''}
                {t('heroStat2')}
              </span>
            </div>
            <span aria-hidden="true">•</span>
            <div className="flex items-center gap-1.5">
              <Zap className="w-4 h-4 text-amber-500" aria-hidden="true" />
              <span>
                {stats?.totalFunding ? `${formatAmount(stats.totalFunding, language)} ` : ''}
                {t('heroStat3')}
              </span>
            </div>
          </motion.div>
        </div>

        {/* Right Column: Live Module Widget (Span 5) */}
        <motion.div variants={fadeUp} className="lg:col-span-5 relative">
          <GlowCard className="p-6 bg-card/90 backdrop-blur-xl border border-border/50 shadow-soft-lg">
            
            {/* Header of Preview Box */}
            <div className="flex items-center justify-between pb-4 border-b border-border/40">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-muted-foreground/30" />
                <div className="w-3 h-3 rounded-full bg-muted-foreground/30" />
                <div className="w-3 h-3 rounded-full bg-muted-foreground/30" />
                <span className="ml-2 text-xs font-semibold text-muted-foreground">
                  {t('heroLiveWidgetTitle')}
                </span>
              </div>
              <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
                Live
              </span>
            </div>

            {/* Content Stats Box */}
            <div className="py-4 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3.5 rounded-xl bg-secondary/40 border border-border/40 shadow-soft-sm">
                  <span className="text-[11px] font-extrabold text-muted-foreground tracking-wide block mb-1">
                    {t('heroLiveMonthlyFunding')}
                  </span>
                  <span className="text-xl font-black text-foreground flex items-center gap-1">
                    {stats?.totalFunding ? formatAmount(stats.totalFunding, language) : '—'}
                    <TrendingUp className="w-4 h-4 text-emerald-700 dark:text-emerald-400" />
                  </span>
                </div>
                <div className="p-3.5 rounded-xl bg-secondary/40 border border-border/40 shadow-soft-sm">
                  <span className="text-[11px] font-extrabold text-muted-foreground tracking-wide block mb-1">
                    {t('heroLiveAiMatchmaking')}
                  </span>
                  <span className="text-xl font-black text-pulse-orange flex items-center gap-1">
                    {stats?.fundingRounds ?? '—'}
                    <Bot className="w-4 h-4 text-pulse-orange" />
                  </span>
                </div>
              </div>

              {/* Ticker Activity Stream */}
              <div className="space-y-2">
                <span className="text-[11px] font-bold text-muted-foreground tracking-wide">
                  {t('heroLiveActivityStream')}
                </span>
                
                {ticker.map((item) => (
                  <div
                    key={item.id}
                    className="p-3 rounded-xl bg-secondary/30 border border-border/40 flex items-center justify-between text-xs shadow-soft-sm"
                  >
                    <div className="flex items-center gap-2 truncate">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          item.type === 'funding' ? 'bg-pulse-orange' : 'bg-emerald-500'
                        }`}
                      />
                      <span className="font-bold text-foreground truncate">{item.source}</span>
                      <span className="text-muted-foreground truncate">{item.title}</span>
                    </div>
                    {item.amount && (
                      <span className="text-[11px] font-mono text-muted-foreground shrink-0">
                        {item.amount}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Floating Accent Tag */}
            <motion.div
              variants={floatingVariant}
              animate="animate"
              className="absolute -bottom-4 -right-4 bg-popover text-popover-foreground text-xs font-extrabold px-4 py-2 rounded-xl shadow-soft-md flex items-center gap-2 border border-border/50"
            >
              <Sparkles className="w-4 h-4 text-pulse-orange" />
              {t('heroSupportedBy')}
            </motion.div>
          </GlowCard>
        </motion.div>
      </motion.div>

    </div>
  );
}
