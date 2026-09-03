import { useNavigate } from 'react-router-dom';
import { ChevronRight, TrendingUp, Sparkles, Trophy } from 'lucide-react';
import { ScrollReveal } from '@/components/ui/ScrollReveal';
import { GlowCard } from '@/components/ui/GlowCard';
import { Button } from '@/components/ui/button';
import { fadeUp, staggerContainer } from '@/lib/motion';
import { motion } from 'framer-motion';
import { useLanguage } from '@/context/LanguageContext';

/**
 * Two documented exits, told in facts.
 *
 * The previous copy carried claims nothing on the platform supports: Chari was
 * badged "Valorisation > $100M", which contradicts its own profile, and both
 * cards were stamped "Milestone Majeur". The Mubawab exit year is deliberately
 * left as a placeholder rather than guessed.
 */
const successStories = [
  {
    id: 'mubawab',
    tagFr: 'Acquisition · Casablanca → Dubaï',
    tagEn: 'Acquisition · Casablanca → Dubai',
    titleFr: 'Mubawab, rachetée par EMPG',
    titleEn: 'Mubawab, acquired by EMPG',
    descFr:
      "Née à Casablanca, Mubawab est devenue la première plateforme immobilière du pays avant d'être rachetée par le groupe EMPG (Dubaï). Une des premières sorties d'envergure de la tech marocaine.",
    descEn:
      'Born in Casablanca, Mubawab became the country’s leading property platform before being acquired by the EMPG group (Dubai). One of the first major exits in Moroccan tech.',
    badgeFr: 'Exit · année à confirmer',
    badgeEn: 'Exit · year to be confirmed',
    route: '/startups/mubawab',
  },
  {
    id: 'chari',
    tagFr: 'Y Combinator · Casablanca',
    tagEn: 'Y Combinator · Casablanca',
    titleFr: 'Chari, le B2B e-commerce des épiceries de quartier',
    titleEn: 'Chari, B2B e-commerce for neighbourhood grocers',
    descFr:
      "Passée par Y Combinator, Chari digitalise l'approvisionnement des épiceries de quartier et leur apporte crédit et services financiers. $19,5M levés à ce jour.",
    descEn:
      'A Y Combinator alumnus, Chari digitises supply for neighbourhood grocers and brings them credit and financial services. $19.5M raised to date.',
    badgeFr: '$19,5M levés · Série A',
    badgeEn: '$19.5M raised · Series A',
    route: '/startups/chari',
  },
];

export default function SuccessStoriesSection() {
  const navigate = useNavigate();
  const { t, language } = useLanguage();
  const isFr = language === 'fr';

  return (
    <ScrollReveal variants={fadeUp} className="w-full py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <span className="text-xs font-bold tracking-wide text-pulse-orange flex items-center gap-1.5 mb-1">
            <Trophy className="w-3.5 h-3.5 text-amber-500" aria-hidden="true" />
            {t('successTag')}
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-foreground tracking-tight">
            {t('successTitle')}
          </h2>
        </div>
        {/* The label now reads "Voir toutes les startups", so it goes to the
            directory. It used to open the AI assistant. */}
        <Button
          onClick={() => navigate('/startups')}
          variant="outline"
          className="text-xs border-border/50 text-pulse-orange self-start sm:self-auto shadow-soft-sm transition-all duration-200 ease-in-out"
        >
          <Sparkles className="w-3.5 h-3.5 mr-1.5" aria-hidden="true" />
          {t('successAiAnalysis')}
        </Button>
      </div>

      {/* Grid Stories */}
      <motion.div
        variants={staggerContainer(0.1)}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.2 }}
        className="grid grid-cols-1 lg:grid-cols-2 gap-6"
      >
        {successStories.map((story) => (
          <motion.div key={story.id} variants={fadeUp}>
            <GlowCard className="p-6 sm:p-8 flex flex-col justify-between h-full bg-card border border-border/40 shadow-soft-md transition-all duration-200 ease-in-out">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="px-3 py-1 text-[11px] font-bold rounded-full bg-pulse-orange/15 text-pulse-orange">
                    {isFr ? story.tagFr : story.tagEn}
                  </span>
                </div>

                <h3 className="text-lg sm:text-xl font-bold text-foreground leading-tight">
                  {isFr ? story.titleFr : story.titleEn}
                </h3>

                <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                  {isFr ? story.descFr : story.descEn}
                </p>

                <div className="p-3 rounded-xl bg-secondary/40 border border-border/40 flex items-center shadow-soft-sm">
                  <span className="text-xs font-bold text-emerald-700 dark:text-emerald-300 flex items-center gap-1.5">
                    <TrendingUp className="w-3.5 h-3.5" aria-hidden="true" />
                    {isFr ? story.badgeFr : story.badgeEn}
                  </span>
                </div>
              </div>

              <div className="pt-6">
                <Button
                  onClick={() => navigate(story.route)}
                  className="w-full sm:w-auto text-xs font-bold bg-pulse-orange hover:bg-pulse-orange-hover text-primary-foreground rounded-xl shadow-soft-sm hover:shadow-soft-md transition-all duration-200 ease-in-out"
                >
                  {t('successReadMore')}
                  <ChevronRight className="w-3.5 h-3.5 ml-1" />
                </Button>
              </div>
            </GlowCard>
          </motion.div>
        ))}
      </motion.div>
    </ScrollReveal>
  );
}
