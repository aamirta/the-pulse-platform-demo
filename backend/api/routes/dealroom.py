"""Deal Room API: a startup's private investor data room.

Authorization for every route in this module is resolved by
``backend.services.dealroom.resolve_access``. Handlers never compare a
client-supplied startup id, participant id or permission against anything; they
state the permission they need and let the service refuse.

Object-level checks are explicit: ``assert_document_in_room`` and friends load a
resource *and* pin it to the room the caller was authorized for, so swapping an
id in the URL yields a 404 rather than someone else's data.
"""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from backend.api.deps import UserOrMemberDep, get_db
from backend.api.limiter import limiter
from backend.core.config import settings
from backend.core.permissions import (
    can_download,
    can_view,
    requires_watermark,
)
from backend.core.signing import (
    DEFAULT_TTL_SECONDS,
    DocumentAccessClaims,
    InvalidAccessToken,
    issue_document_token,
    read_document_token,
)
from backend.core.storage import (
    MAX_DOCUMENT_BYTES,
    StorageError,
    delete_object,
    read_bytes,
    sanitize_filename,
    store_upload,
)
from backend.core.watermark import WatermarkError, WatermarkIdentity, apply_watermark, can_stamp
from backend.models import (
    DealRoom,
    DealRoomAccessGrant,
    DealRoomAccessRequest,
    DealRoomAnswer,
    DealRoomAuditEvent,
    DealRoomDocument,
    DealRoomDocumentVersion,
    DealRoomDocumentView,
    DealRoomFolder,
    DealRoomNdaAcceptance,
    DealRoomParticipant,
    DealRoomQuestion,
    PulseMember,
    Startup,
    User,
)
from backend.schemas_dealroom import (
    AccessGrantItem,
    AccessGrantWrite,
    AccessRequestCreate,
    AccessRequestDecision,
    AccessRequestItem,
    AnswerCreate,
    AnswerItem,
    AuditEventItem,
    DealRoomAnalytics,
    DealRoomOverview,
    DealRoomSettingsUpdate,
    DealRoomSummary,
    DocumentEngagement,
    DocumentItem,
    DocumentLinkResponse,
    DocumentUpdate,
    DocumentVersionItem,
    FolderCreate,
    FolderItem,
    FolderUpdate,
    InvestorEngagement,
    InvestorInvite,
    NdaAccept,
    NdaAcceptanceItem,
    NdaView,
    PagedAudit,
    ParticipantItem,
    ParticipantUpdate,
    QuestionCreate,
    QuestionItem,
    TimelinePoint,
)
from backend.services import dealroom as svc

router = APIRouter(prefix="/deal-rooms", tags=["deal-room"])

DbDep = Annotated[Session, Depends(get_db)]


def _actor(user_or_member: tuple[User | None, PulseMember | None]) -> tuple[User | None, PulseMember | None]:
    """Unpack the authenticated actor, rejecting an unauthenticated caller."""
    user, member = user_or_member
    if user is None and member is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    return user, member


def _room_summary(db: Session, access: svc.DealRoomAccess) -> DealRoomSummary:
    """Build the room header for whoever is asking."""
    room = access.deal_room
    startup = db.query(Startup).filter(Startup.startup_id == room.startup_id).first()
    return DealRoomSummary(
        id=room.id,
        startup_id=room.startup_id,
        startup_name=startup.startup_name if startup else None,
        name=room.name,
        summary=room.summary,
        status=room.status,
        nda_required=room.nda_required,
        nda_version=room.nda_version,
        watermark_enabled=room.watermark_enabled,
        allow_downloads=room.allow_downloads,
        default_permission=room.default_permission,
        created_at=room.created_at,
        updated_at=room.updated_at,
        viewer_role=access.actor_role,
        viewer_permission=access.base_permission,
        nda_satisfied=access.nda_satisfied,
    )


def _version_item(version: DealRoomDocumentVersion | None) -> DocumentVersionItem | None:
    if version is None:
        return None
    return DocumentVersionItem.model_validate(version)


def _document_item(
    db: Session,
    access: svc.DealRoomAccess,
    document: DealRoomDocument,
    *,
    view_stats: dict[int, tuple[int, datetime | None]] | None = None,
) -> DocumentItem:
    """Serialise a document with the calling actor's own effective permission."""
    permission = svc.resolve_document_permission(db, access, document)
    version = svc.current_version(db, document)
    version_count = (
        db.query(func.count(DealRoomDocumentVersion.id))
        .filter(DealRoomDocumentVersion.document_id == document.id)
        .scalar()
        or 0
    )
    views: int | None = None
    last_viewed: datetime | None = None
    if access.is_manager and view_stats is not None:
        views, last_viewed = view_stats.get(document.id, (0, None))

    return DocumentItem(
        id=document.id,
        title=document.title,
        description=document.description,
        category=document.category,
        status=document.status,
        folder_id=document.folder_id,
        created_at=document.created_at,
        updated_at=document.updated_at,
        current_version=_version_item(version),
        version_count=version_count,
        permission=permission,
        can_download=can_download(permission),
        watermarked=requires_watermark(permission),
        view_count=views,
        last_viewed_at=last_viewed,
    )


def _view_stats(db: Session, room_id: int) -> dict[int, tuple[int, datetime | None]]:
    """Return {document_id: (view_count, last_viewed_at)} for a room in one query."""
    rows = (
        db.query(
            DealRoomDocumentView.document_id,
            func.count(DealRoomDocumentView.id),
            func.max(DealRoomDocumentView.created_at),
        )
        .filter(DealRoomDocumentView.deal_room_id == room_id)
        .group_by(DealRoomDocumentView.document_id)
        .all()
    )
    return {row[0]: (row[1], row[2]) for row in rows}


# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------
@router.get(
    "/mine",
    response_model=list[DealRoomSummary],
    summary="List the caller's deal rooms",
    description="Rooms the authenticated actor owns as a startup or is admitted to as an investor.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_my_deal_rooms(
    request: Request,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> list[DealRoomSummary]:
    """Return every room this actor can legitimately open."""
    user, member = _actor(user_or_member)

    room_ids: set[int] = set()
    if svc.is_platform_admin(user):
        room_ids = {r.id for r in db.query(DealRoom.id).all()}
    else:
        owned = svc.owned_startup_ids(db, member)
        if owned:
            room_ids |= {
                r[0] for r in db.query(DealRoom.id).filter(DealRoom.startup_id.in_(owned)).all()
            }
        if member is not None:
            room_ids |= {
                p[0]
                for p in db.query(DealRoomParticipant.deal_room_id)
                .filter(
                    DealRoomParticipant.member_id == member.id,
                    DealRoomParticipant.status == "active",
                )
                .all()
            }

    summaries: list[DealRoomSummary] = []
    for room_id in sorted(room_ids):
        try:
            access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
        except HTTPException:
            # A room whose access has lapsed since the id was collected.
            continue
        summaries.append(_room_summary(db, access))
    return summaries


@router.post(
    "/startups/{startup_id}",
    response_model=DealRoomSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Create a deal room for a startup",
    description="Creates the single deal room for a startup. Only an approved owner of that startup, or an administrator, may do this.",
)
@limiter.limit("10/minute")
def create_deal_room(
    request: Request,
    startup_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> DealRoomSummary:
    """Create a startup's deal room, refusing anyone without an approved claim."""
    user, member = _actor(user_or_member)

    startup = db.query(Startup).filter(Startup.startup_id == startup_id).first()
    if startup is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Startup not found")

    # Ownership comes from the claim table, never from the caller's role string.
    if not svc.is_platform_admin(user) and startup_id not in svc.owned_startup_ids(db, member):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not manage this startup",
        )

    existing = db.query(DealRoom).filter(DealRoom.startup_id == startup_id).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This startup already has a deal room",
        )

    room = DealRoom(
        startup_id=startup_id,
        name=f"{startup.startup_name or 'Startup'} Deal Room",
        status="draft",
        created_by_member_id=member.id if member else None,
        created_at=datetime.utcnow(),
    )
    db.add(room)
    db.flush()

    access = svc.resolve_access(db, deal_room_id=room.id, user=user, member=member)
    svc.record_audit(db, access=access, action=svc.ACTION_ROOM_CREATED, request=request)
    db.commit()
    db.refresh(room)
    access.deal_room = room
    return _room_summary(db, access)


@router.get(
    "/{room_id}",
    response_model=DealRoomSummary,
    summary="Get a deal room",
    description="Returns the room header. Responds 404 for a room the caller may not see, so room existence is not disclosed.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def get_deal_room(
    request: Request,
    room_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> DealRoomSummary:
    """Return one room's header for an authorized caller."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.touch_participant(db, access)
    # Deduplicated: the SPA re-reads this header constantly, and one row per
    # request made the audit trail unreadable.
    svc.record_room_open(db, access=access, request=request)
    db.commit()
    return _room_summary(db, access)


@router.patch(
    "/{room_id}",
    response_model=DealRoomSummary,
    summary="Update deal room settings",
    description="Startup owners and administrators only. Governs NDA gating, watermarking and download policy.",
)
@limiter.limit("30/minute")
def update_deal_room(
    request: Request,
    room_id: int,
    data: DealRoomSettingsUpdate,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> DealRoomSummary:
    """Update room-level policy."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)

    room = access.deal_room
    changes = data.model_dump(exclude_unset=True)
    # Publishing a new NDA text must invalidate prior acceptances, so the version
    # is bumped whenever the body changes without an explicit version.
    if "nda_body" in changes and "nda_version" not in changes:
        current = room.nda_version or "0"
        changes["nda_version"] = str(int(current) + 1) if current.isdigit() else f"{current}-next"

    for field, value in changes.items():
        setattr(room, field, value)
    room.updated_at = datetime.utcnow()

    svc.record_audit(
        db,
        access=access,
        action=svc.ACTION_ROOM_UPDATED,
        resource_type="deal_room",
        resource_id=room.id,
        meta={"fields": sorted(changes)},
        request=request,
    )
    db.commit()
    db.refresh(room)
    return _room_summary(db, access)


@router.get(
    "/{room_id}/overview",
    response_model=DealRoomOverview,
    summary="Deal room overview counters",
    description="Headline counters for the startup's Deal Room dashboard. Startup owners and administrators only.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def deal_room_overview(
    request: Request,
    room_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> DealRoomOverview:
    """Return the counters behind the overview screen."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)

    investor_count = (
        db.query(func.count(DealRoomParticipant.id))
        .filter(DealRoomParticipant.deal_room_id == room_id)
        .scalar()
        or 0
    )
    active_investors = (
        db.query(func.count(DealRoomParticipant.id))
        .filter(
            DealRoomParticipant.deal_room_id == room_id,
            DealRoomParticipant.status == "active",
        )
        .scalar()
        or 0
    )
    documents = (
        db.query(DealRoomDocument)
        .filter(
            DealRoomDocument.deal_room_id == room_id,
            DealRoomDocument.deleted_at.is_(None),
        )
        .all()
    )
    stats = _view_stats(db, room_id)
    viewed = sum(1 for d in documents if stats.get(d.id, (0, None))[0] > 0)

    pending_requests = (
        db.query(func.count(DealRoomAccessRequest.id))
        .filter(
            DealRoomAccessRequest.deal_room_id == room_id,
            DealRoomAccessRequest.status == "pending",
        )
        .scalar()
        or 0
    )
    open_questions = (
        db.query(func.count(DealRoomQuestion.id))
        .filter(DealRoomQuestion.deal_room_id == room_id, DealRoomQuestion.status == "open")
        .scalar()
        or 0
    )
    last_activity = (
        db.query(func.max(DealRoomDocumentView.created_at))
        .filter(DealRoomDocumentView.deal_room_id == room_id)
        .scalar()
    )
    recent = (
        db.query(DealRoomAuditEvent)
        .filter(DealRoomAuditEvent.deal_room_id == room_id)
        .order_by(DealRoomAuditEvent.created_at.desc())
        .limit(10)
        .all()
    )

    # Coverage of the material by the admitted audience, capped at 100.
    denominator = max(len(documents) * max(active_investors, 1), 1)
    total_views = sum(count for count, _ in stats.values())
    engagement = min(100, round(total_views * 100 / denominator))

    return DealRoomOverview(
        room=_room_summary(db, access),
        investor_count=investor_count,
        active_investor_count=active_investors,
        document_count=len(documents),
        documents_viewed=viewed,
        documents_never_viewed=len(documents) - viewed,
        pending_access_requests=pending_requests,
        open_questions=open_questions,
        last_activity_at=last_activity,
        engagement_score=engagement,
        recent_activity=[AuditEventItem.model_validate(e) for e in recent],
    )


# ---------------------------------------------------------------------------
# Folders
# ---------------------------------------------------------------------------
@router.get(
    "/{room_id}/folders",
    response_model=list[FolderItem],
    summary="List folders",
    description="Folders in the room. Investors see only folders holding documents they may view.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_folders(
    request: Request,
    room_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> list[FolderItem]:
    """Return the room's folder tree, filtered to what the caller may see."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)

    folders = (
        db.query(DealRoomFolder)
        .filter(DealRoomFolder.deal_room_id == room_id)
        .order_by(DealRoomFolder.position, DealRoomFolder.name)
        .all()
    )
    documents = db.query(DealRoomDocument).filter(svc.visible_documents_filter(access)).all()

    counts: dict[int, int] = {}
    for document in documents:
        if document.folder_id is None:
            continue
        if not access.is_manager and not can_view(
            svc.resolve_document_permission(db, access, document)
        ):
            continue
        counts[document.folder_id] = counts.get(document.folder_id, 0) + 1

    items = []
    for folder in folders:
        # An investor is not shown an empty folder: its mere name can disclose
        # that a raise involves, say, litigation or a secondary sale.
        if not access.is_manager and counts.get(folder.id, 0) == 0:
            continue
        items.append(
            FolderItem(
                id=folder.id,
                name=folder.name,
                category=folder.category,
                parent_id=folder.parent_id,
                position=folder.position,
                document_count=counts.get(folder.id, 0),
                created_at=folder.created_at,
            )
        )
    return items


@router.post(
    "/{room_id}/folders",
    response_model=FolderItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create a folder",
    description="Startup owners and administrators only.",
)
@limiter.limit("30/minute")
def create_folder(
    request: Request,
    room_id: int,
    data: FolderCreate,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> FolderItem:
    """Create a folder inside the caller's own room."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)

    if data.parent_id is not None:
        # Pins the parent to this room, so a foreign folder id cannot be adopted.
        svc.assert_folder_in_room(db, access, data.parent_id)

    folder = DealRoomFolder(
        deal_room_id=room_id,
        parent_id=data.parent_id,
        name=data.name.strip(),
        category=data.category,
        position=data.position,
        created_by_member_id=member.id if member else None,
        created_at=datetime.utcnow(),
    )
    db.add(folder)
    db.flush()
    svc.record_audit(
        db,
        access=access,
        action=svc.ACTION_FOLDER_CREATED,
        resource_type="folder",
        resource_id=folder.id,
        meta={"name": folder.name, "category": folder.category},
        request=request,
    )
    db.commit()
    db.refresh(folder)
    return FolderItem(
        id=folder.id,
        name=folder.name,
        category=folder.category,
        parent_id=folder.parent_id,
        position=folder.position,
        document_count=0,
        created_at=folder.created_at,
    )


@router.patch(
    "/{room_id}/folders/{folder_id}",
    response_model=FolderItem,
    summary="Update a folder",
    description="Startup owners and administrators only.",
)
@limiter.limit("30/minute")
def update_folder(
    request: Request,
    room_id: int,
    folder_id: int,
    data: FolderUpdate,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> FolderItem:
    """Rename or re-file a folder."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)
    folder = svc.assert_folder_in_room(db, access, folder_id)

    changes = data.model_dump(exclude_unset=True)
    if changes.get("parent_id") is not None:
        if changes["parent_id"] == folder_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A folder cannot be its own parent",
            )
        svc.assert_folder_in_room(db, access, changes["parent_id"])
    for field, value in changes.items():
        setattr(folder, field, value)

    svc.record_audit(
        db,
        access=access,
        action=svc.ACTION_FOLDER_UPDATED,
        resource_type="folder",
        resource_id=folder.id,
        meta={"fields": sorted(changes)},
        request=request,
    )
    db.commit()
    db.refresh(folder)
    count = (
        db.query(func.count(DealRoomDocument.id))
        .filter(
            DealRoomDocument.folder_id == folder.id,
            DealRoomDocument.deleted_at.is_(None),
        )
        .scalar()
        or 0
    )
    return FolderItem(
        id=folder.id,
        name=folder.name,
        category=folder.category,
        parent_id=folder.parent_id,
        position=folder.position,
        document_count=count,
        created_at=folder.created_at,
    )


@router.delete(
    "/{room_id}/folders/{folder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a folder",
    description="Refuses while the folder still holds documents, so nothing is orphaned silently.",
)
@limiter.limit("30/minute")
def delete_folder(
    request: Request,
    room_id: int,
    folder_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> Response:
    """Delete an empty folder."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)
    folder = svc.assert_folder_in_room(db, access, folder_id)

    remaining = (
        db.query(func.count(DealRoomDocument.id))
        .filter(
            DealRoomDocument.folder_id == folder_id,
            DealRoomDocument.deleted_at.is_(None),
        )
        .scalar()
        or 0
    )
    if remaining:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Move or delete the {remaining} document(s) in this folder first",
        )

    svc.record_audit(
        db,
        access=access,
        action=svc.ACTION_FOLDER_DELETED,
        resource_type="folder",
        resource_id=folder_id,
        meta={"name": folder.name},
        request=request,
    )
    db.delete(folder)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------
@router.get(
    "/{room_id}/documents",
    response_model=dict,
    summary="List documents",
    description="Paginated, searchable document list. Each entry carries the caller's own effective permission; documents the caller may not view are omitted entirely.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_documents(
    request: Request,
    room_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
    q: str | None = Query(None, max_length=120, description="Search title and description"),
    category: str | None = Query(None, max_length=40),
    folder_id: int | None = Query(None),
    sort: str = Query("recent", pattern="^(recent|title|category)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
) -> dict[str, Any]:
    """Return a page of documents the caller is permitted to see."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.touch_participant(db, access)

    query = db.query(DealRoomDocument).filter(svc.visible_documents_filter(access))
    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter(
            DealRoomDocument.title.ilike(pattern) | DealRoomDocument.description.ilike(pattern)
        )
    if category:
        query = query.filter(DealRoomDocument.category == category)
    if folder_id is not None:
        svc.assert_folder_in_room(db, access, folder_id)
        query = query.filter(DealRoomDocument.folder_id == folder_id)

    if sort == "title":
        query = query.order_by(DealRoomDocument.title.asc())
    elif sort == "category":
        query = query.order_by(DealRoomDocument.category.asc(), DealRoomDocument.title.asc())
    else:
        query = query.order_by(DealRoomDocument.updated_at.desc(), DealRoomDocument.id.desc())

    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()

    stats = _view_stats(db, room_id) if access.is_manager else None
    items: list[DocumentItem] = []
    for document in rows:
        item = _document_item(db, access, document, view_stats=stats)
        # An investor with no permission on a document is not told it exists.
        if not access.is_manager and not can_view(item.permission):
            continue
        items.append(item)

    db.commit()
    return {
        "items": [i.model_dump() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size),
    }


@router.post(
    "/{room_id}/documents",
    response_model=DocumentItem,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
    description="Uploads the first version of a new document. The file's real type is verified against its magic bytes; the declared MIME type alone is not trusted.",
)
@limiter.limit("20/minute")
async def upload_document(
    request: Request,
    room_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
    file: UploadFile = File(...),
    title: str = Form(..., max_length=255),
    category: str = Form("other", max_length=40),
    folder_id: int | None = Form(None),
    description: str | None = Form(None, max_length=4000),
) -> DocumentItem:
    """Create a document and store its first version in private storage."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)

    if folder_id is not None:
        svc.assert_folder_in_room(db, access, folder_id)

    # Bounded read: never buffer more than the limit, whatever Content-Length says.
    data = await file.read(MAX_DOCUMENT_BYTES + 1)
    if len(data) > MAX_DOCUMENT_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {MAX_DOCUMENT_BYTES // (1024 * 1024)} MB limit",
        )

    document = DealRoomDocument(
        deal_room_id=room_id,
        folder_id=folder_id,
        title=title.strip(),
        description=description,
        category=category,
        status="draft",
        created_by_member_id=member.id if member else None,
        created_at=datetime.utcnow(),
    )
    db.add(document)
    db.flush()

    try:
        stored = store_upload(
            deal_room_id=room_id,
            document_id=document.id,
            data=data,
            declared_type=file.content_type,
            filename=file.filename,
        )
    except StorageError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    version = DealRoomDocumentVersion(
        document_id=document.id,
        version_no=1,
        storage_key=stored.storage_key,
        original_filename=stored.original_filename,
        content_type=stored.content_type,
        byte_size=stored.byte_size,
        sha256=stored.sha256,
        uploaded_by_member_id=member.id if member else None,
        created_at=datetime.utcnow(),
    )
    db.add(version)
    db.flush()
    document.current_version_id = version.id

    svc.record_audit(
        db,
        access=access,
        action=svc.ACTION_DOC_UPLOADED,
        resource_type="document",
        resource_id=document.id,
        meta={
            "title": document.title,
            "filename": stored.original_filename,
            "content_type": stored.content_type,
            "bytes": stored.byte_size,
            "sha256": stored.sha256,
        },
        request=request,
    )
    db.commit()
    db.refresh(document)
    return _document_item(db, access, document)


@router.post(
    "/{room_id}/documents/{document_id}/versions",
    response_model=DocumentItem,
    status_code=status.HTTP_201_CREATED,
    summary="Replace a document",
    description="Uploads a new version. Earlier versions are retained so the audit trail stays resolvable.",
)
@limiter.limit("20/minute")
async def replace_document(
    request: Request,
    room_id: int,
    document_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
    file: UploadFile = File(...),
) -> DocumentItem:
    """Add a new version to an existing document."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)
    document = svc.assert_document_in_room(db, access, document_id)

    data = await file.read(MAX_DOCUMENT_BYTES + 1)
    if len(data) > MAX_DOCUMENT_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {MAX_DOCUMENT_BYTES // (1024 * 1024)} MB limit",
        )

    try:
        stored = store_upload(
            deal_room_id=room_id,
            document_id=document.id,
            data=data,
            declared_type=file.content_type,
            filename=file.filename,
        )
    except StorageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    highest = (
        db.query(func.max(DealRoomDocumentVersion.version_no))
        .filter(DealRoomDocumentVersion.document_id == document.id)
        .scalar()
        or 0
    )
    version = DealRoomDocumentVersion(
        document_id=document.id,
        version_no=highest + 1,
        storage_key=stored.storage_key,
        original_filename=stored.original_filename,
        content_type=stored.content_type,
        byte_size=stored.byte_size,
        sha256=stored.sha256,
        uploaded_by_member_id=member.id if member else None,
        created_at=datetime.utcnow(),
    )
    db.add(version)
    db.flush()
    document.current_version_id = version.id
    document.updated_at = datetime.utcnow()

    svc.record_audit(
        db,
        access=access,
        action=svc.ACTION_DOC_REPLACED,
        resource_type="document",
        resource_id=document.id,
        meta={"version": version.version_no, "sha256": stored.sha256},
        request=request,
    )
    db.commit()
    db.refresh(document)
    return _document_item(db, access, document)


@router.get(
    "/{room_id}/documents/{document_id}/versions",
    response_model=list[DocumentVersionItem],
    summary="List document versions",
    description="Version history. Startup owners and administrators only.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_versions(
    request: Request,
    room_id: int,
    document_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> list[DocumentVersionItem]:
    """Return every retained version of a document."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)
    document = svc.assert_document_in_room(db, access, document_id)
    versions = (
        db.query(DealRoomDocumentVersion)
        .filter(DealRoomDocumentVersion.document_id == document.id)
        .order_by(DealRoomDocumentVersion.version_no.desc())
        .all()
    )
    return [DocumentVersionItem.model_validate(v) for v in versions]


@router.patch(
    "/{room_id}/documents/{document_id}",
    response_model=DocumentItem,
    summary="Update document metadata",
    description="Startup owners and administrators only. Publishing a document is what makes it visible to investors.",
)
@limiter.limit("30/minute")
def update_document(
    request: Request,
    room_id: int,
    document_id: int,
    data: DocumentUpdate,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> DocumentItem:
    """Edit a document's metadata or publication status."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)
    document = svc.assert_document_in_room(db, access, document_id)

    changes = data.model_dump(exclude_unset=True)
    if changes.get("folder_id") is not None:
        svc.assert_folder_in_room(db, access, changes["folder_id"])
    for field, value in changes.items():
        setattr(document, field, value)
    document.updated_at = datetime.utcnow()

    svc.record_audit(
        db,
        access=access,
        action=svc.ACTION_DOC_UPDATED,
        resource_type="document",
        resource_id=document.id,
        meta={"fields": sorted(changes)},
        request=request,
    )
    db.commit()
    db.refresh(document)
    return _document_item(db, access, document)


@router.delete(
    "/{room_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document",
    description="Soft-deletes the record and erases the stored bytes, so audit history stays resolvable while the file itself is gone.",
)
@limiter.limit("20/minute")
def delete_document(
    request: Request,
    room_id: int,
    document_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> Response:
    """Delete a document and purge its stored files."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)
    document = svc.assert_document_in_room(db, access, document_id)

    versions = (
        db.query(DealRoomDocumentVersion)
        .filter(DealRoomDocumentVersion.document_id == document.id)
        .all()
    )
    purged = sum(1 for v in versions if delete_object(v.storage_key))

    document.deleted_at = datetime.utcnow()
    document.status = "archived"
    svc.record_audit(
        db,
        access=access,
        action=svc.ACTION_DOC_DELETED,
        resource_type="document",
        resource_id=document.id,
        meta={"title": document.title, "files_purged": purged},
        request=request,
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Secure delivery
# ---------------------------------------------------------------------------
@router.post(
    "/{room_id}/documents/{document_id}/link",
    response_model=DocumentLinkResponse,
    summary="Mint a short-lived document link",
    description=(
        "Returns a signed URL bound to this document version, this viewer and this intent, "
        "valid for five minutes. Redeeming it re-runs the full permission check against live "
        "data, so revoking access takes effect immediately rather than when the link expires."
    ),
)
@limiter.limit("60/minute")
def create_document_link(
    request: Request,
    room_id: int,
    document_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
    intent: str = Query("preview", pattern="^(preview|download)$"),
) -> DocumentLinkResponse:
    """Issue a signed, expiring link for one document."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    document = svc.assert_document_in_room(db, access, document_id)

    permission = svc.resolve_document_permission(db, access, document)
    if not can_view(permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to open this document",
        )
    if intent == "download" and not can_download(permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This document is view-only for your access level",
        )
    # The NDA gate sits in front of content, not in front of the room itself.
    svc.require_nda(access)

    version = svc.current_version(db, document)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="This document has no file yet"
        )

    watermark = requires_watermark(permission) and access.actor_role == svc.ROLE_INVESTOR
    if watermark and not can_stamp(version.content_type):
        # Refuse rather than quietly serving an unstamped file under a
        # watermark-required permission.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This file format cannot carry a watermark. Ask the startup to publish it "
                "as a PDF, or to grant unwatermarked access."
            ),
        )

    token = issue_document_token(
        DocumentAccessClaims(
            document_id=document.id,
            version_id=version.id,
            member_id=access.actor_member_id,
            user_id=access.actor_user_id,
            deal_room_id=room_id,
            intent=intent,
            watermark=watermark,
        )
    )
    return DocumentLinkResponse(
        url=f"/api/v1/deal-rooms/documents/access/{token}",
        expires_in=DEFAULT_TTL_SECONDS,
        watermarked=watermark,
        content_type=version.content_type,
        filename=version.original_filename,
    )


@router.get(
    "/documents/access/{token}",
    summary="Redeem a document link",
    description=(
        "Streams a document to the viewer named in the signed token. The signature is "
        "necessary but not sufficient: the caller must additionally be signed in *as* the "
        "viewer the token names, and that viewer's permission is re-checked against live "
        "database state before a single byte is sent."
    ),
    response_class=StreamingResponse,
)
@limiter.limit("60/minute")
def redeem_document_link(
    request: Request,
    token: str,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> StreamingResponse:
    """Serve document bytes for a valid, unexpired, still-authorized token.

    The token names a viewer; the session must *be* that viewer. Without this the
    URL is a bearer capability: it travels in a request path, so it reaches proxy
    logs, server access logs and browser history, and anyone who read it there
    could pull the document — watermarked with, and audited against, the innocent
    viewer the token was minted for.
    """
    try:
        claims = read_document_token(token)
    except InvalidAccessToken as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    caller_user, caller_member = _actor(user_or_member)
    caller_member_id = caller_member.id if caller_member else None
    caller_user_id = caller_user.user_id if caller_user else None
    if (claims.member_id, claims.user_id) != (caller_member_id, caller_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This document link was issued to a different account",
        )

    # Re-derive the identity from the token, then re-authorize it from scratch.
    member = (
        db.query(PulseMember).filter(PulseMember.id == claims.member_id).first()
        if claims.member_id is not None
        else None
    )
    user = (
        db.query(User).filter(User.user_id == claims.user_id).first()
        if claims.user_id is not None
        else None
    )
    if member is None and user is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Link is no longer valid")

    access = svc.resolve_access(db, deal_room_id=claims.deal_room_id, user=user, member=member)
    document = svc.assert_document_in_room(db, access, claims.document_id)
    permission = svc.resolve_document_permission(db, access, document)

    if not can_view(permission) or (claims.intent == "download" and not can_download(permission)):
        svc.record_audit(
            db,
            access=access,
            action=svc.ACTION_ACCESS_DENIED,
            resource_type="document",
            resource_id=document.id,
            meta={"reason": "permission_revoked", "intent": claims.intent},
            request=request,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Your access to this document has changed"
        )
    svc.require_nda(access)

    version = (
        db.query(DealRoomDocumentVersion)
        .filter(
            DealRoomDocumentVersion.id == claims.version_id,
            DealRoomDocumentVersion.document_id == document.id,
        )
        .first()
    )
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document version not found")

    try:
        payload = read_bytes(version.storage_key)
    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="The stored file is unavailable"
        ) from exc

    # Whether to stamp is decided here from live permission, not from the token:
    # a token minted before watermarking was switched on cannot escape it.
    must_watermark = requires_watermark(permission) and access.actor_role == svc.ROLE_INVESTOR
    if must_watermark:
        if not can_stamp(version.content_type):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This file format cannot carry a required watermark",
            )
        try:
            payload = apply_watermark(
                payload,
                version.content_type,
                WatermarkIdentity(
                    email=access.actor_email,
                    member_id=access.actor_member_id,
                    ip=svc.client_ip(request),
                    at=datetime.now(UTC),
                ),
            )
        except WatermarkError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(exc)
            ) from exc

    disposition = "attachment" if claims.intent == "download" else "inline"
    filename = sanitize_filename(version.original_filename)

    svc.record_audit(
        db,
        access=access,
        action=(
            svc.ACTION_DOC_DOWNLOADED if claims.intent == "download" else svc.ACTION_DOC_PREVIEWED
        ),
        resource_type="document",
        resource_id=document.id,
        meta={
            "version": version.version_no,
            "watermarked": must_watermark,
            "bytes": len(payload),
        },
        request=request,
    )
    svc.record_document_view(
        db,
        access=access,
        document=document,
        version_id=version.id,
        event="download" if claims.intent == "download" else "view",
        request=request,
    )
    svc.touch_participant(db, access)
    db.commit()

    return StreamingResponse(
        io.BytesIO(payload),
        media_type=version.content_type,
        headers={
            "Content-Disposition": f'{disposition}; filename="{filename}"',
            "Cache-Control": "no-store, private",
            "X-Content-Type-Options": "nosniff",
            # A confidential document must never be framed by a third-party page.
            "Content-Security-Policy": "default-src 'none'; object-src 'self'; frame-ancestors 'self'",
        },
    )


# ---------------------------------------------------------------------------
# Investors
# ---------------------------------------------------------------------------
def _participant_stats(db: Session, room_id: int) -> dict[int, tuple[int, int]]:
    """Return {participant_id: (documents_viewed, downloads)} for a room."""
    rows = (
        db.query(
            DealRoomDocumentView.participant_id,
            func.count(func.distinct(DealRoomDocumentView.document_id)),
            func.sum(case((DealRoomDocumentView.event == "download", 1), else_=0)),
        )
        .filter(DealRoomDocumentView.deal_room_id == room_id)
        .group_by(DealRoomDocumentView.participant_id)
        .all()
    )
    return {row[0]: (row[1] or 0, int(row[2] or 0)) for row in rows if row[0] is not None}


def _question_counts(db: Session, room_id: int) -> dict[int, int]:
    """Return {member_id: questions_asked} for a room."""
    rows = (
        db.query(DealRoomQuestion.asked_by_member_id, func.count(DealRoomQuestion.id))
        .filter(DealRoomQuestion.deal_room_id == room_id)
        .group_by(DealRoomQuestion.asked_by_member_id)
        .all()
    )
    return {row[0]: row[1] for row in rows}


@router.get(
    "/{room_id}/investors",
    response_model=list[ParticipantItem],
    summary="List investors",
    description="The room's investors and their standing. Startup owners and administrators only, so one investor can never enumerate another.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_investors(
    request: Request,
    room_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> list[ParticipantItem]:
    """Return every participant with engagement counters."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)

    participants = (
        db.query(DealRoomParticipant)
        .filter(DealRoomParticipant.deal_room_id == room_id)
        .order_by(DealRoomParticipant.created_at.desc())
        .all()
    )
    member_ids = [p.member_id for p in participants]
    members = {
        m.id: m for m in db.query(PulseMember).filter(PulseMember.id.in_(member_ids)).all()
    } if member_ids else {}
    stats = _participant_stats(db, room_id)
    questions = _question_counts(db, room_id)

    items = []
    for participant in participants:
        profile = members.get(participant.member_id)
        viewed, downloads = stats.get(participant.id, (0, 0))
        items.append(
            ParticipantItem(
                id=participant.id,
                member_id=participant.member_id,
                email=profile.email if profile else None,
                full_name=profile.full_name if profile else None,
                investor_id=participant.investor_id,
                status=participant.status,
                permission=participant.permission,
                expires_at=participant.expires_at,
                nda_accepted_at=participant.nda_accepted_at,
                last_activity_at=participant.last_activity_at,
                created_at=participant.created_at,
                documents_viewed=viewed,
                downloads=downloads,
                questions_asked=questions.get(participant.member_id, 0),
            )
        )
    return items


@router.post(
    "/{room_id}/investors",
    response_model=ParticipantItem,
    status_code=status.HTTP_201_CREATED,
    summary="Invite an investor",
    description="Invites an investor by email. The invitation token is stored only as a hash. Startup owners and administrators only.",
)
@limiter.limit("20/minute")
def invite_investor(
    request: Request,
    room_id: int,
    data: InvestorInvite,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> ParticipantItem:
    """Admit an investor to the room, or re-invite an existing one."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)

    email = data.email
    invitee = db.query(PulseMember).filter(func.lower(PulseMember.email) == email).first()
    if invitee is None:
        # Membership is a link to a real account, not a free-text address: this
        # is what makes per-investor permissions and audit attribution possible.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No community member exists with that email. Ask them to sign up first.",
        )
    if invitee.id == access.actor_member_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot invite yourself to your own deal room",
        )

    _, token_hash = svc.new_invite_token()
    participant = svc.get_participant(db, room_id, invitee)
    if participant is None:
        participant = DealRoomParticipant(
            deal_room_id=room_id,
            member_id=invitee.id,
            status="active",
            permission=data.permission,
            expires_at=data.expires_at,
            invited_by_member_id=access.actor_member_id,
            invite_token_hash=token_hash,
            invite_expires_at=svc.invite_expiry(),
            created_at=datetime.utcnow(),
        )
        db.add(participant)
    else:
        participant.status = "active"
        participant.permission = data.permission
        participant.expires_at = data.expires_at
        participant.invite_token_hash = token_hash
        participant.invite_expires_at = svc.invite_expiry()
    db.flush()

    svc.record_audit(
        db,
        access=access,
        action=svc.ACTION_INVESTOR_INVITED,
        resource_type="participant",
        resource_id=participant.id,
        meta={"email": email, "permission": data.permission},
        request=request,
    )
    db.commit()
    db.refresh(participant)
    return ParticipantItem(
        id=participant.id,
        member_id=participant.member_id,
        email=invitee.email,
        full_name=invitee.full_name,
        investor_id=participant.investor_id,
        status=participant.status,
        permission=participant.permission,
        expires_at=participant.expires_at,
        nda_accepted_at=participant.nda_accepted_at,
        last_activity_at=participant.last_activity_at,
        created_at=participant.created_at,
    )


@router.patch(
    "/{room_id}/investors/{participant_id}",
    response_model=ParticipantItem,
    summary="Update an investor's access",
    description="Suspend, restore, revoke, re-permission or set an expiry. Startup owners and administrators only.",
)
@limiter.limit("30/minute")
def update_investor(
    request: Request,
    room_id: int,
    participant_id: int,
    data: ParticipantUpdate,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> ParticipantItem:
    """Change one investor's standing in the room."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)
    participant = svc.assert_participant_in_room(db, access, participant_id)

    changes = data.model_dump(exclude_unset=True)
    previous_status = participant.status
    for field, value in changes.items():
        setattr(participant, field, value)
    participant.updated_at = datetime.utcnow()

    action = svc.ACTION_PERMISSION_CHANGED
    new_status = changes.get("status")
    if new_status == "suspended":
        action = svc.ACTION_INVESTOR_SUSPENDED
    elif new_status == "revoked":
        action = svc.ACTION_ACCESS_REVOKED
    elif new_status == "active" and previous_status != "active":
        action = svc.ACTION_INVESTOR_RESTORED

    svc.record_audit(
        db,
        access=access,
        action=action,
        resource_type="participant",
        resource_id=participant.id,
        meta={"from": previous_status, "changes": changes},
        request=request,
    )
    db.commit()
    db.refresh(participant)
    profile = db.query(PulseMember).filter(PulseMember.id == participant.member_id).first()
    return ParticipantItem(
        id=participant.id,
        member_id=participant.member_id,
        email=profile.email if profile else None,
        full_name=profile.full_name if profile else None,
        investor_id=participant.investor_id,
        status=participant.status,
        permission=participant.permission,
        expires_at=participant.expires_at,
        nda_accepted_at=participant.nda_accepted_at,
        last_activity_at=participant.last_activity_at,
        created_at=participant.created_at,
    )


@router.delete(
    "/{room_id}/investors/{participant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an investor's access",
    description="Revokes immediately. The row is kept, not deleted, so the audit trail and analytics stay attributable.",
)
@limiter.limit("30/minute")
def revoke_investor(
    request: Request,
    room_id: int,
    participant_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> Response:
    """Revoke an investor's access to the room."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)
    participant = svc.assert_participant_in_room(db, access, participant_id)

    participant.status = "revoked"
    participant.updated_at = datetime.utcnow()
    svc.record_audit(
        db,
        access=access,
        action=svc.ACTION_ACCESS_REVOKED,
        resource_type="participant",
        resource_id=participant.id,
        request=request,
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{room_id}/investors/{participant_id}/grants",
    response_model=list[AccessGrantItem],
    summary="List an investor's resource grants",
    description="Folder and document permission overrides for one investor. Startup owners and administrators only.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_grants(
    request: Request,
    room_id: int,
    participant_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> list[AccessGrantItem]:
    """Return one investor's per-resource overrides."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)
    participant = svc.assert_participant_in_room(db, access, participant_id)
    grants = (
        db.query(DealRoomAccessGrant)
        .filter(DealRoomAccessGrant.participant_id == participant.id)
        .all()
    )
    return [AccessGrantItem.model_validate(g) for g in grants]


@router.put(
    "/{room_id}/investors/{participant_id}/grants",
    response_model=AccessGrantItem,
    summary="Set a resource-level permission",
    description="Grants or updates one investor's permission on a specific folder or document.",
)
@limiter.limit("30/minute")
def set_grant(
    request: Request,
    room_id: int,
    participant_id: int,
    data: AccessGrantWrite,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> AccessGrantItem:
    """Create or replace a folder/document grant for one investor."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)
    participant = svc.assert_participant_in_room(db, access, participant_id)

    # The resource must belong to this room, so a grant cannot name a foreign id.
    if data.resource_type == "folder":
        svc.assert_folder_in_room(db, access, data.resource_id)
    else:
        svc.assert_document_in_room(db, access, data.resource_id)

    grant = (
        db.query(DealRoomAccessGrant)
        .filter(
            DealRoomAccessGrant.participant_id == participant.id,
            DealRoomAccessGrant.resource_type == data.resource_type,
            DealRoomAccessGrant.resource_id == data.resource_id,
        )
        .first()
    )
    if grant is None:
        grant = DealRoomAccessGrant(
            participant_id=participant.id,
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            permission=data.permission,
            created_by_member_id=access.actor_member_id,
            created_at=datetime.utcnow(),
        )
        db.add(grant)
    else:
        grant.permission = data.permission
    db.flush()

    svc.record_audit(
        db,
        access=access,
        action=svc.ACTION_PERMISSION_CHANGED,
        resource_type=data.resource_type,
        resource_id=data.resource_id,
        meta={"participant_id": participant.id, "permission": data.permission},
        request=request,
    )
    db.commit()
    db.refresh(grant)
    return AccessGrantItem.model_validate(grant)


@router.delete(
    "/{room_id}/investors/{participant_id}/grants/{grant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear a resource-level permission",
    description="Removes an override so the investor falls back to their room-wide default.",
)
@limiter.limit("30/minute")
def delete_grant(
    request: Request,
    room_id: int,
    participant_id: int,
    grant_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> Response:
    """Delete one grant."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)
    participant = svc.assert_participant_in_room(db, access, participant_id)

    grant = (
        db.query(DealRoomAccessGrant)
        .filter(
            DealRoomAccessGrant.id == grant_id,
            DealRoomAccessGrant.participant_id == participant.id,
        )
        .first()
    )
    if grant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")

    svc.record_audit(
        db,
        access=access,
        action=svc.ACTION_PERMISSION_CHANGED,
        resource_type=grant.resource_type,
        resource_id=grant.resource_id,
        meta={"participant_id": participant.id, "permission": None},
        request=request,
    )
    db.delete(grant)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Access requests
# ---------------------------------------------------------------------------
@router.post(
    "/startups/{startup_id}/access-requests",
    response_model=AccessRequestItem,
    status_code=status.HTTP_201_CREATED,
    summary="Request access to a deal room",
    description="An investor asks a startup for admission. Available to any authenticated member; the request grants nothing until the startup approves it.",
)
@limiter.limit("10/minute")
def request_access(
    request: Request,
    startup_id: int,
    data: AccessRequestCreate,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> AccessRequestItem:
    """Register an investor's request to enter a room."""
    _user, member = _actor(user_or_member)
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only community members can request deal room access",
        )

    room = db.query(DealRoom).filter(DealRoom.startup_id == startup_id).first()
    # A draft or closed room is not accepting requests, and says nothing about
    # whether it exists.
    if room is None or room.status not in ("active", "paused"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal room not found")

    if startup_id in svc.owned_startup_ids(db, member):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already manage this deal room",
        )

    existing_participant = svc.get_participant(db, room.id, member)
    if existing_participant is not None and existing_participant.status == "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="You already have access to this deal room"
        )

    pending = (
        db.query(DealRoomAccessRequest)
        .filter(
            DealRoomAccessRequest.deal_room_id == room.id,
            DealRoomAccessRequest.member_id == member.id,
            DealRoomAccessRequest.status.in_(("pending", "info_requested")),
        )
        .first()
    )
    if pending is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Your request is already pending review"
        )

    access_request = DealRoomAccessRequest(
        deal_room_id=room.id,
        member_id=member.id,
        message=data.message,
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(access_request)
    db.flush()

    # No DealRoomAccess exists for a non-participant, so the audit row is written
    # from the raw identity instead.
    svc.record_audit(
        db,
        access=None,
        deal_room_id=room.id,
        startup_id=room.startup_id,
        actor_member_id=member.id,
        actor_email=(member.email or "").strip().lower(),
        action=svc.ACTION_ACCESS_REQUESTED,
        resource_type="access_request",
        resource_id=access_request.id,
        request=request,
    )
    db.commit()
    db.refresh(access_request)
    return AccessRequestItem(
        id=access_request.id,
        member_id=member.id,
        email=member.email,
        full_name=member.full_name,
        message=access_request.message,
        status=access_request.status,
        created_at=access_request.created_at,
    )


@router.get(
    "/{room_id}/access-requests",
    response_model=list[AccessRequestItem],
    summary="List access requests",
    description="Pending and decided requests for this room. Startup owners and administrators only.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_access_requests(
    request: Request,
    room_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
    status_filter: str | None = Query(None, alias="status", max_length=20),
) -> list[AccessRequestItem]:
    """Return the room's access requests."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)

    query = db.query(DealRoomAccessRequest).filter(
        DealRoomAccessRequest.deal_room_id == room_id
    )
    if status_filter:
        query = query.filter(DealRoomAccessRequest.status == status_filter)
    rows = query.order_by(DealRoomAccessRequest.created_at.desc()).all()

    member_ids = [r.member_id for r in rows]
    profiles = {
        m.id: m for m in db.query(PulseMember).filter(PulseMember.id.in_(member_ids)).all()
    } if member_ids else {}

    return [
        AccessRequestItem(
            id=r.id,
            member_id=r.member_id,
            email=profiles[r.member_id].email if r.member_id in profiles else None,
            full_name=profiles[r.member_id].full_name if r.member_id in profiles else None,
            message=r.message,
            status=r.status,
            decision_note=r.decision_note,
            created_at=r.created_at,
            decided_at=r.decided_at,
        )
        for r in rows
    ]


@router.post(
    "/{room_id}/access-requests/{request_id}/decision",
    response_model=AccessRequestItem,
    summary="Decide an access request",
    description="Approve (admitting the investor with a chosen permission), reject, or ask for more information.",
)
@limiter.limit("30/minute")
def decide_access_request(
    request: Request,
    room_id: int,
    request_id: int,
    data: AccessRequestDecision,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> AccessRequestItem:
    """Approve, reject, or query an access request."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)

    access_request = (
        db.query(DealRoomAccessRequest)
        .filter(
            DealRoomAccessRequest.id == request_id,
            DealRoomAccessRequest.deal_room_id == room_id,
        )
        .first()
    )
    if access_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    applicant = (
        db.query(PulseMember).filter(PulseMember.id == access_request.member_id).first()
    )

    if data.decision == "approve":
        access_request.status = "approved"
        participant = svc.get_participant(db, room_id, applicant)
        if participant is None:
            participant = DealRoomParticipant(
                deal_room_id=room_id,
                member_id=access_request.member_id,
                status="active",
                permission=data.permission,
                expires_at=data.expires_at,
                invited_by_member_id=access.actor_member_id,
                created_at=datetime.utcnow(),
            )
            db.add(participant)
        else:
            participant.status = "active"
            participant.permission = data.permission
            participant.expires_at = data.expires_at
        db.flush()
        action = svc.ACTION_INVESTOR_APPROVED
        resource_id = participant.id
    elif data.decision == "reject":
        access_request.status = "rejected"
        action = svc.ACTION_INVESTOR_REJECTED
        resource_id = access_request.id
    else:
        access_request.status = "info_requested"
        action = svc.ACTION_ROOM_UPDATED
        resource_id = access_request.id

    access_request.decision_note = data.note
    access_request.decided_by_member_id = access.actor_member_id
    access_request.decided_at = datetime.utcnow()

    svc.record_audit(
        db,
        access=access,
        action=action,
        resource_type="access_request",
        resource_id=resource_id,
        meta={"decision": data.decision, "member_id": access_request.member_id},
        request=request,
    )
    db.commit()
    db.refresh(access_request)
    return AccessRequestItem(
        id=access_request.id,
        member_id=access_request.member_id,
        email=applicant.email if applicant else None,
        full_name=applicant.full_name if applicant else None,
        message=access_request.message,
        status=access_request.status,
        decision_note=access_request.decision_note,
        created_at=access_request.created_at,
        decided_at=access_request.decided_at,
    )


# ---------------------------------------------------------------------------
# NDA
# ---------------------------------------------------------------------------
@router.get(
    "/{room_id}/nda",
    response_model=NdaView,
    summary="Get the room's NDA",
    description="Returns the agreement text and whether the caller has already accepted the current version.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def get_nda(
    request: Request,
    room_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> NdaView:
    """Return the NDA an investor must accept."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    room = access.deal_room

    acceptance = None
    if member is not None:
        acceptance = (
            db.query(DealRoomNdaAcceptance)
            .filter(
                DealRoomNdaAcceptance.deal_room_id == room.id,
                DealRoomNdaAcceptance.member_id == member.id,
                DealRoomNdaAcceptance.nda_version == (room.nda_version or "1"),
            )
            .first()
        )
    return NdaView(
        required=room.nda_required,
        version=room.nda_version,
        body=room.nda_body,
        accepted=acceptance is not None,
        accepted_at=acceptance.accepted_at if acceptance else None,
    )


@router.post(
    "/{room_id}/nda/accept",
    response_model=NdaView,
    summary="Accept the room's NDA",
    description="Records the acceptance against the exact NDA version and text, with the accepting member, time and IP.",
)
@limiter.limit("10/minute")
def accept_nda(
    request: Request,
    room_id: int,
    data: NdaAccept,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> NdaView:
    """Record an investor's NDA acceptance."""
    user, member = _actor(user_or_member)
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only community members can accept a non-disclosure agreement",
        )
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    room = access.deal_room
    if not room.nda_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This deal room does not require an NDA",
        )

    version = room.nda_version or "1"
    existing = (
        db.query(DealRoomNdaAcceptance)
        .filter(
            DealRoomNdaAcceptance.deal_room_id == room.id,
            DealRoomNdaAcceptance.member_id == member.id,
            DealRoomNdaAcceptance.nda_version == version,
        )
        .first()
    )
    if existing is None:
        import hashlib

        existing = DealRoomNdaAcceptance(
            deal_room_id=room.id,
            member_id=member.id,
            participant_id=access.participant.id if access.participant else None,
            nda_version=version,
            # Pins the exact text accepted, so editing the NDA later cannot
            # rewrite what someone agreed to.
            nda_body_sha256=hashlib.sha256((room.nda_body or "").encode("utf-8")).hexdigest(),
            signature_name=data.signature_name.strip(),
            accepted_at=datetime.utcnow(),
            ip=svc.client_ip(request),
            user_agent=svc.user_agent(request),
        )
        db.add(existing)
        if access.participant is not None:
            access.participant.nda_accepted_at = existing.accepted_at
            access.participant.nda_version = version
        db.flush()
        svc.record_audit(
            db,
            access=access,
            action=svc.ACTION_NDA_ACCEPTED,
            resource_type="nda",
            resource_id=existing.id,
            meta={"version": version, "signature": data.signature_name.strip()},
            request=request,
        )
        db.commit()
        db.refresh(existing)

    return NdaView(
        required=True,
        version=version,
        body=room.nda_body,
        accepted=True,
        accepted_at=existing.accepted_at,
    )


@router.get(
    "/{room_id}/nda/acceptances",
    response_model=list[NdaAcceptanceItem],
    summary="List NDA acceptances",
    description="Who has signed, when, and from where. Startup owners and administrators only.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_nda_acceptances(
    request: Request,
    room_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> list[NdaAcceptanceItem]:
    """Return the room's NDA compliance record."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)

    rows = (
        db.query(DealRoomNdaAcceptance)
        .filter(DealRoomNdaAcceptance.deal_room_id == room_id)
        .order_by(DealRoomNdaAcceptance.accepted_at.desc())
        .all()
    )
    member_ids = [r.member_id for r in rows]
    profiles = {
        m.id: m for m in db.query(PulseMember).filter(PulseMember.id.in_(member_ids)).all()
    } if member_ids else {}
    return [
        NdaAcceptanceItem(
            id=r.id,
            member_id=r.member_id,
            email=profiles[r.member_id].email if r.member_id in profiles else None,
            full_name=profiles[r.member_id].full_name if r.member_id in profiles else None,
            nda_version=r.nda_version,
            signature_name=r.signature_name,
            accepted_at=r.accepted_at,
            ip=r.ip,
        )
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
@router.get(
    "/{room_id}/questions",
    response_model=list[QuestionItem],
    summary="List questions",
    description=(
        "Startup owners and administrators see every question. An investor sees only their "
        "own, so one investor's line of enquiry is never disclosed to another."
    ),
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_questions(
    request: Request,
    room_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
    status_filter: str | None = Query(None, alias="status", max_length=20),
) -> list[QuestionItem]:
    """Return the Q&A threads this caller may see."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)

    query = db.query(DealRoomQuestion).filter(DealRoomQuestion.deal_room_id == room_id)
    if not access.is_manager:
        # The isolation that matters most in this view.
        query = query.filter(DealRoomQuestion.asked_by_member_id == access.actor_member_id)
    if status_filter:
        query = query.filter(DealRoomQuestion.status == status_filter)
    rows = query.order_by(DealRoomQuestion.created_at.desc()).all()
    if not rows:
        return []

    question_ids = [q.id for q in rows]
    answers: dict[int, list[DealRoomAnswer]] = {}
    for answer in (
        db.query(DealRoomAnswer)
        .filter(DealRoomAnswer.question_id.in_(question_ids))
        .order_by(DealRoomAnswer.created_at.asc())
        .all()
    ):
        answers.setdefault(answer.question_id, []).append(answer)

    member_ids = {q.asked_by_member_id for q in rows}
    member_ids |= {
        a.answered_by_member_id
        for group in answers.values()
        for a in group
        if a.answered_by_member_id
    }
    profiles = {
        m.id: m for m in db.query(PulseMember).filter(PulseMember.id.in_(member_ids)).all()
    } if member_ids else {}

    document_ids = {q.document_id for q in rows if q.document_id}
    documents = {
        d.id: d
        for d in db.query(DealRoomDocument).filter(DealRoomDocument.id.in_(document_ids)).all()
    } if document_ids else {}

    return [
        QuestionItem(
            id=q.id,
            question=q.question,
            status=q.status,
            document_id=q.document_id,
            document_title=documents[q.document_id].title if q.document_id in documents else None,
            asked_by_member_id=q.asked_by_member_id,
            asked_by_name=(
                profiles[q.asked_by_member_id].full_name
                if q.asked_by_member_id in profiles
                else None
            ),
            created_at=q.created_at,
            answers=[
                AnswerItem(
                    id=a.id,
                    answer=a.answer,
                    answered_by_name=(
                        profiles[a.answered_by_member_id].full_name
                        if a.answered_by_member_id in profiles
                        else "The Pulse"
                    ),
                    created_at=a.created_at,
                )
                for a in answers.get(q.id, [])
            ],
        )
        for q in rows
    ]


@router.post(
    "/{room_id}/questions",
    response_model=QuestionItem,
    status_code=status.HTTP_201_CREATED,
    summary="Ask a question",
    description="An admitted investor asks a question, optionally about a document they can actually see.",
)
@limiter.limit("20/minute")
def create_question(
    request: Request,
    room_id: int,
    data: QuestionCreate,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> QuestionItem:
    """Create a Q&A thread."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only community members can ask questions",
        )

    document_title: str | None = None
    if data.document_id is not None:
        document = svc.assert_document_in_room(db, access, data.document_id)
        # Attaching a question to a document the asker cannot see would confirm
        # that document's existence to them.
        if not can_view(svc.resolve_document_permission(db, access, document)):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        document_title = document.title

    question = DealRoomQuestion(
        deal_room_id=room_id,
        document_id=data.document_id,
        asked_by_member_id=member.id,
        participant_id=access.participant.id if access.participant else None,
        question=data.question.strip(),
        status="open",
        created_at=datetime.utcnow(),
    )
    db.add(question)
    db.flush()
    svc.record_audit(
        db,
        access=access,
        action=svc.ACTION_QUESTION_CREATED,
        resource_type="question",
        resource_id=question.id,
        meta={"document_id": data.document_id},
        request=request,
    )
    db.commit()
    db.refresh(question)
    return QuestionItem(
        id=question.id,
        question=question.question,
        status=question.status,
        document_id=question.document_id,
        document_title=document_title,
        asked_by_member_id=question.asked_by_member_id,
        asked_by_name=member.full_name,
        created_at=question.created_at,
        answers=[],
    )


@router.post(
    "/{room_id}/questions/{question_id}/answers",
    response_model=AnswerItem,
    status_code=status.HTTP_201_CREATED,
    summary="Answer a question",
    description="Startup owners and administrators only.",
)
@limiter.limit("30/minute")
def answer_question(
    request: Request,
    room_id: int,
    question_id: int,
    data: AnswerCreate,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> AnswerItem:
    """Reply to an investor's question."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)

    question = (
        db.query(DealRoomQuestion)
        .filter(
            DealRoomQuestion.id == question_id,
            DealRoomQuestion.deal_room_id == room_id,
        )
        .first()
    )
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    answer = DealRoomAnswer(
        question_id=question.id,
        answered_by_member_id=access.actor_member_id,
        answered_by_user_id=access.actor_user_id,
        answer=data.answer.strip(),
        created_at=datetime.utcnow(),
    )
    db.add(answer)
    question.status = "answered"
    question.updated_at = datetime.utcnow()

    svc.record_audit(
        db,
        access=access,
        action=svc.ACTION_ANSWER_CREATED,
        resource_type="question",
        resource_id=question.id,
        request=request,
    )
    db.commit()
    db.refresh(answer)
    return AnswerItem(
        id=answer.id,
        answer=answer.answer,
        answered_by_name=member.full_name if member else "The Pulse",
        created_at=answer.created_at,
    )


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
@router.get(
    "/{room_id}/analytics",
    response_model=DealRoomAnalytics,
    summary="Investor engagement analytics",
    description=(
        "Which investors read what, and which documents nobody opened. Startup owners and "
        "administrators only: investors are never shown another investor's activity."
    ),
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def deal_room_analytics(
    request: Request,
    room_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
    days: int = Query(30, ge=1, le=365),
) -> DealRoomAnalytics:
    """Return engagement analytics for one room."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)

    documents = (
        db.query(DealRoomDocument)
        .filter(
            DealRoomDocument.deal_room_id == room_id,
            DealRoomDocument.deleted_at.is_(None),
        )
        .all()
    )
    rows = (
        db.query(
            DealRoomDocumentView.document_id,
            func.count(DealRoomDocumentView.id),
            func.count(func.distinct(DealRoomDocumentView.participant_id)),
            func.sum(case((DealRoomDocumentView.event == "download", 1), else_=0)),
            func.max(DealRoomDocumentView.created_at),
        )
        .filter(DealRoomDocumentView.deal_room_id == room_id)
        .group_by(DealRoomDocumentView.document_id)
        .all()
    )
    by_document = {r[0]: (r[1], r[2], int(r[3] or 0), r[4]) for r in rows}

    engaged: list[DocumentEngagement] = []
    never: list[DocumentEngagement] = []
    for document in documents:
        views, investors, downloads, last = by_document.get(document.id, (0, 0, 0, None))
        item = DocumentEngagement(
            document_id=document.id,
            title=document.title,
            category=document.category,
            views=views,
            unique_investors=investors,
            downloads=downloads,
            last_viewed_at=last,
        )
        (engaged if views else never).append(item)
    engaged.sort(key=lambda d: d.views, reverse=True)

    participants = (
        db.query(DealRoomParticipant)
        .filter(DealRoomParticipant.deal_room_id == room_id)
        .all()
    )
    stats = _participant_stats(db, room_id)
    questions = _question_counts(db, room_id)
    member_ids = [p.member_id for p in participants]
    profiles = {
        m.id: m for m in db.query(PulseMember).filter(PulseMember.id.in_(member_ids)).all()
    } if member_ids else {}

    total_documents = max(len(documents), 1)
    investors_out: list[InvestorEngagement] = []
    for participant in participants:
        viewed, downloads = stats.get(participant.id, (0, 0))
        profile = profiles.get(participant.member_id)
        asked = questions.get(participant.member_id, 0)
        # Reading breadth dominates, with downloads and questions as intent signals.
        score = min(
            100,
            round(viewed * 70 / total_documents) + min(downloads * 5, 20) + min(asked * 5, 10),
        )
        investors_out.append(
            InvestorEngagement(
                participant_id=participant.id,
                member_id=participant.member_id,
                full_name=profile.full_name if profile else None,
                email=profile.email if profile else None,
                status=participant.status,
                last_activity_at=participant.last_activity_at,
                documents_viewed=viewed,
                downloads=downloads,
                questions_asked=asked,
                engagement_score=score,
            )
        )
    investors_out.sort(key=lambda i: i.engagement_score, reverse=True)

    cutoff = datetime.utcnow() - timedelta(days=days)
    timeline_rows = (
        db.query(
            func.date(DealRoomDocumentView.created_at),
            func.count(DealRoomDocumentView.id),
            func.sum(case((DealRoomDocumentView.event == "download", 1), else_=0)),
        )
        .filter(
            DealRoomDocumentView.deal_room_id == room_id,
            DealRoomDocumentView.created_at >= cutoff,
        )
        .group_by(func.date(DealRoomDocumentView.created_at))
        .order_by(func.date(DealRoomDocumentView.created_at))
        .all()
    )

    return DealRoomAnalytics(
        total_views=sum(v[0] for v in by_document.values()),
        total_downloads=sum(v[2] for v in by_document.values()),
        active_investors=sum(1 for p in participants if p.status == "active"),
        documents=engaged,
        never_viewed=never,
        investors=investors_out,
        timeline=[
            TimelinePoint(date=str(r[0]), views=r[1], downloads=int(r[2] or 0))
            for r in timeline_rows
        ],
    )


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------
@router.get(
    "/{room_id}/audit",
    response_model=PagedAudit,
    summary="Deal room audit trail",
    description="Filterable by actor, action, resource and date. Startup owners and administrators only.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def deal_room_audit(
    request: Request,
    room_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
    action: str | None = Query(None, max_length=60),
    actor_member_id: int | None = Query(None),
    resource_type: str | None = Query(None, max_length=30),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PagedAudit:
    """Return a filtered page of audit events."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)

    query = db.query(DealRoomAuditEvent).filter(DealRoomAuditEvent.deal_room_id == room_id)
    if action:
        query = query.filter(DealRoomAuditEvent.action == action)
    if actor_member_id is not None:
        query = query.filter(DealRoomAuditEvent.actor_member_id == actor_member_id)
    if resource_type:
        query = query.filter(DealRoomAuditEvent.resource_type == resource_type)
    if date_from is not None:
        query = query.filter(DealRoomAuditEvent.created_at >= date_from)
    if date_to is not None:
        query = query.filter(DealRoomAuditEvent.created_at <= date_to)

    total = query.count()
    rows = (
        query.order_by(DealRoomAuditEvent.created_at.desc(), DealRoomAuditEvent.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PagedAudit(
        items=[AuditEventItem.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get(
    "/{room_id}/audit/export",
    summary="Export the audit trail as CSV",
    description="Streams the full filtered audit trail. Startup owners and administrators only.",
)
@limiter.limit("5/minute")
def export_audit(
    request: Request,
    room_id: int,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
) -> StreamingResponse:
    """Export the room's audit trail."""
    user, member = _actor(user_or_member)
    access = svc.resolve_access(db, deal_room_id=room_id, user=user, member=member)
    svc.require_manager(access)

    query = db.query(DealRoomAuditEvent).filter(DealRoomAuditEvent.deal_room_id == room_id)
    if date_from is not None:
        query = query.filter(DealRoomAuditEvent.created_at >= date_from)
    if date_to is not None:
        query = query.filter(DealRoomAuditEvent.created_at <= date_to)
    rows = query.order_by(DealRoomAuditEvent.created_at.desc()).limit(50_000).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["timestamp", "actor_email", "actor_role", "action", "resource_type", "resource_id", "ip", "detail"]
    )
    for row in rows:
        writer.writerow(
            [
                row.created_at.isoformat() if row.created_at else "",
                row.actor_email or "",
                row.actor_role or "",
                row.action,
                row.resource_type or "",
                row.resource_id if row.resource_id is not None else "",
                row.ip or "",
                row.meta or "",
            ]
        )
    buffer.seek(0)

    stamp = datetime.utcnow().strftime("%Y%m%d")
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="deal-room-{room_id}-audit-{stamp}.csv"',
            "Cache-Control": "no-store, private",
        },
    )
