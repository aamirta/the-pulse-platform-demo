import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Moon, Sun, Menu, ChevronDown, User, Shield, Sparkles, Building, Landmark, Check, Globe, ArrowLeft, Rocket, GraduationCap, Users, BookOpen, Award, LayoutDashboard, LogOut, MessageSquare, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import BrandLogo from '@/components/BrandLogo';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '@/hooks/useTheme';
import { useLanguage } from '@/context/LanguageContext';
import { useAuth } from '@/context/AuthContext';
import { useUnreadMessages } from '@/hooks/useUnreadMessages';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';

interface TopNavProps {
  onMenuToggle: () => void;
  /** Whether the mobile navigation drawer is currently open. */
  mobileMenuOpen?: boolean;
}

export default function TopNav({ onMenuToggle, mobileMenuOpen = false }: TopNavProps) {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const { language, setLanguage, t } = useLanguage();
  // Identity comes from the auth session. The nav used to read only a stale
  // localStorage role key, so it advertised "Sign in" even when signed in and
  // offered no way to sign out.
  const { isAuthenticated, user, member, logout } = useAuth();
  const { unread } = useUnreadMessages();
  const accountName = user?.username ?? member?.full_name ?? '';
  
  // Dashboard Role State (Startup, Investor, Partner, Admin)
  const [activeRole, setActiveRole] = useState<'startup' | 'investor' | 'partner' | 'admin'>(() => {
    const saved = localStorage.getItem('pulse-user-role');
    return (saved as 'startup' | 'investor' | 'partner' | 'admin' | null) || 'startup';
  });

  const [isPowerOpen, setIsPowerOpen] = useState(false);
  const [selectedRole, setSelectedRole] = useState<string | null>(null);
  const [isSubmitted, setIsSubmitted] = useState<boolean>(false);

  const handlePowerOpenChange = (open: boolean) => {
    setIsPowerOpen(open);
    if (!open) {
      setTimeout(() => {
        setSelectedRole(null);
        setIsSubmitted(false);
      }, 200);
    }
  };

  const handleRoleChange = (role: 'startup' | 'investor' | 'partner' | 'admin') => {
    setActiveRole(role);
    localStorage.setItem('pulse-user-role', role);
    if (location.pathname === '/dashboard') {
      navigate(`/dashboard?role=${role}`);
    }
  };

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'startup': return t('roleStartup');
      case 'investor': return t('roleInvestor');
      case 'partner': return t('rolePartner');
      case 'admin': return t('roleAdmin');
      default: return 'User';
    }
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'startup': return <Building className="w-4 h-4 mr-2 text-pulse-orange" />;
      case 'investor': return <Landmark className="w-4 h-4 mr-2 text-emerald-700 dark:text-emerald-400" />;
      case 'partner': return <Sparkles className="w-4 h-4 mr-2 text-purple-600" />;
      case 'admin': return <Shield className="w-4 h-4 mr-2 text-blue-600" />;
      default: return <User className="w-4 h-4 mr-2" />;
    }
  };

  const renderPowerForm = () => {
    const rolesList = [
      {
        id: 'entrepreneur',
        titleFr: 'Entrepreneur / Startup',
        titleEn: 'Entrepreneur / Startup',
        descFr: 'Référencez votre startup et connectez-vous aux investisseurs et incubateurs.',
        descEn: 'List your startup and connect with investors and incubators.',
        icon: <Rocket className="w-5 h-5 text-pulse-orange" />
      },
      {
        id: 'investor',
        titleFr: 'Investisseur / VC',
        titleEn: 'Investor / VC',
        descFr: 'Présentez votre thèse d\'investissement et votre portefeuille marocain.',
        descEn: 'Share your investment thesis and Moroccan portfolio.',
        icon: <Landmark className="w-5 h-5 text-pulse-orange" />
      },
      {
        id: 'program',
        titleFr: 'Programme d\'accompagnement',
        titleEn: 'Support Program',
        descFr: 'Listez vos bootcamps, cohortes et appels à projets actifs.',
        descEn: 'List your active bootcamps, cohorts, and applications.',
        icon: <BookOpen className="w-5 h-5 text-pulse-orange" />
      },
      {
        id: 'incubator',
        titleFr: 'Incubateur / Accélérateur',
        titleEn: 'Incubator / Accelerator',
        descFr: 'Enregistrez votre structure d\'appui pour attirer de nouveaux projets.',
        descEn: 'Register your support structure to attract new projects.',
        icon: <Building className="w-5 h-5 text-pulse-orange" />
      },
      {
        id: 'talent',
        titleFr: 'Talent / Professionnel',
        titleEn: 'Talent / Professional',
        descFr: 'Créez votre profil pour trouver des opportunités dans l\'écosystème.',
        descEn: 'Create your profile to find opportunities in the ecosystem.',
        icon: <GraduationCap className="w-5 h-5 text-pulse-orange" />
      },
      {
        id: 'expert',
        titleFr: 'Expert / Mentor',
        titleEn: 'Expert / Mentor',
        descFr: 'Partagez votre expertise et accompagnez les fondateurs locaux.',
        descEn: 'Share your expertise and guide local founders.',
        icon: <Award className="w-5 h-5 text-pulse-orange" />
      },
      {
        id: 'studio',
        titleFr: 'Venture Studio',
        titleEn: 'Venture Studio',
        descFr: 'Listez les startups co-construites et recrutez des co-fondateurs.',
        descEn: 'List co-built startups and recruit co-founders.',
        icon: <Users className="w-5 h-5 text-pulse-orange" />
      }
    ];

    return (
      <div className="relative overflow-hidden min-h-[400px] flex flex-col justify-between">
        <AnimatePresence mode="wait">
          {isSubmitted ? (
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className="flex flex-col items-center justify-center py-8 text-center my-auto"
            >
              <div className="w-16 h-16 bg-emerald-500/10 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400 rounded-full flex items-center justify-center mb-4 border border-emerald-500/30">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 200, damping: 10, delay: 0.15 }}
                >
                  <Check className="w-8 h-8" />
                </motion.div>
              </div>
              <h3 className="text-xl font-bold text-foreground mb-2">
                {language === 'fr' ? 'Merci pour votre contribution !' : 'Thank you for your contribution!'}
              </h3>
              <p className="text-sm text-muted-foreground max-w-xs mb-6 leading-relaxed">
                {language === 'fr' 
                  ? 'Vos informations ont été soumises pour validation par le comité de l\'écosystème Pulse.'
                  : 'Your information has been submitted for validation by the Pulse ecosystem committee.'}
              </p>
              <Button 
                onClick={() => handlePowerOpenChange(false)}
                className="bg-pulse-orange hover:bg-pulse-orange-hover text-primary-foreground rounded-lg px-6 shadow-soft-sm hover:shadow-soft-md transition-all duration-200"
              >
                {language === 'fr' ? 'Fermer' : 'Close'}
              </Button>
            </motion.div>
          ) : !selectedRole ? (
            <motion.div
              key="selection"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
              className="space-y-4 py-2 flex-1 flex flex-col justify-between"
            >
              <div>
                <DialogDescription className="text-muted-foreground text-xs mb-3">
                  {language === 'fr' 
                    ? 'Sélectionnez votre rôle pour soumettre vos données et figurer sur la plateforme de référence de l\'innovation au Maroc.'
                    : 'Select your role to submit your data and join Morocco\'s premier innovation platform.'}
                </DialogDescription>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 max-h-[440px] overflow-y-auto pr-1">
                  {rolesList.map((role, index) => (
                    <motion.div 
                      key={role.id}
                      onClick={() => setSelectedRole(role.id)}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.2, delay: index * 0.04 }}
                      whileHover={{ scale: 1.02, y: -2 }}
                      whileTap={{ scale: 0.98 }}
                      className="p-4 border border-border/40 bg-secondary/15 hover:border-pulse-orange/40 hover:bg-secondary/30 rounded-xl cursor-pointer hover:shadow-soft-sm transition-all duration-200 ease-in-out flex flex-col items-start gap-2"
                    >
                      <div className="flex items-center gap-2">
                        <div className="p-1.5 bg-background rounded-lg shadow-soft-sm border border-border/10">
                          {role.icon}
                        </div>
                        <h4 className="font-semibold text-xs text-foreground leading-tight">
                          {language === 'fr' ? role.titleFr : role.titleEn}
                        </h4>
                      </div>
                      <p className="text-[11px] text-muted-foreground leading-relaxed">
                        {language === 'fr' ? role.descFr : role.descEn}
                      </p>
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="form"
              initial={{ opacity: 0, x: 25 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -25 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="space-y-4 py-2 flex-1 flex flex-col justify-between"
            >
              <form onSubmit={(e) => { e.preventDefault(); setIsSubmitted(true); }} className="space-y-4 flex flex-col justify-between flex-1">
                <div>
                  <div className="flex items-center justify-between border-b border-border/40 pb-2 mb-3">
                    <button 
                      type="button"
                      onClick={() => setSelectedRole(null)}
                      className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <ArrowLeft className="w-3.5 h-3.5" />
                      {language === 'fr' ? 'Retour' : 'Back'}
                    </button>
                    <span className="text-[11px] uppercase font-bold tracking-wider text-pulse-orange bg-pulse-orange/10 px-2 py-0.5 rounded">
                      {selectedRole}
                    </span>
                  </div>

                  <div className="space-y-3 max-h-[400px] overflow-y-auto pr-1">
                    {selectedRole === 'entrepreneur' && (
                      <>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Nom de la Startup *' : 'Startup Name *'}</label>
                          <Input placeholder="Ex: Chari, Yassir..." required className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Site Web' : 'Website'}</label>
                          <Input type="url" placeholder="https://..." className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Ville *' : 'City *'}</label>
                          <Input placeholder="Ex: Casablanca, Rabat, Marrakech..." required className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Secteurs d\'Activité' : 'Sectors'}</label>
                          <Input placeholder="Ex: FinTech, E-commerce, EdTech..." className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Description *' : 'Description *'}</label>
                          <textarea 
                            required 
                            rows={3} 
                            placeholder={language === 'fr' ? 'Décrivez brièvement le projet...' : 'Briefly describe your project...'}
                            className="w-full p-2 text-xs bg-secondary/40 border border-border/50 rounded-lg text-foreground focus:outline-none focus:border-pulse-orange/40"
                          />
                        </div>
                      </>
                    )}

                    {selectedRole === 'investor' && (
                      <>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Nom du Fonds / VC *' : 'Fund / VC Name *'}</label>
                          <Input placeholder="Ex: Outlierz Ventures, CDG Invest..." required className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Site Web' : 'Website'}</label>
                          <Input type="url" placeholder="https://..." className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Stade d\'Investissement Focus' : 'Investment Stage Focus'}</label>
                          <Input placeholder="Ex: Pre-Seed, Seed, Series A..." className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Secteurs Focus' : 'Sectors Focus'}</label>
                          <Input placeholder="Ex: AgriTech, CleanTech, B2B SaaS..." className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Ticket Moyen ($) *' : 'Average Ticket Size ($) *'}</label>
                          <Input placeholder="Ex: $50K - $250K" required className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                      </>
                    )}

                    {selectedRole === 'program' && (
                      <>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Nom du Programme *' : 'Program Name *'}</label>
                          <Input placeholder="Ex: UM6P Startgate Cohorte 4..." required className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Organisme Porteur *' : 'Supporting Organization *'}</label>
                          <Input placeholder="Ex: UM6P, LaStartupFactory..." required className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Lien du Programme / Candidature' : 'Program / Application Link'}</label>
                          <Input type="url" placeholder="https://..." className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Description du Programme *' : 'Program Description *'}</label>
                          <textarea 
                            required 
                            rows={3} 
                            placeholder={language === 'fr' ? 'Décrivez les critères d\'éligibilité, les avantages...' : 'Describe eligibility criteria, benefits...'}
                            className="w-full p-2 text-xs bg-secondary/40 border border-border/50 rounded-lg text-foreground focus:outline-none focus:border-pulse-orange/40"
                          />
                        </div>
                      </>
                    )}

                    {selectedRole === 'incubator' && (
                      <>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Nom de la Structure d\'Accompagnement *' : 'Incubator/Accelerator Name *'}</label>
                          <Input placeholder="Ex: Impact Lab, Plug & Play Morocco..." required className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Site Web' : 'Website'}</label>
                          <Input type="url" placeholder="https://..." className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Ville & Siège *' : 'City & Headquarter *'}</label>
                          <Input placeholder="Ex: Casablanca, Rabat..." required className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Secteurs Supportés' : 'Supported Sectors'}</label>
                          <Input placeholder="Ex: Tous secteurs, DeepTech, Impact..." className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Présentation de la structure' : 'About the incubator'}</label>
                          <textarea 
                            rows={2} 
                            placeholder={language === 'fr' ? 'Programmes phares, partenaires...' : 'Key programs, partners...'}
                            className="w-full p-2 text-xs bg-secondary/40 border border-border/50 rounded-lg text-foreground focus:outline-none focus:border-pulse-orange/40"
                          />
                        </div>
                      </>
                    )}

                    {selectedRole === 'talent' && (
                      <>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Nom & Prénom *' : 'Full Name *'}</label>
                          <Input placeholder="Ex: Mehdi Filali..." required className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Rôle / Titre *' : 'Role / Title *'}</label>
                          <Input placeholder="Ex: Lead Product Manager, Senior DevOps..." required className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Compétences Clés' : 'Core Skills'}</label>
                          <Input placeholder="Ex: React, Agile, Product Strategy..." className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Lien LinkedIn *' : 'LinkedIn Link *'}</label>
                          <Input type="url" placeholder="https://linkedin.com/in/..." required className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                      </>
                    )}

                    {selectedRole === 'expert' && (
                      <>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Nom & Prénom *' : 'Full Name *'}</label>
                          <Input placeholder="Ex: Youssef Chari..." required className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Titre Actuel *' : 'Current Title *'}</label>
                          <Input placeholder="Ex: Expert en Stratégie, Mentor DeepTech..." required className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Domaines d\'Expertise *' : 'Expertise Areas *'}</label>
                          <Input placeholder="Ex: Go-To-Market, Scaling, fundraising..." required className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Lien LinkedIn *' : 'LinkedIn Link *'}</label>
                          <Input type="url" placeholder="https://linkedin.com/in/..." required className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Mini Bio *' : 'Short Bio *'}</label>
                          <textarea 
                            required 
                            rows={2} 
                            placeholder={language === 'fr' ? 'Plus de 15 ans d\'expérience...' : 'More than 15 years of experience...'}
                            className="w-full p-2 text-xs bg-secondary/40 border border-border/50 rounded-lg text-foreground focus:outline-none focus:border-pulse-orange/40"
                          />
                        </div>
                      </>
                    )}

                    {selectedRole === 'studio' && (
                      <>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Nom du Venture Studio *' : 'Venture Studio Name *'}</label>
                          <Input placeholder="Ex: M3 Ventures Studio..." required className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Site Web' : 'Website'}</label>
                          <Input type="url" placeholder="https://..." className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Ville & Siège *' : 'City & Headquarter *'}</label>
                          <Input placeholder="Ex: Casablanca..." required className="bg-secondary/40 border-border/50 text-foreground text-xs" />
                        </div>
                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-foreground/80">{language === 'fr' ? 'Description / Modèle d\'Accompagnement *' : 'Description / Model *'}</label>
                          <textarea 
                            required 
                            rows={3} 
                            placeholder={language === 'fr' ? 'Comment vous co-construisez les startups...' : 'How you co-build startups...'}
                            className="w-full p-2 text-xs bg-secondary/40 border border-border/50 rounded-lg text-foreground focus:outline-none focus:border-pulse-orange/40"
                          />
                        </div>
                      </>
                    )}
                  </div>
                </div>

                <Button 
                  type="submit"
                  className="w-full bg-pulse-orange hover:bg-pulse-orange-hover text-primary-foreground rounded-lg shadow-soft-sm hover:shadow-soft-md transition-all duration-200 ease-in-out text-xs py-2 mt-3"
                >
                  {language === 'fr' ? 'Soumettre la contribution' : 'Submit contribution'}
                </Button>
              </form>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  };

  return (
    <header className="fixed top-0 left-0 right-0 h-16 bg-card/90 backdrop-blur-md border-b border-border/40 z-50 px-4 lg:px-6 transition-all duration-200 ease-in-out shadow-soft-sm">
      <div className="flex items-center justify-between h-full w-full">
        
        {/* Left: Logo + Mobile Menu */}
        <div className="flex items-center gap-3 shrink-0 lg:w-[240px]">
          <button
            onClick={onMenuToggle}
            aria-label={mobileMenuOpen ? 'Fermer le menu' : 'Ouvrir le menu'}
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-navigation"
            className="lg:hidden inline-flex items-center justify-center min-w-11 min-h-11 p-2 hover:bg-secondary/80 rounded-md transition-all duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
          >
            <Menu className="w-5 h-5 text-muted-foreground hover:text-foreground" aria-hidden="true" />
          </button>
          <button
            onClick={() => navigate('/')}
            aria-label={language === 'fr' ? "The Pulse, retour à l'accueil" : 'The Pulse, back to home'}
            className="flex items-center hover:opacity-85 transition-all duration-200 ease-in-out"
          >
            <BrandLogo className="h-6 sm:h-7" alt="" />
          </button>
        </div>

        {/* Center: Search Bar */}
        <div className="hidden lg:flex flex-1 min-w-0 max-w-xl mx-4 lg:mx-8">
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder={t('searchPlaceholder')}
              className="w-full h-10 pl-10 pr-14 bg-secondary/60 border border-border/40 rounded-full text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:bg-background focus:border-pulse-orange/40 focus:ring-2 focus:ring-pulse-orange/15 shadow-soft-sm transition-all duration-200 ease-in-out"
              onClick={() => navigate('/search')}
              readOnly
            />
            <kbd className="absolute right-3 top-1/2 -translate-y-1/2 hidden lg:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[11px] font-medium text-muted-foreground bg-muted/80 rounded">
              <span>⌘</span>K
            </kbd>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-1.5 sm:gap-2 lg:gap-3">
          
          {/* Global Language Switcher */}
          <button
            onClick={() => setLanguage(language === 'fr' ? 'en' : 'fr')}
            aria-label={`${language.toUpperCase()} — changer de langue / switch language`}
            className="flex items-center gap-1.5 min-h-11 px-2.5 py-1.5 hover:bg-secondary/80 rounded-lg transition-all duration-200 ease-in-out text-xs font-extrabold text-foreground/90 border border-border/50 shadow-soft-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
            title="Changer de langue / Switch language"
          >
            <Globe className="w-3.5 h-3.5 text-pulse-orange" />
            <span>{language.toUpperCase()}</span>
          </button>

          {/* Theme Switcher */}
          <button
            onClick={toggleTheme}
            aria-label={theme === 'dark' ? 'Activer le mode clair' : 'Activer le mode sombre'}
            className="inline-flex items-center justify-center min-w-11 min-h-11 p-2 hover:bg-secondary/80 rounded-md transition-all duration-200 ease-in-out text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
            title={theme === 'dark' ? 'Mode clair' : 'Mode sombre'}
          >
            {theme === 'dark' ? <Sun className="w-5 h-5 text-amber-400 animate-pulse" /> : <Moon className="w-5 h-5" />}
          </button>

          {/* User Role Switcher Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                aria-label={getRoleLabel(activeRole)}
                className="flex items-center gap-1.5 min-h-11 px-2 sm:px-3 py-1.5 rounded-lg border border-border/50 bg-card text-xs font-semibold text-foreground/90 hover:bg-secondary/80 shadow-soft-sm transition-all duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60">
                <span className="relative flex h-2 w-2 mr-0 sm:mr-1">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-pulse-orange opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-pulse-orange"></span>
                </span>
                <span className="hidden sm:inline">{getRoleLabel(activeRole)}</span>
                <ChevronDown className="w-3 h-3 text-muted-foreground" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 bg-popover border-border/50 shadow-soft-md">
              <DropdownMenuLabel className="text-foreground/80">{t('userSpace')}</DropdownMenuLabel>
              <DropdownMenuSeparator className="bg-border/40" />
              
              <DropdownMenuItem onClick={() => handleRoleChange('startup')} className="cursor-pointer focus:bg-secondary/80">
                {getRoleIcon('startup')}
                <span className="flex-1 text-foreground/90">{t('roleStartup')}</span>
                {activeRole === 'startup' && <Check className="w-3.5 h-3.5 text-pulse-orange ml-2" />}
              </DropdownMenuItem>

              <DropdownMenuItem onClick={() => handleRoleChange('investor')} className="cursor-pointer focus:bg-secondary/80">
                {getRoleIcon('investor')}
                <span className="flex-1 text-foreground/90">{t('roleInvestor')}</span>
                {activeRole === 'investor' && <Check className="w-3.5 h-3.5 text-pulse-orange ml-2" />}
              </DropdownMenuItem>

              <DropdownMenuItem onClick={() => handleRoleChange('partner')} className="cursor-pointer focus:bg-secondary/80">
                {getRoleIcon('partner')}
                <span className="flex-1 text-foreground/90">{t('rolePartner')}</span>
                {activeRole === 'partner' && <Check className="w-3.5 h-3.5 text-pulse-orange ml-2" />}
              </DropdownMenuItem>

              <DropdownMenuItem onClick={() => handleRoleChange('admin')} className="cursor-pointer focus:bg-secondary/80">
                {getRoleIcon('admin')}
                <span className="flex-1 text-foreground/90">{t('roleAdmin')}</span>
                {activeRole === 'admin' && <Check className="w-3.5 h-3.5 text-pulse-orange ml-2" />}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Account control.
              Signed out, this routes to the real /login page rather than the
              dialog that used to live here: that form was never wired to
              AuthContext, so submitting it just closed itself and navigated
              home, leaving the caller unauthenticated. */}
          {isAuthenticated ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="outline"
                  className="h-9 px-2 sm:px-3 text-sm font-medium border-border/60 text-foreground/90 hover:bg-secondary/80 rounded-lg shadow-soft-sm"
                  aria-label={accountName || t('connect')}
                >
                  <User className="w-4 h-4 sm:mr-2" />
                  <span className="hidden sm:inline max-w-[120px] truncate">{accountName}</span>
                  <ChevronDown className="w-3.5 h-3.5 ml-1 hidden sm:inline" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 bg-popover border-border/50">
                <DropdownMenuLabel className="text-foreground/90 truncate">
                  {accountName}
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => navigate('/dashboard')}
                  className="cursor-pointer focus:bg-secondary/80"
                >
                  <LayoutDashboard className="w-3.5 h-3.5 mr-2 text-pulse-orange" />
                  <span className="flex-1 text-foreground/90">{t('dashboardTitle')}</span>
                </DropdownMenuItem>
                {/* The account menu is the only navigation that survives on a
                    phone, where the sidebar is behind a drawer, so the two
                    private areas are reachable from here as well. */}
                <DropdownMenuItem
                  onClick={() => navigate('/inbox')}
                  className="cursor-pointer focus:bg-secondary/80"
                >
                  <MessageSquare className="w-3.5 h-3.5 mr-2 text-pulse-orange" />
                  <span className="flex-1 text-foreground/90">
                    {language === 'fr' ? 'Messagerie' : 'Messages'}
                  </span>
                  {unread > 0 && (
                    <span className="bg-pulse-orange text-primary-foreground text-[11px] font-bold min-w-[18px] h-[18px] px-1 rounded-full grid place-items-center">
                      {unread > 99 ? '99+' : unread}
                    </span>
                  )}
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => navigate('/deal-room')}
                  className="cursor-pointer focus:bg-secondary/80"
                >
                  <Lock className="w-3.5 h-3.5 mr-2 text-pulse-orange" />
                  <span className="flex-1 text-foreground/90">Deal Room</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={logout} className="cursor-pointer focus:bg-secondary/80">
                  <LogOut className="w-3.5 h-3.5 mr-2 text-pulse-orange" />
                  <span className="flex-1 text-foreground/90">
                    {language === 'fr' ? 'Déconnexion' : 'Sign out'}
                  </span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Button
              variant="outline"
              onClick={() => navigate('/login')}
              className="h-9 px-2 sm:px-4 text-sm font-medium border-border/60 text-foreground/90 hover:bg-secondary/80 rounded-lg shadow-soft-sm"
              aria-label={t('connect')}
            >
              <span className="hidden sm:inline">{t('connect')}</span>
              <User className="w-4 h-4 sm:ml-2 sm:mr-0" />
            </Button>
          )}

          {/* Power the Pulse Dialog */}
          <Dialog open={isPowerOpen} onOpenChange={handlePowerOpenChange}>
            <DialogTrigger asChild>
              <Button className="h-9 px-2 sm:px-4 text-sm font-medium bg-pulse-orange hover:bg-pulse-orange-hover text-primary-foreground rounded-lg shadow-soft-sm hover:shadow-soft-md transition-all duration-200 ease-in-out" aria-label={t('powerThePulse')}>
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  className="mr-0 sm:mr-1.5"
                >
                  <path
                    d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"
                    fill="currentColor"
                  />
                </svg>
                <span className="hidden sm:inline">{t('powerThePulse')}</span>
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[680px] bg-popover border-border/50 shadow-soft-lg">
              <DialogHeader>
                <DialogTitle className="text-foreground flex items-center gap-2 font-bold text-2xl">
                  <Sparkles className="w-5 h-5 text-pulse-orange" />
                  {t('powerThePulse')}
                </DialogTitle>
              </DialogHeader>
              {renderPowerForm()}
            </DialogContent>
          </Dialog>
          
        </div>
      </div>
    </header>
  );
}
