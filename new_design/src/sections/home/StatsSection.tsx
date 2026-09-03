import { useNavigate } from 'react-router-dom';
import {
  Users,
  Landmark,
  Building2,
  FlaskConical,
  CircleDollarSign,
  Briefcase,
} from 'lucide-react';
import { ScrollReveal } from '@/components/ui/ScrollReveal';
import { GlowCard } from '@/components/ui/GlowCard';
import { CounterNumber } from '@/components/ui/CounterNumber';
import { Skeleton } from '@/components/ui/skeleton';
import { fadeUp, staggerContainer } from '@/lib/motion';
import { motion } from 'framer-motion';
import { useLanguage } from '@/context/LanguageContext';
import { useStats } from '@/hooks/useStats';

function parseFundingValue(value: string): number {
  const cleaned = value.replace(/[^0-9.]/g, '');
  const num = parseFloat(cleaned);
  return Number.isNaN(num) ? 0 : num;
}

/**
 * Characters the tile will actually render, used to pick a font size that fits.
 *
 * Mirrors CounterNumber: whole values are grouped ("1 111"), fractional ones
 * keep one decimal ("278,8"). Rounding here instead would under-count the
 * funding tile by two characters, which is exactly the one that overflows.
 */
function numberWidth(stat: { value: number | null; prefix?: string; suffix?: string }): number {
  if (stat.value === null) return 1
  const body = Number.isInteger(stat.value)
    ? Math.abs(stat.value).toLocaleString('fr-FR')
    : Math.abs(stat.value).toFixed(1)
  return body.length + (stat.prefix?.length ?? 0) + (stat.suffix?.length ?? 0)
}

export default function StatsSection() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const { data: stats, isLoading } = useStats();

  const statItems = [
    {
      id: 'founders',
      value: stats?.founders ?? null,
      suffix: '+',
      label: t('statFounders'),
      icon: <Users className="w-5 h-5 text-pulse-orange" />,
      route: '/founders',
    },
    {
      id: 'investors',
      value: stats?.investors ?? null,
      suffix: '+',
      label: t('statInvestors'),
      icon: <Landmark className="w-5 h-5 text-emerald-700 dark:text-emerald-400" />,
      route: '/investors',
    },
    {
      id: 'startups',
      value: stats?.startups ?? null,
      suffix: '+',
      label: t('statStartups'),
      icon: <Building2 className="w-5 h-5 text-pulse-orange" />,
      route: '/startups',
    },
    {
      id: 'incubators',
      value: stats?.incubators ?? null,
      suffix: '+',
      label: t('statIncubators'),
      icon: <FlaskConical className="w-5 h-5 text-foreground" />,
      route: '/incubators',
    },
    {
      id: 'funding',
      value: stats?.totalFunding ? parseFundingValue(stats.totalFunding) : null,
      prefix: '$',
      suffix: 'M',
      label: t('statTotalFunding'),
      icon: <CircleDollarSign className="w-5 h-5 text-emerald-700 dark:text-emerald-400" />,
      route: '/news?type=funding',
    },
    {
      id: 'opportunities',
      value: stats?.opportunities ?? null,
      suffix: '+',
      label: t('statOpportunities'),
      icon: <Briefcase className="w-5 h-5 text-pulse-orange" />,
      route: '/opportunities',
    },
  ];

  return (
    <ScrollReveal variants={fadeUp} className="w-full py-4">
      {/* One badge for the whole block, rather than the same "LIVE" stamped on
          all six tiles. */}
      <div className="flex justify-end mb-2">
        <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" aria-hidden="true" />
          Live
        </span>
      </div>
      <motion.div
        variants={staggerContainer(0.06)}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.2 }}
        className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4"
      >
        {statItems.map((stat) => (
          <motion.div key={stat.id} variants={fadeUp}>
            <GlowCard
              onClick={() => navigate(stat.route)}
              className="p-4 flex flex-col justify-between h-full bg-card border border-border/40 shadow-soft-sm hover:shadow-soft-md transition-all duration-200 ease-in-out"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 rounded-lg bg-secondary/60 border border-border/30">
                  {stat.icon}
                </div>
              </div>

              <div className="space-y-0.5">
                {isLoading ? (
                  <Skeleton className="h-8 w-20" />
                ) : stat.value === null ? (
                  <span
                    className="text-xl sm:text-2xl lg:text-[26px] font-black text-muted-foreground tracking-tight whitespace-nowrap"
                    aria-label={t('errorLoading')}
                  >
                    —
                  </span>
                ) : (
                  <CounterNumber
                    value={stat.value}
                    prefix={stat.prefix}
                    suffix={stat.suffix}
                    /* Six narrow columns leave ~83px per tile. A plain count
                       fits, but a currency amount ("$278,8M") is half again as
                       wide and was being clipped, so long values step down. */
                    className={`${
                      numberWidth(stat) > 6
                        ? 'text-lg sm:text-xl lg:text-[20px]'
                        : 'text-xl sm:text-2xl lg:text-[26px]'
                    } font-black text-foreground tracking-tight whitespace-nowrap`}
                  />
                )}
                <p className="text-xs font-semibold text-muted-foreground truncate">
                  {stat.label}
                </p>
              </div>
            </GlowCard>
          </motion.div>
        ))}
      </motion.div>
    </ScrollReveal>
  );
}
