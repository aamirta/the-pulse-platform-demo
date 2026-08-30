"""Admin API routes."""

from datetime import datetime
from io import StringIO
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.api.common import or_404
from backend.api.deps import AdminUserDep, get_db
from backend.api.limiter import limiter

# The list/detail serializers live with their public read routes; reused here so
# admin writes return exactly the same shape the directory pages already consume.
from backend.api.routes.founders import _to_detail as founder_to_detail
from backend.api.routes.funding_rounds import _to_detail as funding_round_to_detail
from backend.api.routes.incubators import _to_detail as incubator_to_detail
from backend.api.routes.investors import _to_detail as investor_to_detail
from backend.api.routes.members import _member_sort_clause
from backend.api.routes.startups import _to_detail as startup_to_detail
from backend.core.config import settings
from backend.core.security import generate_secure_token
from backend.models import (
    BadgeGeneration,
    Founder,
    FundingRound,
    Incubator,
    Investor,
    PulseMember,
    Startup,
)
from backend.schemas import (
    AdminMemberUpdate,
    BadgeGenerateRequest,
    BadgeGenerationResponse,
    BulkActionRequest,
    BulkActionResponse,
    FounderDetail,
    FounderWrite,
    FundingRoundDetail,
    FundingRoundWrite,
    IncubatorDetail,
    IncubatorWrite,
    InvestorDetail,
    InvestorWrite,
    PaginatedResponse,
    PulseMemberDetail,
    PulseMemberListItem,
    StartupDetail,
    StartupWrite,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/members",
    response_model=PaginatedResponse[PulseMemberListItem],
    summary="Admin member list",
    description="List all community members with admin privileges.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def admin_list_members(
    request: Request,
    admin: AdminUserDep,
    db: Session = Depends(get_db),
    role: str | None = None,
    is_confirmed: bool | None = None,
    search: str | None = None,
    sort_by: str = Query("created_at", description="Column to sort by"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginatedResponse[PulseMemberListItem]:
    """Return paginated members for admin management."""
    query = db.query(PulseMember)
    if role:
        query = query.filter(PulseMember.role.ilike(f"%{role}%"))
    if is_confirmed is not None:
        query = query.filter(PulseMember.is_confirmed == is_confirmed)
    if search:
        query = query.filter(
            (PulseMember.full_name.ilike(f"%{search}%"))
            | (PulseMember.email.ilike(f"%{search}%"))
            | (PulseMember.role.ilike(f"%{search}%"))
        )
    query = query.order_by(_member_sort_clause(sort_by, order))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[PulseMemberListItem.model_validate(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get(
    "/members/{member_id}",
    response_model=PulseMemberDetail,
    summary="Admin member detail",
    description="Return full member details for admin management.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def admin_get_member(
    request: Request,
    admin: AdminUserDep,
    member_id: int,
    db: Session = Depends(get_db),
) -> PulseMemberDetail:
    """Return a single member for admin review."""
    member = or_404(db.query(PulseMember).filter(PulseMember.id == member_id).first())
    return PulseMemberDetail.model_validate(member)


@router.put(
    "/members/{member_id}",
    response_model=PulseMemberDetail,
    summary="Admin update member",
    description="Update a member record as an administrator.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def admin_update_member(
    request: Request,
    admin: AdminUserDep,
    member_id: int,
    data: AdminMemberUpdate,
    db: Session = Depends(get_db),
) -> PulseMemberDetail:
    """Update a member record (admin only)."""
    member = or_404(db.query(PulseMember).filter(PulseMember.id == member_id).first())
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(member, field, value)
    db.commit()
    db.refresh(member)
    return PulseMemberDetail.model_validate(member)


@router.delete(
    "/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Admin delete member",
    description="Delete a member record as an administrator.",
)
@limiter.limit("10/minute")
def admin_delete_member(
    request: Request,
    admin: AdminUserDep,
    member_id: int,
    db: Session = Depends(get_db),
) -> Response:
    """Delete a member record (admin only)."""
    member = or_404(db.query(PulseMember).filter(PulseMember.id == member_id).first())
    db.delete(member)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/members/{member_id}/confirm",
    response_model=PulseMemberDetail,
    summary="Confirm member",
    description="Mark a community member as confirmed.",
)
@limiter.limit("10/minute")
def admin_confirm_member(
    request: Request,
    admin: AdminUserDep,
    member_id: int,
    db: Session = Depends(get_db),
) -> PulseMemberDetail:
    """Confirm a member (admin only)."""
    member = or_404(db.query(PulseMember).filter(PulseMember.id == member_id).first())
    member.is_confirmed = True
    db.commit()
    db.refresh(member)
    return PulseMemberDetail.model_validate(member)


@router.post(
    "/members/bulk",
    response_model=BulkActionResponse,
    summary="Bulk member action",
    description="Apply a bulk action (confirm, delete, activate, deactivate) to a list of member IDs.",
)
@limiter.limit("5/minute")
def admin_bulk_members(
    request: Request,
    admin: AdminUserDep,
    data: BulkActionRequest,
    db: Session = Depends(get_db),
) -> BulkActionResponse:
    """Apply a bulk action to community members."""
    members = db.query(PulseMember).filter(PulseMember.id.in_(data.ids)).all()
    processed = 0
    if data.action == "confirm" or data.action == "activate":
        for member in members:
            member.is_confirmed = True
            processed += 1
    elif data.action == "deactivate":
        for member in members:
            member.is_confirmed = False
            processed += 1
    elif data.action == "delete":
        for member in members:
            db.delete(member)
            processed += 1
    db.commit()
    return BulkActionResponse(
        action=data.action,
        processed=processed,
        message=f"Bulk action '{data.action}' processed {processed} members",
    )


@router.post(
    "/badge/generate",
    response_model=BadgeGenerationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate badge",
    description="Generate a member badge and record the generation event.",
)
@limiter.limit("10/minute")
def generate_badge(
    request: Request,
    admin: AdminUserDep,
    data: BadgeGenerateRequest,
    db: Session = Depends(get_db),
) -> BadgeGenerationResponse:
    """Generate a badge for a member (admin only)."""
    badge = BadgeGeneration(
        full_name=data.full_name,
        category=data.category,
        role_label=data.role_label,
        ref_url=data.ref_url,
        created_at=datetime.utcnow(),
    )
    db.add(badge)
    db.commit()
    db.refresh(badge)
    return BadgeGenerationResponse.model_validate(badge)


@router.get(
    "/badge/generations",
    response_model=PaginatedResponse[BadgeGenerationResponse],
    summary="Badge generation history",
    description="Return badge generation audit history.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_badge_generations(
    request: Request,
    admin: AdminUserDep,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginatedResponse[BadgeGenerationResponse]:
    """Return badge generation history (admin only)."""
    query = db.query(BadgeGeneration).order_by(desc(BadgeGeneration.created_at))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[BadgeGenerationResponse.model_validate(b) for b in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get(
    "/export/members",
    summary="Export members CSV",
    description="Export all community members as a CSV file (admin only).",
)
@limiter.limit("10/minute")
def export_members_csv(
    request: Request,
    admin: AdminUserDep,
    db: Session = Depends(get_db),
) -> Response:
    """Export members as CSV (admin only)."""
    import csv

    members = db.query(PulseMember).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "email", "full_name", "role", "is_confirmed", "created_at"])
    for m in members:
        writer.writerow([m.id, m.email, m.full_name, m.role, m.is_confirmed, m.created_at])
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=pulse_members.csv"},
    )


# ---------------------------------------------------------------------------
# Directory entity CRUD
#
# The public directory routes are read-only by design. These admin-guarded
# endpoints supply the create/edit/delete half of the workflow, which previously
# existed nowhere in the backend.
# ---------------------------------------------------------------------------
def _apply_fields(instance: object, payload: BaseModel) -> None:
    """Copy the payload's explicitly-set fields onto a model instance."""
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(instance, field, value)


def _require(value: str | None, field: str) -> str:
    """Return a required create field or raise a 422-style validation error."""
    if not value or not value.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"{field} is required",
        )
    return value.strip()


def _delete_or_404(db: Session, model: type, pk_column: Any, pk_value: Any) -> Response:
    """Delete a row by primary key, returning 204 or raising 404."""
    instance = or_404(db.query(model).filter(pk_column == pk_value).first())
    db.delete(instance)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Startups --------------------------------------------------------------
@router.post(
    "/startups",
    response_model=StartupDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create startup",
    description="Create a startup directory entry (admin only).",
)
@limiter.limit("30/minute")
def admin_create_startup(
    request: Request,
    admin: AdminUserDep,
    data: StartupWrite,
    db: Session = Depends(get_db),
) -> StartupDetail:
    """Create a startup."""
    startup = Startup(startup_name=_require(data.startup_name, "startup_name"))
    _apply_fields(startup, data)
    db.add(startup)
    db.commit()
    db.refresh(startup)
    return startup_to_detail(startup)


@router.put(
    "/startups/{startup_id}",
    response_model=StartupDetail,
    summary="Update startup",
    description="Update a startup directory entry (admin only).",
)
@limiter.limit("30/minute")
def admin_update_startup(
    request: Request,
    admin: AdminUserDep,
    startup_id: int,
    data: StartupWrite,
    db: Session = Depends(get_db),
) -> StartupDetail:
    """Update a startup."""
    startup = or_404(db.query(Startup).filter(Startup.startup_id == startup_id).first())
    _apply_fields(startup, data)
    db.commit()
    db.refresh(startup)
    return startup_to_detail(startup)


@router.delete(
    "/startups/{startup_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete startup",
    description="Delete a startup directory entry (admin only).",
)
@limiter.limit("30/minute")
def admin_delete_startup(
    request: Request, admin: AdminUserDep, startup_id: int, db: Session = Depends(get_db)
) -> Response:
    """Delete a startup."""
    return _delete_or_404(db, Startup, Startup.startup_id, startup_id)


# --- Founders --------------------------------------------------------------
@router.post(
    "/founders",
    response_model=FounderDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create founder",
    description="Create a founder directory entry (admin only).",
)
@limiter.limit("30/minute")
def admin_create_founder(
    request: Request,
    admin: AdminUserDep,
    data: FounderWrite,
    db: Session = Depends(get_db),
) -> FounderDetail:
    """Create a founder.

    Founder Id is a string key with no sequence, so a collision-resistant token
    is generated rather than relying on a database default.
    """
    founder = Founder(founder_id=generate_secure_token(16), name=_require(data.name, "name"))
    _apply_fields(founder, data)
    db.add(founder)
    db.commit()
    db.refresh(founder)
    return founder_to_detail(db, founder)


@router.put(
    "/founders/{founder_id}",
    response_model=FounderDetail,
    summary="Update founder",
    description="Update a founder directory entry (admin only).",
)
@limiter.limit("30/minute")
def admin_update_founder(
    request: Request,
    admin: AdminUserDep,
    founder_id: str,
    data: FounderWrite,
    db: Session = Depends(get_db),
) -> FounderDetail:
    """Update a founder."""
    founder = or_404(db.query(Founder).filter(Founder.founder_id == founder_id).first())
    _apply_fields(founder, data)
    db.commit()
    db.refresh(founder)
    return founder_to_detail(db, founder)


@router.delete(
    "/founders/{founder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete founder",
    description="Delete a founder directory entry (admin only).",
)
@limiter.limit("30/minute")
def admin_delete_founder(
    request: Request, admin: AdminUserDep, founder_id: str, db: Session = Depends(get_db)
) -> Response:
    """Delete a founder."""
    return _delete_or_404(db, Founder, Founder.founder_id, founder_id)


# --- Investors -------------------------------------------------------------
@router.post(
    "/investors",
    response_model=InvestorDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create investor",
    description="Create an investor directory entry (admin only).",
)
@limiter.limit("30/minute")
def admin_create_investor(
    request: Request,
    admin: AdminUserDep,
    data: InvestorWrite,
    db: Session = Depends(get_db),
) -> InvestorDetail:
    """Create an investor."""
    investor = Investor(investor_name=_require(data.investor_name, "investor_name"))
    _apply_fields(investor, data)
    db.add(investor)
    db.commit()
    db.refresh(investor)
    return investor_to_detail(investor)


@router.put(
    "/investors/{investor_id}",
    response_model=InvestorDetail,
    summary="Update investor",
    description="Update an investor directory entry (admin only).",
)
@limiter.limit("30/minute")
def admin_update_investor(
    request: Request,
    admin: AdminUserDep,
    investor_id: int,
    data: InvestorWrite,
    db: Session = Depends(get_db),
) -> InvestorDetail:
    """Update an investor."""
    investor = or_404(db.query(Investor).filter(Investor.investor_id == investor_id).first())
    _apply_fields(investor, data)
    db.commit()
    db.refresh(investor)
    return investor_to_detail(investor)


@router.delete(
    "/investors/{investor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete investor",
    description="Delete an investor directory entry (admin only).",
)
@limiter.limit("30/minute")
def admin_delete_investor(
    request: Request, admin: AdminUserDep, investor_id: int, db: Session = Depends(get_db)
) -> Response:
    """Delete an investor."""
    return _delete_or_404(db, Investor, Investor.investor_id, investor_id)


# --- Incubators ------------------------------------------------------------
@router.post(
    "/incubators",
    response_model=IncubatorDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create incubator",
    description="Create an incubator or programme entry (admin only).",
)
@limiter.limit("30/minute")
def admin_create_incubator(
    request: Request,
    admin: AdminUserDep,
    data: IncubatorWrite,
    db: Session = Depends(get_db),
) -> IncubatorDetail:
    """Create an incubator."""
    incubator = Incubator(incubator=_require(data.incubator, "incubator"))
    _apply_fields(incubator, data)
    db.add(incubator)
    db.commit()
    db.refresh(incubator)
    return incubator_to_detail(incubator)


@router.put(
    "/incubators/{incubator_id}",
    response_model=IncubatorDetail,
    summary="Update incubator",
    description="Update an incubator or programme entry (admin only).",
)
@limiter.limit("30/minute")
def admin_update_incubator(
    request: Request,
    admin: AdminUserDep,
    incubator_id: int,
    data: IncubatorWrite,
    db: Session = Depends(get_db),
) -> IncubatorDetail:
    """Update an incubator."""
    incubator = or_404(db.query(Incubator).filter(Incubator.incubator_id == incubator_id).first())
    _apply_fields(incubator, data)
    db.commit()
    db.refresh(incubator)
    return incubator_to_detail(incubator)


@router.delete(
    "/incubators/{incubator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete incubator",
    description="Delete an incubator or programme entry (admin only).",
)
@limiter.limit("30/minute")
def admin_delete_incubator(
    request: Request, admin: AdminUserDep, incubator_id: int, db: Session = Depends(get_db)
) -> Response:
    """Delete an incubator."""
    return _delete_or_404(db, Incubator, Incubator.incubator_id, incubator_id)


# --- Funding rounds --------------------------------------------------------
@router.post(
    "/funding-rounds",
    response_model=FundingRoundDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create funding round",
    description="Record a funding round (admin only).",
)
@limiter.limit("30/minute")
def admin_create_funding_round(
    request: Request,
    admin: AdminUserDep,
    data: FundingRoundWrite,
    db: Session = Depends(get_db),
) -> FundingRoundDetail:
    """Create a funding round."""
    funding_round = FundingRound(startup_name=_require(data.startup_name, "startup_name"))
    _apply_fields(funding_round, data)
    db.add(funding_round)
    db.commit()
    db.refresh(funding_round)
    return funding_round_to_detail(db, funding_round)


@router.put(
    "/funding-rounds/{funding_round_id}",
    response_model=FundingRoundDetail,
    summary="Update funding round",
    description="Update a funding round (admin only).",
)
@limiter.limit("30/minute")
def admin_update_funding_round(
    request: Request,
    admin: AdminUserDep,
    funding_round_id: int,
    data: FundingRoundWrite,
    db: Session = Depends(get_db),
) -> FundingRoundDetail:
    """Update a funding round."""
    funding_round = or_404(
        db.query(FundingRound).filter(FundingRound.funding_round_id == funding_round_id).first()
    )
    _apply_fields(funding_round, data)
    db.commit()
    db.refresh(funding_round)
    return funding_round_to_detail(db, funding_round)


@router.delete(
    "/funding-rounds/{funding_round_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete funding round",
    description="Delete a funding round (admin only).",
)
@limiter.limit("30/minute")
def admin_delete_funding_round(
    request: Request, admin: AdminUserDep, funding_round_id: int, db: Session = Depends(get_db)
) -> Response:
    """Delete a funding round."""
    return _delete_or_404(db, FundingRound, FundingRound.funding_round_id, funding_round_id)
