/**
 * Deal Room API contracts.
 *
 * These mirror `backend/schemas_dealroom.py`. Permissions are resolved on the
 * server and arrive already narrowed for the current viewer, so the UI reads
 * `permission` / `can_download` rather than deriving anything from the role.
 */

/** The seven permission levels, ordered as the backend ranks them. */
export type DealRoomPermission =
  | 'none'
  | 'view'
  | 'view_watermark'
  | 'download'
  | 'download_watermark'
  | 'upload'
  | 'manage';

export type DealRoomStatus = 'draft' | 'active' | 'paused' | 'closed';
export type ViewerRole = 'admin' | 'startup' | 'investor';
export type DocumentStatus = 'draft' | 'published' | 'archived';
export type ParticipantStatus =
  | 'invited'
  | 'requested'
  | 'active'
  | 'suspended'
  | 'revoked'
  | 'rejected';

export const DOCUMENT_CATEGORIES = [
  'company_overview',
  'pitch_deck',
  'business_model',
  'market',
  'traction',
  'financials',
  'legal',
  'team',
  'cap_table',
  'product',
  'other',
] as const;

export type DocumentCategory = (typeof DOCUMENT_CATEGORIES)[number];

/** Human labels per category, in both supported languages. */
export const CATEGORY_LABELS: Record<DocumentCategory, { en: string; fr: string }> = {
  company_overview: { en: 'Company Overview', fr: "Présentation de l'entreprise" },
  pitch_deck: { en: 'Pitch Deck', fr: 'Pitch Deck' },
  business_model: { en: 'Business Model', fr: 'Modèle économique' },
  market: { en: 'Market', fr: 'Marché' },
  traction: { en: 'Traction', fr: 'Traction' },
  financials: { en: 'Financials', fr: 'Données financières' },
  legal: { en: 'Legal', fr: 'Juridique' },
  team: { en: 'Team', fr: 'Équipe' },
  cap_table: { en: 'Cap Table', fr: 'Table de capitalisation' },
  product: { en: 'Product / Technology', fr: 'Produit / Technologie' },
  other: { en: 'Other', fr: 'Autre' },
};

export interface DealRoomSummary {
  id: number;
  startup_id: number;
  startup_name: string | null;
  name: string | null;
  summary: string | null;
  status: DealRoomStatus;
  nda_required: boolean;
  nda_version: string | null;
  watermark_enabled: boolean;
  allow_downloads: boolean;
  default_permission: DealRoomPermission;
  created_at: string | null;
  updated_at: string | null;
  /** Resolved server-side for the caller; never chosen by the client. */
  viewer_role: ViewerRole;
  viewer_permission: DealRoomPermission;
  nda_satisfied: boolean;
}

export interface AuditEvent {
  id: number;
  action: string;
  actor_email: string | null;
  actor_role: string | null;
  resource_type: string | null;
  resource_id: number | null;
  meta: string | null;
  ip: string | null;
  created_at: string | null;
}

export interface DealRoomOverview {
  room: DealRoomSummary;
  investor_count: number;
  active_investor_count: number;
  document_count: number;
  documents_viewed: number;
  documents_never_viewed: number;
  pending_access_requests: number;
  open_questions: number;
  last_activity_at: string | null;
  engagement_score: number;
  recent_activity: AuditEvent[];
}

export interface DealRoomFolder {
  id: number;
  name: string;
  category: DocumentCategory;
  parent_id: number | null;
  position: number;
  document_count: number;
  created_at: string | null;
}

export interface DocumentVersion {
  id: number;
  version_no: number;
  original_filename: string;
  content_type: string;
  byte_size: number;
  page_count: number | null;
  created_at: string | null;
  uploaded_by_member_id: number | null;
}

export interface DealRoomDocument {
  id: number;
  title: string;
  description: string | null;
  category: DocumentCategory;
  status: DocumentStatus;
  folder_id: number | null;
  created_at: string | null;
  updated_at: string | null;
  current_version: DocumentVersion | null;
  version_count: number;
  permission: DealRoomPermission;
  can_download: boolean;
  watermarked: boolean;
  /** Startup-side only; null for investors so reading habits stay private. */
  view_count: number | null;
  last_viewed_at: string | null;
}

export interface PagedDocuments {
  items: DealRoomDocument[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface Participant {
  id: number;
  member_id: number;
  email: string | null;
  full_name: string | null;
  investor_id: number | null;
  status: ParticipantStatus;
  permission: DealRoomPermission;
  expires_at: string | null;
  nda_accepted_at: string | null;
  last_activity_at: string | null;
  created_at: string | null;
  documents_viewed: number;
  downloads: number;
  questions_asked: number;
}

export interface AccessGrant {
  id: number;
  resource_type: 'folder' | 'document';
  resource_id: number;
  permission: DealRoomPermission;
  created_at: string | null;
}

export interface AccessRequest {
  id: number;
  member_id: number;
  email: string | null;
  full_name: string | null;
  message: string | null;
  status: 'pending' | 'approved' | 'rejected' | 'info_requested';
  decision_note: string | null;
  created_at: string | null;
  decided_at: string | null;
}

export interface NdaView {
  required: boolean;
  version: string | null;
  body: string | null;
  accepted: boolean;
  accepted_at: string | null;
}

export interface NdaAcceptance {
  id: number;
  member_id: number;
  email: string | null;
  full_name: string | null;
  nda_version: string;
  signature_name: string | null;
  accepted_at: string | null;
  ip: string | null;
}

export interface QuestionAnswer {
  id: number;
  answer: string;
  answered_by_name: string | null;
  created_at: string | null;
}

export interface Question {
  id: number;
  question: string;
  status: 'open' | 'answered' | 'closed';
  document_id: number | null;
  document_title: string | null;
  asked_by_member_id: number;
  asked_by_name: string | null;
  created_at: string | null;
  answers: QuestionAnswer[];
}

export interface DocumentEngagement {
  document_id: number;
  title: string;
  category: DocumentCategory;
  views: number;
  unique_investors: number;
  downloads: number;
  last_viewed_at: string | null;
}

export interface InvestorEngagement {
  participant_id: number;
  member_id: number;
  full_name: string | null;
  email: string | null;
  status: ParticipantStatus;
  last_activity_at: string | null;
  documents_viewed: number;
  downloads: number;
  questions_asked: number;
  engagement_score: number;
}

export interface TimelinePoint {
  date: string;
  views: number;
  downloads: number;
}

export interface DealRoomAnalytics {
  total_views: number;
  total_downloads: number;
  active_investors: number;
  documents: DocumentEngagement[];
  never_viewed: DocumentEngagement[];
  investors: InvestorEngagement[];
  timeline: TimelinePoint[];
}

export interface PagedAudit {
  items: AuditEvent[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface DocumentLink {
  url: string;
  expires_in: number;
  watermarked: boolean;
  content_type: string;
  filename: string;
}

export interface EntityClaim {
  id: number;
  member_id: number;
  member_email: string | null;
  member_name: string | null;
  entity_type: 'startup' | 'investor' | 'incubator';
  entity_id: number;
  entity_name: string | null;
  entity_role: string;
  status: 'pending' | 'approved' | 'rejected' | 'revoked';
  created_at: string | null;
  approved_at: string | null;
}
