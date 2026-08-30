import { useState } from 'react';
import { useLanguage } from '@/context/LanguageContext';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Scale, Coins, Building, Users, Globe, Clock, ArrowRight, FileText } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';

interface Guide {
  id: string;
  category: 'funding' | 'legal' | 'incubator' | 'talent' | 'tax' | 'expansion';
  titleFr: string;
  titleEn: string;
  subtitleFr: string;
  subtitleEn: string;
  readTimeFr: string;
  readTimeEn: string;
  icon: React.ReactNode;
  contentFr: string[];
  contentEn: string[];
}

export default function Guides() {
  const { language } = useLanguage();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedGuide, setSelectedGuide] = useState<Guide | null>(null);

  const categories = [
    { id: 'all', labelFr: 'Tous', labelEn: 'All' },
    { id: 'funding', labelFr: 'Financement', labelEn: 'Funding' },
    { id: 'legal', labelFr: 'Cadre Légal', labelEn: 'Legal Framework' },
    { id: 'incubator', labelFr: 'Accompagnement', labelEn: 'Support' },
    { id: 'talent', labelFr: 'Talents', labelEn: 'Talent & HR' },
    { id: 'tax', labelFr: 'Fiscalité', labelEn: 'Taxation' },
    { id: 'expansion', labelFr: 'Expansion', labelEn: 'Expansion' },
  ];

  const guidesList: Guide[] = [
    {
      id: 'fundraising-morocco',
      category: 'funding',
      titleFr: 'Le Guide Complet de la Levée de Fonds au Maroc',
      titleEn: 'The Complete Guide to Fundraising in Morocco',
      subtitleFr: 'Comprendre les étapes clés, les investisseurs actifs et la préparation de votre pitch deck.',
      subtitleEn: 'Understand key milestones, active investors, and pitch deck preparation.',
      readTimeFr: '8 min de lecture',
      readTimeEn: '8 min read',
      icon: <Coins className="w-5 h-5 text-pulse-orange" />,
      contentFr: [
        '### 1. Comprendre l\'écosystème du capital-risque marocain',
        'Le financement de startups au Maroc a connu une accélération majeure avec le lancement du fonds Innov Invest de la CCG (Tamwilcom) et l\'émergence de fonds locaux et régionaux. Les financements sont généralement structurés en trois grandes étapes : l\'amorçage (Pre-seed/Seed), la série A et l\'expansion.',
        '### 2. Principaux acteurs du financement au Maroc',
        '- **Fonds de Capital-Risque (VC) :** Outlierz Ventures, CDG Invest (212 Founders), Maroc Numeric Fund II (MNF II), Azur Partners.',
        '- **Réseaux de Business Angels :** Angels4Africa, des investisseurs de la diaspora marocaine.',
        '- **Subventions et Prêts d\'honneur :** Programmes de Tamwilcom (ex-CCG) comme Innov Startup (jusqu\'à 200,000 DH de subvention).',
        '### 3. Structurer son dossier d\'investissement',
        'Pour convaincre un fonds marocain, votre pitch deck doit mettre l\'accent sur :',
        '- **L\'opportunité de marché :** Le Maroc comme marché initial avec un potentiel d\'expansion vers l\'Afrique francophone ou l\'Europe.',
        '- **L\'équipe :** Profils complémentaires avec une forte capacité d\'exécution locale.',
        '- **La traction :** Métriques d\'engagement, chiffre d\'affaires ou partenariats pilotes validés.',
        '### 4. Aspects juridiques spécifiques',
        'La levée de fonds s\'accompagne de la négociation d\'une *Term Sheet* suivie du pacte d\'actionnaires. Les startups enregistrées au Maroc doivent veiller aux réglementations de l\'Office des Changes en cas d\'entrée d\'investisseurs étrangers dans leur capital.'
      ],
      contentEn: [
        '### 1. Understanding the Moroccan Venture Capital Ecosystem',
        'Startup funding in Morocco has accelerated significantly with the launch of the Innov Invest fund by CCG (Tamwilcom) and the growth of local and regional VCs. Funding is generally structured around three key phases: Pre-seed/Seed, Series A, and Expansion.',
        '### 2. Main Funding Players in Morocco',
        '- **Venture Capital Funds (VCs):** Outlierz Ventures, CDG Invest (212 Founders), Maroc Numeric Fund II (MNF II), Azur Partners.',
        '- **Business Angel Networks:** Angels4Africa, diaspora investor groups.',
        '- **Grants and Soft Loans:** Tamwilcom programs like Innov Startup (up to 200,000 DH in grants).',
        '### 3. Structuring Your Investment Pitch',
        'To convince a Moroccan VC, your pitch deck must highlight:',
        '- **Market Opportunity:** Morocco as a launchpad with clear expansion plans to Francophone Africa or Europe.',
        '- **The Team:** Complementary skills with deep local execution capability.',
        '- **Traction:** Solid engagement metrics, revenue, or validated pilot agreements.',
        '### 4. Key Legal Aspects',
        'Fundraising involves negotiating a Term Sheet followed by a Shareholder Agreement (SHA). Startups incorporated in Morocco must coordinate closely with the Office des Changes when foreign investors join the cap table.'
      ]
    },
    {
      id: 'startup-label-act',
      category: 'legal',
      titleFr: 'Le Label Startup & Startup Act Maroc',
      titleEn: 'The Startup Label & Moroccan Startup Act',
      subtitleFr: 'Comment labelliser sa startup et bénéficier des avantages douaniers, de change et fiscaux.',
      subtitleEn: 'How to label your startup and leverage customs, forex, and tax benefits.',
      readTimeFr: '5 min de lecture',
      readTimeEn: '5 min read',
      icon: <Scale className="w-5 h-5 text-pulse-orange" />,
      contentFr: [
        '### 1. Qu\'est-ce que la labellisation Startup au Maroc ?',
        'Le label est un statut officiel accordé aux entreprises innovantes à fort potentiel de croissance au Maroc. Il permet de distinguer les startups des PME classiques auprès des administrations publiques.',
        '### 2. Les critères d\'éligibilité',
        'Pour obtenir le label, l\'entreprise doit :',
        '- Être constituée légalement au Maroc depuis moins de 8 ans.',
        '- Avoir un modèle économique innovant et hautement scalable.',
        '- Présenter des dépenses de R&D significatives ou être incubée par une structure accréditée.',
        '### 3. Les principaux avantages du Label',
        '- **Facilités de l\'Office des Changes :** Autorisation de disposer de comptes en devises étrangères pour régler les services numériques internationaux.',
        '- **Facilités douanières :** Simplification des procédures d\'importation et d\'exportation pour le matériel informatique ou technologique.',
        '- **Accès prioritaire aux marchés publics :** Mesures favorisant la collaboration des startups avec les grands donneurs d\'ordres étatiques.'
      ],
      contentEn: [
        '### 1. What is the Startup Label in Morocco?',
        'The Startup Label is an official status granted to innovative companies with high growth potential in Morocco. It distinguishes startups from traditional SMEs in the eyes of government agencies.',
        '### 2. Eligibility Criteria',
        'To receive the label, the company must:',
        '- Be legally incorporated in Morocco for less than 8 years.',
        '- Show an innovative and highly scalable business model.',
        '- Demonstrate significant R&D expenses or be backed by an accredited incubator.',
        '### 3. Major Advantages of the Label',
        '- **Forex/Exchange Facilities:** Permission to maintain foreign currency accounts to pay for international SaaS and software services.',
        '- **Customs Facilities:** Streamlined import/export processes for hardware and technological components.',
        '- **Priority Public Procurement:** Incentives promoting startup partnerships with state enterprises.'
      ]
    },
    {
      id: 'incubation-programs',
      category: 'incubator',
      titleFr: 'Choisir son Incubateur au Maroc',
      titleEn: 'Choosing Your Incubator in Morocco',
      subtitleFr: 'Comparatif des meilleurs programmes d\'incubation et d\'accélération de l\'écosystème.',
      subtitleEn: 'Comparison of the top incubation and acceleration programs in the ecosystem.',
      readTimeFr: '6 min de lecture',
      readTimeEn: '6 min read',
      icon: <Building className="w-5 h-5 text-pulse-orange" />,
      contentFr: [
        '### 1. Pourquoi rejoindre un incubateur ?',
        'Un incubateur apporte de la structuration, du mentorat de haut niveau, un espace de coworking et surtout un accès facilité aux premiers financements et investisseurs.',
        '### 2. Les programmes phares au Maroc',
        '- **Startgate (UM6P - Ben Guerir) :** Le plus grand hub de startups du Maroc avec des infrastructures exceptionnelles, des connexions avec des universités globales et des programmes sectoriels (AgriTech, Mining, Biotech).',
        '- **Impact Lab (Casablanca) :** Pionnier de l\'accompagnement de startups à fort impact social et environnemental au Maroc.',
        '- **LaStartupFactory (Casablanca) :** Spécialisée dans l\'innovation d\'entreprise (Open Innovation) et l\'accélération de projets digitaux.',
        '- **212 Founders (CDG Invest) :** Un programme d\'accompagnement et d\'investissement unique (pouvant investir jusqu\'à 3 MDH en pré-amorçage).',
        '### 3. Comment réussir sa candidature ?',
        '- **Montrer la validation du problème :** Ne présentez pas seulement une idée, montrez que vous avez parlé à de futurs clients.',
        '- **Avoir un MVP :** Un prototype même simple démontre votre capacité d\'exécution.',
        '- **Être engagé à plein temps :** Les jurys privilégient les fondateurs dédiés à 100% à leur projet.'
      ],
      contentEn: [
        '### 1. Why Join an Incubator?',
        'An incubator provides structured methodologies, expert mentorship, coworking space, and direct access to early funding opportunities and investors.',
        '### 2. Top Programs in Morocco',
        '- **Startgate (UM6P - Ben Guerir):** The largest startup campus in Morocco featuring world-class facilities, global university networks, and targeted vertical tracks (AgriTech, CleanTech, Mining).',
        '- **Impact Lab (Casablanca):** A pioneer in backing impact-driven and sustainability startups.',
        '- **LaStartupFactory (Casablanca):** Focused heavily on corporate partnerships (Open Innovation) and digital acceleration.',
        '- **212 Founders (CDG Invest):** A highly selective acceleration and funding program that can deploy up to 3 million dirhams in pre-seed equity.',
        '### 3. Tips for a Successful Application',
        '- **Prove Problem Validation:** Don\'t just pitch an idea; show you have surveyed or interviewed real prospective users.',
        '- **Build a MVP:** Even a basic prototype shows capability to build and ship.',
        '- **Commit Full-Time:** Selection panels look for founders who are fully committed to their startup.'
      ]
    },
    {
      id: 'talent-recruitment-morocco',
      category: 'talent',
      titleFr: 'Recruter et Fidéliser ses Talents Tech',
      titleEn: 'Recruiting & Retaining Tech Talents',
      subtitleFr: 'Attirer les meilleurs profils de développeurs, chefs de produit et growth hackers au Maroc.',
      subtitleEn: 'Attract top developer profiles, product managers, and growth hackers in Morocco.',
      readTimeFr: '7 min de lecture',
      readTimeEn: '7 min read',
      icon: <Users className="w-5 h-5 text-pulse-orange" />,
      contentFr: [
        '### 1. Le marché des talents tech au Maroc',
        'Le Maroc dispose d\'un excellent vivier d\'ingénieurs formés dans des écoles prestigieuses (EMI, EHTP, ENSIAS, 1337, Youcode), mais la concurrence internationale (télétravail pour l\'Europe) est intense.',
        '### 2. Rendre sa startup attractive',
        '- **Une culture d\'entreprise forte :** Autonomie, flexibilité (télétravail partiel), et mission stimulante.',
        '- **Mettre en place un plan d\'options d\'achat d\'actions (ESOP) :** Associer les employés clés au capital pour compenser des salaires initiaux parfois plus bas que les multinationales.',
        '### 3. Les canaux de recrutement efficaces',
        '- **LinkedIn :** Le réseau incontournable pour approcher directement les profils expérimentés.',
        '- **Hackathons et Écoles partenaires :** Idéal pour recruter des juniors passionnés directement à la sortie d\'écoles de code comme 1337.',
        '- **Plateformes de freelancing locales :** Pour valider des compétences sur des missions courtes avant une embauche.'
      ],
      contentEn: [
        '### 1. The Tech Talent Market in Morocco',
        'Morocco has a strong pipeline of engineers trained in top-tier institutions (EMI, EHTP, ENSIAS, 1337, Youcode), but competition from remote European firms is fierce.',
        '### 2. Making Your Startup Attractive',
        '- **Strong Corporate Culture:** Autonomy, flexible remote setups, and an impactful mission.',
        '- **ESOP/Equity Incentives:** Setting up an Employee Stock Ownership Plan to let key hires participate in the future upside.',
        '### 3. Effective Hiring Channels',
        '- **LinkedIn:** Essential for direct sourcing of mid-to-senior profiles.',
        '- **Hackathons & Coding Schools:** Direct outreach to fresh, motivated graduates from programs like 1337 or Youcode.',
        '- **Local Freelance Platforms:** Great for screening candidates on short trial projects before offering full-time roles.'
      ]
    },
    {
      id: 'taxation-incentives',
      category: 'tax',
      titleFr: 'Fiscalité et Avantages Fiscaux des Startups',
      titleEn: 'Taxation & Fiscal Incentives for Startups',
      subtitleFr: 'Comprendre l\'Impôt sur les Sociétés (IS), l\'IR et les exonérations applicables aux jeunes entreprises.',
      subtitleEn: 'Understand Corporate Income Tax (IS), Personal Income Tax (IR), and exemptions.',
      readTimeFr: '5 min de lecture',
      readTimeEn: '5 min read',
      icon: <FileText className="w-5 h-5 text-pulse-orange" />,
      contentFr: [
        '### 1. Exonérations de la TVA sur les biens d\'investissement',
        'Les nouvelles entreprises constituées au Maroc peuvent être exonérées de la TVA sur le matériel et les biens d\'équipement acquis localement ou importés, sous conditions de délais (36 mois à compter du début d\'activité).',
        '### 2. Barèmes de l\'Impôt sur les Sociétés (IS)',
        'Le Maroc applique un barème progressif d\'IS. Les entreprises réalisant un bénéfice net inférieur à 300 000 DH bénéficient généralement de taux réduits.',
        '### 3. Incitations fiscales de la Loi de Finances',
        'Des allègements spécifiques de l\'impôt sur le revenu (IR) peuvent s\'appliquer pour les salaires des collaborateurs recrutés par les startups innovantes, notamment dans le cadre de dispositifs nationaux d\'aide à l\'emploi (ANAPEC).'
      ],
      contentEn: [
        '### 1. VAT Exemptions on Equipment Assets',
        'Newly incorporated companies in Morocco can request exemption from VAT on capital goods and machinery purchased locally or imported within the first 36 months of launching.',
        '### 2. Corporate Income Tax (IS) Brackets',
        'Morocco uses a progressive CIT structure. Companies earning a net profit of less than 300,000 DH fall into lower tax brackets, favoring early-stage cash flow.',
        '### 3. Employment & Payroll Tax Relief',
        'Special income tax (IR) relief programs, often coordinated via ANAPEC contract schemes, reduce social security and payroll burdens on startup hiring budgets.'
      ]
    },
    {
      id: 'regional-expansion',
      category: 'expansion',
      titleFr: 'S\'étendre du Maroc vers l\'Afrique Subsaharienne',
      titleEn: 'Expanding from Morocco to Subsaharian Africa',
      subtitleFr: 'Les aspects logistiques, de change et réglementaires pour adresser les marchés régionaux.',
      subtitleEn: 'Logistics, foreign exchange, and regulatory frameworks to capture regional markets.',
      readTimeFr: '6 min de lecture',
      readTimeEn: '6 min read',
      icon: <Globe className="w-5 h-5 text-pulse-orange" />,
      contentFr: [
        '### 1. Le Maroc comme hub vers l\'Afrique',
        'Grâce aux liaisons de Royal Air Maroc, à la présence de grands groupes bancaires marocains (Attijariwafa Bank, BCP, Bank of Africa) et au cadre de Casablanca Finance City (CFC), le Maroc est un tremplin idéal vers l\'Afrique francophone (Sénégal, Côte d\'Ivoire, Cameroun).',
        '### 2. Gérer le flux financier (Office des Changes)',
        'L\'expansion nécessite souvent l\'envoi de fonds à l\'étranger pour créer des filiales. L\'obtention du statut CFC ou du Label Startup permet de simplifier l\'octroi d\'allocations devises pour investissement à l\'étranger.',
        '### 3. Adapter son produit au marché local',
        '- **Moyens de paiement :** Intégrer les solutions de Mobile Money (MTN, Orange Money) incontournables dans la région.',
        '- **Connectivité :** Optimiser l\'application pour une utilisation faible en données mobiles et sur des téléphones d\'entrée de gamme.'
      ],
      contentEn: [
        '### 1. Morocco as a Gateway to Africa',
        'Leveraging Royal Air Maroc connections, the international presence of Moroccan banks (Attijariwafa Bank, BCP, Bank of Africa), and the Casablanca Finance City (CFC) framework, Morocco is an ideal pad to expand into Francophone Africa.',
        '### 2. Managing International Capital Flows',
        'Setting up regional subsidiaries requires sending equity capital abroad. Obtaining the CFC status or the Startup Label unlocks accelerated foreign exchange approvals for international investments.',
        '### 3. Adapting Your Tech to Local Realities',
        '- **Payment Methods:** Integrate Mobile Money (MTN, Orange Money, Wave) which dominate consumer transactions in target West African markets.',
        '- **Connectivity:** Design lightweight applications with offline capabilities to mitigate high mobile data costs.'
      ]
    }
  ];

  const filteredGuides = guidesList.filter((guide) => {
    const matchesSearch =
      guide.titleFr.toLowerCase().includes(searchQuery.toLowerCase()) ||
      guide.titleEn.toLowerCase().includes(searchQuery.toLowerCase()) ||
      guide.subtitleFr.toLowerCase().includes(searchQuery.toLowerCase()) ||
      guide.subtitleEn.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesCategory = selectedCategory === 'all' || guide.category === selectedCategory;

    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-1 font-serif">
          {language === 'fr' ? 'Guides de l\'écosystème' : 'Ecosystem Guides'}
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          {language === 'fr' 
            ? 'Retrouvez toutes les ressources et informations essentielles pour structurer, financer et développer votre projet innovant au Maroc.'
            : 'Find all essential resources and insights to structure, fund, and scale your innovative project in Morocco.'}
        </p>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col sm:flex-row gap-4 items-stretch sm:items-center justify-between">
        <div className="flex flex-wrap gap-1.5">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 ${
                selectedCategory === cat.id
                  ? 'bg-pulse-orange text-white shadow-soft-sm'
                  : 'bg-secondary/40 text-muted-foreground hover:bg-secondary/60 hover:text-foreground'
              }`}
            >
              {language === 'fr' ? cat.labelFr : cat.labelEn}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-[260px]">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder={language === 'fr' ? 'Rechercher un guide...' : 'Search guides...'}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-secondary/30 border-border/50 text-xs w-full rounded-lg"
          />
        </div>
      </div>

      {/* Guides Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <AnimatePresence mode="popLayout">
          {filteredGuides.length > 0 ? (
            filteredGuides.map((guide, index) => (
              <motion.div
                key={guide.id}
                layout
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.2, delay: index * 0.03 }}
                whileHover={{ y: -2 }}
                onClick={() => setSelectedGuide(guide)}
                className="p-5 bg-white dark:bg-zinc-900 border border-zinc-150/40 dark:border-zinc-800 rounded-xl cursor-pointer hover:shadow-soft-md transition-all group flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="p-2 bg-pulse-orange/5 dark:bg-pulse-orange/10 rounded-lg">
                      {guide.icon}
                    </div>
                    <div className="flex items-center gap-1 text-[11px] text-muted-foreground font-medium">
                      <Clock className="w-3.5 h-3.5" />
                      <span>{language === 'fr' ? guide.readTimeFr : guide.readTimeEn}</span>
                    </div>
                  </div>
                  <h3 className="text-base font-bold text-zinc-900 dark:text-white mb-2 group-hover:text-pulse-orange transition-colors duration-200">
                    {language === 'fr' ? guide.titleFr : guide.titleEn}
                  </h3>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed mb-4">
                    {language === 'fr' ? guide.subtitleFr : guide.subtitleEn}
                  </p>
                </div>
                <div className="flex items-center gap-1 text-xs font-bold text-pulse-orange group-hover:gap-2 transition-all mt-2">
                  <span>{language === 'fr' ? 'Lire le guide' : 'Read Guide'}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              </motion.div>
            ))
          ) : (
            <div className="col-span-2 text-center py-12 text-sm text-muted-foreground">
              {language === 'fr' ? 'Aucun guide trouvé' : 'No guides found'}
            </div>
          )}
        </AnimatePresence>
      </div>

      {/* Guide Detail Dialog */}
      <Dialog open={!!selectedGuide} onOpenChange={() => setSelectedGuide(null)}>
        <DialogContent className="sm:max-w-[720px] max-h-[85vh] overflow-y-auto bg-popover border-border/50 shadow-soft-lg p-6">
          {selectedGuide && (
            <>
              <DialogHeader className="border-b border-border/30 pb-4 mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <Badge className="bg-pulse-orange/10 text-pulse-orange hover:bg-pulse-orange/15 font-semibold text-[10px]">
                    {language === 'fr' 
                      ? categories.find(c => c.id === selectedGuide.category)?.labelFr 
                      : categories.find(c => c.id === selectedGuide.category)?.labelEn}
                  </Badge>
                  <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
                    <Clock className="w-3 h-3" />
                    <span>{language === 'fr' ? selectedGuide.readTimeFr : selectedGuide.readTimeEn}</span>
                  </div>
                </div>
                <DialogTitle className="text-xl sm:text-2xl font-extrabold text-foreground leading-tight">
                  {language === 'fr' ? selectedGuide.titleFr : selectedGuide.titleEn}
                </DialogTitle>
                <DialogDescription className="text-xs sm:text-sm text-muted-foreground mt-1">
                  {language === 'fr' ? selectedGuide.subtitleFr : selectedGuide.subtitleEn}
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4 text-sm text-foreground/90 leading-relaxed pr-2">
                {(language === 'fr' ? selectedGuide.contentFr : selectedGuide.contentEn).map((paragraph, index) => {
                  if (paragraph.startsWith('###')) {
                    return (
                      <h4 key={index} className="text-base font-extrabold text-foreground pt-3 border-t border-border/10 mt-4 first:border-t-0 first:pt-0">
                        {paragraph.replace('### ', '')}
                      </h4>
                    );
                  }
                  if (paragraph.startsWith('-')) {
                    return (
                      <div key={index} className="pl-4 border-l-2 border-pulse-orange/40 italic text-muted-foreground py-0.5 my-1">
                        {paragraph.replace('- ', '')}
                      </div>
                    );
                  }
                  return <p key={index}>{paragraph}</p>;
                })}
              </div>

              <div className="mt-6 pt-4 border-t border-border/30 flex justify-end">
                <Button 
                  onClick={() => setSelectedGuide(null)} 
                  className="bg-pulse-orange hover:bg-pulse-orange-hover text-primary-foreground text-xs rounded-lg px-4"
                >
                  {language === 'fr' ? 'Fermer' : 'Close'}
                </Button>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
