"""Authorization and shaping for Deal Room marketplace posts.

The private data room resolves every request through
``backend.services.dealroom.resolve_access``. The board is a different problem:
its content is deliberately visible to the whole signed-in community, so the
question is not "may you see this room?" but "is this yours to change?".

Three rules carry the whole surface, and every route composes them rather than
comparing ids inline:

``resolve_actor``      who is calling, as a member id plus an admin flag
``assert_can_manage``  the caller authored this post, or administers the platform
``verify_attribution`` the caller may actually speak for the entity they named

Nothing here trusts an author id, entity id or status sent by a client.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.post_taxonomy import (
    HIDDEN_MODERATION_STATUSES,
    STATUS_ARCHIVED,
    STATUS_CLOSED,
    STATUS_PUBLISHED,
    can_transition,
)
from backend.models import (
    DealRoom,
    DealRoomPost,
    DealRoomPostReport,
    DealRoomPostResponse,
    Incubator,
    Investor,
    MemberEntityLink,
    PulseMember,
    Startup,
    User,
)

# Entity tables a post may be attributed to, with the column holding the
# display name. Kept as data so adding a type is one line, not a new branch.
_ENTITY_TABLES: dict[str, tuple[Any, Any]] = {
    "startup": (Startup.startup_id, Startup.startup_name),
    "investor": (Investor.investor_id, Investor.investor_name),
    # The incubator table's display column is "Incubator", mapped as `incubator`.
    "incubator": (Incubator.incubator_id, Incubator.incubator),
}


@dataclass
class PostActor:
    """The resolved identity behind a marketplace request."""

    member: PulseMember | None
    user: User | None

    @property
    def is_admin(self) -> bool:
        return self.user is not None and self.user.username == settings.ADMIN_USERNAME

    @property
    def member_id(self) -> int | None:
        return self.member.id if self.member else None

    @property
    def is_authenticated(self) -> bool:
        return self.member is not None or self.user is not None

    @property
    def email(self) -> str:
        if self.member is not None:
            return (self.member.email or "").strip().lower()
        if self.user is not None:
            return (self.user.email or "").strip().lower()
        return ""

    @property
    def display_name(self) -> str:
        if self.member is not None:
            return self.member.full_name or ""
        return getattr(self.user, "username", "") or ""


def resolve_actor(user_or_member: tuple[User | None, PulseMember | None]) -> PostActor:
    """Return the caller as a :class:`PostActor`, without requiring a session."""
    user, member = user_or_member
    return PostActor(member=member, user=user)


def require_member(actor: PostActor) -> PulseMember:
    """Return the calling member, or refuse.

    Authoring, responding and reporting are all member actions: they attach to a
    ``pulse_members`` row, which the platform administrator does not have. The
    admin moderates the board rather than participating in it.
    """
    if actor.member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only community members can do this. Sign in with a member account.",
        )
    if not actor.member.is_confirmed:
        # An unconfirmed address cannot receive the replies a post invites, so
        # posting from one would strand every responder.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Confirm your email address before posting to the Deal Room",
        )
    return actor.member


def require_admin(actor: PostActor) -> User:
    """Return the calling administrator, or refuse."""
    if not actor.is_admin or actor.user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return actor.user


# ---------------------------------------------------------------------------
# Visibility
# ---------------------------------------------------------------------------
def visible_posts_filter(actor: PostActor) -> Any:
    """Return the predicate limiting a board query to what this caller may list.

    Everyone sees published and closed posts that have not been removed. Closed
    is included deliberately: a raise that has just been filled must still open
    from the link in someone's inbox, so the reader can see *why* their thread
    went quiet rather than hitting a 404. The board narrows further to published
    on its own, so a closed post is reachable but never browsable.

    An author additionally sees their own drafts and archived posts, so the same
    query backs both the board and the "my posts" view without a second code
    path that could disagree with it. The administrator sees everything, which
    is what makes the moderation queue work.
    """
    if actor.is_admin:
        return DealRoomPost.id.isnot(None)

    public = DealRoomPost.status.in_((STATUS_PUBLISHED, STATUS_CLOSED)) & (
        DealRoomPost.moderation_status.notin_(tuple(HIDDEN_MODERATION_STATUSES))
    )
    if actor.member_id is None:
        return public
    return or_(public, DealRoomPost.author_member_id == actor.member_id)


def load_post(db: Session, post_id: int, actor: PostActor) -> DealRoomPost:
    """Load one post the caller is allowed to see, or 404.

    A post the caller may not see is reported absent rather than forbidden: the
    two are indistinguishable on purpose, so a removed post cannot be confirmed
    to still exist by whoever had it removed.
    """
    post = (
        db.query(DealRoomPost)
        .filter(DealRoomPost.id == post_id, visible_posts_filter(actor))
        .first()
    )
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


def can_manage(post: DealRoomPost, actor: PostActor) -> bool:
    """Return True if the caller may edit, retitle, close or delete this post."""
    if actor.is_admin:
        return True
    return actor.member_id is not None and post.author_member_id == actor.member_id


def assert_can_manage(post: DealRoomPost, actor: PostActor) -> None:
    """Raise unless the caller owns this post."""
    if not can_manage(post, actor):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the author can change this post",
        )


def assert_transition(post: DealRoomPost, target: str) -> None:
    """Raise unless the lifecycle move is legal from the post's current state."""
    if post.status == target:
        return
    if not can_transition(post.status, target):
        article = "An" if post.status[:1] in "aeiou" else "A"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{article} {post.status} post cannot be moved to {target}",
        )


def apply_transition(post: DealRoomPost, target: str) -> None:
    """Move a post to ``target``, stamping the matching timestamp."""
    assert_transition(post, target)
    now = datetime.utcnow()
    if target == STATUS_PUBLISHED:
        # published_at is set on the first publish only, so re-opening a closed
        # post does not jump it back to the top of a newest-first board.
        if post.published_at is None:
            post.published_at = now
        post.closed_at = None
    elif target == STATUS_ARCHIVED:
        post.closed_at = post.closed_at or now
    else:
        post.closed_at = now
    post.status = target
    post.updated_at = now


# ---------------------------------------------------------------------------
# Entity attribution
# ---------------------------------------------------------------------------
def owned_entity_ids(db: Session, member: PulseMember | None, entity_type: str) -> set[int]:
    """Return ids of ``entity_type`` this member holds an approved claim on."""
    if member is None:
        return set()
    rows = (
        db.query(MemberEntityLink.entity_id)
        .filter(
            MemberEntityLink.member_id == member.id,
            MemberEntityLink.entity_type == entity_type,
            MemberEntityLink.status == "approved",
        )
        .all()
    )
    return {row[0] for row in rows}


def verify_attribution(
    db: Session, actor: PostActor, entity_type: str | None, entity_id: int | None
) -> str | None:
    """Return the entity's display name, or raise if the caller cannot claim it.

    Posting "on behalf of Acme" is a statement other members will rely on, so it
    is checked against ``member_entity_links`` exactly the way deal room
    ownership is. An unverified pair is refused rather than silently dropped:
    saving the post without the attribution the author asked for would publish
    something they did not write.
    """
    if entity_type is None or entity_id is None:
        return None

    columns = _ENTITY_TABLES.get(entity_type)
    if columns is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported entity type"
        )

    # The administrator may attribute freely; they are not claiming to be the
    # entity, they are curating on its behalf.
    if not actor.is_admin and entity_id not in owned_entity_ids(db, actor.member, entity_type):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"You do not have an approved claim on this {entity_type}. "
                "Claim it from its profile page first."
            ),
        )

    id_column, name_column = columns
    row = db.query(name_column).filter(id_column == entity_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
    return row[0]


def verify_deal_room(db: Session, actor: PostActor, deal_room_id: int | None) -> int | None:
    """Return the deal room id if the caller may advertise it, else raise.

    Attaching a data room to a post tells readers where the documents are. Only
    the room's owner may do that; otherwise a post could point traffic at
    somebody else's private room.
    """
    if deal_room_id is None:
        return None
    room = db.query(DealRoom).filter(DealRoom.id == deal_room_id).first()
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal room not found")
    if actor.is_admin:
        return room.id
    if room.startup_id not in owned_entity_ids(db, actor.member, "startup"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only link a deal room you manage",
        )
    return room.id


# ---------------------------------------------------------------------------
# Shaping
# ---------------------------------------------------------------------------
def split_tags(raw: str | None) -> list[str]:
    """Return the display tags for a post, de-duplicated and trimmed."""
    if not raw:
        return []
    seen: set[str] = set()
    tags: list[str] = []
    for chunk in raw.split(","):
        tag = chunk.strip()
        key = tag.lower()
        if tag and key not in seen:
            seen.add(key)
            tags.append(tag)
    return tags[:12]


def normalise_tags(raw: str | None) -> str | None:
    """Return the canonical stored form of a tag string."""
    tags = split_tags(raw)
    return ", ".join(tags) if tags else None


def author_directory(db: Session, member_ids: list[int]) -> dict[int, PulseMember]:
    """Return {member_id: PulseMember} for a page of posts, in one query."""
    unique = {mid for mid in member_ids if mid is not None}
    if not unique:
        return {}
    return {
        member.id: member
        for member in db.query(PulseMember).filter(PulseMember.id.in_(unique)).all()
    }


def responded_post_ids(db: Session, member_id: int | None, post_ids: list[int]) -> set[int]:
    """Return which of these posts the member has already responded to.

    One query for the whole page. Without it the board would either omit the
    "already contacted" state or issue a query per card.
    """
    if member_id is None or not post_ids:
        return set()
    rows = (
        db.query(DealRoomPostResponse.post_id)
        .filter(
            DealRoomPostResponse.post_id.in_(post_ids),
            DealRoomPostResponse.responder_member_id == member_id,
        )
        .all()
    )
    return {row[0] for row in rows}


def open_report_count(db: Session, post_id: int) -> int:
    """Return how many unreviewed reports stand against a post."""
    return (
        db.query(func.count(DealRoomPostReport.id))
        .filter(DealRoomPostReport.post_id == post_id, DealRoomPostReport.status == "open")
        .scalar()
        or 0
    )


def sync_response_count(db: Session, post: DealRoomPost) -> None:
    """Recompute a post's response counter from the rows that back it.

    The counter is denormalised so the board can sort and display without a
    join, which means it can drift if a response is ever deleted. Recomputing
    rather than incrementing keeps the displayed number honest.
    """
    post.response_count = (
        db.query(func.count(DealRoomPostResponse.id))
        .filter(DealRoomPostResponse.post_id == post.id)
        .scalar()
        or 0
    )


__all__ = [
    "PostActor",
    "apply_transition",
    "assert_can_manage",
    "assert_transition",
    "author_directory",
    "can_manage",
    "load_post",
    "normalise_tags",
    "open_report_count",
    "owned_entity_ids",
    "require_admin",
    "require_member",
    "resolve_actor",
    "responded_post_ids",
    "split_tags",
    "sync_response_count",
    "verify_attribution",
    "verify_deal_room",
    "visible_posts_filter",
]
