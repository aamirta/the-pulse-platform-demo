"""Search API routes."""

from typing import cast

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.api.limiter import limiter
from backend.core.config import settings
from backend.models import Founder, Investor, Startup
from backend.schemas import SearchResponse, SearchResult

router = APIRouter(prefix="/search", tags=["search"])


@router.get(
    "/",
    response_model=SearchResponse,
    summary="Global search",
    description="Search across startups, founders, and investors by name, sector, location, or description.",
)
@limiter.limit(settings.RATE_LIMIT_SEARCH)
def global_search(
    request: Request,
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    role: str | None = Query(None, description="Filter by role: startup, founder, investor"),
    db: Session = Depends(get_db),
) -> SearchResponse:
    """Global search across the ecosystem."""
    term = f"%{q}%"
    results: list[SearchResult] = []
    limit = 50

    if role is None or role == "startup":
        startups = (
            db.query(Startup)
            .filter(
                Startup.startup_name.ilike(term)
                | Startup.sector.ilike(term)
                | Startup.location.ilike(term)
                | Startup.description.ilike(term)
            )
            .limit(limit)
            .all()
        )
        results.extend(
            SearchResult(
                id=str(s.startup_id),
                type="startup",
                title=s.startup_name or "",
                subtitle=s.location or "",
                url=f"/startups/{s.startup_id}",
            )
            for s in startups
        )

    if role is None or role == "founder":
        founders = (
            db.query(Founder)
            .filter(
                Founder.name.ilike(term)
                | Founder.first_name.ilike(term)
                | Founder.last_name.ilike(term)
                | Founder.current_title.ilike(term)
                | Founder.location.ilike(term)
            )
            .limit(limit)
            .all()
        )
        results.extend(
            SearchResult(
                id=f.founder_id,
                type="founder",
                title=f.name or f"{f.first_name or ''} {f.last_name or ''}".strip(),
                subtitle=f.current_title or "",
                url=f"/founders/{f.founder_id}",
            )
            for f in founders
        )

    if role is None or role == "investor":
        investors = (
            db.query(Investor)
            .filter(
                Investor.investor_name.ilike(term)
                | Investor.description.ilike(term)
                | Investor.hq_location.ilike(term)
                | Investor.preferred_industry.ilike(term)
            )
            .limit(limit)
            .all()
        )
        results.extend(
            SearchResult(
                id=str(i.investor_id),
                type="investor",
                title=i.investor_name or "",
                subtitle=i.hq_location or "",
                url=f"/investors/{i.investor_id}",
            )
            for i in investors
        )

    return SearchResponse(query=q, results=results[:limit], total=len(results[:limit]))


@router.get(
    "/{role}",
    response_model=SearchResponse,
    summary="Role-based search",
    description="Search within a single entity type: startup, founder, or investor.",
)
@limiter.limit(settings.RATE_LIMIT_SEARCH)
def role_search(
    request: Request,
    role: str,
    q: str = Query(..., min_length=1, max_length=100),
    db: Session = Depends(get_db),
) -> SearchResponse:
    """Search scoped to a specific role."""
    return cast(SearchResponse, global_search(request, q=q, role=role, db=db))
