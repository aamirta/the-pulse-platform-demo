"""Funding round API routes."""

import csv
import io
from typing import Any, cast

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from backend.api.common import apply_search_filter, format_currency, or_404
from backend.api.deps import AdminUserDep, get_db
from backend.api.limiter import limiter
from backend.core.config import settings
from backend.models import FundingRound, Startup
from backend.schemas import FundingRoundDetail, FundingRoundListItem, PaginatedResponse

router = APIRouter(prefix="/funding-rounds", tags=["funding-rounds"])


def _startup_logo(db: Session, startup_id: int | None) -> str:
    """Return the logo URL for a startup ID."""
    if startup_id is None:
        return ""
    startup = db.query(Startup).filter(Startup.startup_id == startup_id).first()
    return startup.logo_url or "" if startup else ""


def _to_list_item(db: Session, fr: FundingRound) -> FundingRoundListItem:
    """Map a FundingRound ORM instance to the frontend list schema."""
    amount_value = fr.raised_amount_usd or fr.raised_amount
    amount = format_currency(amount_value, fr.native_currency_of_deal or "USD")
    return FundingRoundListItem(
        id=str(fr.funding_round_id),
        startup=fr.startup_name or "",
        startupLogo=_startup_logo(db, fr.startup_id),
        amount=amount,
        round=fr.round_name or "",
        investor=fr.lead_investor or fr.institutional_investors or "",
        date=fr.date or "",
    )


def _to_detail(db: Session, fr: FundingRound) -> FundingRoundDetail:
    """Map a FundingRound ORM instance to the full detail schema."""
    base = _to_list_item(db, fr).model_dump()
    base["funding_round_id"] = fr.funding_round_id
    detail = FundingRoundDetail(**base)
    detail.deal_id = fr.deal_id
    detail.deal_type = fr.deal_type
    detail.deal_type2 = fr.deal_type2
    detail.deal_status = fr.deal_status
    detail.raised_amount = float(cast(Any, fr.raised_amount)) if fr.raised_amount is not None else None
    detail.raised_amount_usd = (
        float(cast(Any, fr.raised_amount_usd)) if fr.raised_amount_usd is not None else None
    )
    detail.total_funding_usd = (
        float(cast(Any, fr.total_funding_usd)) if fr.total_funding_usd is not None else None
    )
    detail.native_currency_of_deal = fr.native_currency_of_deal
    detail.overview = fr.overview
    detail.lead_investor = fr.lead_investor
    detail.institutional_investors = fr.institutional_investors
    detail.angel_investors = fr.angel_investors
    detail.ceo = fr.ceo
    detail.city = fr.city
    detail.country = fr.country
    detail.region = fr.region
    detail.startup_id = fr.startup_id
    return detail


@router.get(
    "/",
    response_model=PaginatedResponse[FundingRoundListItem],
    summary="List funding rounds",
    description="Paginated list of funding rounds with optional filtering by startup, round, year, investor, and search.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_funding_rounds(
    request: Request,
    db: Session = Depends(get_db),
    startup: str | None = None,
    round: str | None = None,
    year: str | None = None,
    investor: str | None = None,
    search: str | None = None,
    sort_by: str = Query("date", description="Column to sort by"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginatedResponse[FundingRoundListItem]:
    """Return a paginated list of funding rounds."""
    query = db.query(FundingRound)
    if startup:
        query = query.filter(FundingRound.startup_name.ilike(f"%{startup}%"))
    if round:
        query = query.filter(FundingRound.round_name.ilike(f"%{round}%"))
    if year:
        query = query.filter(FundingRound.date.ilike(f"%{year}%"))
    if investor:
        query = query.filter(
            (FundingRound.lead_investor.ilike(f"%{investor}%"))
            | (FundingRound.institutional_investors.ilike(f"%{investor}%"))
        )
    if search:
        query = apply_search_filter(
            query,
            FundingRound,
            search,
            "startup_name",
            "round_name",
            "lead_investor",
            "deal_synopsis",
        )

    sort_column = getattr(FundingRound, sort_by, FundingRound.date)
    query = query.order_by(desc(sort_column) if order == "desc" else asc(sort_column))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[_to_list_item(db, fr) for fr in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get(
    "/export",
    summary="Export funding rounds as CSV",
    description="Download the current funding round directory as a CSV file (admin only).",
)
@limiter.limit("10/minute")
def export_funding_rounds(
    request: Request,
    admin: AdminUserDep,
    db: Session = Depends(get_db),
    startup: str | None = None,
    round: str | None = None,
    year: str | None = None,
    investor: str | None = None,
    search: str | None = None,
) -> Response:
    """Export filtered funding rounds as a CSV download."""
    query = db.query(FundingRound)
    if startup:
        query = query.filter(FundingRound.startup_name.ilike(f"%{startup}%"))
    if round:
        query = query.filter(FundingRound.round_name.ilike(f"%{round}%"))
    if year:
        query = query.filter(FundingRound.date.ilike(f"%{year}%"))
    if investor:
        query = query.filter(
            (FundingRound.lead_investor.ilike(f"%{investor}%"))
            | (FundingRound.institutional_investors.ilike(f"%{investor}%"))
        )
    if search:
        query = apply_search_filter(
            query,
            FundingRound,
            search,
            "startup_name",
            "round_name",
            "lead_investor",
            "deal_synopsis",
        )

    query = query.order_by(FundingRound.date.desc().nullslast())
    rows = query.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["Round", "Startup", "Amount USD", "Deal Type", "Lead Investor", "Year", "City"]
    )
    for fr in rows:
        writer.writerow(
            [
                fr.round_name or "",
                fr.startup_name or "",
                fr.raised_amount_usd or "",
                fr.deal_type or "",
                fr.lead_investor or "",
                fr.founded_year or "",
                fr.city or "",
            ]
        )

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=funding_rounds_export.csv"},
    )


@router.get(
    "/{funding_round_id}",
    response_model=FundingRoundDetail,
    summary="Funding round detail",
    description="Return detailed information for a single funding round.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def get_funding_round(request: Request, funding_round_id: int, db: Session = Depends(get_db)) -> FundingRoundDetail:
    """Return a single funding round by ID."""
    fr = or_404(
        db.query(FundingRound).filter(FundingRound.funding_round_id == funding_round_id).first()
    )
    return _to_detail(db, fr)
