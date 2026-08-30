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

export default function StatsSection() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const { data: stats, isLoading } = useStats();

  const statItems = [
    {
      id: 'founders',
      value: stats?.founders ?? 120,
      suffix: '+',
      label: t('statFounders'),
      icon: <Users className="w-5 h-5 text-pulse-orange" />,
      route: '/founders',
    },
    {
      id: 'investors',
      value: stats?.investors ?? 85,
      suffix: '+',
      label: t('statInvestors'),
      icon: <Landmark className="w-5 h-5 text-emerald-500" />,
      route: '/investors',
    },
    {
      id: 'startups',
      value: stats?.startups ?? 500,
      suffix: '+',
      label: t('statStartups'),
      icon: <Building2 className="w-5 h-5 text-pulse-orange" />,
      route: '/startups',
    },
    {
      id: 'incubators',
      value: stats?.incubators ?? 40,
      suffix: '+',
      label: t('statIncubators'),
      icon: <FlaskConical className="w-5 h-5 text-foreground" />,
      route: '/startups?type=incubateur',
    },
    {
      id: 'funding',
      value: parseFundingValue(stats?.totalFunding ?? ''),
      prefix: '$',
      suffix: 'M+',
      label: t('statTotalFunding'),
      icon: <CircleDollarSign className="w-5 h-5 text-emerald-500" />,
      route: '/news?type=funding',
    },
    {
      id: 'opportunities',
      value: stats?.opportunities ?? 65,
      suffix: '+',
      label: t('statOpportunities'),
      icon: <Briefcase className="w-5 h-5 text-pulse-orange" />,
      route: '/opportunities',
    },
  ];

  return (
    <ScrollReveal variants={fadeUp} className="w-full py-4">
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
                <span className="text-[10px] font-bold text-muted-foreground font-mono uppercase">
                  LIVE
                </span>
              </div>

              <div className="space-y-0.5">
                {isLoading ? (
                  <Skeleton className="h-8 w-20" />
                ) : (
                  <CounterNumber
                    value={stat.value}
                    prefix={stat.prefix}
                    suffix={stat.suffix}
                    className="text-2xl sm:text-3xl font-black text-foreground tracking-tight"
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
