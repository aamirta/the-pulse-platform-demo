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
        ? "Comment référencer ma startup sur The Pulse ?" 
        : "How to list my startup on The Pulse?",
      answer: language === 'fr'
        ? "Pour référencer votre entreprise, cliquez sur 'Power the Pulse' dans la barre supérieure ou créez un compte Startup. Après validation de nos équipes sous 24 à 48 heures, votre fiche sera publiée et visible par les investisseurs qualifiés du réseau."
        : "To list your startup, click 'Power the Pulse' in the top header or create a Startup account. After team validation within 24-48h, your profile will be published to the verified investors in the network.",
    },
    {
      id: 'faq-2',
      question: language === 'fr'
        ? "Comment les investisseurs accèdent-ils aux opportunités de dealflow ?"
        : "How do investors access dealflow opportunities?",
      answer: language === 'fr'
        ? "Les fonds de VC et Business Angels certifiés disposent d'un tableau de bord 'Investisseur' dédié leur permettant de filtrer les levées de fonds par secteur, ticket cible, MRR et niveau de maturité."
        : "Certified VC funds and Business Angels get access to a dedicated Investor Workspace with granular filters by sector, check size, MRR, and maturity level.",
    },
    {
      id: 'faq-4',
      question: language === 'fr'
        ? "Comment l'Assistant IA analyse-t-il les opportunités du marché marocain ?"
        : "How does the AI Assistant analyze Moroccan market opportunities?",
      answer: language === 'fr'
        ? "Notre IA exploite la base de données certifiée The Pulse, synchronisée avec les rapports officiels de l'AMIC et des ministères de tutelle. Les données sensibles des startups restent confidentielles et protégées."
        : "Our AI model draws directly from The Pulse's verified dataset, cross-referenced with official AMIC reports. Sensitive startup data remains completely confidential.",
    },
  ];

  return (
    <ScrollReveal variants={fadeUp} className="w-full py-8 space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center space-y-2">
        <span className="text-xs font-extrabold uppercase tracking-widest text-pulse-orange flex items-center justify-center gap-1.5">
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
