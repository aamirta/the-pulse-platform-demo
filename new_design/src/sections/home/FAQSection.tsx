import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { HelpCircle } from 'lucide-react';
import { ScrollReveal } from '@/components/ui/ScrollReveal';
import { fadeUp } from '@/lib/motion';
import { useLanguage } from '@/context/LanguageContext';

export default function FAQSection() {
  const { t, language } = useLanguage();

  const faqs = [
    {
      id: 'faq-1',
      question: language === 'fr'
        ? 'Comment référencer ma startup ?'
        : 'How do I list my startup?',
      answer: language === 'fr'
        ? "Cliquez sur « Power the Pulse » dans la barre supérieure, ou créez un compte. Vous renseignez votre fiche, nous la relisons avant publication."
        : 'Click "Power the Pulse" in the top bar, or create an account. You fill in your profile and we review it before publishing.',
    },
    {
      id: 'faq-2',
      question: language === 'fr'
        ? "Comment accéder au dealflow en tant qu'investisseur ?"
        : 'How do I access the dealflow as an investor?',
      answer: language === 'fr'
        ? "Créez un compte investisseur et demandez l'accès à la Deal Room. Vous y voyez les startups qui lèvent et pouvez filtrer par secteur, stade et montant recherché."
        : 'Create an investor account and request access to the Deal Room. You will see the startups that are raising, filterable by sector, stage and target amount.',
    },
    {
      id: 'faq-3',
      question: language === 'fr'
        ? "D'où viennent les données de l'Assistant IA ?"
        : 'Where does the AI Assistant get its data?',
      answer: language === 'fr'
        ? "De la base The Pulse : startups, fondateurs, investisseurs, levées et programmes référencés sur la plateforme. L'assistant répond à partir de ces fiches, pas d'une source extérieure."
        : 'From The Pulse database: the startups, founders, investors, funding rounds and programmes listed on the platform. The assistant answers from those records, not from an outside source.',
    },
    {
      // Added at the review's request: the live site carries an MVP banner, and
      // the platform should say plainly how complete its data is.
      id: 'faq-4',
      question: language === 'fr'
        ? 'Les données sont-elles fiables ?'
        : 'Is the data reliable?',
      answer: language === 'fr'
        ? "The Pulse est un MVP en cours d'évolution. Les fiches proviennent de sources publiques et des contributions de l'écosystème : certaines sont incomplètes ou datées. Si vous repérez une erreur sur votre fiche, signalez-la, nous la corrigeons."
        : 'The Pulse is an MVP still evolving. Records come from public sources and from the ecosystem itself, so some are incomplete or out of date. If you spot an error on your profile, tell us and we will correct it.',
    },
  ];

  return (
    <ScrollReveal variants={fadeUp} className="w-full py-8 space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center space-y-2">
        <span className="text-xs font-extrabold tracking-wide text-pulse-orange flex items-center justify-center gap-1.5">
          <HelpCircle className="w-3.5 h-3.5" />
          {t('faqTag')}
        </span>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-foreground tracking-tight">
          {t('faqTitle')}
        </h2>
        <p className="text-xs sm:text-sm text-muted-foreground">
          {t('faqSubtitle')}
        </p>
      </div>

      {/* Accordion List */}
      <div className="bg-card border border-border/40 rounded-3xl p-6 sm:p-8 shadow-soft-md">
        <Accordion type="single" collapsible className="w-full space-y-3">
          {faqs.map((faq) => (
            <AccordionItem
              key={faq.id}
              value={faq.id}
              className="border border-border/40 rounded-2xl px-4 py-1 data-[state=open]:bg-secondary/40 shadow-soft-sm transition-all duration-200 ease-in-out"
            >
              <AccordionTrigger className="text-sm font-bold text-foreground hover:no-underline hover:text-pulse-orange transition-colors">
                {faq.question}
              </AccordionTrigger>
              <AccordionContent className="text-xs sm:text-sm text-muted-foreground leading-relaxed pt-1 pb-3">
                {faq.answer}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </ScrollReveal>
  );
}
