"""Pydantic v2 request/response schemas for The Pulse API.

Schemas are organized by domain and are designed to match the frontend TypeScript
types in ``new_design/src/types/index.ts`` while remaining faithful to the
SQLAlchemy 2.0 models in ``backend/models.py``.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

# ---------------------------------------------------------------------------
# Common / pagination
# ---------------------------------------------------------------------------

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Shared query parameters for paginated list endpoints."""

    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated list wrapper."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str


# ---------------------------------------------------------------------------
# Auth / users
# ---------------------------------------------------------------------------


class Token(BaseModel):
    """Access token response after login."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenResponse(Token):
    """Refreshed token pair.

    The member fields are populated only when a member refresh token was
    exchanged, so the SPA can restore the member profile after a reload.
    """

    member_id: int | None = None
    full_name: str | None = None
    role: str | None = None
    email: str | None = None


class TokenPayload(BaseModel):
    """Decoded access token payload."""

    sub: str | None = None
    type: str | None = None
    exp: int | None = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request body."""

    refresh_token: str


class UserLogin(BaseModel):
    """Username/password login request."""

    username: str
    password: str


class UserPublic(BaseModel):
    """Public user representation."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    username: str
    role: str = "admin"
    is_active: bool = True


class UserMe(UserPublic):
    """Authenticated user profile response."""


class MemberLogin(BaseModel):
    """Pulse member login request (email + password)."""

    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)


class ForgotPasswordRequest(BaseModel):
    """Request a password reset email."""

    email: str = Field(..., max_length=255)


class ResetPasswordRequest(BaseModel):
    """Reset a member password using a token."""

    token: str = Field(..., max_length=100)
    new_password: str = Field(..., min_length=8, max_length=128)


class MemberToken(BaseModel):
    """JWT token response for a pulse member."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    member_id: int
    full_name: str
    role: str


# ---------------------------------------------------------------------------
# Startups
# ---------------------------------------------------------------------------


class StartupListItem(BaseModel):
    """Startup list item matching the frontend ``Startup`` type."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    sector: list[str]
    stage: str = ""
    status: str = ""
    location: str = ""
    description: str = ""
    funding: float | None
    fundingCurrency: str = "USD"
    teamSize: str = ""
    yearFounded: int | None
    logo: str = ""
    website: str | None = None
    linkedin: str | None = None


class StartupDetail(StartupListItem):
    """Extended startup detail response."""

    startup_id: int
    numero_ice: str | None = None
    numero_rc: str | None = None
    forme_juridique: str | None = None
    activite: str | None = None
    region: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    employees: str | None = None
    revenue: str | None = None
    valuation: str | None = None
    raised_funds: float | None = None
    total_funding_usd: float | None = None
    total_funding: float | None = None
    total_funding_currency_code: str | None = None
    incubated_by: str | None = None
    financed_by: str | None = None
    country_code: str | None = None
    address: str | None = None
    facebook_url: str | None = None
    twitter_url: str | None = None
    youtube_link: str | None = None
    instagram_link: str | None = None
    homepage_url: str | None = None

    @field_serializer("raised_funds", "total_funding_usd", "total_funding", "funding")
    def serialize_decimal(self, value: Any | None) -> float | None:
        if value is None:
            return None
        if isinstance(value, Decimal):
            return float(value)
        return float(value) if value else None


class StartupFilter(BaseModel):
    """Query parameters for startup list/filters."""

    sector: str | None = None
    stage: str | None = None
    status: str | None = None
    location: str | None = None
    legal_form: str | None = None
    search: str | None = None
    min_funding: float | None = None
    max_funding: float | None = None
    sort_by: str = "startup_name"
    order: str = "asc"


class StartupExportRequest(BaseModel):
    """Export request for startups."""

    format: str = Field(default="csv", pattern="^(csv|json|xlsx)$")
    filters: StartupFilter | None = None


# ---------------------------------------------------------------------------
# Incubators
# ---------------------------------------------------------------------------


class IncubatorListItem(BaseModel):
    """Incubator list item matching the legacy Incubator directory."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = ""
    type: str = ""
    status: str = ""
    city: str = ""
    investmentPhases: list[str] = []
    image: str = ""
    sectors: list[str] = []
    linkedin: str | None = None


class IncubatorDetail(IncubatorListItem):
    """Extended incubator detail response."""

    incubator_id: int
    description: str | None = None
    email: str | None = None
    telephone: str | None = None
    ville_organisme: str | None = None
    date_creation: str | None = None
    partners_or_sponsors: str | None = None


class IncubatorFilter(BaseModel):
    """Query parameters for incubator list."""

    city: str | None = None
    phase: str | None = None
    type: str | None = None
    search: str | None = None


# ---------------------------------------------------------------------------
# Founders
# ---------------------------------------------------------------------------


class FounderListItem(BaseModel):
    """Founder list item matching the frontend ``Founder`` type."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    role: str = ""
    startup: str = ""
    startupId: str | None = None
    location: str = ""
    bio: str = ""
    avatar: str = ""
    linkedin: str | None = None
    experience: str | None = None
    # "founder" | "cofounder" — derived from how many people founded the same
    # company, never stored. See backend/api/routes/founders.py.
    founder_type: str = "founder"


class FounderDetail(FounderListItem):
    """Extended founder detail response."""

    founder_id: str
    first_name: str | None = None
    last_name: str | None = None
    current_employer: str | None = None
    company_details_name: str | None = None
    skills: str | None = None
    profile_pic: str | None = None
    link_twitter: str | None = None
    link_facebook: str | None = None
    link_instagram: str | None = None
    link_github: str | None = None
    link_aboutme: str | None = None
    link_angellist: str | None = None
    link_stackoverflow: str | None = None


class FounderFilter(BaseModel):
    """Query parameters for founder list."""

    startup: str | None = None
    location: str | None = None
    search: str | None = None


# ---------------------------------------------------------------------------
# Investors
# ---------------------------------------------------------------------------


class InvestorListItem(BaseModel):
    """Investor list item matching the frontend ``Investor`` type."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: str = ""
    location: str = ""
    focus: list[str]
    portfolio: float | None
    investments: float | None
    logo: str = ""
    website: str | None = None


class InvestorDetail(InvestorListItem):
    """Extended investor detail response."""

    investor_id: int
    investor_status: str | None = None
    hq_email: str | None = None
    hq_phone: str | None = None
    primary_investor_type: str | None = None
    description: str | None = None
    preferred_industry: str | None = None
    preferred_geography: str | None = None
    preferred_investment_types: str | None = None
    preferred_verticals: str | None = None
    total_active_portfolio: float | None = None
    total_investments: float | None = None
    aum: float | None = None
    dry_powder: float | None = None
    linkedin_url: str | None = None
    facebook_url: str | None = None
    twitter_url: str | None = None

    @field_serializer(
        "portfolio",
        "investments",
        "total_active_portfolio",
        "total_investments",
        "aum",
        "dry_powder",
    )
    def serialize_decimal(self, value: Any | None) -> float | None:
        if value is None:
            return None
        if isinstance(value, Decimal):
            return float(value)
        return float(value) if value else None


class InvestorFilter(BaseModel):
    """Query parameters for investor list."""

    type: str | None = None
    location: str | None = None
    focus: str | None = None
    search: str | None = None


# ---------------------------------------------------------------------------
# Funding rounds
# ---------------------------------------------------------------------------


class FundingRoundListItem(BaseModel):
    """Funding round list item matching the frontend ``FundingRound`` type."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    startup: str = ""
    startupLogo: str = ""
    amount: str = ""
    round: str = ""
    investor: str = ""
    date: str = ""


class FundingRoundDetail(FundingRoundListItem):
    """Extended funding round detail response."""

    funding_round_id: int
    deal_id: str | None = None
    deal_type: str | None = None
    deal_type2: str | None = None
    deal_status: str | None = None
    raised_amount: float | None = None
    raised_amount_usd: float | None = None
    total_funding_usd: float | None = None
    native_currency_of_deal: str | None = None
    overview: str | None = None
    lead_investor: str | None = None
    institutional_investors: str | None = None
    angel_investors: str | None = None
    ceo: str | None = None
    city: str | None = None
    country: str | None = None
    region: str | None = None
    startup_id: int | None = None

    @field_serializer("raised_amount", "raised_amount_usd", "total_funding_usd")
    def serialize_decimal(self, value: Any | None) -> float | None:
        if value is None:
            return None
        if isinstance(value, Decimal):
            return float(value)
        return float(value) if value else None


class FundingRoundFilter(BaseModel):
    """Query parameters for funding round list."""

    startup: str | None = None
    round: str | None = None
    year: str | None = None
    investor: str | None = None
    search: str | None = None


# ---------------------------------------------------------------------------
# Articles / News
# ---------------------------------------------------------------------------


class NewsItem(BaseModel):
    """News item matching the frontend ``NewsItem`` type."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str = "news"
    title: str
    description: str = ""
    source: str = ""
    sourceAvatar: str = "/avatars/pulse.jpg"
    # Pre-rendered relative date. Kept for compatibility, but it is French-only;
    # clients should prefer ``publishedAt`` and format it in the active locale.
    date: str = ""
    #: ISO 8601 timestamp so the SPA can format dates per language.
    publishedAt: datetime | None = None
    image: str = ""
    tags: list[str] = []
    amount: str | None = None
    round: str | None = None
    eventDate: str | None = None


class ArticleDetail(BaseModel):
    """Full article detail response."""

    model_config = ConfigDict(from_attributes=True)

    article_id: int
    title: str
    content: str | None = None
    summary: str | None = None
    category: str | None = None
    source: str | None = None
    source_url: str | None = None
    author: str | None = None
    image_url: str | None = None
    tags: str | None = None
    is_featured: bool | None = False
    published_at: datetime | None = None
    created_at: datetime | None = None


class ArticleCreate(BaseModel):
    """Article creation request (admin only)."""

    title: str = Field(..., min_length=1, max_length=500)
    content: str | None = None
    summary: str | None = None
    category: str | None = "news"
    source: str | None = None
    source_url: str | None = None
    author: str | None = None
    image_url: str | None = None
    tags: str | None = None
    is_featured: bool = False


class ArticleFilter(BaseModel):
    """Query parameters for article/news list."""

    category: str | None = None
    search: str | None = None
    is_featured: bool | None = None


# ---------------------------------------------------------------------------
# Events / Opportunities (derived from frontend types and resources)
# ---------------------------------------------------------------------------


class EventItem(BaseModel):
    """Event item matching the frontend ``Event`` type."""

    id: str
    title: str
    description: str = ""
    location: str = ""
    startDate: str = ""
    endDate: str | None = None
    organizer: str = ""
    image: str = ""
    attendees: int | None = None


class OpportunityItem(BaseModel):
    """Opportunity item matching the frontend ``Opportunity`` type."""

    id: str
    title: str
    organization: str = ""
    deadline: str = ""
    category: str = ""
    description: str = ""


class TrendItem(BaseModel):
    """Trend item matching the frontend ``Trend`` type."""

    tag: str
    count: int


class EcosystemStatItem(BaseModel):
    """Ecosystem stat item matching the frontend ``EcosystemStat`` type."""

    label: str
    value: str
    icon: str


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


class HomeStats(BaseModel):
    """Home page statistics response."""

    startups: int
    founders: int
    investors: int
    incubators: int
    totalFunding: str
    opportunities: int
    sectors: int
    cities: int
    fundingRounds: int


class ChartSeries(BaseModel):
    """Generic chart series data."""

    labels: list[str]
    values: list[Any]


class StatsResponse(BaseModel):
    """Aggregated stats and charts response."""

    counts: HomeStats
    trends: list[TrendItem]
    fundingByStage: ChartSeries
    fundingByYear: ChartSeries
    topSectors: ChartSeries
    topFundedStartups: ChartSeries | None = None
    fundingBySector: ChartSeries | None = None


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


class PasswordChangeRequest(BaseModel):
    """Change the authenticated account's own password.

    The current password is required so a stolen access token alone cannot lock
    the legitimate owner out.
    """

    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=12, max_length=128)


class StartupWrite(BaseModel):
    """Admin create/update payload for a startup.

    Every field is optional so the same model serves PATCH-style updates; the
    create endpoint enforces that a name is present.
    """

    startup_name: str | None = Field(None, max_length=255)
    sector: str | None = None
    stage: str | None = Field(None, max_length=100)
    status: str | None = Field(None, max_length=100)
    location: str | None = Field(None, max_length=255)
    description: str | None = None
    contact_email: str | None = Field(None, max_length=255)
    homepage_url: str | None = Field(None, max_length=500)
    linkedin: str | None = Field(None, max_length=500)
    logo_url: str | None = None


class FounderWrite(BaseModel):
    """Admin create/update payload for a founder."""

    name: str | None = Field(None, max_length=255)
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    current_title: str | None = Field(None, max_length=255)
    current_employer: str | None = Field(None, max_length=255)
    location: str | None = Field(None, max_length=255)
    linkedin_url: str | None = Field(None, max_length=500)
    profile_pic: str | None = None
    skills: str | None = None


class InvestorWrite(BaseModel):
    """Admin create/update payload for an investor."""

    investor_name: str | None = Field(None, max_length=255)
    primary_investor_type: str | None = Field(None, max_length=100)
    hq_location: str | None = Field(None, max_length=255)
    hq_email: str | None = Field(None, max_length=255)
    description: str | None = None
    preferred_industry: str | None = None
    domain: str | None = Field(None, max_length=255)
    linkedin_url: str | None = Field(None, max_length=500)
    logo_url: str | None = None


class IncubatorWrite(BaseModel):
    """Admin create/update payload for an incubator or programme."""

    incubator: str | None = Field(None, max_length=255)
    type_organisme: str | None = Field(None, max_length=100)
    statut: str | None = Field(None, max_length=100)
    ville_organisme: str | None = Field(None, max_length=255)
    secteurs: str | None = None
    description: str | None = None
    email: str | None = Field(None, max_length=255)
    linkedin: str | None = Field(None, max_length=500)
    image_url: str | None = None


class FundingRoundWrite(BaseModel):
    """Admin create/update payload for a funding round."""

    startup_name: str | None = Field(None, max_length=255)
    startup_id: int | None = None
    round_name: str | None = Field(None, max_length=255)
    raised_amount_usd: float | None = None
    date: str | None = Field(None, max_length=50)
    lead_investor: str | None = None
    deal_type: str | None = Field(None, max_length=100)


class ResourceApplicationCreate(BaseModel):
    """Register for an event or apply to an opportunity."""

    message: str | None = Field(None, max_length=5000)


class ResourceApplicationResponse(BaseModel):
    """A stored registration or application."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    resource_id: int
    member_id: int
    kind: str
    message: str | None = None
    status: str
    created_at: datetime | None = None


class ResourceApplicationItem(ResourceApplicationResponse):
    """A stored submission enriched with the resource it points at."""

    resource_title: str | None = None
    resource_category: str | None = None


class AssistantQuery(BaseModel):
    """A natural-language question answered from the platform's own data."""

    question: str = Field(..., min_length=1, max_length=500)


class AssistantAnswer(BaseModel):
    """An answer derived from live database aggregates.

    ``sources`` names the tables the figures came from so the response can be
    audited; nothing here is generated text with invented numbers.
    """

    answer: str
    intent: str
    data: list[TrendItem] = []
    sources: list[str] = []


class DashboardStat(BaseModel):
    """A single headline figure on the dashboard."""

    key: str
    label: str
    value: str
    hint: str | None = None


class DashboardModerationItem(BaseModel):
    """A member awaiting administrator confirmation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    role: str
    created_at: datetime | None = None


class DashboardResponse(BaseModel):
    """Role-scoped dashboard payload.

    ``role`` is resolved from the authenticated identity on the server;
    ``moderation_queue`` is only ever populated for administrators.
    """

    role: str
    stats: list[DashboardStat]
    funding_by_year: ChartSeries
    moderation_queue: list[DashboardModerationItem] = []
    recent_posts: list["PostItem"] = []


class SearchResult(BaseModel):
    """Single global search result."""

    id: str
    type: str
    title: str
    subtitle: str = ""
    url: str = ""


class SearchResponse(BaseModel):
    """Global search response."""

    query: str
    results: list[SearchResult]
    total: int


class RoleBasedSearchResponse(BaseModel):
    """Role-based search response (e.g., startups, founders, investors)."""

    query: str
    role: str
    results: list[SearchResult]
    total: int


# ---------------------------------------------------------------------------
# Pulse members / community
# ---------------------------------------------------------------------------


class PulseMemberListItem(BaseModel):
    """Pulse member list item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: str
    is_confirmed: bool | None = False
    profile_pic: str | None = None
    linkedin: str | None = None
    created_at: datetime | None = None


class PulseMemberPublicItem(BaseModel):
    """Publicly safe view of a member — never includes contact details.

    Used by any endpoint reachable without an admin token so the community
    directory cannot be scraped for email addresses.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    role: str
    profile_pic: str | None = None
    linkedin: str | None = None
    created_at: datetime | None = None


class PulseMemberDetail(PulseMemberListItem):
    """Pulse member detail response (owner or admin only).

    ``confirmation_token`` is deliberately not exposed: it is a bearer secret
    that confirms the account, so it stays server-side.
    """

    form_data: str | None = None


class PulseMemberCreate(BaseModel):
    """Pulse member creation request."""

    email: str = Field(..., max_length=255)
    full_name: str = Field(..., min_length=1, max_length=150)
    role: str = Field(..., max_length=50)
    profile_pic: str | None = None
    linkedin: str | None = None
    form_data: str | None = None


class MemberOnboardRequest(BaseModel):
    """Member onboarding registration with password and role-specific form data."""

    email: str = Field(..., max_length=255)
    full_name: str = Field(..., min_length=1, max_length=150)
    role: str = Field(..., max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    profile_pic: str | None = None
    linkedin: str | None = None
    form_data: dict[str, Any] | None = None


class MemberOnboardResponse(BaseModel):
    """Response after onboarding registration."""

    message: str
    member_id: int
    confirmation_token: str | None = None
    confirmation_url: str | None = None


class PulseMemberUpdate(BaseModel):
    """Fields a member may change on their own profile.

    ``email``, ``role`` and ``is_confirmed`` are intentionally absent. Email
    scopes direct-message access, role drives authorisation, and is_confirmed
    gates login — allowing self-service edits to any of them would let a member
    escalate privileges or take over another member's inbox. Administrators
    change those through :class:`AdminMemberUpdate`.
    """

    full_name: str | None = Field(None, max_length=150)
    profile_pic: str | None = None
    linkedin: str | None = None
    form_data: str | None = None


class PulseMemberFilter(BaseModel):
    """Query parameters for pulse member list."""

    role: str | None = None
    is_confirmed: bool | None = None
    search: str | None = None


class BadgeGenerateRequest(BaseModel):
    """Badge generation request."""

    full_name: str
    category: str
    role_label: str
    ref_url: str | None = None


class BadgeGenerationResponse(BaseModel):
    """Badge generation audit response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int | None = None
    full_name: str | None = None
    category: str | None = None
    role_label: str | None = None
    ref_url: str | None = None
    created_at: datetime | None = None


# A single ceiling for every inbox write. ``min_length=1`` alone lets a body of
# spaces through, which the handlers then ``.strip()`` into an empty row, so the
# bound and the emptiness check are defined together and reused by both schemas.
MAX_MESSAGE_LENGTH = 5000


def _validated_message_body(value: str) -> str:
    """Return a trimmed message body, refusing one that is only whitespace."""
    trimmed = value.strip()
    if not trimmed:
        raise ValueError("Message cannot be empty")
    return trimmed


class DirectMessageCreate(BaseModel):
    """Direct message creation request."""

    post_id: int | None = None
    to_name: str | None = Field(None, max_length=100)
    to_email: str = Field(..., max_length=255)
    from_name: str | None = Field(None, max_length=100)
    from_email: str | None = Field(None, max_length=255)
    message: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH)

    _check_message = field_validator("message")(_validated_message_body)


class DirectMessageResponse(BaseModel):
    """Direct message response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int | None = None
    to_name: str | None = None
    to_email: str | None = None
    from_name: str | None = None
    from_email: str | None = None
    message: str
    is_read: bool = False
    created_at: datetime | None = None


class ConversationPartner(BaseModel):
    """Summary of a conversation partner for the inbox.

    Carries the avatar and profile ids the Flask inbox resolved, so the rebuilt
    UI can show who it is talking to and link through to their profile.
    """

    email: str
    name: str | None = None
    unread_count: int = 0
    last_message_at: datetime | None = None
    last_message_preview: str | None = None
    profile_pic: str | None = None
    member_id: int | None = None
    expert_id: int | None = None
    role: str | None = None
    message_count: int = 0


class StartConversationRequest(BaseModel):
    """Open a conversation with a member identified by id rather than address."""

    message: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH)

    _check_message = field_validator("message")(_validated_message_body)


class EntityContact(BaseModel):
    """Whether a directory entity has a member account that can be messaged.

    Profile pages are rendered from the directory tables (``Startups``,
    ``Investors``, ``Incubators``), which hold no account. Before a page can
    offer a Message button it has to know whether anyone actually holds the
    entity, and which member id to address — this is that answer.

    ``contactable`` is false rather than 404 when nobody claims the entity, so
    the profile renders a disabled control with an explanation instead of the
    page failing to load.
    """

    model_config = ConfigDict(from_attributes=True)

    contactable: bool
    entity_type: str
    # A string because founder ids are: scraped rows carry a number, onboarded
    # ones a random token. Startup/investor/incubator ids are numeric, and are
    # returned in their string form so one response shape covers every profile.
    entity_id: str
    member_id: int | None = None
    full_name: str | None = None
    role: str | None = None
    profile_pic: str | None = None
    # True when the entity is claimed by the caller themselves, so the client
    # can say "this is you" instead of offering a message-yourself button.
    is_self: bool = False


class StartConversationResponse(BaseModel):
    """The created message plus the thread key the inbox needs to open it."""

    partner_email: str
    partner_name: str | None = None
    message: DirectMessageResponse


class MessageSearchHit(BaseModel):
    """One message matched by an inbox search, with just enough partner context.

    Deliberately not the full message row: a search result needs to identify the
    thread it belongs to, not re-expose every column of the record.
    """

    id: int
    partner_email: str
    partner_name: str | None = None
    partner_pic: str | None = None
    outgoing: bool
    message: str
    is_read: bool = False
    created_at: datetime | None = None


class ConversationReply(BaseModel):
    """Reply body for a conversation thread."""

    message: str = Field(..., min_length=1, max_length=MAX_MESSAGE_LENGTH)

    _check_message = field_validator("message")(_validated_message_body)


class ConversationThreadResponse(BaseModel):
    """A page of messages between the current actor and a partner.

    Paginated because the Flask original loaded every message ever exchanged;
    the newest page is returned first and older messages are fetched on demand.
    """

    partner_email: str
    messages: list[DirectMessageResponse]
    total: int
    page: int = 1
    page_size: int = 50
    pages: int = 1
    partner: ConversationPartner | None = None


class PostItem(BaseModel):
    """Community newsfeed post item."""

    model_config = ConfigDict(from_attributes=True)

    post_id: int
    author_name: str | None = None
    author_role: str | None = None
    content: str
    post_type: str | None = None
    image_url: str | None = None
    link_url: str | None = None
    link_title: str | None = None
    tags: str | None = None
    likes_count: int = 0
    comments_count: int = 0
    is_published: bool | None = True
    created_at: datetime | None = None
    author_pic: str | None = None
    author_founder_id: str | None = None
    # Whether the *caller* has already liked this post. Resolved server-side so
    # the list can render the correct heart on first paint; the full ``likes``
    # array is only ever returned by the single-post endpoint.
    liked_by_me: bool = False


class PostCreate(BaseModel):
    """Newsfeed post creation request."""

    author_name: str | None = Field(None, max_length=100)
    author_role: str | None = Field(None, max_length=100)
    content: str = Field(..., min_length=1)
    post_type: str | None = "post"
    image_url: str | None = None
    link_url: str | None = None
    link_title: str | None = Field(None, max_length=255)
    tags: str | None = None


class PostCommentItem(BaseModel):
    """Newsfeed comment item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_type: str
    actor_id: int
    content: str
    created_at: datetime | None = None


class PostLikeItem(BaseModel):
    """Newsfeed like item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_type: str
    actor_id: int
    created_at: datetime | None = None


class PostDetail(PostItem):
    """Newsfeed post with likes and comments."""

    likes: list[PostLikeItem] = []
    comments: list[PostCommentItem] = []


class PostCommentCreate(BaseModel):
    """Newsfeed comment creation request."""

    content: str = Field(..., min_length=1, max_length=5000)


# ---------------------------------------------------------------------------
# Resources / opportunities
# ---------------------------------------------------------------------------


class ResourceListItem(BaseModel):
    """Resource list item."""

    model_config = ConfigDict(from_attributes=True)

    resource_id: int
    title: str
    description: str | None = None
    category: str | None = None
    resource_type: str | None = None
    url: str | None = None
    organization: str | None = None
    tags: str | None = None
    is_featured: bool | None = False
    published_at: datetime | None = None


class ResourceDetail(ResourceListItem):
    """Resource detail response."""

    created_at: datetime | None = None


class ResourceCreate(BaseModel):
    """Resource creation request (admin only)."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    category: str | None = None
    resource_type: str | None = None
    url: str | None = None
    organization: str | None = None
    tags: str | None = None
    is_featured: bool = False


class ResourceFilter(BaseModel):
    """Query parameters for resource list."""

    category: str | None = None
    resource_type: str | None = None
    search: str | None = None
    is_featured: bool | None = None


# ---------------------------------------------------------------------------
# Maps / visualizer
# ---------------------------------------------------------------------------


class MapPoint(BaseModel):
    """Single point on the ecosystem map."""

    id: str
    type: str
    name: str
    latitude: float | None = None
    longitude: float | None = None
    city: str = ""
    country: str = ""
    count: int = 1


class MapDataResponse(BaseModel):
    """Map / visualizer data response."""

    points: list[MapPoint]
    total: int


class CityAggregation(BaseModel):
    """City-level aggregation for the map visualizer."""

    city: str
    country: str
    startups: int
    founders: int
    investors: int


# ---------------------------------------------------------------------------
# Admin / bulk actions
# ---------------------------------------------------------------------------


class BulkActionRequest(BaseModel):
    """Bulk action request on a list of IDs."""

    ids: list[int]
    action: str = Field(..., pattern="^(confirm|delete|activate|deactivate|export)$")


class BulkActionResponse(BaseModel):
    """Bulk action response."""

    action: str
    processed: int
    message: str


class AdminMemberUpdate(BaseModel):
    """Admin-only member update."""

    email: str | None = None
    full_name: str | None = None
    role: str | None = None
    is_confirmed: bool | None = None
    profile_pic: str | None = None
    linkedin: str | None = None
    form_data: str | None = None


# ---------------------------------------------------------------------------
# Ecosystem relationship graph
# ---------------------------------------------------------------------------


class GraphNode(BaseModel):
    """A single entity in the ecosystem relationship graph."""

    id: str
    refId: str
    name: str
    type: str
    sector: str | None = None
    location: str | None = None
    connections: int = 0


class GraphLink(BaseModel):
    """A verified relationship between two entities in the graph."""

    source: str
    target: str
    type: str


class GraphTotals(BaseModel):
    """Full-ecosystem relationship counts, before any display limiting."""

    startups: int
    founders: int
    investors: int
    incubators: int
    founded: int
    invested: int
    incubated: int
    supported: int = 0


class EcosystemGraph(BaseModel):
    """Ecosystem relationship graph derived entirely from persisted records."""

    nodes: list[GraphNode]
    links: list[GraphLink]
    totals: GraphTotals
    truncated: bool = False


class ExpertListItem(BaseModel):
    """Ecosystem expert / mentor list item."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    title: str | None = None
    organization: str | None = None
    location: str | None = None
    expertiseDomain: str | None = None
    yearsExperience: str | None = None
    skills: list[str] = []
    availability: str | None = None
    linkedin: str | None = None
    profilePic: str | None = None


class ExpertDetail(ExpertListItem):
    """Ecosystem expert / mentor detail response."""

    professionalBio: str | None = None
    servicesOffered: str | None = None
    industriesOfInterest: list[str] = []
    achievements: str | None = None
    languages: str | None = None
    portfolioWebsite: str | None = None
    email: str | None = None
    createdAt: datetime | None = None


class CofounderProjectListItem(BaseModel):
    """Co-founder search posting list item."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    domain: str | None = None
    stage: str | None = None
    description: str | None = None
    rolesNeeded: list[str] = []
    skillsNeeded: list[str] = []
    authorName: str | None = None
    authorAffiliation: str | None = None
    authorLinkedin: str | None = None
    commitmentType: str | None = None
    locationPreference: str | None = None
    equityOffered: str | None = None


class CofounderProjectDetail(CofounderProjectListItem):
    """Co-founder search posting detail response."""

    contactInfo: str | None = None
    createdAt: datetime | None = None
