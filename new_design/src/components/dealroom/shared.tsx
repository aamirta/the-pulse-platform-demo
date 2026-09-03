import type { ReactNode } from 'react';
import { Download, Eye, EyeOff, Lock, PenLine, Settings2, ShieldCheck } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import type { DealRoomPermission, DocumentCategory } from '@/types/dealroom';
import { CATEGORY_LABELS } from '@/types/dealroom';

/** Card shell shared by every Deal Room panel, matching the dashboard cards. */
export function Panel({
  title,
  action,
  children,
  className = '',
}: {
  title?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 ${className}`}
    >
      {(title || action) && (
        <header className="flex items-center justify-between gap-3 px-4 py-3 border-b border-zinc-100 dark:border-zinc-800">
          {title && (
            <h2 className="text-sm font-semibold text-zinc-900 dark:text-white">{title}</h2>
          )}
          {action}
        </header>
      )}
      {children}
    </section>
  );
}

/** Headline number card, mirroring the dashboard's stat treatment. */
export function StatCard({
  label,
  value,
  hint,
  icon: Icon,
  tone = 'default',
}: {
  label: string;
  value: string | number;
  hint?: string;
  icon?: React.ComponentType<{ className?: string }>;
  tone?: 'default' | 'warning' | 'success';
}) {
  const toneClass =
    tone === 'warning'
      ? 'text-amber-600 dark:text-amber-400'
      : tone === 'success'
        ? 'text-emerald-700 dark:text-emerald-400'
        : 'text-zinc-900 dark:text-white';
  return (
    <div className="bg-white dark:bg-zinc-900 p-5 rounded-xl border border-zinc-100 dark:border-zinc-800 flex items-center justify-between gap-3 ve-card-lift">
      <div className="min-w-0">
        <span className="text-xs text-zinc-600 dark:text-zinc-300 block mb-1">{label}</span>
        <span className={`text-2xl font-bold ${toneClass}`}>{value}</span>
        {hint && (
          <span className="text-[11px] text-zinc-600 dark:text-zinc-300 block mt-0.5 truncate">
            {hint}
          </span>
        )}
      </div>
      {Icon && <Icon className="w-5 h-5 text-zinc-300 dark:text-zinc-600 flex-shrink-0" />}
    </div>
  );
}

/** Consistent empty state: says what is missing and what to do about it. */
export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="px-6 py-12 text-center">
      <Icon className="w-8 h-8 text-zinc-200 dark:text-zinc-700 mx-auto mb-3 ve-float" />
      <p className="text-sm font-medium text-zinc-700 dark:text-zinc-200">{title}</p>
      {description && (
        <p className="text-xs text-zinc-600 dark:text-zinc-300 mt-1 max-w-sm mx-auto leading-relaxed">
          {description}
        </p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

/** Row skeletons that mirror the real list, so layout does not jump on load. */
export function RowSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="p-4 space-y-3">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="flex items-center gap-3 animate-pulse">
          <div className="w-9 h-9 rounded-lg bg-zinc-100 dark:bg-zinc-800" />
          <div className="flex-1 space-y-2">
            <div className="h-3 w-1/3 bg-zinc-100 dark:bg-zinc-800 rounded" />
            <div className="h-2 w-1/4 bg-zinc-100 dark:bg-zinc-800 rounded" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function ErrorState({ message, onRetry, retryLabel }: { message: string; onRetry?: () => void; retryLabel: string }) {
  return (
    <div className="px-6 py-10 text-center">
      <p className="text-sm text-zinc-700 dark:text-zinc-300 mb-3">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="text-xs font-medium text-pulse-orange hover:underline"
        >
          {retryLabel}
        </button>
      )}
    </div>
  );
}

const PERMISSION_META: Record<
  DealRoomPermission,
  { en: string; fr: string; icon: React.ComponentType<{ className?: string }> }
> = {
  none: { en: 'No access', fr: 'Aucun accès', icon: Lock },
  view: { en: 'View', fr: 'Consulter', icon: Eye },
  view_watermark: { en: 'View + watermark', fr: 'Consulter + filigrane', icon: ShieldCheck },
  download: { en: 'Download', fr: 'Télécharger', icon: Download },
  download_watermark: {
    en: 'Download + watermark',
    fr: 'Télécharger + filigrane',
    icon: ShieldCheck,
  },
  upload: { en: 'Upload', fr: 'Téléverser', icon: PenLine },
  manage: { en: 'Manage', fr: 'Gérer', icon: Settings2 },
};

/** Renders a permission level as a labelled chip. */
export function PermissionBadge({
  permission,
  language,
  className = '',
}: {
  permission: DealRoomPermission;
  language: string;
  className?: string;
}) {
  const meta = PERMISSION_META[permission] ?? PERMISSION_META.none;
  const Icon = meta.icon;
  const muted = permission === 'none';
  return (
    <Badge
      variant="secondary"
      className={`text-[11px] font-medium gap-1 ${
        muted ? 'text-zinc-500 dark:text-zinc-400' : 'text-zinc-600 dark:text-zinc-300'
      } ${className}`}
    >
      <Icon className="w-2.5 h-2.5" />
      {language === 'en' ? meta.en : meta.fr}
    </Badge>
  );
}

export function permissionLabel(permission: DealRoomPermission, language: string): string {
  const meta = PERMISSION_META[permission] ?? PERMISSION_META.none;
  return language === 'en' ? meta.en : meta.fr;
}

export function categoryLabel(category: DocumentCategory, language: string): string {
  const meta = CATEGORY_LABELS[category] ?? CATEGORY_LABELS.other;
  return language === 'en' ? meta.en : meta.fr;
}

/** Status chip for rooms, documents and participants. */
export function StatusPill({ status, language }: { status: string; language: string }) {
  const labels: Record<string, { en: string; fr: string; className: string }> = {
    draft: { en: 'Draft', fr: 'Brouillon', className: 'bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300' },
    active: { en: 'Active', fr: 'Actif', className: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400' },
    paused: { en: 'Paused', fr: 'En pause', className: 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-400' },
    closed: { en: 'Closed', fr: 'Fermé', className: 'bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400' },
    published: { en: 'Published', fr: 'Publié', className: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400' },
    archived: { en: 'Archived', fr: 'Archivé', className: 'bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400' },
    invited: { en: 'Invited', fr: 'Invité', className: 'bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-400' },
    suspended: { en: 'Suspended', fr: 'Suspendu', className: 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-400' },
    revoked: { en: 'Revoked', fr: 'Révoqué', className: 'bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-400' },
    rejected: { en: 'Rejected', fr: 'Refusé', className: 'bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-400' },
    pending: { en: 'Pending', fr: 'En attente', className: 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-400' },
    approved: { en: 'Approved', fr: 'Approuvé', className: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400' },
    info_requested: { en: 'Info requested', fr: 'Infos demandées', className: 'bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-400' },
    open: { en: 'Open', fr: 'Ouverte', className: 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-400' },
    answered: { en: 'Answered', fr: 'Répondue', className: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400' },
  };
  const meta = labels[status] ?? {
    en: status,
    fr: status,
    className: 'bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold ${meta.className}`}>
      {language === 'en' ? meta.en : meta.fr}
    </span>
  );
}

/** Human file size. */
export function formatBytes(bytes: number): string {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** exponent).toFixed(exponent === 0 ? 0 : 1)} ${units[exponent]}`;
}

/** Short absolute date; deal rooms are audited, so exact dates beat "2 days ago". */
export function formatDate(value: string | null, language: string): string {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleDateString(language === 'en' ? 'en-GB' : 'fr-FR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

export function formatDateTime(value: string | null, language: string): string {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleString(language === 'en' ? 'en-GB' : 'fr-FR', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Human labels for the audit actions defined in `backend/services/dealroom.py`.
 *
 * The identifiers stay verbatim in the CSV export, where they are a stable
 * contract, but a deal room is shown to founders and investors rather than to
 * engineers — leaving `deal_room.opened` on screen reads as unfinished software.
 */
const AUDIT_ACTION_LABELS: Record<string, { en: string; fr: string }> = {
  'deal_room.opened': { en: 'Opened the room', fr: 'A ouvert la room' },
  'deal_room.created': { en: 'Created the room', fr: 'A créé la room' },
  'deal_room.updated': { en: 'Updated room settings', fr: 'A modifié les paramètres' },
  'document.uploaded': { en: 'Uploaded a document', fr: 'A ajouté un document' },
  'document.replaced': { en: 'Replaced a document', fr: 'A remplacé un document' },
  'document.previewed': { en: 'Previewed a document', fr: 'A consulté un document' },
  'document.downloaded': { en: 'Downloaded a document', fr: 'A téléchargé un document' },
  'document.deleted': { en: 'Deleted a document', fr: 'A supprimé un document' },
  'document.updated': { en: 'Updated a document', fr: 'A modifié un document' },
  'folder.created': { en: 'Created a folder', fr: 'A créé un dossier' },
  'folder.updated': { en: 'Renamed a folder', fr: 'A renommé un dossier' },
  'folder.deleted': { en: 'Deleted a folder', fr: 'A supprimé un dossier' },
  'permission.changed': { en: 'Changed permissions', fr: 'A modifié les permissions' },
  'investor.invited': { en: 'Invited an investor', fr: 'A invité un investisseur' },
  'investor.approved': { en: 'Approved an investor', fr: 'A approuvé un investisseur' },
  'investor.rejected': { en: 'Rejected a request', fr: 'A refusé une demande' },
  'investor.suspended': { en: 'Suspended an investor', fr: 'A suspendu un investisseur' },
  'investor.restored': { en: 'Restored an investor', fr: 'A réactivé un investisseur' },
  'access.revoked': { en: 'Revoked access', fr: "A révoqué l'accès" },
  'access.requested': { en: 'Requested access', fr: "A demandé l'accès" },
  'access.denied': { en: 'Access denied', fr: 'Accès refusé' },
  'nda.accepted': { en: 'Signed the NDA', fr: 'A signé le NDA' },
  'question.created': { en: 'Asked a question', fr: 'A posé une question' },
  'answer.created': { en: 'Answered a question', fr: 'A répondu à une question' },
};

/** Return a readable label for an audit action, falling back to the raw code. */
export function auditActionLabel(action: string, language: string): string {
  const entry = AUDIT_ACTION_LABELS[action];
  if (!entry) {
    // An action added on the server but not yet translated should still read as
    // words rather than as a dotted identifier.
    return action.replace(/[._]/g, ' ').replace(/^./, (c) => c.toUpperCase());
  }
  return language === 'en' ? entry.en : entry.fr;
}

/** Tone for an audit row: denials and revocations have to stand out from noise. */
export function auditActionTone(action: string): 'danger' | 'warning' | 'default' {
  if (action === 'access.denied') return 'danger';
  if (action === 'access.revoked' || action.includes('rejected') || action.includes('suspended')) {
    return 'warning';
  }
  return 'default';
}

export { EyeOff };
