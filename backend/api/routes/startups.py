"""Startup API routes."""

import csv
import io
import re
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from backend.api.common import (
    apply_search_filter,
    or_404,
    safe_int,
    split_tags,
)
from backend.api.deps import AdminUserDep, get_db
from backend.api.limiter import limiter
from backend.core.config import settings
from backend.models import Startup
from backend.schemas import (
    PaginatedResponse,
    StartupDetail,
    StartupListItem,
)

router = APIRouter(prefix="/startups", tags=["startups"])


# English/French stage aliases so the frontend can use familiar labels.
_STAGE_ALIASES = {
    "seed": "AMORCAGE",
    "early": "AMORCAGE",
    "pre-seed": "AMORCAGE",
    "preseed": "AMORCAGE",
    "amorçage": "AMORCAGE",
    "amorcage": "AMORCAGE",
    "ideation": "IDEATION",
    "scaling": "SCALING",
    "growth": "SCALING",
    "international": "INTERNATIONALISATION",
    "internationalization": "INTERNATIONALISATION",
    "expansion": "INTERNATIONALISATION",
}


def _normalize_stage(stage: str) -> str:
    """Return the canonical French stage label from a user-supplied alias."""
    return _STAGE_ALIASES.get(stage.strip().lower(), stage)


def _sector_tag_filter(db: Session, column: Any, tag: str) -> Any:
    """Match a single sector tag anywhere in a comma-separated sector string.

    Uses Postgres regex for exact tag matching. Falls back to substring matching
    on SQLite so the test suite still works.
    """
    tag = tag.strip()
    if not tag:
        return None

    dialect_name = db.bind.dialect.name if db.bind else "sqlite"
    if dialect_name == "postgresql":
        # Match tag as a whole token, ignoring surrounding whitespace and case.
        regex = f"(^|,\\s*){re.escape(tag)}(\\s*,|$)"
        return column.op("~*")(regex)

    # SQLite fallback used by the test suite.
    return column.ilike(f"%{tag}%")


def _to_list_item(startup: Startup) -> StartupListItem:
    """Map a Startup ORM instance to the frontend list schema."""
    funding = None
    if startup.total_funding_usd is not None:
        funding = float(cast(Any, startup.total_funding_usd))
    elif startup.raised_funds is not None:
        funding = float(cast(Any, startup.raised_funds))
    return StartupListItem(
        id=str(startup.startup_id),
        name=startup.startup_name or "",
        sector=split_tags(startup.sector),
        stage=startup.stage or "",
        status=startup.status_startup or "",
        location=startup.location or "",
        description=startup.description or "",
        funding=funding,
        fundingCurrency=startup.total_funding_currency_code or "USD",
        teamSize=startup.employees or "",
        yearFounded=safe_int(startup.year_founded),
        logo=startup.logo_url or "",
        website=startup.homepage_url or startup.entreprise_contact_site_web,
        linkedin=startup.linkedin,
    )


def _to_detail(startup: Startup) -> StartupDetail:
    """Map a Startup ORM instance to the full detail schema."""
    base = _to_list_item(startup).model_dump()
    base["startup_id"] = startup.startup_id
    detail = StartupDetail(**base)
    detail.numero_ice = startup.numero_ice
    detail.numero_rc = startup.numero_rc
    detail.forme_juridique = startup.forme_juridique
    detail.activite = startup.activite
    detail.region = startup.region
    detail.contact_email = startup.contact_email
    detail.phone = startup.phone
    detail.employees = startup.employees
    detail.revenue = startup.revenue
    detail.valuation = startup.valuation
    detail.raised_funds = float(cast(Any, startup.raised_funds)) if startup.raised_funds is not None else None
    detail.total_funding_usd = (
        float(cast(Any, startup.total_funding_usd)) if startup.total_funding_usd is not None else None
    )
    detail.total_funding = (
        float(cast(Any, startup.total_funding)) if startup.total_funding is not None else None
    )
    detail.total_funding_currency_code = startup.total_funding_currency_code
    detail.incubated_by = startup.incubated_by
    detail.financed_by = startup.financed_by
    detail.country_code = startup.country_code
    detail.address = startup.address
    detail.facebook_url = startup.facebook_url
    detail.twitter_url = startup.twitter_url
    detail.youtube_link = startup.youtube_link
    detail.instagram_link = startup.instagram_link
    detail.homepage_url = startup.homepage_url
    return detail


@router.get(
    "/",
    response_model=PaginatedResponse[StartupListItem],
    summary="List startups",
    description="Paginated list of startups with optional filtering by sector, stage, status, location and search.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_startups(
    request: Request,
    db: Session = Depends(get_db),
    sector: str | None = None,
    stage: str | None = None,
    status: str | None = None,
    location: str | None = None,
    legal_form: str | None = None,
    search: str | None = None,
    min_funding: float | None = None,
    max_funding: float | None = None,
    sort_by: str = Query("startup_name", description="Column to sort by"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginatedResponse[StartupListItem]:
    """Return a paginated list of startups."""
    query = db.query(Startup)
    if sector:
        sector_filter = _sector_tag_filter(db, Startup.sector, sector)
        if sector_filter is not None:
            query = query.filter(sector_filter)
    if stage:
        stage_value = _normalize_stage(stage)
        query = query.filter(Startup.stage.ilike(stage_value))
    if status:
        query = query.filter(Startup.status_startup.ilike(f"%{status}%"))
    if location:
        query = query.filter(Startup.location.ilike(f"%{location}%"))
    if legal_form:
        query = query.filter(Startup.forme_juridique.ilike(f"%{legal_form}%"))
    if search:
        query = apply_search_filter(
            query, Startup, search, "startup_name", "sector", "location", "description"
        )
    if min_funding is not None:
        query = query.filter(Startup.total_funding_usd >= min_funding)
    if max_funding is not None:
        query = query.filter(Startup.total_funding_usd <= max_funding)

    sort_column = getattr(Startup, sort_by, Startup.startup_name)
    query = query.order_by(desc(sort_column).nullslast() if order == "desc" else asc(sort_column))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[_to_list_item(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get(
    "/filters",
    response_model=dict,
    summary="Startup filter options",
    description="Return available sectors, stages, statuses and locations for filtering.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def startup_filters(request: Request, db: Session = Depends(get_db)) -> dict[str, list[str]]:
    """Return distinct filter values for startups."""
    rows = db.query(Startup).all()
    sectors = sorted({tag.strip() for s in rows for tag in split_tags(s.sector) if tag})
    stages = sorted({s.stage for s in rows if s.stage})
    statuses = sorted({s.status_startup for s in rows if s.status_startup})
    locations = sorted({s.location for s in rows if s.location})
    legal_forms = sorted({s.forme_juridique for s in rows if s.forme_juridique})
    return {
        "sectors": sectors,
        "stages": stages,
        "statuses": statuses,
        "locations": locations,
        "legal_forms": legal_forms,
    }


@router.get(
    "/export",
    summary="Export startups as CSV",
    description="Download the current startup directory as a CSV file (admin only).",
)
@limiter.limit("10/minute")
def export_startups(
    request: Request,
    admin: AdminUserDep,
    db: Session = Depends(get_db),
    sector: str | None = None,
    stage: str | None = None,
    status: str | None = None,
    location: str | None = None,
    legal_form: str | None = None,
    search: str | None = None,
    min_funding: float | None = None,
    max_funding: float | None = None,
) -> Response:
    """Export filtered startups as a CSV download."""
    query = db.query(Startup)
    if sector:
        sector_filter = _sector_tag_filter(db, Startup.sector, sector)
        if sector_filter is not None:
            query = query.filter(sector_filter)
    if stage:
        stage_value = _normalize_stage(stage)
        query = query.filter(Startup.stage.ilike(stage_value))
    if status:
        query = query.filter(Startup.status_startup.ilike(f"%{status}%"))
    if location:
        query = query.filter(Startup.location.ilike(f"%{location}%"))
    if legal_form:
        query = query.filter(Startup.forme_juridique.ilike(f"%{legal_form}%"))
    if search:
        query = apply_search_filter(
            query, Startup, search, "startup_name", "sector", "location", "description"
        )
    if min_funding is not None:
        query = query.filter(Startup.total_funding_usd >= min_funding)
    if max_funding is not None:
        query = query.filter(Startup.total_funding_usd <= max_funding)

    query = query.order_by(Startup.total_funding_usd.desc().nullslast())
    rows = query.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Sector", "Location", "Region", "Stage", "Website"])
    for s in rows:
        writer.writerow(
            [
                s.startup_name or "",
                s.sector or "",
                s.location or "",
                s.region or "",
                s.stage or "",
                s.homepage_url or s.entreprise_contact_site_web or "",
            ]
        )

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=startups_export.csv"},
    )


@router.get(
    "/{startup_id}",
    response_model=StartupDetail,
    summary="Startup detail",
    description="Return detailed information for a single startup.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def get_startup(request: Request, startup_id: str, db: Session = Depends(get_db)) -> StartupDetail:
    """Return a single startup by numeric id, or by name/slug.

    Editorial links in the SPA point at readable slugs such as
    ``/startups/mubawab``. Typing this parameter as ``int`` made every one of
    them answer 422, so a name lookup is supported as a fallback and those links
    resolve instead of erroring.
    """
    if startup_id.isdigit():
        found = db.query(Startup).filter(Startup.startup_id == int(startup_id)).first()
        return _to_detail(or_404(found))

    # Slug form. Names carry punctuation the URL does not ("Spore.bio" ->
    # "spore-bio"), so both sides are reduced to alphanumerics before comparing.
    def normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]", "", value.lower())

    target = normalize(startup_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    # Narrow in SQL on the first token, then match exactly in Python so the
    # comparison stays punctuation-insensitive without a full table scan.
    first_token = re.split(r"[-_\s]+", startup_id)[0]
    candidates = (
        db.query(Startup)
        .filter(Startup.startup_name.isnot(None))
        .filter(Startup.startup_name.ilike(f"{first_token}%"))
        .limit(200)
        .all()
    )
    found = next(
        (s for s in candidates if normalize(cast(str, s.startup_name)) == target),
        None,
    )
    return _to_detail(or_404(found))
