"""Pydantic schemas for the Deal Room API.

Kept in their own module because ``backend/schemas.py`` already carries the whole
public directory surface; the deal room is a self-contained bounded context.

Request models deliberately omit every field a client must not choose: there is
no ``startup_id`` on a create body, no ``member_id`` on a question, and no
``from_email`` anywhere. Those are taken from the authenticated identity.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.core.permissions import DEAL_ROOM_CATEGORIES

_INVESTOR_PERMISSIONS = ("none", "view", "view_watermark", "download", "download_watermark")


def _check(value: str, allowed: tuple[str, ...], label: str) -> str:
    if value not in allowed:
        raise ValueError(f"{label} must be one of: {', '.join(allowed)}")
    return value


# ---------------------------------------------------------------------------
# Deal room
# ---------------------------------------------------------------------------
class DealRoomSettingsUpdate(BaseModel):
    """Fields the owning startup or an administrator may change on a room."""

    name: str | None = Field(None, max_length=200)
    summary: str | None = Field(None, max_length=4000)
    status: str | None = None
    nda_required: bool | None = None
    nda_version: str | None = Field(None, max_length=40)
    nda_body: str | None = Field(None, max_length=40000)
    watermark_enabled: bool | None = None
    default_permission: str | None = None
    allow_downloads: bool | None = None

    @field_validator("status")
    @classmethod
    def _status(cls, v: str | None) -> str | None:
        return v if v is None else _check(v, ("draft", "active", "paused", "closed"), "status")

    @field_validator("default_permission")
    @classmethod
    def _permission(cls, v: str | None) -> str | None:
        return v if v is None else _check(v, _INVESTOR_PERMISSIONS, "default_permission")


class DealRoomSummary(BaseModel):
    """The room header shown to any actor who may see the room at all."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    startup_id: int
    startup_name: str | None = None
    name: str | None = None
    summary: str | None = None
    status: str
    nda_required: bool
    nda_version: str | None = None
    watermark_enabled: bool
    allow_downloads: bool
    default_permission: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    # Resolved for the caller, never sent by them.
    viewer_role: str
    viewer_permission: str
    nda_satisfied: bool


class DealRoomOverview(BaseModel):
    """Counters backing the startup's Deal Room overview screen."""

    room: DealRoomSummary
    investor_count: int
    active_investor_count: int
    document_count: int
    documents_viewed: int
    documents_never_viewed: int
    pending_access_requests: int
    open_questions: int
    last_activity_at: datetime | None = None
    engagement_score: int = Field(0, ge=0, le=100)
    recent_activity: list[AuditEventItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Folders and documents
# ---------------------------------------------------------------------------
class FolderCreate(BaseModel):
    """Create a folder inside the caller's own room."""

    name: str = Field(..., min_length=1, max_length=160)
    category: str = "other"
    parent_id: int | None = None
    position: int = 0

    @field_validator("category")
    @classmethod
    def _category(cls, v: str) -> str:
        return _check(v, DEAL_ROOM_CATEGORIES, "category")


class FolderUpdate(BaseModel):
    """Rename or re-file a folder."""

    name: str | None = Field(None, min_length=1, max_length=160)
    category: str | None = None
    parent_id: int | None = None
    position: int | None = None

    @field_validator("category")
    @classmethod
    def _category(cls, v: str | None) -> str | None:
        return v if v is None else _check(v, DEAL_ROOM_CATEGORIES, "category")


class FolderItem(BaseModel):
    """A folder as returned to the client."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    parent_id: int | None = None
    position: int
    document_count: int = 0
    created_at: datetime | None = None


class DocumentVersionItem(BaseModel):
    """One revision of a document. ``storage_key`` is never exposed."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    version_no: int
    original_filename: str
    content_type: str
    byte_size: int
    page_count: int | None = None
    created_at: datetime | None = None
    uploaded_by_member_id: int | None = None


class DocumentItem(BaseModel):
    """A document as returned to the client, with the caller's own permission."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    category: str
    status: str
    folder_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    current_version: DocumentVersionItem | None = None
    version_count: int = 1
    # What *this* caller may do with it, resolved server-side.
    permission: str
    can_download: bool
    watermarked: bool
    # Startup-side only; omitted for investors so one investor's reading habits
    # are never disclosed to another.
    view_count: int | None = None
    last_viewed_at: datetime | None = None


class DocumentUpdate(BaseModel):
    """Editable document metadata."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=4000)
    category: str | None = None
    folder_id: int | None = None
    status: str | None = None

    @field_validator("category")
    @classmethod
    def _category(cls, v: str | None) -> str | None:
        return v if v is None else _check(v, DEAL_ROOM_CATEGORIES, "category")

    @field_validator("status")
    @classmethod
    def _status(cls, v: str | None) -> str | None:
        return v if v is None else _check(v, ("draft", "published", "archived"), "status")


class DocumentLinkResponse(BaseModel):
    """A short-lived, viewer-bound URL for one document."""

    url: str
    expires_in: int
    watermarked: bool
    content_type: str
    filename: str


# ---------------------------------------------------------------------------
# Investors
# ---------------------------------------------------------------------------
class InvestorInvite(BaseModel):
    """Invite an investor by email. The room is taken from the path, not the body."""

    email: str = Field(..., min_length=3, max_length=255)
    permission: str = "view_watermark"
    expires_at: datetime | None = None
    message: str | None = Field(None, max_length=2000)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        candidate = v.strip().lower()
        local, _, domain = candidate.partition("@")
        if not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
            raise ValueError("Enter a valid email address")
        return candidate

    @field_validator("permission")
    @classmethod
    def _permission(cls, v: str) -> str:
        return _check(v, _INVESTOR_PERMISSIONS, "permission")


class ParticipantUpdate(BaseModel):
    """Change an investor's standing or default permission."""

    status: str | None = None
    permission: str | None = None
    expires_at: datetime | None = None

    @field_validator("status")
    @classmethod
    def _status(cls, v: str | None) -> str | None:
        return (
            v
            if v is None
            else _check(v, ("active", "suspended", "revoked", "rejected"), "status")
        )

    @field_validator("permission")
    @classmethod
    def _permission(cls, v: str | None) -> str | None:
        return v if v is None else _check(v, _INVESTOR_PERMISSIONS, "permission")


class ParticipantItem(BaseModel):
    """An investor's membership as shown to the startup."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int
    email: str | None = None
    full_name: str | None = None
    investor_id: int | None = None
    status: str
    permission: str
    expires_at: datetime | None = None
    nda_accepted_at: datetime | None = None
    last_activity_at: datetime | None = None
    created_at: datetime | None = None
    documents_viewed: int = 0
    downloads: int = 0
    questions_asked: int = 0


class AccessGrantWrite(BaseModel):
    """Grant or clear a folder/document permission for one investor."""

    resource_type: str
    resource_id: int
    permission: str

    @field_validator("resource_type")
    @classmethod
    def _resource_type(cls, v: str) -> str:
        return _check(v, ("folder", "document"), "resource_type")

    @field_validator("permission")
    @classmethod
    def _permission(cls, v: str) -> str:
        return _check(v, _INVESTOR_PERMISSIONS, "permission")


class AccessGrantItem(BaseModel):
    """A resource-level permission override."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    resource_type: str
    resource_id: int
    permission: str
    created_at: datetime | None = None


# ---------------------------------------------------------------------------
# Access requests
# ---------------------------------------------------------------------------
class AccessRequestCreate(BaseModel):
    """An investor's request to be admitted."""

    message: str | None = Field(None, max_length=2000)


class AccessRequestDecision(BaseModel):
    """The startup's decision on a request."""

    decision: str
    note: str | None = Field(None, max_length=2000)
    permission: str = "view_watermark"
    expires_at: datetime | None = None

    @field_validator("decision")
    @classmethod
    def _decision(cls, v: str) -> str:
        return _check(v, ("approve", "reject", "request_info"), "decision")

    @field_validator("permission")
    @classmethod
    def _permission(cls, v: str) -> str:
        return _check(v, _INVESTOR_PERMISSIONS, "permission")


class AccessRequestItem(BaseModel):
    """A pending or decided access request."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int
    email: str | None = None
    full_name: str | None = None
    message: str | None = None
    status: str
    decision_note: str | None = None
    created_at: datetime | None = None
    decided_at: datetime | None = None


# ---------------------------------------------------------------------------
# NDA
# ---------------------------------------------------------------------------
class NdaView(BaseModel):
    """The NDA an investor is asked to accept."""

    required: bool
    version: str | None = None
    body: str | None = None
    accepted: bool
    accepted_at: datetime | None = None


class NdaAccept(BaseModel):
    """An investor's acceptance. The identity is taken from the session."""

    signature_name: str = Field(..., min_length=2, max_length=160)
    accepted: bool

    @field_validator("accepted")
    @classmethod
    def _accepted(cls, v: bool) -> bool:
        if not v:
            raise ValueError("The agreement must be accepted to continue")
        return v


class NdaAcceptanceItem(BaseModel):
    """An NDA acceptance record, for the startup's compliance view."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int
    email: str | None = None
    full_name: str | None = None
    nda_version: str
    signature_name: str | None = None
    accepted_at: datetime | None = None
    ip: str | None = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
class QuestionCreate(BaseModel):
    """An investor's question, optionally about a specific document."""

    question: str = Field(..., min_length=3, max_length=5000)
    document_id: int | None = None


class AnswerCreate(BaseModel):
    """A startup or administrator reply."""

    answer: str = Field(..., min_length=1, max_length=10000)


class AnswerItem(BaseModel):
    """One answer in a question thread."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    answer: str
    answered_by_name: str | None = None
    created_at: datetime | None = None


class QuestionItem(BaseModel):
    """A question with its answers."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    status: str
    document_id: int | None = None
    document_title: str | None = None
    asked_by_member_id: int
    asked_by_name: str | None = None
    created_at: datetime | None = None
    answers: list[AnswerItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Analytics and audit
# ---------------------------------------------------------------------------
class DocumentEngagement(BaseModel):
    """Per-document engagement, shown only to the startup and administrators."""

    document_id: int
    title: str
    category: str
    views: int
    unique_investors: int
    downloads: int
    last_viewed_at: datetime | None = None


class InvestorEngagement(BaseModel):
    """Per-investor engagement, shown only to the startup and administrators."""

    participant_id: int
    member_id: int
    full_name: str | None = None
    email: str | None = None
    status: str
    last_activity_at: datetime | None = None
    documents_viewed: int
    downloads: int
    questions_asked: int
    engagement_score: int = Field(0, ge=0, le=100)


class DealRoomAnalytics(BaseModel):
    """The analytics payload for one room."""

    total_views: int
    total_downloads: int
    active_investors: int
    documents: list[DocumentEngagement]
    never_viewed: list[DocumentEngagement]
    investors: list[InvestorEngagement]
    timeline: list[TimelinePoint]


class TimelinePoint(BaseModel):
    """One day of aggregate engagement."""

    date: str
    views: int
    downloads: int


class AuditEventItem(BaseModel):
    """One audit trail entry."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    actor_email: str | None = None
    actor_role: str | None = None
    resource_type: str | None = None
    resource_id: int | None = None
    meta: str | None = None
    ip: str | None = None
    created_at: datetime | None = None


class PagedAudit(BaseModel):
    """A page of audit events."""

    items: list[AuditEventItem]
    total: int
    page: int
    page_size: int
    pages: int


# ---------------------------------------------------------------------------
# Entity claims (the identity bridge)
# ---------------------------------------------------------------------------
class EntityClaimCreate(BaseModel):
    """A member's claim to represent a directory entity."""

    entity_type: str
    entity_id: int

    @field_validator("entity_type")
    @classmethod
    def _entity_type(cls, v: str) -> str:
        return _check(v, ("startup", "investor", "incubator"), "entity_type")


class EntityClaimItem(BaseModel):
    """A claim and its approval state."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int
    member_email: str | None = None
    member_name: str | None = None
    entity_type: str
    entity_id: int
    entity_name: str | None = None
    entity_role: str
    status: str
    created_at: datetime | None = None
    approved_at: datetime | None = None


class EntityClaimDecision(BaseModel):
    """An administrator's decision on a claim."""

    decision: str

    @field_validator("decision")
    @classmethod
    def _decision(cls, v: str) -> str:
        return _check(v, ("approve", "reject", "revoke"), "decision")


DealRoomOverview.model_rebuild()
DealRoomAnalytics.model_rebuild()

__all__ = [n for n in dir() if n[0].isupper() and not n.startswith("_")]
