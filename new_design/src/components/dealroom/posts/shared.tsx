/**
 * Presentation vocabulary for the opportunity marketplace.
 *
 * Labels only. Every *value* these translate comes from the API — the server's
 * taxonomy decides what a post type is, this decides how to say it in English
 * and French. A value with no entry here falls back to a de-slugged version of
 * itself, so a post type added on the server renders sensibly before anyone
 * touches the client.
 */

import type { ReactNode } from 'react';
import {
  Banknote,
  Briefcase,
  GraduationCap,
  Handshake,
  Lightbulb,
  TrendingUp,
  UserPlus,
  Users,
  Wrench,
} from 'lucide-react';
import type { PostStatus, PostType } from '@/types/dealroomPosts';

/** Turn an unknown slug into something readable rather than showing raw snake_case. */
export function humanise(value: string | null | undefined): string {
  if (!value) return '';
  return value
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

const POST_TYPE_LABELS: Record<string, { en: string; fr: string }> = {
  raising_capital: { en: 'Raising capital', fr: 'Levée de fonds' },
  offering_capital: { en: 'Offering capital', fr: 'Capital disponible' },
  seeking_cofounder: { en: 'Seeking co-founder', fr: 'Recherche cofondateur' },
  seeking_advisor: { en: 'Seeking advisor', fr: 'Recherche conseiller' },
  seeking_talent: { en: 'Hiring', fr: 'Recrutement' },
  seeking_partnership: { en: 'Seeking partnership', fr: 'Recherche partenariat' },
  offering_service: { en: 'Offering a service', fr: 'Service proposé' },
  offering_mentorship: { en: 'Offering mentorship', fr: 'Mentorat proposé' },
};

const COUNTERPARTY_LABELS: Record<string, { en: string; fr: string }> = {
  any: { en: 'Anyone', fr: 'Tout le monde' },
  investor: { en: 'Investors', fr: 'Investisseurs' },
  founder: { en: 'Founders', fr: 'Fondateurs' },
  startup: { en: 'Startups', fr: 'Startups' },
  expert: { en: 'Experts', fr: 'Experts' },
  incubator: { en: 'Incubators', fr: 'Incubateurs' },
  service_provider: { en: 'Service providers', fr: 'Prestataires' },
  talent: { en: 'Talent', fr: 'Talents' },
};

const COMMITMENT_LABELS: Record<string, { en: string; fr: string }> = {
  full_time: { en: 'Full time', fr: 'Temps plein' },
  part_time: { en: 'Part time', fr: 'Temps partiel' },
  advisory: { en: 'Advisory', fr: 'Conseil' },
  one_off: { en: 'One-off', fr: 'Ponctuel' },
  equity_only: { en: 'Equity only', fr: 'Equity uniquement' },
};

const STAGE_LABELS: Record<string, { en: string; fr: string }> = {
  idea: { en: 'Idea', fr: 'Idée' },
  pre_seed: { en: 'Pre-seed', fr: 'Pré-amorçage' },
  seed: { en: 'Seed', fr: 'Amorçage' },
  series_a: { en: 'Series A', fr: 'Série A' },
  series_b: { en: 'Series B', fr: 'Série B' },
  growth: { en: 'Growth', fr: 'Croissance' },
  not_applicable: { en: 'Not applicable', fr: 'Sans objet' },
};

const STATUS_LABELS: Record<string, { en: string; fr: string }> = {
  draft: { en: 'Draft', fr: 'Brouillon' },
  published: { en: 'Live', fr: 'En ligne' },
  closed: { en: 'Closed', fr: 'Clôturé' },
  archived: { en: 'Archived', fr: 'Archivé' },
};

const REPORT_REASON_LABELS: Record<string, { en: string; fr: string }> = {
  spam: { en: 'Spam or repetitive', fr: 'Spam ou répétitif' },
  misleading: { en: 'Misleading claims', fr: 'Informations trompeuses' },
  offensive: { en: 'Offensive content', fr: 'Contenu offensant' },
  scam: { en: 'Looks like a scam', fr: 'Semble frauduleux' },
  off_topic: { en: 'Not an opportunity', fr: 'Hors sujet' },
  other: { en: 'Something else', fr: 'Autre' },
};

function lookup(
  table: Record<string, { en: string; fr: string }>,
  value: string | null | undefined,
  language: string,
): string {
  if (!value) return '';
  const entry = table[value];
  if (!entry) return humanise(value);
  return language === 'en' ? entry.en : entry.fr;
}

export const postTypeLabel = (v: string | null | undefined, lang: string) =>
  lookup(POST_TYPE_LABELS, v, lang);
export const counterpartyLabel = (v: string | null | undefined, lang: string) =>
  lookup(COUNTERPARTY_LABELS, v, lang);
export const commitmentLabel = (v: string | null | undefined, lang: string) =>
  lookup(COMMITMENT_LABELS, v, lang);
export const stageLabel = (v: string | null | undefined, lang: string) =>
  lookup(STAGE_LABELS, v, lang);
export const postStatusLabel = (v: string | null | undefined, lang: string) =>
  lookup(STATUS_LABELS, v, lang);
export const reportReasonLabel = (v: string | null | undefined, lang: string) =>
  lookup(REPORT_REASON_LABELS, v, lang);

/** Icon per post type, so the board is scannable without reading every label. */
export function PostTypeIcon({ type, className }: { type: PostType | string; className?: string }) {
  const icons: Record<string, typeof TrendingUp> = {
    raising_capital: TrendingUp,
    offering_capital: Banknote,
    seeking_cofounder: UserPlus,
    seeking_advisor: Lightbulb,
    seeking_talent: Briefcase,
    seeking_partnership: Handshake,
    offering_service: Wrench,
    offering_mentorship: GraduationCap,
  };
  const Icon = icons[type] ?? Users;
  return <Icon className={className} />;
}

/**
 * Tone per post type. Capital in and capital out are the two the eye should
 * separate fastest, so they take the two strongest colours.
 */
export function postTypeTone(type: string): string {
  switch (type) {
    case 'raising_capital':
      return 'bg-pulse-orange/10 text-pulse-orange border-pulse-orange/20';
    case 'offering_capital':
      return 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20';
    case 'seeking_cofounder':
      return 'bg-violet-500/10 text-violet-700 dark:text-violet-400 border-violet-500/20';
    case 'seeking_talent':
      return 'bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20';
    case 'seeking_partnership':
      return 'bg-cyan-500/10 text-cyan-700 dark:text-cyan-400 border-cyan-500/20';
    case 'offering_mentorship':
    case 'seeking_advisor':
      return 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20';
    default:
      return 'bg-zinc-500/10 text-zinc-700 dark:text-zinc-300 border-zinc-500/20';
  }
}

export function statusTone(status: PostStatus | string): string {
  switch (status) {
    case 'published':
      return 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20';
    case 'draft':
      return 'bg-zinc-500/10 text-zinc-600 dark:text-zinc-400 border-zinc-500/20';
    case 'closed':
      return 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20';
    default:
      return 'bg-zinc-500/10 text-zinc-500 border-zinc-500/20';
  }
}

/**
 * Render an amount range the way a person would say it.
 *
 * Values arrive as decimal strings from the API. Large figures are abbreviated
 * because a data room raise is quoted in millions and "4 000 000 MAD" costs
 * more width than it earns on a card.
 */
export function formatAmountRange(
  min: string | number | null,
  max: string | number | null,
  currency: string | null,
  language: string,
): string | null {
  const lo = min == null ? null : Number(min);
  const hi = max == null ? null : Number(max);
  const loOk = lo != null && !Number.isNaN(lo);
  const hiOk = hi != null && !Number.isNaN(hi);
  if (!loOk && !hiOk) return null;

  const unit = currency || 'MAD';
  const short = (value: number): string => {
    if (value >= 1_000_000) {
      const m = value / 1_000_000;
      return `${Number.isInteger(m) ? m : m.toFixed(1)}M`;
    }
    if (value >= 1_000) {
      const k = value / 1_000;
      return `${Number.isInteger(k) ? k : k.toFixed(0)}k`;
    }
    return String(value);
  };

  if (loOk && hiOk) {
    return lo === hi ? `${short(lo)} ${unit}` : `${short(lo)}–${short(hi)} ${unit}`;
  }
  const single = (loOk ? lo : hi) as number;
  const prefix = loOk
    ? language === 'en'
      ? 'From'
      : 'À partir de'
    : language === 'en'
      ? 'Up to'
      : "Jusqu'à";
  return `${prefix} ${short(single)} ${unit}`;
}

/** "3 days ago" / "il y a 3 jours", falling back to a date past a week. */
export function relativeTime(value: string | null, language: string): string {
  if (!value) return '';
  const then = new Date(value.endsWith('Z') ? value : `${value}Z`);
  if (Number.isNaN(then.getTime())) return '';
  const seconds = Math.floor((Date.now() - then.getTime()) / 1000);
  const en = language === 'en';

  if (seconds < 60) return en ? 'just now' : "à l'instant";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return en ? `${minutes}m ago` : `il y a ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return en ? `${hours}h ago` : `il y a ${hours} h`;
  const days = Math.floor(hours / 24);
  if (days < 7) return en ? `${days}d ago` : `il y a ${days} j`;
  return then.toLocaleDateString(en ? 'en-GB' : 'fr-FR', {
    day: 'numeric',
    month: 'short',
    year: then.getFullYear() === new Date().getFullYear() ? undefined : 'numeric',
  });
}

/** Days until a deadline; negative when it has passed, null when there is none. */
export function daysUntil(value: string | null): number | null {
  if (!value) return null;
  const then = new Date(value.endsWith('Z') ? value : `${value}Z`);
  if (Number.isNaN(then.getTime())) return null;
  return Math.ceil((then.getTime() - Date.now()) / 86_400_000);
}

/** Initials fallback for an author with no avatar. */
export function initials(name: string | null | undefined): string {
  const parts = (name ?? '').trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return '?';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/** Small labelled chip used across cards and the detail sheet. */
export function Chip({
  icon,
  children,
  className = '',
}: {
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] font-medium ${className}`}
    >
      {icon}
      {children}
    </span>
  );
}
