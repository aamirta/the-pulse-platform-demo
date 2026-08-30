/**
 * Deal Room marketplace contracts.
 *
 * These mirror `backend/schemas_dealroom_posts.py`. Vocabularies (post types,
 * counterparties, stages) are *not* hard-coded as unions the client invents —
 * they arrive from `GET /deal-room-posts/meta`, so the server stays the single
 * source of truth for what a valid post looks like. The string literal unions
 * below exist for editor help only; every list the UI renders comes from the API.
 */

export type PostType =
  | 'raising_capital'
  | 'offering_capital'
  | 'seeking_cofounder'
  | 'seeking_advisor'
  | 'seeking_talent'
  | 'seeking_partnership'
  | 'offering_service'
  | 'offering_mentorship';

export type CounterpartyType =
  | 'any'
  | 'investor'
  | 'founder'
  | 'startup'
  | 'expert'
  | 'incubator'
  | 'service_provider'
  | 'talent';

export type PostStatus = 'draft' | 'published' | 'closed' | 'archived';
export type ModerationStatus = 'visible' | 'flagged' | 'removed';
export type ResponseStatus = 'pending' | 'accepted' | 'declined';
export type ReportReason = 'spam' | 'misleading' | 'offensive' | 'scam' | 'off_topic' | 'other';
export type EntityType = 'startup' | 'investor' | 'incubator';

/** The public face of a post's author, addressable by member id. */
export interface PostAuthor {
  member_id: number;
  full_name: string | null;
  role: string | null;
  profile_pic: string | null;
  entity_type: EntityType | null;
  entity_id: number | null;
  entity_name: string | null;
}

/** A post as it appears on the board. */
export interface DealRoomPostListItem {
  id: number;
  post_type: PostType;
  title: string;
  summary: string;
  counterparty_type: CounterpartyType;
  sector: string | null;
  stage: string | null;
  location: string | null;
  /** Decimals arrive as strings from the API; parse before arithmetic. */
  amount_min: string | number | null;
  amount_max: string | number | null;
  currency: string | null;
  commitment: string | null;
  deadline: string | null;
  tags: string[];
  status: PostStatus;
  moderation_status: ModerationStatus;
  view_count: number;
  response_count: number;
  created_at: string | null;
  published_at: string | null;
  author: PostAuthor;
  /** Whether the signed-in caller has already responded. */
  responded_by_me: boolean;
  /** Whether the caller may edit, publish, close or delete this post. */
  can_manage: boolean;
  has_deal_room: boolean;
}

/** A post opened on its own. */
export interface DealRoomPostDetail extends DealRoomPostListItem {
  details: string;
  looking_for: string | null;
  equity_offered: string | null;
  deal_room_id: number | null;
  moderation_note: string | null;
  updated_at: string | null;
  closed_at: string | null;
  /** Only populated for the author or an administrator. */
  open_report_count: number | null;
}

/** The create/edit body. Everything optional except what the composer requires. */
export interface DealRoomPostInput {
  post_type: PostType;
  title: string;
  summary: string;
  details: string;
  looking_for?: string | null;
  counterparty_type?: CounterpartyType;
  sector?: string | null;
  stage?: string | null;
  location?: string | null;
  amount_min?: number | null;
  amount_max?: number | null;
  currency?: string | null;
  equity_offered?: string | null;
  commitment?: string | null;
  deadline?: string | null;
  tags?: string | null;
  entity_type?: EntityType | null;
  entity_id?: number | null;
  deal_room_id?: number | null;
  publish?: boolean;
}

export interface PostResponseItem {
  id: number;
  post_id: number;
  responder: PostAuthor;
  message: string;
  status: ResponseStatus;
  created_at: string | null;
  decided_at: string | null;
}

/** What `POST /{id}/respond` returns: the record plus where the thread landed. */
export interface PostResponseCreated {
  response: PostResponseItem;
  partner_email: string;
  partner_name: string | null;
}

export interface PostReportItem {
  id: number;
  post_id: number;
  post_title: string | null;
  reporter_member_id: number;
  reporter_name: string | null;
  reason: ReportReason;
  detail: string | null;
  status: 'open' | 'actioned' | 'dismissed';
  created_at: string | null;
  reviewed_at: string | null;
}

/** One selectable filter value with its live count. */
export interface PostMetaOption {
  value: string;
  count: number;
}

/** Everything the composer and filter bar render, served by the API. */
export interface PostMeta {
  post_types: PostType[];
  counterparty_types: CounterpartyType[];
  commitment_levels: string[];
  suggested_stages: string[];
  report_reasons: ReportReason[];
  response_statuses: ResponseStatus[];
  sectors: PostMetaOption[];
  stages: PostMetaOption[];
  locations: PostMetaOption[];
  type_counts: PostMetaOption[];
}

/** Board query parameters. Undefined keys are omitted from the request. */
export interface BoardFilters {
  q?: string;
  post_type?: PostType | '';
  counterparty_type?: CounterpartyType | '';
  sector?: string;
  stage?: string;
  location?: string;
  amount_min?: number;
  amount_max?: number;
  has_deal_room?: boolean;
  sort?: 'recent' | 'responses' | 'views' | 'deadline';
  page?: number;
  page_size?: number;
}

/**
 * Whether a directory entity has a member account behind it.
 *
 * Returned by `GET /members/by-entity/{type}/{id}`. Profile pages read this to
 * decide whether to offer a Message button — `contactable: false` means nobody
 * has claimed the entity, not that the request failed.
 */
export interface EntityContact {
  contactable: boolean;
  entity_type: string;
  /** A string because founder ids are: scraped rows are numeric, onboarded ones are tokens. */
  entity_id: string;
  member_id: number | null;
  full_name: string | null;
  role: string | null;
  profile_pic: string | null;
  /** True when the entity is claimed by the viewer themselves. */
  is_self: boolean;
}
