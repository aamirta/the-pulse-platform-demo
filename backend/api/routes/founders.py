"""Founder API routes."""

import csv
import io
from dataclasses import dataclass

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy import asc, desc, func
from sqlalchemy.orm import Session

from backend.api.common import apply_search_filter, or_404
from backend.api.deps import AdminUserDep, get_db
from backend.api.limiter import limiter
from backend.core.config import settings
from backend.models import Founder, Startup, StartupFounder
from backend.schemas import FounderDetail, FounderListItem, PaginatedResponse

router = APIRouter(prefix="/founders", tags=["founders"])


def _startup_name_for_founder(db: Session, founder_id: str) -> tuple[str | None, str | None]:
    """Return (startup_name, startup_id) for a founder's first linked startup."""
    link = db.query(StartupFounder).filter(StartupFounder.founder_id == founder_id).first()
    if not link:
        return None, None
    startup = db.query(Startup).filter(Startup.startup_id == link.startup_id).first()
    if startup:
        return startup.startup_name or "", str(startup.startup_id)
    return None, None


@dataclass
class _FounderContext:
    """Per-founder facts that need the join tables, resolved for a whole page.

    ``_startup_name_for_founder`` costs two queries per founder, so rendering a
    page of twenty issued forty. Co-founder status needs a third lookup on top.
    Resolving the page in a fixed number of queries keeps the cost flat as the
    directory grows.
    """

    startup_name: str | None = None
    startup_id: str | None = None
    #: True when this founder shares a startup with at least one other founder.
    is_cofounder: bool = False


def _founder_contexts(db: Session, founder_ids: list[str]) -> dict[str, _FounderContext]:
    """Resolve startup and co-founder status for a page of founders.

    "Co-founder" is not a stored flag — nothing in the data declares it. It is
    derived: a person who founded a company alongside someone else *is* a
    co-founder of it, and a sole founder is not. That reading is the only one
    the directory can support honestly, and it comes straight from how many
    rows ``StartupFounders`` holds for the same startup.
    """
    if not founder_ids:
        return {}

    links = (
        db.query(StartupFounder)
        .filter(StartupFounder.founder_id.in_(founder_ids))
        .all()
    )
    if not links:
        return {fid: _FounderContext() for fid in founder_ids}

    startup_ids = {link.startup_id for link in links}

    # How many founders each of those startups has, in one grouped query.
    team_sizes = dict(
        db.query(StartupFounder.startup_id, func.count(StartupFounder.founder_id))
        .filter(StartupFounder.startup_id.in_(startup_ids))
        .group_by(StartupFounder.startup_id)
        .all()
    )
    startups = {
        row.startup_id: row
        for row in db.query(Startup).filter(Startup.startup_id.in_(startup_ids)).all()
    }

    contexts: dict[str, _FounderContext] = {fid: _FounderContext() for fid in founder_ids}
    for link in links:
        context = contexts[link.founder_id]
        # A founder may appear on several startups; the first link supplies the
        # displayed company, matching what the single-record lookup did.
        if context.startup_id is None:
            startup = startups.get(link.startup_id)
            if startup is not None:
                context.startup_name = startup.startup_name or ""
                context.startup_id = str(startup.startup_id)
        # Co-founder of *any* of their companies is enough to call them one.
        if team_sizes.get(link.startup_id, 0) > 1:
            context.is_cofounder = True
    return contexts


def _to_list_item(
    db: Session, founder: Founder, context: _FounderContext | None = None
) -> FounderListItem:
    """Map a Founder ORM instance to the frontend list schema.

    ``context`` is supplied when rendering a page, so the join lookups happen
    once for the whole page rather than per row.
    """
    if context is None:
        context = _founder_contexts(db, [founder.founder_id]).get(
            founder.founder_id, _FounderContext()
        )
    return FounderListItem(
        id=founder.founder_id,
        name=founder.name or f"{founder.first_name or ''} {founder.last_name or ''}".strip(),
        role=founder.current_title or "",
        startup=context.startup_name or founder.company_details_name or "",
        startupId=context.startup_id,
        location=founder.location or "",
        bio=founder.skills or founder.most_recent_ended_exp_title or "",
        avatar=founder.profile_pic or "",
        linkedin=founder.linkedin_url,
        experience=founder.most_recent_ended_exp_title or "",
        founder_type="cofounder" if context.is_cofounder else "founder",
    )


def _to_detail(db: Session, founder: Founder) -> FounderDetail:
    """Map a Founder ORM instance to the full detail schema."""
    base = _to_list_item(db, founder).model_dump()
    base["founder_id"] = founder.founder_id
    detail = FounderDetail(**base)
    detail.first_name = founder.first_name
    detail.last_name = founder.last_name
    detail.current_employer = founder.current_employer
    detail.company_details_name = founder.company_details_name
    detail.skills = founder.skills
    detail.profile_pic = founder.profile_pic
    detail.link_twitter = founder.link_twitter
    detail.link_facebook = founder.link_facebook
    detail.link_instagram = founder.link_instagram
    detail.link_github = founder.link_github
    detail.link_aboutme = founder.link_aboutme
    detail.link_angellist = founder.link_angellist
    detail.link_stackoverflow = founder.link_stackoverflow
    return detail


@router.get(
    "/",
    response_model=PaginatedResponse[FounderListItem],
    summary="List founders",
    description="Paginated list of founders with optional filtering by startup, location, and search.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_founders(
    request: Request,
    db: Session = Depends(get_db),
    startup: str | None = None,
    location: str | None = None,
    search: str | None = None,
    founder_type: str | None = Query(
        None,
        pattern="^(founder|cofounder)$",
        description="Restrict to sole founders or to people who founded alongside others",
    ),
    sort_by: str = Query("name", description="Column to sort by"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginatedResponse[FounderListItem]:
    """Return a paginated list of founders."""
    query = db.query(Founder)
    if startup:
        query = query.filter(Founder.startups.any(Startup.startup_name.ilike(f"%{startup}%")))
    if location:
        query = query.filter(Founder.location.ilike(f"%{location}%"))
    if search:
        query = apply_search_filter(
            query, Founder, search, "name", "first_name", "last_name", "current_title"
        )

    if founder_type is not None:
        # Co-founder status lives in the join table, not on the founder row, so
        # the filter is a subquery over startups with more than one founder.
        shared = (
            db.query(StartupFounder.startup_id)
            .group_by(StartupFounder.startup_id)
            .having(func.count(StartupFounder.founder_id) > 1)
            .subquery()
        )
        cofounder_ids = db.query(StartupFounder.founder_id).filter(
            StartupFounder.startup_id.in_(db.query(shared.c.startup_id))
        )
        if founder_type == "cofounder":
            query = query.filter(Founder.founder_id.in_(cofounder_ids))
        else:
            query = query.filter(~Founder.founder_id.in_(cofounder_ids))

    sort_column = getattr(Founder, sort_by, Founder.name)
    query = query.order_by(desc(sort_column) if order == "desc" else asc(sort_column))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    contexts = _founder_contexts(db, [f.founder_id for f in items])
    return PaginatedResponse(
        items=[_to_list_item(db, f, contexts.get(f.founder_id)) for f in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get(
    "/export",
    summary="Export founders as CSV",
    description="Download the current founder directory as a CSV file (admin only).",
)
@limiter.limit("10/minute")
def export_founders(
    request: Request,
    admin: AdminUserDep,
    db: Session = Depends(get_db),
    startup: str | None = None,
    location: str | None = None,
    search: str | None = None,
) -> Response:
    """Export filtered founders as a CSV download."""
    query = db.query(Founder)
    if startup:
        query = query.filter(Founder.startups.any(Startup.startup_name.ilike(f"%{startup}%")))
    if location:
        query = query.filter(Founder.location.ilike(f"%{location}%"))
    if search:
        query = apply_search_filter(
            query, Founder, search, "name", "first_name", "last_name", "current_title"
        )

    query = query.order_by(Founder.name.asc())
    rows = query.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Title", "Company", "Location"])
    for f in rows:
        name = f.name or ""
        if not name and (f.first_name or f.last_name):
            name = f"{(f.first_name or '')} {(f.last_name or '')}".strip()
        writer.writerow(
            [
                name,
                f.current_title or "",
                f.company_details_name or "",
                f.location or "",
            ]
        )

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=founders_export.csv"},
    )


@router.get(
    "/{founder_id}",
    response_model=FounderDetail,
    summary="Founder detail",
    description="Return detailed information for a single founder.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def get_founder(request: Request, founder_id: str, db: Session = Depends(get_db)) -> FounderDetail:
    """Return a single founder by ID."""
    founder = or_404(db.query(Founder).filter(Founder.founder_id == founder_id).first())
    return _to_detail(db, founder)
