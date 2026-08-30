"""Pydantic schemas for the Deal Room opportunity marketplace.

Separate from ``schemas_dealroom.py`` for the same reason that module is
separate from ``schemas.py``: the private data room and the public opportunity
board are different bounded contexts that happen to share a page.

As in the rest of the deal room, request models omit every field the client must
not choose. There is no ``author_member_id`` on a create body, no ``status`` that
bypasses the transition rules, no ``moderation_status`` outside the admin body,
and no counter a client could inflate.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.core.post_taxonomy import (
    COMMITMENT_LEVELS,
    COUNTERPARTY_TYPES,
    MODERATION_STATUSES,
    POST_TYPES,
    REPORT_REASONS,
    RESPONSE_STATUSES,
)


def _check(value: str, allowed: tuple[str, ...], label: str) -> str:
    if value not in allowed:
        raise ValueError(f"{label} must be one of: {', '.join(allowed)}")
    return value


# ---------------------------------------------------------------------------
# Author / attribution blocks shared by list and detail
# ---------------------------------------------------------------------------
class PostAuthor(BaseModel):
    """The public face of whoever posted.

    Carries ``member_id`` rather than an email so the client can open a
    conversation through ``POST /members/{id}/messages`` without ever holding
    the address, matching how the rest of the directory works.
    """

    member_id: int
    full_name: str | None = None
    role: str | None = None
    profile_pic: str | None = None
    # Set when the author posted on behalf of a directory entity they claim.
    entity_type: str | None = None
    entity_id: int | None = None
    entity_name: str | None = None


# ---------------------------------------------------------------------------
# Write models
# ---------------------------------------------------------------------------
class DealRoomPostCreate(BaseModel):
    """A new opportunity. Created as a draft unless ``publish`` is set."""

    post_type: str
    title: str = Field(..., min_length=6, max_length=160)
    summary: str = Field(..., min_length=20, max_length=400)
    details: str = Field(..., min_length=40, max_length=8000)
    looking_for: str | None = Field(None, max_length=2000)
    counterparty_type: str = "any"

    sector: str | None = Field(None, max_length=120)
    stage: str | None = Field(None, max_length=60)
    location: str | None = Field(None, max_length=120)

    amount_min: Decimal | None = Field(None, ge=0, le=Decimal("999999999999.99"))
    amount_max: Decimal | None = Field(None, ge=0, le=Decimal("999999999999.99"))
    currency: str | None = Field("MAD", max_length=8)
    equity_offered: str | None = Field(None, max_length=60)
    commitment: str | None = None
    deadline: datetime | None = None
    tags: str | None = Field(None, max_length=400)

    # Attribution is *requested* here and verified server-side against an
    # approved claim; an unverifiable pair is refused rather than dropped.
    entity_type: str | None = None
    entity_id: int | None = None
    # Offer the private data room alongside the post. Ownership re-checked.
    deal_room_id: int | None = None

    publish: bool = False

    @field_validator("post_type")
    @classmethod
    def _post_type(cls, v: str) -> str:
        return _check(v, POST_TYPES, "post_type")

    @field_validator("counterparty_type")
    @classmethod
    def _counterparty(cls, v: str) -> str:
        return _check(v, COUNTERPARTY_TYPES, "counterparty_type")

    @field_validator("commitment")
    @classmethod
    def _commitment(cls, v: str | None) -> str | None:
        return v if v is None else _check(v, COMMITMENT_LEVELS, "commitment")

    @field_validator("entity_type")
    @classmethod
    def _entity_type(cls, v: str | None) -> str | None:
        return v if v is None else _check(v, ("startup", "investor", "incubator"), "entity_type")

    @field_validator("title", "summary", "details")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("This field cannot be blank")
        return stripped

    @model_validator(mode="after")
    def _coherent(self) -> DealRoomPostCreate:
        # An inverted range is a typo that would silently exclude the post from
        # every amount filter, so it is refused at the door.
        if (
            self.amount_min is not None
            and self.amount_max is not None
            and self.amount_min > self.amount_max
        ):
            raise ValueError("amount_min cannot be greater than amount_max")
        # Attribution needs both halves or neither.
        if (self.entity_type is None) != (self.entity_id is None):
            raise ValueError("entity_type and entity_id must be provided together")
        if self.deadline is not None:
            deadline = self.deadline.replace(tzinfo=None)
            if deadline <= datetime.utcnow():
                raise ValueError("deadline must be in the future")
        return self


class DealRoomPostUpdate(BaseModel):
    """A partial edit. Every field optional; status moves through its own route."""

    post_type: str | None = None
    title: str | None = Field(None, min_length=6, max_length=160)
    summary: str | None = Field(None, min_length=20, max_length=400)
    details: str | None = Field(None, min_length=40, max_length=8000)
    looking_for: str | None = Field(None, max_length=2000)
    counterparty_type: str | None = None

    sector: str | None = Field(None, max_length=120)
    stage: str | None = Field(None, max_length=60)
    location: str | None = Field(None, max_length=120)

    amount_min: Decimal | None = Field(None, ge=0, le=Decimal("999999999999.99"))
    amount_max: Decimal | None = Field(None, ge=0, le=Decimal("999999999999.99"))
    currency: str | None = Field(None, max_length=8)
    equity_offered: str | None = Field(None, max_length=60)
    commitment: str | None = None
    deadline: datetime | None = None
    tags: str | None = Field(None, max_length=400)

    entity_type: str | None = None
    entity_id: int | None = None
    deal_room_id: int | None = None

    @field_validator("post_type")
    @classmethod
    def _post_type(cls, v: str | None) -> str | None:
        return v if v is None else _check(v, POST_TYPES, "post_type")

    @field_validator("counterparty_type")
    @classmethod
    def _counterparty(cls, v: str | None) -> str | None:
        return v if v is None else _check(v, COUNTERPARTY_TYPES, "counterparty_type")

    @field_validator("commitment")
    @classmethod
    def _commitment(cls, v: str | None) -> str | None:
        return v if v is None else _check(v, COMMITMENT_LEVELS, "commitment")

    @field_validator("entity_type")
    @classmethod
    def _entity_type(cls, v: str | None) -> str | None:
        return v if v is None else _check(v, ("startup", "investor", "incubator"), "entity_type")

    @model_validator(mode="after")
    def _coherent(self) -> DealRoomPostUpdate:
        if (
            self.amount_min is not None
            and self.amount_max is not None
            and self.amount_min > self.amount_max
        ):
            raise ValueError("amount_min cannot be greater than amount_max")
        if self.deadline is not None:
            deadline = self.deadline.replace(tzinfo=None)
            if deadline <= datetime.utcnow():
                raise ValueError("deadline must be in the future")
        return self


class DealRoomPostStatusChange(BaseModel):
    """Move a post through its lifecycle. Legality checked against the taxonomy."""

    status: str

    @field_validator("status")
    @classmethod
    def _status(cls, v: str) -> str:
        # "draft" is absent: a published post cannot be pulled back into a draft,
        # because people may already be mid-conversation about it. Close it.
        return _check(v, ("published", "closed", "archived"), "status")


# ---------------------------------------------------------------------------
# Read models
# ---------------------------------------------------------------------------
class DealRoomPostListItem(BaseModel):
    """A post as it appears on the board."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    post_type: str
    title: str
    summary: str
    counterparty_type: str
    sector: str | None = None
    stage: str | None = None
    location: str | None = None
    amount_min: Decimal | None = None
    amount_max: Decimal | None = None
    currency: str | None = None
    commitment: str | None = None
    deadline: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    status: str
    moderation_status: str
    view_count: int = 0
    response_count: int = 0
    created_at: datetime | None = None
    published_at: datetime | None = None
    author: PostAuthor
    # True when the *caller* has already responded, so the client can render
    # "Contacted" instead of offering a duplicate.
    responded_by_me: bool = False
    # True when the caller may edit or delete this post.
    can_manage: bool = False
    has_deal_room: bool = False


class DealRoomPostDetail(DealRoomPostListItem):
    """A post opened on its own, with the long-form fields."""

    details: str
    looking_for: str | None = None
    equity_offered: str | None = None
    deal_room_id: int | None = None
    moderation_note: str | None = None
    updated_at: datetime | None = None
    closed_at: datetime | None = None
    # Populated only for the author: how many reports are open against it.
    open_report_count: int | None = None


# ---------------------------------------------------------------------------
# Responses (expressions of interest)
# ---------------------------------------------------------------------------
class PostResponseCreate(BaseModel):
    """Express interest in a post. The text also opens a message thread."""

    message: str = Field(..., min_length=10, max_length=2000)

    @field_validator("message")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("A message is required")
        return stripped


class PostResponseDecision(BaseModel):
    """The author's disposition of one response."""

    status: str

    @field_validator("status")
    @classmethod
    def _status(cls, v: str) -> str:
        return _check(v, ("accepted", "declined"), "status")


class PostResponseItem(BaseModel):
    """One expression of interest, as the post's author sees it."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    responder: PostAuthor
    message: str
    status: str
    created_at: datetime | None = None
    decided_at: datetime | None = None


class PostResponseCreated(BaseModel):
    """The result of responding: the record plus where the conversation went."""

    response: PostResponseItem
    # The address the client should open in the inbox. Resolved server-side.
    partner_email: str
    partner_name: str | None = None


# ---------------------------------------------------------------------------
# Reporting and moderation
# ---------------------------------------------------------------------------
class PostReportCreate(BaseModel):
    reason: str
    detail: str | None = Field(None, max_length=1000)

    @field_validator("reason")
    @classmethod
    def _reason(cls, v: str) -> str:
        return _check(v, REPORT_REASONS, "reason")


class PostReportItem(BaseModel):
    """A report, as an administrator sees it."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    post_title: str | None = None
    reporter_member_id: int
    reporter_name: str | None = None
    reason: str
    detail: str | None = None
    status: str
    created_at: datetime | None = None
    reviewed_at: datetime | None = None


class PostModerationAction(BaseModel):
    """An administrator's decision on a post."""

    moderation_status: str
    note: str | None = Field(None, max_length=1000)
    # Close any open reports against the post in the same call.
    resolve_reports: bool = True

    @field_validator("moderation_status")
    @classmethod
    def _moderation(cls, v: str) -> str:
        return _check(v, MODERATION_STATUSES, "moderation_status")


# ---------------------------------------------------------------------------
# Filter vocabulary served to the client
# ---------------------------------------------------------------------------
class PostMetaOption(BaseModel):
    """One selectable value, with how many live posts currently carry it."""

    value: str
    count: int = 0


class PostMeta(BaseModel):
    """Everything the composer and the board's filter bar need to render.

    Served from the API rather than duplicated in the client so the two cannot
    disagree about what a valid post looks like. ``sectors``, ``stages`` and
    ``locations`` are derived from the posts that actually exist, so the filter
    bar never offers a value that would return nothing.
    """

    post_types: list[str]
    counterparty_types: list[str]
    commitment_levels: list[str]
    suggested_stages: list[str]
    report_reasons: list[str]
    response_statuses: list[str] = Field(default_factory=lambda: list(RESPONSE_STATUSES))
    sectors: list[PostMetaOption] = Field(default_factory=list)
    stages: list[PostMetaOption] = Field(default_factory=list)
    locations: list[PostMetaOption] = Field(default_factory=list)
    type_counts: list[PostMetaOption] = Field(default_factory=list)


__all__ = [
    "DealRoomPostCreate",
    "DealRoomPostDetail",
    "DealRoomPostListItem",
    "DealRoomPostStatusChange",
    "DealRoomPostUpdate",
    "PostAuthor",
    "PostMeta",
    "PostMetaOption",
    "PostModerationAction",
    "PostReportCreate",
    "PostReportItem",
    "PostResponseCreate",
    "PostResponseCreated",
    "PostResponseDecision",
    "PostResponseItem",
]
