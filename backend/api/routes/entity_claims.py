"""Member-to-entity claims: the identity bridge behind startup-scoped access.

``PulseMember.role`` is free text captured at onboarding, so it cannot prove
*which* startup someone speaks for. A member claims an entity here; an
administrator approves it; only then does any startup-scoped feature treat them
as its owner. Nothing grants itself.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from backend.api.deps import AdminUserDep, UserOrMemberDep, get_db
from backend.api.limiter import limiter
from backend.core.config import settings
from backend.models import Incubator, Investor, MemberEntityLink, PulseMember, Startup
from backend.schemas_dealroom import (
    EntityClaimCreate,
    EntityClaimDecision,
    EntityClaimItem,
)

router = APIRouter(prefix="/entity-claims", tags=["entity-claims"])

DbDep = Annotated[Session, Depends(get_db)]

_ENTITY_LOADERS = {
    "startup": (Startup, Startup.startup_id, "startup_name"),
    "investor": (Investor, Investor.investor_id, "investor_name"),
    "incubator": (Incubator, Incubator.incubator_id, "incubator"),
}


def _entity_name(db: Session, entity_type: str, entity_id: int) -> str | None:
    """Return the display name of a directory entity, or None if it is gone."""
    model, pk, name_field = _ENTITY_LOADERS[entity_type]
    row = db.query(model).filter(pk == entity_id).first()
    return getattr(row, name_field, None) if row else None


def _item(db: Session, link: MemberEntityLink, member: PulseMember | None = None) -> EntityClaimItem:
    """Serialise a claim with its member and entity names resolved."""
    if member is None:
        member = db.query(PulseMember).filter(PulseMember.id == link.member_id).first()
    return EntityClaimItem(
        id=link.id,
        member_id=link.member_id,
        member_email=member.email if member else None,
        member_name=member.full_name if member else None,
        entity_type=link.entity_type,
        entity_id=link.entity_id,
        entity_name=_entity_name(db, link.entity_type, link.entity_id),
        entity_role=link.entity_role,
        status=link.status,
        created_at=link.created_at,
        approved_at=link.approved_at,
    )


@router.post(
    "",
    response_model=EntityClaimItem,
    status_code=status.HTTP_201_CREATED,
    summary="Claim a directory entity",
    description=(
        "A member asserts that they represent a startup, investor or incubator. The claim "
        "starts as pending and confers nothing until an administrator approves it."
    ),
)
@limiter.limit("10/minute")
def create_claim(
    request: Request,
    data: EntityClaimCreate,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> EntityClaimItem:
    """Register a pending claim for the authenticated member."""
    _user, member = user_or_member
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only community members can claim a directory entity",
        )

    if _entity_name(db, data.entity_type, data.entity_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No {data.entity_type} with that id",
        )

    existing = (
        db.query(MemberEntityLink)
        .filter(
            MemberEntityLink.member_id == member.id,
            MemberEntityLink.entity_type == data.entity_type,
            MemberEntityLink.entity_id == data.entity_id,
        )
        .first()
    )
    if existing is not None:
        if existing.status in ("pending", "approved"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"You already have a {existing.status} claim on this entity",
            )
        # A previously rejected or revoked claim may be re-submitted, but it
        # re-enters review rather than resuming its old standing.
        existing.status = "pending"
        existing.approved_at = None
        existing.approved_by_user_id = None
        db.commit()
        db.refresh(existing)
        return _item(db, existing, member)

    link = MemberEntityLink(
        member_id=member.id,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        entity_role="owner",
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return _item(db, link, member)


@router.get(
    "/mine",
    response_model=list[EntityClaimItem],
    summary="List my claims",
    description="The authenticated member's own claims and their approval state.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_my_claims(
    request: Request,
    db: DbDep,
    user_or_member: UserOrMemberDep = (None, None),
) -> list[EntityClaimItem]:
    """Return the caller's claims."""
    _user, member = user_or_member
    if member is None:
        return []
    links = (
        db.query(MemberEntityLink)
        .filter(MemberEntityLink.member_id == member.id)
        .order_by(MemberEntityLink.created_at.desc())
        .all()
    )
    return [_item(db, link, member) for link in links]


@router.get(
    "/admin",
    response_model=list[EntityClaimItem],
    summary="Review entity claims",
    description="All claims across the platform, filterable by status. Administrators only.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_all_claims(
    request: Request,
    admin: AdminUserDep,
    db: DbDep,
    status_filter: str | None = Query(None, alias="status", max_length=20),
    entity_type: str | None = Query(None, max_length=20),
) -> list[EntityClaimItem]:
    """Return every claim for administrator review."""
    query = db.query(MemberEntityLink)
    if status_filter:
        query = query.filter(MemberEntityLink.status == status_filter)
    if entity_type:
        query = query.filter(MemberEntityLink.entity_type == entity_type)
    links = query.order_by(MemberEntityLink.created_at.desc()).limit(500).all()

    member_ids = [link.member_id for link in links]
    profiles = (
        {m.id: m for m in db.query(PulseMember).filter(PulseMember.id.in_(member_ids)).all()}
        if member_ids
        else {}
    )
    return [_item(db, link, profiles.get(link.member_id)) for link in links]


@router.post(
    "/admin/{claim_id}/decision",
    response_model=EntityClaimItem,
    summary="Decide an entity claim",
    description=(
        "Approve, reject or revoke a claim. Approving is what lets a member manage that "
        "entity's Deal Room; revoking withdraws it on the member's next request."
    ),
)
@limiter.limit("30/minute")
def decide_claim(
    request: Request,
    claim_id: int,
    data: EntityClaimDecision,
    admin: AdminUserDep,
    db: DbDep,
) -> EntityClaimItem:
    """Record an administrator's decision on a claim."""
    link = db.query(MemberEntityLink).filter(MemberEntityLink.id == claim_id).first()
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    if data.decision == "approve":
        link.status = "approved"
        link.approved_at = datetime.utcnow()
        link.approved_by_user_id = admin.user_id
    elif data.decision == "reject":
        link.status = "rejected"
        link.approved_at = None
    else:
        link.status = "revoked"
        link.approved_at = None

    db.commit()
    db.refresh(link)
    return _item(db, link)
