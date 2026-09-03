import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Award,
  ChevronRight,
  Building,
  CheckCircle,
} from 'lucide-react';
import { ScrollReveal } from '@/components/ui/ScrollReveal';
import { FadeInImage } from '@/enhancements/FadeInImage';
import { GlowCard } from '@/components/ui/GlowCard';
import { fadeUp, staggerContainer } from '@/lib/motion';
import { useLanguage } from '@/context/LanguageContext';

// Naming follows the review. 212 Founders, CDG Invest and Technopark were
// listed here but the review notes they do not appear on the live site, so they
// are not shown: an unverified partnership is a claim, not a logo. These three
// match the footer, which already carried only the confirmed set.
const partners = [
  { name: 'Africa Business School – UM6P', tag: 'Université & recherche' },
  { name: 'Tamwilcom', tag: 'Financement & garantie' },
  { name: 'AMIC', tag: 'Association marocaine des investisseurs en capital' },
];

const mentors = [
  {
    id: 1,
    name: 'Karim Zaz',
    role: 'Ex-CEO Wanadoo & Investor',
    expertise: 'Telecom & Growth',
    company: 'Capital Tech',
    initials: 'KZ',
    image: '/avatars/karim-zaz.jpg',
  },
  {
    id: 2,
    name: 'Amine El Kabbaj',
    role: 'Managing Partner',
    expertise: 'Venture Capital & M&A',
    company: 'Outlierz Ventures',
    initials: 'AK',
    image: '/avatars/amine.jpg',
  },
  {
    id: 3,
    name: 'Salma Kabbaj',
    role: 'Co-Fondatrice IMPACT',
    expertise: 'Fintech & Inclusion',
    company: 'Impact Lab',
    initials: 'SK',
    image: '/avatars/salma-kabbaj.jpg',
  },
  {
    id: 4,
    name: 'Youssef Mamou',
    role: 'Ex-Careem & Founder',
    expertise: 'Product & Scaling',
    company: 'Chari.ma',
    initials: 'YM',
    image: '/avatars/youssef-chari.jpg',
  },
];

export default function MentorPartnerSection() {
  const navigate = useNavigate();
  const { t } = useLanguage();

  return (
    <ScrollReveal variants={fadeUp} className="w-full py-8 space-y-8">
      {/* 1. Partner Logo Ticker / Banner */}
      <div className="w-full p-6 rounded-3xl bg-card text-foreground border border-border/40 shadow-soft-md space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-extrabold tracking-wide text-muted-foreground flex items-center gap-1.5">
            <Building className="w-3.5 h-3.5 text-pulse-orange" />
            {t('partnersTitle')}
          </span>
          <span className="text-[11px] text-muted-foreground font-mono">{t('partnersTagline')}</span>
        </div>

        {/* Logo Cards Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-2">
          {partners.map((p) => (
            <div
              key={p.name}
              className="p-3 rounded-xl bg-secondary/40 border border-border/40 flex flex-col items-center justify-center text-center hover:bg-secondary/70 shadow-soft-sm transition-all duration-200 ease-in-out group"
            >
              <span className="text-xs font-black tracking-wider text-foreground group-hover:text-pulse-orange transition-colors">
                {p.name}
              </span>
              <span className="text-[11px] text-muted-foreground mt-0.5 line-clamp-1">
                {p.tag}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* 2. Mentor Network Grid Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <span className="text-xs font-extrabold tracking-wide text-pulse-orange flex items-center gap-1.5 mb-1">
            <Award className="w-3.5 h-3.5" />
            {t('mentorsTag')}
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-foreground tracking-tight">
            {t('mentorsTitle')}
          </h2>
        </div>
        <button
          onClick={() => navigate('/founders')}
          className="inline-flex items-center gap-1 min-h-11 px-1 text-xs text-muted-foreground hover:text-pulse-orange transition-all duration-200 ease-in-out font-semibold self-start sm:self-auto rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
        >
          {t('mentorsSeeAll')} <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Mentor Cards Grid */}
      <motion.div
        variants={staggerContainer(0.08)}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.2 }}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        {mentors.map((m) => (
          <motion.div key={m.id} variants={fadeUp}>
            <GlowCard className="p-5 flex flex-col justify-between h-full bg-card border border-border/40 shadow-soft-sm hover:shadow-soft-md transition-all duration-200 ease-in-out">
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-11 h-11 rounded-xl overflow-hidden bg-pulse-orange/15 text-pulse-orange font-bold text-sm flex items-center justify-center border border-pulse-orange/30 flex-shrink-0">
                    {m.image ? (
                      <FadeInImage
                        src={m.image}
                        alt={m.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      m.initials
                    )}
                  </div>
                  <div className="min-w-0">
                    <h3 className="text-sm font-bold text-foreground truncate">
                      {m.name}
                    </h3>
                    <p className="text-[11px] text-muted-foreground truncate">
                      {m.role}
                    </p>
                  </div>
                </div>

                <div className="space-y-1 pt-1">
                  <span className="text-[11px] font-extrabold tracking-wide text-muted-foreground">
                    {t('mentorExpertiseLabel')}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-pulse-orange/10 text-pulse-orange">
                      {m.expertise}
                    </span>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-border/40 flex items-center justify-between text-[11px] text-muted-foreground">
                <span>{m.company}</span>
                <CheckCircle className="w-3.5 h-3.5 text-emerald-700 dark:text-emerald-400" />
              </div>
            </GlowCard>
          </motion.div>
        ))}
      </motion.div>
    </ScrollReveal>
  );
}
