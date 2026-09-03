import { useNavigate } from 'react-router-dom';
import HeroSection from '@/sections/home/HeroSection';
import StatsSection from '@/sections/home/StatsSection';
import NewsFeed from '@/sections/home/NewsFeed';
import PlatformOverviewSection from '@/sections/home/PlatformOverviewSection';
import FeaturesBentoSection from '@/sections/home/FeaturesBentoSection';
import MentorPartnerSection from '@/sections/home/MentorPartnerSection';
import SuccessStoriesSection from '@/sections/home/SuccessStoriesSection';
import FAQSection from '@/sections/home/FAQSection';

import { Skeleton } from '@/components/ui/skeleton';
import { FadeInImage } from '@/enhancements/FadeInImage';
import { ScrollReveal } from '@/components/ui/ScrollReveal';
import { GlowCard } from '@/components/ui/GlowCard';
import { fadeUp, staggerContainer } from '@/lib/motion';
import { motion } from 'framer-motion';
import { Rocket, Landmark, ChevronRight } from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';
import { useStartups } from '@/hooks/useStartups';
import { useInvestors } from '@/hooks/useInvestors';
import { ImageWithFallback } from '@/components/ImageWithFallback';

export default function Home() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const { data: startups = [], isLoading: startupsLoading } = useStartups();
  const { data: investors = [], isLoading: investorsLoading } = useInvestors();

  // Get top startups by funding to show in Trending
  const trendingStartups = startups
    .filter((s) => ['spore-bio', 'woliz', 'chari'].includes(s.id))
    .slice(0, 3);

  // Get active investors
  const activeInvestors = investors
    .filter((i) => ['um6p-ventures', '212-founders', 'maroc-numeric-fund'].includes(i.id))
    .slice(0, 3);

  return (
    <div className="space-y-10 pb-10 max-w-[1400px] mx-auto">
      
      {/* 1. Hero Section */}
      <HeroSection />

      {/* 2. Key Metrics Row */}
      <StatsSection />

      {/* 3. News Feed */}
      <NewsFeed />

      {/* 4. Platform 4-Pillar Overview */}
      <PlatformOverviewSection />

      {/* 5. Trending Startups & Active Investors Panels */}
      <ScrollReveal variants={fadeUp} className="w-full">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* Trending Startups Panel */}
          <GlowCard className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-zinc-900 dark:text-white flex items-center gap-2">
                <Rocket className="w-4 h-4 text-pulse-orange" />
                {t('trendingStartupsTitle')}
              </h3>
              <button
                onClick={() => navigate('/startups')}
                className="inline-flex items-center gap-0.5 min-h-11 px-1 text-xs font-bold text-zinc-600 dark:text-zinc-300 hover:text-pulse-orange transition-colors rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
              >
                {t('seeAll')} <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <motion.div
              variants={staggerContainer(0.06)}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.2 }}
              className="space-y-3"
            >
              {startupsLoading ? (
                Array.from({ length: 3 }).map((_, idx) => (
                  <div key={idx} className="flex items-center gap-3 p-3 rounded-xl">
                    <Skeleton className="w-10 h-10 rounded-lg" />
                    <div className="flex-1 space-y-1.5">
                      <Skeleton className="h-3 w-24" />
                      <Skeleton className="h-2.5 w-32" />
                    </div>
                    <Skeleton className="h-3 w-12" />
                  </div>
                ))
              ) : (
                trendingStartups.map((s) => (
                  <motion.div key={s.id} variants={fadeUp}>
                    <div
                      onClick={() => navigate(`/startups/${s.id}`)}
                      className="flex items-center gap-3 p-3 bg-zinc-50 dark:bg-zinc-800/40 hover:bg-orange-50/40 dark:hover:bg-zinc-800/80 rounded-xl cursor-pointer transition-all group border border-zinc-100 dark:border-zinc-800/60"
                    >
                      <div className="w-10 h-10 rounded-lg overflow-hidden flex items-center justify-center flex-shrink-0 bg-white dark:bg-zinc-800 border border-zinc-150 dark:border-zinc-700/50">
                        {s.logo ? (
                          <ImageWithFallback src={s.logo} alt={s.name} className="w-full h-full object-contain p-1" />
                        ) : (
                          <div className="w-full h-full bg-orange-500/10 text-pulse-orange font-bold flex items-center justify-center">
                            {s.name[0]}
                          </div>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-xs font-bold text-zinc-900 dark:text-white group-hover:text-pulse-orange transition-colors truncate">
                          {s.name}
                        </h4>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          <span className="text-[11px] text-zinc-600 dark:text-zinc-300 font-medium">
                            {s.sector[0]}
                          </span>
                          <span className="text-[11px] text-zinc-300 dark:text-zinc-700">•</span>
                          <span className="text-[11px] text-zinc-600 dark:text-zinc-300 font-medium">
                            {s.location}
                          </span>
                        </div>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <span className="text-xs font-bold text-zinc-900 dark:text-white block">
                          {s.fundingCurrency}{(s.funding / 1000000).toFixed(1)}M
                        </span>
                        <span className="text-[11px] font-extrabold text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">
                          {s.stage}
                        </span>
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
            </motion.div>
          </GlowCard>

          {/* Active Investors Panel */}
          <GlowCard className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-zinc-900 dark:text-white flex items-center gap-2">
                <Landmark className="w-4 h-4 text-emerald-700 dark:text-emerald-400" />
                {t('activeInvestorsTitle')}
              </h3>
              <button
                onClick={() => navigate('/investors')}
                className="inline-flex items-center gap-0.5 min-h-11 px-1 text-xs font-bold text-zinc-600 dark:text-zinc-300 hover:text-pulse-orange transition-colors rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
              >
                {t('seeAll')} <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <motion.div
              variants={staggerContainer(0.06)}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.2 }}
              className="space-y-3"
            >
              {investorsLoading ? (
                Array.from({ length: 3 }).map((_, idx) => (
                  <div key={idx} className="flex items-center gap-3 p-3 rounded-xl">
                    <Skeleton className="w-10 h-10 rounded-lg" />
                    <div className="flex-1 space-y-1.5">
                      <Skeleton className="h-3 w-24" />
                      <Skeleton className="h-2.5 w-32" />
                    </div>
                    <Skeleton className="h-3 w-12" />
                  </div>
                ))
              ) : (
                activeInvestors.map((i) => (
                  <motion.div key={i.id} variants={fadeUp}>
                    <div
                      onClick={() => navigate(`/investors/${i.id}`)}
                      className="flex items-center gap-3 p-3 bg-zinc-50 dark:bg-zinc-800/40 hover:bg-emerald-50/40 dark:hover:bg-zinc-800/80 rounded-xl cursor-pointer transition-all group border border-zinc-100 dark:border-zinc-800/60"
                    >
                      <div className="w-10 h-10 rounded-lg overflow-hidden flex items-center justify-center flex-shrink-0 bg-white dark:bg-zinc-800 border border-zinc-150 dark:border-zinc-700/50">
                        {i.logo ? (
                          <FadeInImage src={i.logo} alt={i.name} className="w-full h-full object-contain p-1" />
                        ) : (
                          <div className="w-full h-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 font-bold flex items-center justify-center">
                            {i.name[0]}
                          </div>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-xs font-bold text-zinc-900 dark:text-white group-hover:text-emerald-700 dark:text-emerald-400 transition-colors truncate">
                          {i.name}
                        </h4>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          <span className="text-[11px] text-zinc-600 dark:text-zinc-300 font-medium truncate">
                            {i.type}
                          </span>
                          <span className="text-[11px] text-zinc-300 dark:text-zinc-700">•</span>
                          <span className="text-[11px] text-zinc-600 dark:text-zinc-300 font-medium truncate">
                            {i.location}
                          </span>
                        </div>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <span className="text-xs font-bold text-zinc-900 dark:text-white block">
                          {i.portfolio} startups
                        </span>
                        <span className="text-[11px] font-extrabold text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">
                          {t('portfolioLabel')}
                        </span>
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
            </motion.div>
          </GlowCard>

        </div>
      </ScrollReveal>

      {/* 6. Features Bento Section */}
      <FeaturesBentoSection />

      {/* 8. Success Stories */}
      <SuccessStoriesSection />

      {/* 9. Mentor Network & Partners */}
      <MentorPartnerSection />

      {/* 10. FAQ Accordion */}
      <FAQSection />

    </div>
  );
}
