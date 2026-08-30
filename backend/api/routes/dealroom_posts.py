"""Deal Room opportunity marketplace.

The board where members say what they are looking for — capital, a co-founder,
an advisor, a partner — and where anyone can answer. It sits alongside the
private data rooms in ``dealroom.py`` and links to them: a post may advertise
its author's room, but reading the post never grants access to the room.

Responding is the seam with the inbox. ``POST /{id}/respond`` writes a
``DealRoomPostResponse`` *and* a ``DirectMessage`` in one transaction, so an
expression of interest becomes an ordinary conversation the author can continue
in their inbox. There is no second messaging system: the thread is keyed by the
same two email addresses as every other thread on the platform.

Every authorization decision resolves through ``backend.services.dealroom_posts``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, status
from sqlalchemy import asc, desc, func, or_
from sqlalchemy.orm import Session

from backend.api.deps import DbDep, OptionalUserOrMemberDep, UserOrMemberDep
from backend.api.limiter import limiter
from backend.core.config import settings
from backend.core.post_taxonomy import (
    COMMITMENT_LEVELS,
    COUNTERPARTY_TYPES,
    MODERATION_FLAGGED,
    MODERATION_REMOVED,
    MODERATION_VISIBLE,
    POST_TYPES,
    REPORT_REASONS,
    STATUS_ARCHIVED,
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    SUGGESTED_STAGES,
)
from backend.models import (
    DealRoomPost,
    DealRoomPostReport,
    DealRoomPostResponse,
    DirectMessage,
    PulseMember,
)
from backend.schemas import PaginatedResponse
from backend.schemas_dealroom_posts import (
    DealRoomPostCreate,
    DealRoomPostDetail,
    DealRoomPostListItem,
    DealRoomPostStatusChange,
    DealRoomPostUpdate,
    PostAuthor,
    PostMeta,
    PostMetaOption,
    PostModerationAction,
    PostReportCreate,
    PostReportItem,
    PostResponseCreate,
    PostResponseCreated,
    PostResponseDecision,
    PostResponseItem,
)
from backend.services import dealroom_posts as svc

router = APIRouter(prefix="/deal-room-posts", tags=["deal-room-marketplace"])


# ---------------------------------------------------------------------------
# Shaping helpers
# ---------------------------------------------------------------------------
def _author_block(post: DealRoomPost, member: PulseMember | None) -> PostAuthor:
    """Return the public author block for a post."""
    return PostAuthor(
        member_id=post.author_member_id,
        full_name=member.full_name if member else None,
        role=member.role if member else None,
        profile_pic=member.profile_pic if member else None,
        entity_type=post.entity_type,
        entity_id=post.entity_id,
        entity_name=post.entity_name,
    )


def _list_item(
    post: DealRoomPost,
    member: PulseMember | None,
    *,
    responded: bool,
    can_manage: bool,
) -> DealRoomPostListItem:
    return DealRoomPostListItem(
        id=post.id,
        post_type=post.post_type,
        title=post.title,
        summary=post.summary,
        counterparty_type=post.counterparty_type,
        sector=post.sector,
        stage=post.stage,
        location=post.location,
        amount_min=post.amount_min,
        amount_max=post.amount_max,
        currency=post.currency,
        commitment=post.commitment,
        deadline=post.deadline,
        tags=svc.split_tags(post.tags),
        status=post.status,
        moderation_status=post.moderation_status,
        view_count=post.view_count or 0,
        response_count=post.response_count or 0,
        created_at=post.created_at,
        published_at=post.published_at,
        author=_author_block(post, member),
        responded_by_me=responded,
        can_manage=can_manage,
        has_deal_room=post.deal_room_id is not None,
    )


def _detail(
    post: DealRoomPost,
    member: PulseMember | None,
    *,
    responded: bool,
    can_manage: bool,
    open_reports: int | None,
) -> DealRoomPostDetail:
    base = _list_item(post, member, responded=responded, can_manage=can_manage)
    return DealRoomPostDetail(
        **base.model_dump(),
        details=post.details,
        looking_for=post.looking_for,
        equity_offered=post.equity_offered,
        deal_room_id=post.deal_room_id,
        moderation_note=post.moderation_note if can_manage else None,
        updated_at=post.updated_at,
        closed_at=post.closed_at,
        open_report_count=open_reports,
    )


def _page(
    db: Session,
    query: Any,
    actor: svc.PostActor,
    page: int,
    page_size: int,
) -> PaginatedResponse[DealRoomPostListItem]:
    """Materialise a board page: count, slice, then enrich in two queries."""
    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()

    directory = svc.author_directory(db, [p.author_member_id for p in rows])
    responded = svc.responded_post_ids(db, actor.member_id, [p.id for p in rows])

    items = [
        _list_item(
            post,
            directory.get(post.author_member_id),
            responded=post.id in responded,
            can_manage=svc.can_manage(post, actor),
        )
        for post in rows
    ]
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


def _like(term: str) -> str:
    """Return a LIKE pattern treating the caller's term as literal text.

    Same reasoning as the inbox search: unescaped, ``%`` matches everything and
    turns the filter off.
    """
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped.lower()}%"


def _apply_write_fields(
    post: DealRoomPost, data: DealRoomPostCreate | DealRoomPostUpdate, *, partial: bool
) -> None:
    """Copy the client-settable fields onto a post.

    ``partial`` distinguishes a PATCH, where an absent key means "leave it
    alone", from a create, where every field is present. Without the
    ``exclude_unset`` pass a PATCH would blank every field the client omitted.
    """
    payload = data.model_dump(exclude_unset=partial)
    for field in (
        "post_type",
        "title",
        "summary",
        "details",
        "looking_for",
        "counterparty_type",
        "sector",
        "stage",
        "location",
        "amount_min",
        "amount_max",
        "currency",
        "equity_offered",
        "commitment",
        "deadline",
    ):
        if field in payload:
            value = payload[field]
            if isinstance(value, str):
                value = value.strip() or None
            setattr(post, field, value)
    if "tags" in payload:
        post.tags = svc.normalise_tags(payload["tags"])


# ---------------------------------------------------------------------------
# Filter vocabulary
# ---------------------------------------------------------------------------
@router.get(
    "/meta",
    response_model=PostMeta,
    summary="Filter and composer vocabulary",
    description=(
        "The value lists the composer and the board's filter bar render. Fixed "
        "vocabularies come from the server's taxonomy; sectors, stages and locations "
        "are derived from the posts that actually exist, so a filter never offers a "
        "value that would return nothing."
    ),
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def post_meta(request: Request, db: DbDep) -> PostMeta:
    """Return everything a client needs to render the board's controls."""

    def facet(column: Any) -> list[PostMetaOption]:
        rows = (
            db.query(column, func.count(DealRoomPost.id))
            .filter(
                DealRoomPost.status == STATUS_PUBLISHED,
                DealRoomPost.moderation_status != MODERATION_REMOVED,
                column.isnot(None),
                column != "",
            )
            .group_by(column)
            .order_by(desc(func.count(DealRoomPost.id)))
            .limit(40)
            .all()
        )
        return [PostMetaOption(value=value, count=count) for value, count in rows]

    return PostMeta(
        post_types=list(POST_TYPES),
        counterparty_types=list(COUNTERPARTY_TYPES),
        commitment_levels=list(COMMITMENT_LEVELS),
        suggested_stages=list(SUGGESTED_STAGES),
        report_reasons=list(REPORT_REASONS),
        sectors=facet(DealRoomPost.sector),
        stages=facet(DealRoomPost.stage),
        locations=facet(DealRoomPost.location),
        type_counts=facet(DealRoomPost.post_type),
    )


# ---------------------------------------------------------------------------
# The board
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=PaginatedResponse[DealRoomPostListItem],
    summary="Browse opportunities",
    description=(
        "The public board: published, unremoved posts, newest first. Each card reports "
        "whether the signed-in caller has already responded."
    ),
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_posts(
    request: Request,
    db: DbDep,
    actor_dep: OptionalUserOrMemberDep = (None, None),
    q: str | None = Query(None, max_length=160, description="Free text over title, summary, details"),
    post_type: str | None = Query(None, max_length=40),
    counterparty_type: str | None = Query(None, max_length=40),
    sector: str | None = Query(None, max_length=120),
    stage: str | None = Query(None, max_length=60),
    location: str | None = Query(None, max_length=120),
    amount_min: float | None = Query(None, ge=0, description="Only posts whose range reaches this"),
    amount_max: float | None = Query(
        None, ge=0, description="Only posts whose range starts below this"
    ),
    has_deal_room: bool | None = Query(None),
    sort: str = Query("recent", pattern="^(recent|responses|views|deadline)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginatedResponse[DealRoomPostListItem]:
    """Return a filtered page of the opportunity board."""
    actor = svc.resolve_actor(actor_dep)

    query = db.query(DealRoomPost).filter(svc.visible_posts_filter(actor))
    # Someone browsing the board wants live opportunities. An author's own
    # drafts are reachable through /mine, not mixed into everyone's feed.
    query = query.filter(DealRoomPost.status == STATUS_PUBLISHED)

    if q and q.strip():
        needle = _like(q.strip())
        query = query.filter(
            or_(
                func.lower(DealRoomPost.title).like(needle, escape="\\"),
                func.lower(DealRoomPost.summary).like(needle, escape="\\"),
                func.lower(DealRoomPost.details).like(needle, escape="\\"),
                func.lower(DealRoomPost.tags).like(needle, escape="\\"),
                func.lower(DealRoomPost.entity_name).like(needle, escape="\\"),
            )
        )
    if post_type:
        query = query.filter(DealRoomPost.post_type == post_type)
    if counterparty_type:
        # "any" posts welcome everyone, so they match every counterparty filter.
        query = query.filter(
            or_(
                DealRoomPost.counterparty_type == counterparty_type,
                DealRoomPost.counterparty_type == "any",
            )
        )
    if sector:
        query = query.filter(func.lower(DealRoomPost.sector).like(_like(sector), escape="\\"))
    if stage:
        query = query.filter(DealRoomPost.stage == stage)
    if location:
        query = query.filter(func.lower(DealRoomPost.location).like(_like(location), escape="\\"))
    if has_deal_room is not None:
        query = query.filter(
            DealRoomPost.deal_room_id.isnot(None)
            if has_deal_room
            else DealRoomPost.deal_room_id.is_(None)
        )
    # Range overlap, not containment: a post asking 1-5M matches a search for
    # "at least 3M" because the ranges intersect. A post with no figures is not
    # excluded by an amount filter, since absence is not a mismatch.
    if amount_min is not None:
        query = query.filter(
            or_(DealRoomPost.amount_max.is_(None), DealRoomPost.amount_max >= amount_min)
        )
    if amount_max is not None:
        query = query.filter(
            or_(DealRoomPost.amount_min.is_(None), DealRoomPost.amount_min <= amount_max)
        )

    order = {
        "recent": (desc(DealRoomPost.published_at), desc(DealRoomPost.id)),
        "responses": (desc(DealRoomPost.response_count), desc(DealRoomPost.id)),
        "views": (desc(DealRoomPost.view_count), desc(DealRoomPost.id)),
        # Soonest real deadline first; undated posts sort last rather than
        # occupying the top of a deadline view.
        "deadline": (asc(DealRoomPost.deadline).nullslast(), desc(DealRoomPost.id)),
    }[sort]
    query = query.order_by(*order)

    return _page(db, query, actor, page, page_size)


@router.get(
    "/mine",
    response_model=PaginatedResponse[DealRoomPostListItem],
    summary="My opportunities",
    description="Every post the caller has authored, in any state, including drafts.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def my_posts(
    request: Request,
    db: DbDep,
    actor_dep: UserOrMemberDep = (None, None),
    status_filter: str | None = Query(None, alias="status", max_length=20),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginatedResponse[DealRoomPostListItem]:
    """Return the caller's own posts."""
    actor = svc.resolve_actor(actor_dep)
    member = svc.require_member(actor)

    query = db.query(DealRoomPost).filter(DealRoomPost.author_member_id == member.id)
    if status_filter:
        query = query.filter(DealRoomPost.status == status_filter)
    query = query.order_by(desc(DealRoomPost.updated_at), desc(DealRoomPost.id))
    return _page(db, query, actor, page, page_size)


@router.get(
    "/{post_id}",
    response_model=DealRoomPostDetail,
    summary="Open an opportunity",
    description=(
        "The full post. Viewing increments the post's counter once per request, except "
        "for the author's own visits, which would otherwise inflate their own metrics."
    ),
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def get_post(
    request: Request,
    post_id: int,
    db: DbDep,
    actor_dep: OptionalUserOrMemberDep = (None, None),
) -> DealRoomPostDetail:
    """Return one post."""
    actor = svc.resolve_actor(actor_dep)
    post = svc.load_post(db, post_id, actor)

    manageable = svc.can_manage(post, actor)
    if not manageable:
        post.view_count = (post.view_count or 0) + 1
        db.commit()
        db.refresh(post)

    author = db.query(PulseMember).filter(PulseMember.id == post.author_member_id).first()
    responded = bool(svc.responded_post_ids(db, actor.member_id, [post.id]))
    return _detail(
        post,
        author,
        responded=responded,
        can_manage=manageable,
        open_reports=svc.open_report_count(db, post.id) if manageable else None,
    )


# ---------------------------------------------------------------------------
# Authoring
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=DealRoomPostDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create an opportunity",
    description=(
        "Any confirmed community member may post. Entity attribution and any linked "
        "deal room are verified against the author's approved claims, so a post can "
        "never speak for a company the author does not represent."
    ),
)
@limiter.limit("10/minute")
def create_post(
    request: Request,
    data: DealRoomPostCreate,
    db: DbDep,
    actor_dep: UserOrMemberDep = (None, None),
) -> DealRoomPostDetail:
    """Create a post, as a draft unless the author asked to publish immediately."""
    actor = svc.resolve_actor(actor_dep)
    member = svc.require_member(actor)

    entity_name = svc.verify_attribution(db, actor, data.entity_type, data.entity_id)
    deal_room_id = svc.verify_deal_room(db, actor, data.deal_room_id)

    now = datetime.utcnow()
    post = DealRoomPost(
        author_member_id=member.id,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        entity_name=entity_name,
        deal_room_id=deal_room_id,
        status=STATUS_PUBLISHED if data.publish else STATUS_DRAFT,
        moderation_status=MODERATION_VISIBLE,
        published_at=now if data.publish else None,
        view_count=0,
        response_count=0,
        created_at=now,
        updated_at=now,
    )
    _apply_write_fields(post, data, partial=False)

    db.add(post)
    db.commit()
    db.refresh(post)
    return _detail(post, member, responded=False, can_manage=True, open_reports=0)


@router.patch(
    "/{post_id}",
    response_model=DealRoomPostDetail,
    summary="Edit an opportunity",
    description="Author or administrator only. Status changes go through /status.",
)
@limiter.limit("30/minute")
def update_post(
    request: Request,
    post_id: int,
    data: DealRoomPostUpdate,
    db: DbDep,
    actor_dep: UserOrMemberDep = (None, None),
) -> DealRoomPostDetail:
    """Apply a partial edit to a post."""
    actor = svc.resolve_actor(actor_dep)
    post = svc.load_post(db, post_id, actor)
    svc.assert_can_manage(post, actor)

    if post.status == STATUS_ARCHIVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An archived post cannot be edited",
        )

    payload = data.model_dump(exclude_unset=True)
    if "entity_type" in payload or "entity_id" in payload:
        entity_type = payload.get("entity_type", post.entity_type)
        entity_id = payload.get("entity_id", post.entity_id)
        if (entity_type is None) != (entity_id is None):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="entity_type and entity_id must be provided together",
            )
        post.entity_name = svc.verify_attribution(db, actor, entity_type, entity_id)
        post.entity_type = entity_type
        post.entity_id = entity_id
    if "deal_room_id" in payload:
        post.deal_room_id = svc.verify_deal_room(db, actor, payload["deal_room_id"])

    _apply_write_fields(post, data, partial=True)

    # Cross-field coherence has to be re-checked against the merged row: a PATCH
    # that sends only amount_min can still invert a range the create validated.
    if (
        post.amount_min is not None
        and post.amount_max is not None
        and post.amount_min > post.amount_max
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="amount_min cannot be greater than amount_max",
        )

    post.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(post)

    author = db.query(PulseMember).filter(PulseMember.id == post.author_member_id).first()
    return _detail(
        post,
        author,
        responded=False,
        can_manage=True,
        open_reports=svc.open_report_count(db, post.id),
    )


@router.post(
    "/{post_id}/status",
    response_model=DealRoomPostDetail,
    summary="Publish, close or archive",
    description=(
        "Moves a post through its lifecycle. Illegal transitions are refused: a "
        "published post cannot return to draft, and an archived post is terminal."
    ),
)
@limiter.limit("30/minute")
def change_status(
    request: Request,
    post_id: int,
    data: DealRoomPostStatusChange,
    db: DbDep,
    actor_dep: UserOrMemberDep = (None, None),
) -> DealRoomPostDetail:
    """Change a post's lifecycle state."""
    actor = svc.resolve_actor(actor_dep)
    post = svc.load_post(db, post_id, actor)
    svc.assert_can_manage(post, actor)

    if post.moderation_status == MODERATION_REMOVED and not actor.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This post was removed by a moderator and cannot be republished",
        )

    svc.apply_transition(post, data.status)
    db.commit()
    db.refresh(post)

    author = db.query(PulseMember).filter(PulseMember.id == post.author_member_id).first()
    return _detail(
        post,
        author,
        responded=False,
        can_manage=True,
        open_reports=svc.open_report_count(db, post.id),
    )


@router.delete(
    "/{post_id}",
    summary="Delete an opportunity",
    description=(
        "Deletes a draft outright. A post that has already been published is archived "
        "instead, because people may be mid-conversation about it and their message "
        "threads must keep making sense."
    ),
)
@limiter.limit("20/minute")
def delete_post(
    request: Request,
    post_id: int,
    db: DbDep,
    actor_dep: UserOrMemberDep = (None, None),
) -> dict[str, Any]:
    """Delete or archive a post depending on whether anyone has seen it."""
    actor = svc.resolve_actor(actor_dep)
    post = svc.load_post(db, post_id, actor)
    svc.assert_can_manage(post, actor)

    if post.status == STATUS_DRAFT and (post.response_count or 0) == 0:
        db.delete(post)
        db.commit()
        return {"deleted": True, "archived": False, "id": post_id}

    post.status = STATUS_ARCHIVED
    post.closed_at = post.closed_at or datetime.utcnow()
    post.updated_at = datetime.utcnow()
    db.commit()
    return {"deleted": False, "archived": True, "id": post_id}


# ---------------------------------------------------------------------------
# Responding — the bridge into the inbox
# ---------------------------------------------------------------------------
@router.post(
    "/{post_id}/respond",
    response_model=PostResponseCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Respond to an opportunity",
    description=(
        "Registers interest and opens a direct message thread with the author in the "
        "same transaction. The conversation is an ordinary inbox thread, so the author "
        "answers it where they answer everything else. One response per member per post."
    ),
)
@limiter.limit("10/minute")
def respond_to_post(
    request: Request,
    post_id: int,
    data: PostResponseCreate,
    db: DbDep,
    actor_dep: UserOrMemberDep = (None, None),
) -> PostResponseCreated:
    """Express interest in a post and start the conversation."""
    actor = svc.resolve_actor(actor_dep)
    member = svc.require_member(actor)
    post = svc.load_post(db, post_id, actor)

    if post.author_member_id == member.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot respond to your own post",
        )
    if post.status != STATUS_PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This opportunity is no longer open for responses",
        )
    if post.moderation_status == MODERATION_REMOVED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    existing = (
        db.query(DealRoomPostResponse)
        .filter(
            DealRoomPostResponse.post_id == post.id,
            DealRoomPostResponse.responder_member_id == member.id,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already responded to this opportunity",
        )

    author = db.query(PulseMember).filter(PulseMember.id == post.author_member_id).first()
    if author is None or not author.email:
        # The author's account is gone or unusable, so there is nowhere to send
        # the message. Recording interest that reaches nobody would be a lie.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This post's author can no longer be contacted",
        )

    responder_email = (member.email or "").strip().lower()
    author_email = author.email.strip().lower()
    if responder_email == author_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot respond to your own post",
        )

    now = datetime.utcnow()
    response = DealRoomPostResponse(
        post_id=post.id,
        responder_member_id=member.id,
        message=data.message,
        status="pending",
        created_at=now,
    )
    db.add(response)

    # The message carries the post's title so the author can tell which of their
    # opportunities it answers without leaving the inbox.
    body = f'Re: "{post.title}"\n\n{data.message}'
    db.add(
        DirectMessage(
            to_name=author.full_name,
            to_email=author_email,
            from_name=member.full_name,
            from_email=responder_email,
            message=body,
            is_read=False,
            created_at=now,
        )
    )

    db.flush()
    svc.sync_response_count(db, post)
    post.updated_at = now
    db.commit()
    db.refresh(response)

    return PostResponseCreated(
        response=PostResponseItem(
            id=response.id,
            post_id=post.id,
            responder=PostAuthor(
                member_id=member.id,
                full_name=member.full_name,
                role=member.role,
                profile_pic=member.profile_pic,
            ),
            message=response.message,
            status=response.status,
            created_at=response.created_at,
        ),
        partner_email=author_email,
        partner_name=author.full_name,
    )


@router.get(
    "/{post_id}/responses",
    response_model=list[PostResponseItem],
    summary="Who responded",
    description=(
        "The author's view of everyone who expressed interest. Author or administrator only."
    ),
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_responses(
    request: Request,
    post_id: int,
    db: DbDep,
    actor_dep: UserOrMemberDep = (None, None),
    status_filter: str | None = Query(None, alias="status", max_length=20),
) -> list[PostResponseItem]:
    """Return the responses to one post."""
    actor = svc.resolve_actor(actor_dep)
    post = svc.load_post(db, post_id, actor)
    # Responders are not shown to each other: one investor's interest in a raise
    # is not the business of the next investor to open the post.
    svc.assert_can_manage(post, actor)

    query = db.query(DealRoomPostResponse).filter(DealRoomPostResponse.post_id == post.id)
    if status_filter:
        query = query.filter(DealRoomPostResponse.status == status_filter)
    rows = query.order_by(desc(DealRoomPostResponse.created_at)).all()
    if not rows:
        return []

    directory = svc.author_directory(db, [r.responder_member_id for r in rows])
    items: list[PostResponseItem] = []
    for row in rows:
        who = directory.get(row.responder_member_id)
        items.append(
            PostResponseItem(
                id=row.id,
                post_id=row.post_id,
                responder=PostAuthor(
                    member_id=row.responder_member_id,
                    full_name=who.full_name if who else None,
                    role=who.role if who else None,
                    profile_pic=who.profile_pic if who else None,
                ),
                message=row.message,
                status=row.status,
                created_at=row.created_at,
                decided_at=row.decided_at,
            )
        )
    return items


@router.post(
    "/{post_id}/responses/{response_id}/decision",
    response_model=PostResponseItem,
    summary="Accept or decline a response",
    description=(
        "Marks a response for the author's own tracking. It sends nothing: the "
        "conversation already exists in the inbox and is where the author replies."
    ),
)
@limiter.limit("30/minute")
def decide_response(
    request: Request,
    post_id: int,
    response_id: int,
    data: PostResponseDecision,
    db: DbDep,
    actor_dep: UserOrMemberDep = (None, None),
) -> PostResponseItem:
    """Record the author's disposition of one response."""
    actor = svc.resolve_actor(actor_dep)
    post = svc.load_post(db, post_id, actor)
    svc.assert_can_manage(post, actor)

    response = (
        db.query(DealRoomPostResponse)
        .filter(
            DealRoomPostResponse.id == response_id,
            DealRoomPostResponse.post_id == post.id,
        )
        .first()
    )
    if response is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Response not found")

    response.status = data.status
    response.decided_at = datetime.utcnow()
    db.commit()
    db.refresh(response)

    responder = (
        db.query(PulseMember).filter(PulseMember.id == response.responder_member_id).first()
    )
    return PostResponseItem(
        id=response.id,
        post_id=response.post_id,
        responder=PostAuthor(
            member_id=response.responder_member_id,
            full_name=responder.full_name if responder else None,
            role=responder.role if responder else None,
            profile_pic=responder.profile_pic if responder else None,
        ),
        message=response.message,
        status=response.status,
        created_at=response.created_at,
        decided_at=response.decided_at,
    )


# ---------------------------------------------------------------------------
# Reporting and moderation
# ---------------------------------------------------------------------------
@router.post(
    "/{post_id}/report",
    status_code=status.HTTP_201_CREATED,
    summary="Report an opportunity",
    description=(
        "Flags a post for moderator review. Reporting does not hide the post: "
        "suppression on an unreviewed accusation would make this a censorship button."
    ),
)
@limiter.limit("10/minute")
def report_post(
    request: Request,
    post_id: int,
    data: PostReportCreate,
    db: DbDep,
    actor_dep: UserOrMemberDep = (None, None),
) -> dict[str, Any]:
    """Record a report against a post."""
    actor = svc.resolve_actor(actor_dep)
    member = svc.require_member(actor)
    post = svc.load_post(db, post_id, actor)

    if post.author_member_id == member.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot report your own post",
        )

    existing = (
        db.query(DealRoomPostReport)
        .filter(
            DealRoomPostReport.post_id == post.id,
            DealRoomPostReport.reporter_member_id == member.id,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reported this post",
        )

    db.add(
        DealRoomPostReport(
            post_id=post.id,
            reporter_member_id=member.id,
            reason=data.reason,
            detail=data.detail,
            status="open",
            created_at=datetime.utcnow(),
        )
    )
    # Visible but marked, so moderators can find it and readers still judge it
    # for themselves until a human decides.
    if post.moderation_status == MODERATION_VISIBLE:
        post.moderation_status = MODERATION_FLAGGED
    db.commit()
    return {"reported": True, "post_id": post.id}


@router.get(
    "/admin/reports",
    response_model=PaginatedResponse[PostReportItem],
    summary="Moderation queue",
    description="Reports awaiting review. Administrators only.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_reports(
    request: Request,
    db: DbDep,
    actor_dep: UserOrMemberDep = (None, None),
    status_filter: str = Query("open", alias="status", max_length=20),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginatedResponse[PostReportItem]:
    """Return the moderation queue."""
    actor = svc.resolve_actor(actor_dep)
    svc.require_admin(actor)

    query = db.query(DealRoomPostReport)
    if status_filter and status_filter != "all":
        query = query.filter(DealRoomPostReport.status == status_filter)
    query = query.order_by(desc(DealRoomPostReport.created_at))

    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()

    posts = {
        p.id: p
        for p in db.query(DealRoomPost).filter(
            DealRoomPost.id.in_([r.post_id for r in rows] or [0])
        )
    }
    reporters = svc.author_directory(db, [r.reporter_member_id for r in rows])

    items: list[PostReportItem] = []
    for row in rows:
        post = posts.get(row.post_id)
        who = reporters.get(row.reporter_member_id)
        items.append(
            PostReportItem(
                id=row.id,
                post_id=row.post_id,
                post_title=post.title if post else None,
                reporter_member_id=row.reporter_member_id,
                reporter_name=who.full_name if who else None,
                reason=row.reason,
                detail=row.detail,
                status=row.status,
                created_at=row.created_at,
                reviewed_at=row.reviewed_at,
            )
        )
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.post(
    "/admin/{post_id}/moderate",
    response_model=DealRoomPostDetail,
    summary="Moderate an opportunity",
    description=(
        "Set a post's moderation state and optionally close its open reports. "
        "Administrators only."
    ),
)
@limiter.limit("30/minute")
def moderate_post(
    request: Request,
    post_id: int,
    data: PostModerationAction,
    db: DbDep,
    actor_dep: UserOrMemberDep = (None, None),
) -> DealRoomPostDetail:
    """Apply a moderator's decision to a post."""
    actor = svc.resolve_actor(actor_dep)
    user = svc.require_admin(actor)

    post = db.query(DealRoomPost).filter(DealRoomPost.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    now = datetime.utcnow()
    post.moderation_status = data.moderation_status
    post.moderation_note = data.note
    post.updated_at = now

    if data.resolve_reports:
        (
            db.query(DealRoomPostReport)
            .filter(DealRoomPostReport.post_id == post.id, DealRoomPostReport.status == "open")
            .update(
                {
                    "status": (
                        "actioned" if data.moderation_status == MODERATION_REMOVED else "dismissed"
                    ),
                    "reviewed_at": now,
                    "reviewed_by_user_id": user.user_id,
                },
                synchronize_session=False,
            )
        )

    db.commit()
    db.refresh(post)

    author = db.query(PulseMember).filter(PulseMember.id == post.author_member_id).first()
    return _detail(
        post,
        author,
        responded=False,
        can_manage=True,
        open_reports=svc.open_report_count(db, post.id),
    )
