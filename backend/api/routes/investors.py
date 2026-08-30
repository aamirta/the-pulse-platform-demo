"""Investor API routes."""

import csv
import io
from typing import Any, cast

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from backend.api.common import apply_search_filter, or_404, split_tags
from backend.api.deps import AdminUserDep, get_db
from backend.api.limiter import limiter
from backend.core.config import settings
from backend.models import Investor
from backend.schemas import InvestorDetail, InvestorListItem, PaginatedResponse

router = APIRouter(prefix="/investors", tags=["investors"])


def _to_list_item(investor: Investor) -> InvestorListItem:
    """Map an Investor ORM instance to the frontend list schema."""
    focus = split_tags(investor.preferred_industry)
    if not focus and investor.preferred_verticals:
        focus = split_tags(investor.preferred_verticals)
    return InvestorListItem(
        id=str(investor.investor_id),
        name=investor.investor_name or "",
        type=investor.primary_investor_type or investor.type or "",
        location=investor.hq_location or investor.city or investor.region or "",
        focus=focus,
        portfolio=float(cast(Any, investor.total_active_portfolio))
        if investor.total_active_portfolio is not None
        else None,
        investments=float(cast(Any, investor.total_investments))
        if investor.total_investments is not None
        else None,
        logo=investor.logo_url or "",
        website=investor.domain or investor.linkedin_url,
    )


def _to_detail(investor: Investor) -> InvestorDetail:
    """Map an Investor ORM instance to the full detail schema."""
    base = _to_list_item(investor).model_dump()
    base["investor_id"] = investor.investor_id
    detail = InvestorDetail(**base)
    detail.investor_status = investor.investor_status
    detail.hq_email = investor.hq_email
    detail.hq_phone = investor.hq_phone
    detail.primary_investor_type = investor.primary_investor_type
    detail.description = investor.description
    detail.preferred_industry = investor.preferred_industry
    detail.preferred_geography = investor.preferred_geography
    detail.preferred_investment_types = investor.preferred_investment_types
    detail.preferred_verticals = investor.preferred_verticals
    detail.total_active_portfolio = (
        float(cast(Any, investor.total_active_portfolio))
        if investor.total_active_portfolio is not None
        else None
    )
    detail.total_investments = (
        float(cast(Any, investor.total_investments)) if investor.total_investments is not None else None
    )
    detail.aum = float(cast(Any, investor.aum)) if investor.aum is not None else None
    detail.dry_powder = float(cast(Any, investor.dry_powder)) if investor.dry_powder is not None else None
    detail.linkedin_url = investor.linkedin_url
    detail.facebook_url = investor.facebook_url
    detail.twitter_url = investor.twitter_url
    return detail


@router.get(
    "/",
    response_model=PaginatedResponse[InvestorListItem],
    summary="List investors",
    description="Paginated list of investors with optional filtering by type, location, focus, and search.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_investors(
    request: Request,
    db: Session = Depends(get_db),
    type: str | None = None,
    location: str | None = None,
    focus: str | None = None,
    search: str | None = None,
    sort_by: str = Query("investor_name", description="Column to sort by"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginatedResponse[InvestorListItem]:
    """Return a paginated list of investors."""
    query = db.query(Investor)
    if type:
        query = query.filter(
            (Investor.primary_investor_type.ilike(f"%{type}%")) | (Investor.type.ilike(f"%{type}%"))
        )
    if location:
        query = query.filter(
            (Investor.hq_location.ilike(f"%{location}%"))
            | (Investor.city.ilike(f"%{location}%"))
            | (Investor.region.ilike(f"%{location}%"))
        )
    if focus:
        query = query.filter(
            (Investor.preferred_industry.ilike(f"%{focus}%"))
            | (Investor.preferred_verticals.ilike(f"%{focus}%"))
        )
    if search:
        query = apply_search_filter(
            query, Investor, search, "investor_name", "description", "hq_location"
        )

    sort_column = getattr(Investor, sort_by, Investor.investor_name)
    query = query.order_by(desc(sort_column) if order == "desc" else asc(sort_column))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[_to_list_item(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get(
    "/export",
    summary="Export investors as CSV",
    description="Download the current investor directory as a CSV file (admin only).",
)
@limiter.limit("10/minute")
def export_investors(
    request: Request,
    admin: AdminUserDep,
    db: Session = Depends(get_db),
    type: str | None = None,
    location: str | None = None,
    focus: str | None = None,
    search: str | None = None,
) -> Response:
    """Export filtered investors as a CSV download."""
    query = db.query(Investor)
    if type:
        query = query.filter(
            (Investor.primary_investor_type.ilike(f"%{type}%")) | (Investor.type.ilike(f"%{type}%"))
        )
    if location:
        query = query.filter(
            (Investor.hq_location.ilike(f"%{location}%"))
            | (Investor.city.ilike(f"%{location}%"))
            | (Investor.region.ilike(f"%{location}%"))
        )
    if focus:
        query = query.filter(
            (Investor.preferred_industry.ilike(f"%{focus}%"))
            | (Investor.preferred_verticals.ilike(f"%{focus}%"))
        )
    if search:
        query = apply_search_filter(
            query, Investor, search, "investor_name", "description", "hq_location"
        )

    query = query.order_by(Investor.investor_name.asc())
    rows = query.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Type", "Location", "Status", "Investment Count"])
    for inv in rows:
        writer.writerow(
            [
                inv.investor_name or "",
                inv.primary_investor_type or inv.type or "",
                inv.city or inv.hq_location or "",
                inv.investor_status or "",
                inv.investment_count or "",
            ]
        )

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=investors_export.csv"},
    )


@router.get(
    "/{investor_id}",
    response_model=InvestorDetail,
    summary="Investor detail",
    description="Return detailed information for a single investor.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def get_investor(request: Request, investor_id: int, db: Session = Depends(get_db)) -> InvestorDetail:
    """Return a single investor by ID."""
    investor = or_404(db.query(Investor).filter(Investor.investor_id == investor_id).first())
    return _to_detail(investor)
