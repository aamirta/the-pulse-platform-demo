import { useState } from 'react';
import { Clock, ChevronDown, Newspaper } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { FadeInImage } from '@/enhancements/FadeInImage';
import { ScrollReveal } from '@/components/ui/ScrollReveal';
import { GlowCard } from '@/components/ui/GlowCard';
import { fadeUp, staggerContainer } from '@/lib/motion';
import { motion, AnimatePresence } from 'framer-motion';
import { useLanguage } from '@/context/LanguageContext';
import { useNews } from '@/hooks/useNews';
import type { NewsItem } from '@/types';

type TabType = 'all' | 'news' | 'funding' | 'events';

// Keyed by every NewsItem type, so a 'blog' item gets its own badge instead of
// silently falling back to the 'news' styling.
const badgeConfig: Record<NewsItem['type'], { text: string; className: string }> = {
  funding: { text: 'LEVÉE DE FONDS', className: 'bg-pulse-orange/15 text-pulse-orange border border-pulse-orange/30' },
  news: { text: 'ACTUALITÉ', className: 'bg-secondary text-foreground/80 border border-border/40' },
  event: { text: 'ÉVÉNEMENT', className: 'bg-secondary text-foreground/80 border border-border/40' },
  blog: { text: 'BLOG', className: 'bg-secondary text-foreground/80 border border-border/40' },
};

export default function NewsFeed() {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<TabType>('all');
  const [showAll, setShowAll] = useState(false);
  const { data: newsItems = [], isLoading } = useNews();

  const tabs: { key: TabType; label: string }[] = [
    { key: 'all', label: t('newsTabAll') },
    { key: 'news', label: t('newsTabNews') },
    { key: 'funding', label: t('newsTabFunding') },
    { key: 'events', label: t('newsTabEvents') },
  ];

  const filteredNews =
    activeTab === 'all'
      ? newsItems.slice(0, 3)
      : newsItems.filter((item) => item.type === activeTab).slice(0, 3);

  const displayNews = showAll ? newsItems : filteredNews;

  return (
    <ScrollReveal variants={fadeUp} className="w-full py-4 space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <h2 className="text-lg font-extrabold text-foreground flex items-center gap-2">
          <Newspaper className="w-4 h-4 text-pulse-orange" />
          {t('newsTitle')}
        </h2>
        <div className="flex items-center gap-1 overflow-x-auto pb-1 scrollbar-none">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => {
                setActiveTab(tab.key);
                setShowAll(false);
              }}
              className={`px-3 py-1.5 text-xs font-bold rounded-full transition-all duration-200 ease-in-out flex-shrink-0 ${
                activeTab === tab.key
                  ? 'bg-pulse-orange text-primary-foreground shadow-soft-sm'
                  : 'text-muted-foreground hover:text-foreground hover:bg-secondary/70'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* News Cards Stack */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab + (showAll ? '-all' : '-short')}
          variants={staggerContainer(0.06)}
          initial="hidden"
          animate="visible"
          className="space-y-3"
        >
          {isLoading ? (
            Array.from({ length: 3 }).map((_, idx) => (
              <GlowCard key={idx} className="p-4 flex gap-4 bg-card border border-border/40 shadow-soft-sm">
                <Skeleton className="hidden sm:block w-[120px] h-[84px] rounded-xl" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-5 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                  <div className="flex gap-2">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-4 w-16" />
                  </div>
                </div>
              </GlowCard>
            ))
          ) : (
            displayNews.map((item) => {
              const badge = badgeConfig[item.type] || badgeConfig.news;
              return (
                <motion.div key={item.id} variants={fadeUp}>
                  <GlowCard className="p-4 flex gap-4 group bg-card border border-border/40 shadow-soft-sm hover:shadow-soft-md transition-all duration-200 ease-in-out">
                    {/* Image */}
                    {/* Articles without an image used to render <img src="">, which
                        makes the browser re-request the current page. The tile is
                        kept (so the row keeps its rhythm) with a typographic
                        placeholder instead. */}
                    <div className="hidden sm:block w-[120px] h-[84px] rounded-xl overflow-hidden flex-shrink-0 relative">
                      {item.image ? (
                        <>
                          <FadeInImage
                            src={item.image}
                            alt={item.title}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                          />
                          <div className="absolute inset-0 bg-zinc-950/10 group-hover:bg-transparent transition-colors" />
                        </>
                      ) : (
                        <div
                          aria-hidden="true"
                          className="w-full h-full flex items-center justify-center bg-secondary/60 border border-border/40 text-muted-foreground text-lg font-bold"
                        >
                          {(item.title || '?').trim().charAt(0).toUpperCase()}
                        </div>
                      )}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1.5">
                        <Badge className={`text-[11px] font-extrabold tracking-wider px-2 py-0.5 ${badge.className}`}>
                          {badge.text}
                        </Badge>
                      </div>
                      <h3 className="text-sm font-bold text-foreground mb-1 leading-snug line-clamp-1 group-hover:text-pulse-orange transition-colors">
                        {item.title}
                      </h3>
                      <p className="text-xs text-muted-foreground mb-2 line-clamp-2 leading-relaxed">
                        {item.description}
                      </p>
                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-1.5">
                          <div className="w-5 h-5 rounded-full bg-pulse-orange/15 flex items-center justify-center">
                            <span className="text-[11px] font-bold text-pulse-orange">
                              {item.source[0]}
                            </span>
                          </div>
                          <span className="text-xs text-muted-foreground font-medium">
                            {item.source}
                          </span>
                        </div>
                        <div className="flex items-center gap-1 text-muted-foreground">
                          <Clock className="w-3 h-3" />
                          <span className="text-[11px]">{item.date}</span>
                        </div>
                      </div>
                    </div>

                    {/* Right Side: Amount or Date */}
                    {item.amount && (
                      <div className="flex flex-col items-end justify-center flex-shrink-0 pl-2">
                        <span className="text-base sm:text-lg font-extrabold text-foreground flex items-center gap-0.5">
                          {item.amount}
                        </span>
                        <span className="text-[11px] font-bold text-pulse-orange bg-pulse-orange/10 px-2 py-0.5 rounded">
                          {item.round}
                        </span>
                      </div>
                    )}
                    {item.eventDate && (
                      <div className="flex flex-col items-center justify-center flex-shrink-0 px-3 py-2 bg-secondary/60 border border-border/40 rounded-xl shadow-soft-sm">
                        <span className="text-xs font-bold text-foreground">
                          {item.eventDate.split(' ')[0]}
                        </span>
                        <span className="text-[11px] text-muted-foreground">
                          {item.eventDate.split(' ').slice(1).join(' ')}
                        </span>
                      </div>
                    )}
                  </GlowCard>
                </motion.div>
              );
            })
          )}
        </motion.div>
      </AnimatePresence>

      {/* Show More Button */}
      {!showAll && newsItems.length > 3 && (
        <div className="flex justify-center pt-1">
          <button
            onClick={() => setShowAll(true)}
            className="flex items-center gap-1 px-4 py-2 text-xs font-bold text-muted-foreground hover:text-pulse-orange transition-all duration-200 ease-in-out rounded-full border border-border/40 hover:border-pulse-orange/40 shadow-soft-sm"
          >
            {t('newsShowMore')}
            <ChevronDown className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </ScrollReveal>
  );
}
