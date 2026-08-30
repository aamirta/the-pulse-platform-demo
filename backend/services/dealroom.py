"""Deal Room authorization, audit and analytics services.

Every Deal Room request resolves its access through :func:`resolve_access` and,
for anything touching a file, :func:`resolve_document_permission`. Keeping the
decision in one place is the point: route handlers never compare ids themselves,
so there is a single implementation to audit and a single place a rule can be
wrong.

Nothing here trusts a startup id, investor id, participant id or permission sent
by a client. Ownership is read from ``member_entity_links``; membership from
``deal_room_participants``; both are re-read on every request so a revocation
takes effect on the next call rather than when a token expires.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException, Request, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.permissions import (
    PERMISSION_MANAGE,
    PERMISSION_NONE,
    can_download,
    can_manage,
    can_upload,
    can_view,
    cap_downloads,
    is_valid_permission,
    rank,
    requires_watermark,
    with_watermark,
)
from backend.core.signing import hash_invite_token
from backend.models import (
    DealRoom,
    DealRoomAccessGrant,
    DealRoomAuditEvent,
    DealRoomDocument,
    DealRoomDocumentVersion,
    DealRoomDocumentView,
    DealRoomFolder,
    DealRoomNdaAcceptance,
    DealRoomParticipant,
    MemberEntityLink,
    PulseMember,
    User,
)

ROLE_ADMIN = "admin"
ROLE_STARTUP = "startup"
ROLE_INVESTOR = "investor"

# Audit action names. Centralised so the admin filter UI and the writers cannot
# drift apart.
ACTION_ROOM_OPENED = "deal_room.opened"
ACTION_ROOM_CREATED = "deal_room.created"
ACTION_ROOM_UPDATED = "deal_room.updated"
ACTION_DOC_UPLOADED = "document.uploaded"
ACTION_DOC_REPLACED = "document.replaced"
ACTION_DOC_PREVIEWED = "document.previewed"
ACTION_DOC_DOWNLOADED = "document.downloaded"
ACTION_DOC_DELETED = "document.deleted"
ACTION_DOC_UPDATED = "document.updated"
ACTION_FOLDER_CREATED = "folder.created"
ACTION_FOLDER_UPDATED = "folder.updated"
ACTION_FOLDER_DELETED = "folder.deleted"
ACTION_PERMISSION_CHANGED = "permission.changed"
ACTION_INVESTOR_INVITED = "investor.invited"
ACTION_INVESTOR_APPROVED = "investor.approved"
ACTION_INVESTOR_REJECTED = "investor.rejected"
ACTION_INVESTOR_SUSPENDED = "investor.suspended"
ACTION_INVESTOR_RESTORED = "investor.restored"
ACTION_ACCESS_REVOKED = "access.revoked"
ACTION_ACCESS_REQUESTED = "access.requested"
ACTION_NDA_ACCEPTED = "nda.accepted"
ACTION_QUESTION_CREATED = "question.created"
ACTION_ANSWER_CREATED = "answer.created"
ACTION_ACCESS_DENIED = "access.denied"

AUDIT_ACTIONS: tuple[str, ...] = tuple(
    value
    for name, value in sorted(globals().items())
    if name.startswith("ACTION_") and isinstance(value, str)
)


class DealRoomError(HTTPException):
    """Base for Deal Room access failures."""


def _not_found() -> HTTPException:
    """Return a 404 used for both 'absent' and 'not yours'.

    Answering 403 for a room that exists but belongs to someone else would let a
    caller enumerate which startups have a deal room, so the two cases are
    deliberately indistinguishable.
    """
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal room not found")


def _forbidden(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


@dataclass
class DealRoomAccess:
    """The resolved standing of one actor in one deal room."""

    deal_room: DealRoom
    actor_role: str
    member: PulseMember | None
    user: User | None
    participant: DealRoomParticipant | None
    # Room-wide permission before folder/document grants are applied.
    base_permission: str
    nda_satisfied: bool

    @property
    def is_manager(self) -> bool:
        """True for the owning startup and for platform administrators."""
        return self.actor_role in (ROLE_ADMIN, ROLE_STARTUP)

    @property
    def actor_email(self) -> str:
        if self.member is not None:
            return (self.member.email or "").strip().lower()
        if self.user is not None:
            return (self.user.email or "").strip().lower()
        return ""

    @property
    def actor_member_id(self) -> int | None:
        return self.member.id if self.member else None

    @property
    def actor_user_id(self) -> int | None:
        return getattr(self.user, "user_id", None) if self.user else None


# ---------------------------------------------------------------------------
# Identity: which entities does this member speak for?
# ---------------------------------------------------------------------------
def owned_startup_ids(db: Session, member: PulseMember | None) -> set[int]:
    """Return the startup ids this member has an approved claim on."""
    if member is None:
        return set()
    rows = (
        db.query(MemberEntityLink.entity_id)
        .filter(
            MemberEntityLink.member_id == member.id,
            MemberEntityLink.entity_type == "startup",
            MemberEntityLink.status == "approved",
        )
        .all()
    )
    return {row[0] for row in rows}


def is_platform_admin(user: User | None) -> bool:
    """Return True if this User row is the configured platform administrator."""
    return user is not None and user.username == settings.ADMIN_USERNAME


def _participant_is_live(participant: DealRoomParticipant, now: datetime) -> bool:
    """Return True if a participant row currently confers access.

    Expiry is evaluated here rather than by a background job, so an elapsed
    ``expires_at`` locks the investor out on their very next request.
    """
    if participant.status != "active":
        return False
    expires_at = participant.expires_at
    return not (expires_at is not None and _as_naive(expires_at) <= now)


def _as_naive(value: Any) -> datetime:
    """Return a naive UTC datetime, matching how the DateTime columns are stored."""
    if isinstance(value, datetime):
        return value.replace(tzinfo=None) if value.tzinfo else value
    return datetime.utcnow()


def get_participant(
    db: Session, deal_room_id: int, member: PulseMember | None
) -> DealRoomParticipant | None:
    """Return this member's participant row for the room, whatever its status."""
    if member is None:
        return None
    return (
        db.query(DealRoomParticipant)
        .filter(
            DealRoomParticipant.deal_room_id == deal_room_id,
            DealRoomParticipant.member_id == member.id,
        )
        .first()
    )


def nda_is_satisfied(db: Session, room: DealRoom, member: PulseMember | None) -> bool:
    """Return True if this room's NDA gate is open for this member."""
    if not room.nda_required:
        return True
    if member is None:
        return False
    return (
        db.query(DealRoomNdaAcceptance)
        .filter(
            DealRoomNdaAcceptance.deal_room_id == room.id,
            DealRoomNdaAcceptance.member_id == member.id,
            DealRoomNdaAcceptance.nda_version == (room.nda_version or "1"),
        )
        .first()
        is not None
    )


# ---------------------------------------------------------------------------
# The choke point
# ---------------------------------------------------------------------------
def resolve_access(
    db: Session,
    *,
    deal_room_id: int | None = None,
    startup_id: int | None = None,
    user: User | None,
    member: PulseMember | None,
    require: str = PERMISSION_NONE,
) -> DealRoomAccess:
    """Resolve an actor's access to a deal room, or raise.

    Exactly one of ``deal_room_id`` or ``startup_id`` identifies the room. The
    caller states the minimum permission it needs via ``require``; anything less
    raises before the handler runs.
    """
    if (deal_room_id is None) == (startup_id is None):
        raise ValueError("Pass exactly one of deal_room_id or startup_id")

    query = db.query(DealRoom)
    room = (
        query.filter(DealRoom.id == deal_room_id).first()
        if deal_room_id is not None
        else query.filter(DealRoom.startup_id == startup_id).first()
    )
    if room is None:
        raise _not_found()

    now = datetime.utcnow()

    # 1. Platform administrator.
    if is_platform_admin(user):
        return DealRoomAccess(
            deal_room=room,
            actor_role=ROLE_ADMIN,
            member=None,
            user=user,
            participant=None,
            base_permission=PERMISSION_MANAGE,
            nda_satisfied=True,
        )

    # 2. The owning startup. Read from the claim table, never from a role string.
    if member is not None and room.startup_id in owned_startup_ids(db, member):
        return DealRoomAccess(
            deal_room=room,
            actor_role=ROLE_STARTUP,
            member=member,
            user=None,
            participant=None,
            base_permission=PERMISSION_MANAGE,
            nda_satisfied=True,
        )

    # 3. An admitted investor.
    participant = get_participant(db, room.id, member)
    if participant is not None and _participant_is_live(participant, now):
        # A closed or draft room is invisible to investors even while their
        # participant row remains active, so pausing a raise cuts access at once.
        if room.status not in ("active", "paused"):
            raise _not_found()
        if room.status == "paused":
            raise _forbidden("This deal room is temporarily paused by the startup")

        permission = participant.permission
        if not is_valid_permission(permission):
            permission = PERMISSION_NONE
        # Room-level switches narrow, never widen, a participant's grant.
        permission = cap_downloads(permission, allow_downloads=room.allow_downloads)
        if room.watermark_enabled:
            permission = with_watermark(permission)
        # An investor can never reach manage/upload through a participant row.
        if rank(permission) > rank("download_watermark"):
            permission = PERMISSION_NONE

        access = DealRoomAccess(
            deal_room=room,
            actor_role=ROLE_INVESTOR,
            member=member,
            user=None,
            participant=participant,
            base_permission=permission,
            nda_satisfied=nda_is_satisfied(db, room, member),
        )
        _enforce(access, require)
        return access

    # 4. Everyone else: the room does not exist as far as they are concerned.
    raise _not_found()


def _enforce(access: DealRoomAccess, require: str) -> None:
    """Raise unless ``access`` meets the required permission level."""
    if require == PERMISSION_NONE:
        return
    if rank(access.base_permission) < rank(require):
        raise _forbidden("You do not have permission to perform this action")


def require_manager(access: DealRoomAccess) -> None:
    """Raise unless the actor may administer this room."""
    if not access.is_manager or not can_manage(access.base_permission):
        raise _forbidden("Only the startup or an administrator can do this")


def require_nda(access: DealRoomAccess) -> None:
    """Raise unless the room's NDA gate is open for this actor."""
    if not access.nda_satisfied:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must accept the non-disclosure agreement before opening documents",
        )


# ---------------------------------------------------------------------------
# Resource-level permission
# ---------------------------------------------------------------------------
def _folder_chain(db: Session, folder_id: int | None, deal_room_id: int) -> list[int]:
    """Return folder ids from the given folder up to the root, nearest first."""
    chain: list[int] = []
    seen: set[int] = set()
    current = folder_id
    # Bounded walk: a cycle introduced by a bad write must not hang the request.
    while current is not None and current not in seen and len(chain) < 32:
        seen.add(current)
        folder = (
            db.query(DealRoomFolder)
            .filter(DealRoomFolder.id == current, DealRoomFolder.deal_room_id == deal_room_id)
            .first()
        )
        if folder is None:
            break
        chain.append(folder.id)
        current = folder.parent_id
    return chain


def resolve_document_permission(
    db: Session, access: DealRoomAccess, document: DealRoomDocument
) -> str:
    """Return the actor's effective permission on one document.

    Most specific grant wins: a document grant beats the nearest folder grant,
    which beats an ancestor folder's, which beats the participant default. Room
    switches then narrow the result, so a grant can never out-rank the room.
    """
    if document.deal_room_id != access.deal_room.id:
        # Cross-room reference: treat as absent rather than leaking its existence.
        raise _not_found()

    if access.is_manager:
        return PERMISSION_MANAGE

    participant = access.participant
    if participant is None:
        return PERMISSION_NONE

    # An unpublished document is startup-side work in progress.
    if document.status != "published" or document.deleted_at is not None:
        return PERMISSION_NONE

    grants = {
        (g.resource_type, g.resource_id): g.permission
        for g in db.query(DealRoomAccessGrant).filter(
            DealRoomAccessGrant.participant_id == participant.id
        )
    }

    effective: str | None = grants.get(("document", document.id))
    if effective is None:
        for folder_id in _folder_chain(db, document.folder_id, access.deal_room.id):
            candidate = grants.get(("folder", folder_id))
            if candidate is not None:
                effective = candidate
                break
    if effective is None:
        effective = access.base_permission

    if not is_valid_permission(effective):
        return PERMISSION_NONE

    room = access.deal_room
    effective = cap_downloads(effective, allow_downloads=room.allow_downloads)
    if room.watermark_enabled:
        effective = with_watermark(effective)
    # A grant may not promote an investor past download.
    if rank(effective) > rank("download_watermark"):
        effective = PERMISSION_NONE
    return effective


def visible_documents_filter(access: DealRoomAccess) -> Any:
    """Return a SQLAlchemy filter limiting a document query to this actor's room.

    Startup-side callers see drafts; investors see only published, undeleted
    documents. The room predicate is always present, which is what keeps one
    startup's documents out of another's listing.
    """
    base = and_(
        DealRoomDocument.deal_room_id == access.deal_room.id,
        DealRoomDocument.deleted_at.is_(None),
    )
    if access.is_manager:
        return base
    return and_(base, DealRoomDocument.status == "published")


def assert_document_in_room(
    db: Session, access: DealRoomAccess, document_id: int
) -> DealRoomDocument:
    """Load a document, refusing any id that does not belong to this room."""
    document = (
        db.query(DealRoomDocument)
        .filter(
            DealRoomDocument.id == document_id,
            DealRoomDocument.deal_room_id == access.deal_room.id,
            DealRoomDocument.deleted_at.is_(None),
        )
        .first()
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document


def assert_folder_in_room(db: Session, access: DealRoomAccess, folder_id: int) -> DealRoomFolder:
    """Load a folder, refusing any id that does not belong to this room."""
    folder = (
        db.query(DealRoomFolder)
        .filter(
            DealRoomFolder.id == folder_id,
            DealRoomFolder.deal_room_id == access.deal_room.id,
        )
        .first()
    )
    if folder is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found")
    return folder


def assert_participant_in_room(
    db: Session, access: DealRoomAccess, participant_id: int
) -> DealRoomParticipant:
    """Load a participant, refusing any id that does not belong to this room."""
    participant = (
        db.query(DealRoomParticipant)
        .filter(
            DealRoomParticipant.id == participant_id,
            DealRoomParticipant.deal_room_id == access.deal_room.id,
        )
        .first()
    )
    if participant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investor not found")
    return participant


def current_version(db: Session, document: DealRoomDocument) -> DealRoomDocumentVersion | None:
    """Return the document's current version row."""
    if document.current_version_id is None:
        return None
    return (
        db.query(DealRoomDocumentVersion)
        .filter(
            DealRoomDocumentVersion.id == document.current_version_id,
            DealRoomDocumentVersion.document_id == document.id,
        )
        .first()
    )


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------
def client_ip(request: Request | None) -> str | None:
    """Return the client IP, preferring the first hop in X-Forwarded-For."""
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:45]
    return request.client.host[:45] if request.client else None


def user_agent(request: Request | None) -> str | None:
    """Return a truncated User-Agent header."""
    if request is None:
        return None
    value = request.headers.get("user-agent")
    return value[:255] if value else None


def record_audit(
    db: Session,
    *,
    access: DealRoomAccess | None,
    action: str,
    resource_type: str | None = None,
    resource_id: int | None = None,
    meta: dict[str, Any] | None = None,
    request: Request | None = None,
    deal_room_id: int | None = None,
    startup_id: int | None = None,
    actor_member_id: int | None = None,
    actor_email: str | None = None,
    commit: bool = False,
) -> DealRoomAuditEvent:
    """Append one audit event. Never raises into the caller's happy path.

    The row is added to the caller's session so it commits atomically with the
    action it describes: an action that rolls back must not leave a log claiming
    it happened.
    """
    event = DealRoomAuditEvent(
        deal_room_id=deal_room_id if access is None else access.deal_room.id,
        startup_id=startup_id if access is None else access.deal_room.startup_id,
        actor_member_id=actor_member_id if access is None else access.actor_member_id,
        actor_user_id=None if access is None else access.actor_user_id,
        actor_email=actor_email if access is None else access.actor_email,
        actor_role=None if access is None else access.actor_role,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        meta=json.dumps(meta, default=str)[:4000] if meta else None,
        ip=client_ip(request),
        user_agent=user_agent(request),
        created_at=datetime.utcnow(),
    )
    db.add(event)
    if commit:
        db.commit()
    return event


def touch_participant(db: Session, access: DealRoomAccess) -> None:
    """Record that an investor was active just now."""
    if access.participant is not None:
        access.participant.last_activity_at = datetime.utcnow()


# A visit is one sitting, not one HTTP request.
ROOM_OPEN_DEDUPE_MINUTES = 30


def record_room_open(
    db: Session, *, access: DealRoomAccess, request: Request | None = None
) -> DealRoomAuditEvent | None:
    """Log that an actor opened the room, at most once per sitting.

    ``GET /deal-rooms/{id}`` is the room's header endpoint: the SPA calls it on
    mount, after every mutation and on each tab change, so logging every call
    buried the trail under dozens of identical rows and made "who looked at my
    data room" unreadable — the one question the trail exists to answer. Repeat
    reads inside :data:`ROOM_OPEN_DEDUPE_MINUTES` therefore collapse into the
    visit already recorded.
    """
    since = datetime.utcnow() - timedelta(minutes=ROOM_OPEN_DEDUPE_MINUTES)
    recent = (
        db.query(DealRoomAuditEvent.id)
        .filter(
            DealRoomAuditEvent.deal_room_id == access.deal_room.id,
            DealRoomAuditEvent.action == ACTION_ROOM_OPENED,
            DealRoomAuditEvent.actor_member_id == access.actor_member_id,
            DealRoomAuditEvent.actor_user_id == access.actor_user_id,
            DealRoomAuditEvent.created_at >= since,
        )
        .first()
    )
    if recent is not None:
        return None
    return record_audit(db, access=access, action=ACTION_ROOM_OPENED, request=request)


def record_document_view(
    db: Session,
    *,
    access: DealRoomAccess,
    document: DealRoomDocument,
    version_id: int | None,
    event: str,
    request: Request | None = None,
) -> None:
    """Record an investor's engagement with a document for analytics.

    Startup-side and administrator activity is not recorded: the analytics are
    about investor interest, and counting the owner's own views would distort it.
    """
    if access.actor_role != ROLE_INVESTOR or access.participant is None:
        return
    db.add(
        DealRoomDocumentView(
            deal_room_id=access.deal_room.id,
            document_id=document.id,
            document_version_id=version_id,
            participant_id=access.participant.id,
            member_id=access.actor_member_id,
            event=event,
            ip=client_ip(request),
            created_at=datetime.utcnow(),
        )
    )


# ---------------------------------------------------------------------------
# Invitations
# ---------------------------------------------------------------------------
def new_invite_token() -> tuple[str, str]:
    """Return a fresh invitation token and the digest to store for it."""
    token = secrets.token_urlsafe(32)
    return token, hash_invite_token(token)


def invite_expiry(days: int = 14) -> datetime:
    """Return the default expiry for a new invitation."""
    return datetime.utcnow() + timedelta(days=days)


# Re-exported for handlers so they import permission helpers from one place.
__all__ = [
    "AUDIT_ACTIONS",
    "ROLE_ADMIN",
    "ROLE_INVESTOR",
    "ROLE_STARTUP",
    "DealRoomAccess",
    "assert_document_in_room",
    "assert_folder_in_room",
    "assert_participant_in_room",
    "can_download",
    "can_manage",
    "can_upload",
    "can_view",
    "client_ip",
    "current_version",
    "invite_expiry",
    "is_platform_admin",
    "nda_is_satisfied",
    "new_invite_token",
    "owned_startup_ids",
    "record_audit",
    "record_document_view",
    "record_room_open",
    "require_manager",
    "require_nda",
    "requires_watermark",
    "resolve_access",
    "resolve_document_permission",
    "touch_participant",
    "user_agent",
    "visible_documents_filter",
]
