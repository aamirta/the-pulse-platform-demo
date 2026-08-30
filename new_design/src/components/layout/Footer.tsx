import { useState } from 'react';
import { ChevronDown, Info, Mail, ShieldAlert, Lock, Globe } from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

export default function Footer() {
  const [modalType, setModalType] = useState<'about' | 'contact' | 'legal' | 'privacy' | null>(null);
  const { language, setLanguage, t } = useLanguage();

  const renderModalContent = () => {
    switch (modalType) {
      case 'about':
        return (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-xl font-serif dark:text-white">
                <Info className="w-5 h-5 text-pulse-orange" />
                {t('footerAbout')}
              </DialogTitle>
              <DialogDescription className="dark:text-zinc-400">
                La plateforme de référence de l'écosystème d'innovation au Maroc.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-3 py-3 text-sm text-zinc-600 dark:text-zinc-300 leading-relaxed">
              <p>
                <strong>The Pulse</strong> a pour mission de cartographier, connecter et dynamiser l'écosystème technologique et entrepreneurial marocain.
              </p>
              <p>
                En rassemblant les données clés sur les startups, les fondateurs, les investisseurs, les incubateurs et les opportunités, nous offrons aux acteurs nationaux et internationaux une visibilité unique et des outils d'aide à la décision.
              </p>
              <p className="text-xs text-zinc-400">Version 2.0.0 (Juillet 2026) — Fièrement soutenu par nos partenaires.</p>
            </div>
          </>
        );
      case 'contact':
        return (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-xl font-serif dark:text-white">
                <Mail className="w-5 h-5 text-pulse-orange" />
                {t('footerContact')}
              </DialogTitle>
              <DialogDescription className="dark:text-zinc-400">
                Notre équipe est à votre écoute pour toute suggestion ou partenariat.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-3 text-sm text-zinc-600 dark:text-zinc-300">
              <div className="space-y-2">
                <p><strong>E-mail :</strong> support@thepulse.ma</p>
                <p><strong>Téléphone :</strong> +212 (0) 5 22 22 88 44</p>
                <p><strong>Adresse :</strong> Technopark, Secteur Startup, Casablanca, Maroc</p>
              </div>
              <p className="text-xs text-zinc-400">Nous répondons généralement sous 24h ouvrées.</p>
            </div>
          </>
        );
      case 'legal':
        return (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-xl font-serif dark:text-white">
                <ShieldAlert className="w-5 h-5 text-pulse-orange" />
                {t('footerLegal')}
              </DialogTitle>
              <DialogDescription className="dark:text-zinc-400">
                Informations réglementaires concernant la plateforme.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-3 py-3 text-xs text-zinc-650 dark:text-zinc-350 leading-relaxed max-h-[300px] overflow-y-auto pr-1">
              <p><strong>Éditeur :</strong> Association The Pulse Maroc, association à but non lucratif enregistrée sous le numéro 2024/009182.</p>
              <p><strong>Directeur de la Publication :</strong> Direction de l'Innovation & de l'Entrepreneuriat.</p>
              <p><strong>Hébergeur :</strong> AWS Europe (Paris Region), 38 Avenue John F. Kennedy, L-1855 Luxembourg.</p>
              <p><strong>Droits d'auteur :</strong> Le contenu de ce site, y compris les logos, bases de données de startups, designs et codes sources, est protégé par le droit de la propriété intellectuelle au Maroc.</p>
            </div>
          </>
        );
      case 'privacy':
        return (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-xl font-serif dark:text-white">
                <Lock className="w-5 h-5 text-pulse-orange" />
                {t('footerPrivacy')}
              </DialogTitle>
              <DialogDescription className="dark:text-zinc-400">
                Protection de vos données personnelles et conformité.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-3 py-3 text-xs text-zinc-650 dark:text-zinc-350 leading-relaxed max-h-[300px] overflow-y-auto pr-1">
              <p>
                Conformément à la <strong>loi n° 09-08</strong> relative à la protection des personnes physiques à l'égard du traitement des données à caractère personnel au Maroc, The Pulse s'engage à protéger la confidentialité de vos informations.
              </p>
              <p>
                <strong>Collecte des données :</strong> Nous collectons uniquement les informations publiques sur les entreprises de l'écosystème et les données de compte fournies volontairement par les utilisateurs (nom, e-mail, organisation).
              </p>
              <p>
                <strong>Vos droits :</strong> Vous disposez d'un droit d'accès, de rectification et d'opposition au traitement de vos données personnelles. Pour exercer ce droit, écrivez à privacy@thepulse.ma.
              </p>
            </div>
          </>
        );
      default:
        return null;
    }
  };

  return (
    <footer className="mt-8 -mx-4 lg:-mx-6 px-4 lg:px-6 py-6 bg-card/60 border-t border-border/40 transition-all duration-200 ease-in-out">
      <div className="flex flex-col lg:flex-row items-center justify-between gap-4">
        {/* Partners */}
        <div className="flex items-center gap-4 flex-wrap">
          <span className="text-xs text-muted-foreground">{t('footerSupportedBy')}</span>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5 opacity-70 hover:opacity-100 transition-all duration-200 ease-in-out">
              <div className="w-8 h-8 bg-white border border-border/40 rounded flex items-center justify-center shadow-soft-sm overflow-hidden p-0.5">
                <img src="/avatars/um6p_logo.png" alt="UM6P" className="w-full h-full object-contain" />
              </div>
              <span className="inline-flex items-center min-h-6 text-[11px] font-medium text-foreground/75 hover:text-foreground transition-colors">
                Africa Business School
              </span>
            </div>
            <div className="flex items-center gap-1.5 opacity-70 hover:opacity-100 transition-all duration-200 ease-in-out">
              <div className="w-8 h-8 bg-white border border-border/40 rounded flex items-center justify-center shadow-soft-sm overflow-hidden p-0.5">
                <img src="/avatars/tamwilcom_logo.png" alt="TAMWILCOM" className="w-full h-full object-contain" />
              </div>
              <div className="flex flex-col">
                <span className="inline-flex items-center min-h-6 text-[11px] font-medium text-foreground/75 hover:text-foreground leading-tight transition-colors">
                  TAMWILCOM
                </span>
                <span className="text-[10px] text-foreground/90 leading-tight">
                  GROUPE CDG
                </span>
              </div>
            </div>
            <div className="flex items-center gap-1.5 opacity-70 hover:opacity-100 transition-all duration-200 ease-in-out">
              <div className="w-8 h-8 bg-white border border-border/40 rounded flex items-center justify-center shadow-soft-sm overflow-hidden p-0.5">
                <img src="/avatars/amic_logo.png" alt="AMIC" className="w-full h-full object-contain" />
              </div>
              <div className="flex flex-col">
                <span className="inline-flex items-center min-h-6 text-[11px] font-medium text-foreground/75 hover:text-foreground leading-tight transition-colors">
                  AMIC
                </span>
                <span className="text-[10px] text-foreground/90 leading-tight">
                  Agence Marocaine
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Links */}
        <div className="flex items-center gap-4 lg:gap-6 flex-wrap justify-center">
          <button
            onClick={() => setModalType('about')}
            className="inline-flex items-center min-h-11 px-1 text-xs text-muted-foreground hover:text-pulse-orange transition-all duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60 rounded"
          >
            {t('footerAbout')}
          </button>
          <button
            onClick={() => setModalType('contact')}
            className="inline-flex items-center min-h-11 px-1 text-xs text-muted-foreground hover:text-pulse-orange transition-all duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60 rounded"
          >
            {t('footerContact')}
          </button>
          <button
            onClick={() => setModalType('legal')}
            className="inline-flex items-center min-h-11 px-1 text-xs text-muted-foreground hover:text-pulse-orange transition-all duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60 rounded"
          >
            {t('footerLegal')}
          </button>
          <button
            onClick={() => setModalType('privacy')}
            className="inline-flex items-center min-h-11 px-1 text-xs text-muted-foreground hover:text-pulse-orange transition-all duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60 rounded"
          >
            {t('footerPrivacy')}
          </button>
          <button
            onClick={() => setLanguage(language === 'fr' ? 'en' : 'fr')}
            aria-label={`${language.toUpperCase()} — changer de langue / switch language`}
            className="inline-flex items-center gap-1.5 min-h-11 px-2.5 py-1 text-xs font-bold text-foreground/90 border border-border/50 rounded-md hover:bg-secondary/80 shadow-soft-sm transition-all duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
          >
            <Globe className="w-3 h-3 text-pulse-orange" />
            {language.toUpperCase()}
            <ChevronDown className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Info Dialog Container */}
      <Dialog open={modalType !== null} onOpenChange={(open) => !open && setModalType(null)}>
        <DialogContent className="sm:max-w-[440px] bg-popover border-border/50 shadow-soft-lg">
          {renderModalContent()}
        </DialogContent>
      </Dialog>
    </footer>
  );
}
