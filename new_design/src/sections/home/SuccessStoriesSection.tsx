import { useNavigate } from 'react-router-dom';
import { ChevronRight, TrendingUp, Sparkles, Trophy } from 'lucide-react';
import { ScrollReveal } from '@/components/ui/ScrollReveal';
import { GlowCard } from '@/components/ui/GlowCard';
import { Button } from '@/components/ui/button';
import { fadeUp, staggerContainer } from '@/lib/motion';
import { motion } from 'framer-motion';
import { useLanguage } from '@/context/LanguageContext';

const successStories = [
  {
    id: 'mubawab',
    title: "L'Acquisition de Mubawab par le Groupe EMPG (Dubaï)",
    sector: 'RealTech / PropTech',
    impact: 'Acquisition Régionale Majeure',
    date: 'Casablanca ➔ Dubaï',
    description:
      "Fondée à Casablanca, Mubawab est devenue la plateforme immobilière leader au Maroc. Son acquisition par EMPG atteste de la valeur et de la maturité internationale des champions tech marocains.",
    highlight: 'Rachat à valeur record',
    route: '/startups/mubawab',
  },
  {
    id: 'chari',
    title: "Chari.ma : Le Géant de la B2B E-Commerce & Fintech",
    sector: 'Fintech / E-Commerce B2B',
    impact: 'Valorisation > $100M',
    date: 'Sélection Y Combinator',
    description:
      "Accélérée par Y Combinator, Chari numérise l'approvisionnement des épiceries de quartier et leur fournit des services financiers inclusifs sur toute l'Afrique du Nord.",
    highlight: 'Série A $5M+ Levé',
    route: '/startups/chari',
  },
];

export default function SuccessStoriesSection() {
  const navigate = useNavigate();
  const { t } = useLanguage();

  return (
    <ScrollReveal variants={fadeUp} className="w-full py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <span className="text-xs font-extrabold uppercase tracking-widest text-pulse-orange flex items-center gap-1.5 mb-1">
            <Trophy className="w-3.5 h-3.5 text-amber-500" />
            {t('successTag')}
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-foreground tracking-tight">
            {t('successTitle')}
          </h2>
        </div>
        <Button
          onClick={() => navigate('/ai-assistant')}
          variant="outline"
          className="text-xs border-border/50 text-pulse-orange self-start sm:self-auto shadow-soft-sm transition-all duration-200 ease-in-out"
        >
          <Sparkles className="w-3.5 h-3.5 mr-1.5" />
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
                  <span className="px-3 py-1 text-[10px] font-extrabold uppercase tracking-wider rounded-full bg-pulse-orange/15 text-pulse-orange">
                    {story.impact}
                  </span>
                  <span className="text-xs font-mono text-muted-foreground">
                    {story.date}
                  </span>
                </div>

                <h3 className="text-lg sm:text-xl font-bold text-foreground leading-tight">
                  {story.title}
                </h3>

                <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                  {story.description}
                </p>

                <div className="p-3 rounded-xl bg-secondary/40 border border-border/40 flex items-center justify-between shadow-soft-sm">
                  <span className="text-xs font-semibold text-foreground">
                    Milestone Majeur
                  </span>
                  <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                    <TrendingUp className="w-3.5 h-3.5" /> {story.highlight}
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
