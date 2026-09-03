import { useLocation, useNavigate } from 'react-router-dom';
import {
  Home,
  Building2,
  Landmark,
  FlaskConical,
  Rocket,
  Users,
  UserRound,
  Handshake,
  Rss,
  Briefcase,
  Calendar,
  BarChart3,
  BookOpen,
  FileText,
  Search,
  Network,
  Lock,
  MessageSquare,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/context/LanguageContext';
import { useAuth } from '@/context/AuthContext';
import { useUnreadMessages } from '@/hooks/useUnreadMessages';

export default function LeftSidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { t, language } = useLanguage();
  const { member, user } = useAuth();
  const { unread } = useUnreadMessages();
  const signedIn = !!member || !!user;

  const navItems: {
    label: string;
    icon: React.ReactNode;
    href: string;
    section?: string;
    badge?: number;
  }[] = [
    { label: t('navHome'), icon: <Home className="w-[18px] h-[18px]" />, href: '/' },
    {
      label: t('navStartups'),
      icon: <Building2 className="w-[18px] h-[18px]" />,
      href: '/startups',
      section: language === 'fr' ? 'DECOUVRIR' : 'DISCOVER',
    },
    {
      label: t('navInvestors'),
      icon: <Landmark className="w-[18px] h-[18px]" />,
      href: '/investors',
      section: language === 'fr' ? 'DECOUVRIR' : 'DISCOVER',
    },
    {
      label: t('navIncubators'),
      icon: <FlaskConical className="w-[18px] h-[18px]" />,
      href: '/incubators',
      section: language === 'fr' ? 'DECOUVRIR' : 'DISCOVER',
    },
    {
      label: t('navVentureStudios'),
      icon: <Rocket className="w-[18px] h-[18px]" />,
      href: '/startups?type=venture-studio',
      section: language === 'fr' ? 'DECOUVRIR' : 'DISCOVER',
    },
    {
      label: t('navVisualizer'),
      icon: <Network className="w-[18px] h-[18px]" />,
      href: '/visualizer',
      section: language === 'fr' ? 'DECOUVRIR' : 'DISCOVER',
    },
    {
      // The people directory. Distinct from "Co-fondateurs recherchés" below,
      // which lists co-founder *postings* rather than the founders themselves.
      label: t('navFounders'),
      icon: <UserRound className="w-[18px] h-[18px]" />,
      href: '/founders',
      section: language === 'fr' ? 'DECOUVRIR' : 'DISCOVER',
    },
    {
      label: t('navExperts'),
      icon: <Users className="w-[18px] h-[18px]" />,
      href: '/founders?type=expert',
      section: language === 'fr' ? 'DECOUVRIR' : 'DISCOVER',
    },
    {
      label: t('navCofounders'),
      icon: <Handshake className="w-[18px] h-[18px]" />,
      href: '/founders?type=co-founder',
      section: language === 'fr' ? 'DECOUVRIR' : 'DISCOVER',
    },
    {
      label: t('navNews'),
      icon: <Rss className="w-[18px] h-[18px]" />,
      href: '/news',
      section: language === 'fr' ? 'PARTICIPER' : 'ENGAGE',
    },
    {
      label: t('navOpportunities'),
      icon: <Briefcase className="w-[18px] h-[18px]" />,
      href: '/opportunities',
      section: language === 'fr' ? 'PARTICIPER' : 'ENGAGE',
    },
    {
      label: 'Deal Room',
      icon: <Lock className="w-[18px] h-[18px]" />,
      href: '/deal-room',
      section: language === 'fr' ? 'PARTICIPER' : 'ENGAGE',
    },
    // Messaging is only meaningful once there is an identity to attribute it to,
    // so the entry appears with the session rather than sending guests to a
    // sign-in wall. Its absence was why the inbox had no way in at all.
    ...(signedIn
      ? [
          {
            label: language === 'fr' ? 'Messagerie' : 'Messages',
            icon: <MessageSquare className="w-[18px] h-[18px]" />,
            href: '/inbox',
            section: language === 'fr' ? 'PARTICIPER' : 'ENGAGE',
            badge: unread,
          },
        ]
      : []),
    {
      // Was '/opportunities?type=talent', which rendered the Opportunities
      // page under the Talents label. The marketplace has its own route now.
      label: t('navTalent'),
      icon: <Search className="w-[18px] h-[18px]" />,
      href: '/talents',
      section: language === 'fr' ? 'PARTICIPER' : 'ENGAGE',
    },
    {
      label: t('navEvents'),
      icon: <Calendar className="w-[18px] h-[18px]" />,
      href: '/events',
      section: language === 'fr' ? 'PARTICIPER' : 'ENGAGE',
    },
    {
      label: t('navAnalytics'),
      icon: <BarChart3 className="w-[18px] h-[18px]" />,
      href: '/analytics',
      section: language === 'fr' ? 'RESSOURCES' : 'RESOURCES',
    },
    {
      label: t('navGuides'),
      icon: <BookOpen className="w-[18px] h-[18px]" />,
      href: '/guides',
      section: language === 'fr' ? 'RESSOURCES' : 'RESOURCES',
    },
    {
      label: t('navBlog'),
      icon: <FileText className="w-[18px] h-[18px]" />,
      href: '/news?type=blog',
      section: language === 'fr' ? 'RESSOURCES' : 'RESOURCES',
    },
  ];

  const sections = language === 'fr'
    ? ['DECOUVRIR', 'PARTICIPER', 'RESSOURCES']
    : ['DISCOVER', 'ENGAGE', 'RESOURCES'];

  // The keys above are internal grouping ids; these are what the reader sees.
  // Rendered in sentence case, per the editorial rules in the review.
  const sectionLabels: Record<string, string> = {
    DECOUVRIR: 'Découvrir',
    PARTICIPER: 'Participer',
    RESSOURCES: 'Ressources',
    DISCOVER: 'Discover',
    ENGAGE: 'Engage',
    RESOURCES: 'Resources',
  };

  const isActive = (href: string) => {
    const [hrefPath, hrefQuery] = href.split('?');
    
    if (hrefPath === '/') {
      return location.pathname === '/' && !location.search;
    }
    
    const pathMatches = location.pathname === hrefPath || location.pathname.startsWith(hrefPath + '/');
    if (!pathMatches) return false;
    
    if (hrefQuery) {
      return location.search.includes(hrefQuery);
    } else {
      return !location.search.includes('type=');
    }
  };

  return (
    <div className="flex flex-col h-full py-4 bg-card/60 transition-all duration-200 ease-in-out overflow-y-auto pb-24">
      {/* Home Button */}
      <div className="px-3 mb-2 space-y-1">
        <button
          onClick={() => navigate('/')}
          className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ease-in-out ${
            isActive('/')
              ? 'bg-pulse-orange-50/70 dark:bg-pulse-orange/15 text-pulse-orange border-l-[3px] border-pulse-orange shadow-soft-sm'
              : 'text-muted-foreground hover:bg-secondary/70 hover:text-foreground border-l-[3px] border-transparent'
          }`}
        >
          <Home className="w-[18px] h-[18px]" />
          {t('navHome')}
        </button>
      </div>

      {/* Sections */}
      {sections.map((section) => (
        <div key={section} className="mb-2">
          <div className="px-5 py-2">
            <span className="text-[11px] font-semibold text-muted-foreground tracking-wider">
              {sectionLabels[section] ?? section}
            </span>
          </div>
          {navItems
            .filter((item) => item.section === section)
            .map((item) => (
              <div key={item.label} className="px-3">
                <button
                  onClick={() => navigate(item.href)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-200 ease-in-out ${
                    isActive(item.href)
                      ? 'bg-pulse-orange-50/70 dark:bg-pulse-orange/15 text-pulse-orange font-medium shadow-soft-sm'
                      : 'text-muted-foreground hover:bg-secondary/70 hover:text-foreground font-normal'
                  }`}
                >
                  <span
                    className={
                      isActive(item.href) ? 'text-pulse-orange' : 'text-muted-foreground'
                    }
                  >
                    {item.icon}
                  </span>
                  <span className="flex-1 text-left">{item.label}</span>
                  {item.badge ? (
                    <span
                      className="bg-pulse-orange text-primary-foreground text-[11px] font-bold min-w-[18px] h-[18px] px-1 rounded-full grid place-items-center"
                      aria-label={`${item.badge} ${language === 'fr' ? 'non lus' : 'unread'}`}
                    >
                      {item.badge > 99 ? '99+' : item.badge}
                    </span>
                  ) : null}
                </button>
              </div>
            ))}
        </div>
      ))}

      {/* Spacer */}
      <div className="flex-1" />

      {/* CTA Card */}
      <div className="mx-3 mt-4 p-4 rounded-xl bg-secondary/50 border border-border/40 shadow-soft-sm">
        <h4 className="text-sm font-semibold text-foreground mb-1">
          {t('joinEcosystem')}
        </h4>
        <p className="text-xs text-muted-foreground mb-3 leading-relaxed">
          {t('joinSub')}
        </p>
        <Button
          onClick={() => navigate('/register')}
          className="w-full h-9 text-xs font-medium bg-pulse-orange hover:bg-pulse-orange-hover text-primary-foreground rounded-lg shadow-soft-sm hover:shadow-soft-md transition-all duration-200 ease-in-out"
        >
          {t('createAccount')}
        </Button>
      </div>
    </div>
  );
}
