export interface Startup {
  id: string;
  name: string;
  sector: string[];
  stage: string;
  status: string;
  location: string;
  description: string;
  funding: number;
  fundingCurrency: string;
  teamSize: string;
  yearFounded: number;
  logo: string;
  website?: string;
  linkedin?: string;
}

export interface Founder {
  id: string;
  name: string;
  role: string;
  startup: string;
  startupId: string;
  location: string;
  bio: string;
  avatar: string;
  linkedin?: string;
  experience?: string;
  /** Delimited skill list from the founder detail endpoint. */
  skills?: string | null;
  /**
   * "founder" for a sole founder, "cofounder" for someone who founded a company
   * alongside others. Derived server-side from the startup-founder join, never
   * stored, so the client must not try to work it out for itself.
   */
  founder_type?: 'founder' | 'cofounder';
}

/** Ecosystem expert / mentor, from `GET /experts/`. */
export interface Expert {
  id: string;
  name: string;
  title?: string | null;
  organization?: string | null;
  location?: string | null;
  expertiseDomain?: string | null;
  yearsExperience?: string | null;
  skills: string[];
  availability?: string | null;
  linkedin?: string | null;
  profilePic?: string | null;
}

/**
 * A project seeking co-founders, from `GET /cofounders/`.
 *
 * These are postings, not people — the Co-founders section renders them as
 * opportunity cards rather than profile cards.
 */
export interface CofounderProject {
  id: string;
  title: string;
  domain?: string | null;
  stage?: string | null;
  description?: string | null;
  rolesNeeded: string[];
  skillsNeeded: string[];
  authorName?: string | null;
  authorAffiliation?: string | null;
  authorLinkedin?: string | null;
  commitmentType?: string | null;
  locationPreference?: string | null;
  equityOffered?: string | null;
}

export interface Investor {
  id: string;
  name: string;
  type: string;
  location: string;
  focus: string[];
  portfolio: number;
  investments: number;
  logo: string;
  website?: string;
}

export interface NewsItem {
  id: string;
  type: 'funding' | 'news' | 'event' | 'blog';
  title: string;
  description: string;
  source: string;
  sourceAvatar: string;
  /** Pre-rendered relative date from the API — French only. */
  date: string;
  /** ISO timestamp; format this per active language rather than using `date`. */
  publishedAt?: string | null;
  image: string;
  tags?: string[];
  amount?: string;
  round?: string;
  eventDate?: string;
}

export interface FundingRound {
  id: string;
  startup: string;
  startupLogo: string;
  amount: string;
  round: string;
  investor: string;
  date: string;
}

export interface Event {
  id: string;
  title: string;
  description: string;
  location: string;
  startDate: string;
  endDate?: string;
  organizer: string;
  image: string;
  attendees?: number;
}

export interface Opportunity {
  id: string;
  title: string;
  organization: string;
  deadline: string;
  category: string;
  description: string;
}

export interface Trend {
  tag: string;
  count: number;
}

export interface EcosystemStat {
  label: string;
  value: string;
  icon: string;
}

export interface NavItem {
  label: string;
  icon: string;
  href: string;
  section?: string;
}

export type GraphNodeType = 'startup' | 'founder' | 'investor' | 'incubator';
export type GraphLinkType = 'founded' | 'invested' | 'incubated' | 'supported';

export interface EcosystemGraphNode {
  id: string;
  refId: string;
  name: string;
  type: GraphNodeType;
  sector?: string | null;
  location?: string | null;
  connections: number;
}

export interface EcosystemGraphLink {
  source: string;
  target: string;
  type: GraphLinkType;
}

export interface EcosystemGraphTotals {
  startups: number;
  founders: number;
  investors: number;
  incubators: number;
  founded: number;
  invested: number;
  incubated: number;
  supported: number;
}

export interface EcosystemGraphData {
  nodes: EcosystemGraphNode[];
  links: EcosystemGraphLink[];
  totals: EcosystemGraphTotals;
  truncated: boolean;
}

export interface Incubator {
  id: number;
  name: string;
  type: string;
  status: string;
  city: string;
  investmentPhases: string[];
  image: string;
  sectors: string[];
  linkedin?: string | null;
}
