"""Ecosystem expert / mentor API routes.

The `experts` table and its ORM model existed with no route exposing them, so
the frontend's "Experts & Mentors" section had nothing to call and fell back to
filtering the founders list against hardcoded mock IDs.
"""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from backend.api.common import apply_search_filter, or_404, split_tags
from backend.api.deps import get_db
from backend.api.limiter import limiter
from backend.core.config import settings
from backend.models import Expert
from backend.schemas import ExpertDetail, ExpertListItem, PaginatedResponse

router = APIRouter(prefix="/experts", tags=["experts"])


def _to_list_item(expert: Expert) -> ExpertListItem:
    """Map an Expert ORM instance to the frontend list schema."""
    return ExpertListItem(
        id=str(expert.expert_id),
        name=expert.full_name or "",
        title=expert.current_title,
        organization=expert.organization,
        location=expert.location,
        expertiseDomain=expert.expertise_domain,
        yearsExperience=expert.years_experience,
        skills=split_tags(expert.skills),
        availability=expert.availability,
        linkedin=expert.linkedin_url,
        profilePic=expert.profile_pic,
    )


def _to_detail(expert: Expert) -> ExpertDetail:
    """Map an Expert ORM instance to the full detail schema."""
    detail = ExpertDetail(**_to_list_item(expert).model_dump())
    detail.professionalBio = expert.professional_bio
    detail.servicesOffered = expert.services_offered
    detail.industriesOfInterest = split_tags(expert.industries_of_interest)
    detail.achievements = expert.achievements
    detail.languages = expert.languages
    detail.portfolioWebsite = expert.portfolio_website
    detail.email = expert.email
    detail.createdAt = expert.created_at
    return detail


@router.get(
    "/",
    response_model=PaginatedResponse[ExpertListItem],
    summary="List experts and mentors",
    description="Paginated list of ecosystem experts with optional filtering by domain, location, and search.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_experts(
    request: Request,
    db: Session = Depends(get_db),
    domain: str | None = None,
    location: str | None = None,
    availability: str | None = None,
    search: str | None = None,
    sort_by: str = Query("full_name", description="Column to sort by"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginatedResponse[ExpertListItem]:
    """Return a paginated list of experts."""
    query = db.query(Expert)
    if domain:
        query = query.filter(
            (Expert.expertise_domain.ilike(f"%{domain}%"))
            | (Expert.industries_of_interest.ilike(f"%{domain}%"))
        )
    if location:
        query = query.filter(Expert.location.ilike(f"%{location}%"))
    if availability:
        query = query.filter(Expert.availability.ilike(f"%{availability}%"))
    if search:
        query = apply_search_filter(
            query, Expert, search, "full_name", "current_title", "organization", "skills"
        )

    sort_column = getattr(Expert, sort_by, Expert.full_name)
    query = query.order_by(desc(sort_column) if order == "desc" else asc(sort_column))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[_to_list_item(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get(
    "/filters",
    response_model=dict,
    summary="Expert filter options",
    description="Return available expertise domains, locations, and availabilities for filtering.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def expert_filters(request: Request, db: Session = Depends(get_db)) -> dict[str, list[str]]:
    """Return distinct filter values for experts."""
    rows = db.query(Expert).all()
    return {
        "domains": sorted({e.expertise_domain for e in rows if e.expertise_domain}),
        "locations": sorted({e.location for e in rows if e.location}),
        "availabilities": sorted({e.availability for e in rows if e.availability}),
    }


@router.get(
    "/{expert_id}",
    response_model=ExpertDetail,
    summary="Expert detail",
    description="Return detailed information for a single expert or mentor.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def get_expert(request: Request, expert_id: int, db: Session = Depends(get_db)) -> ExpertDetail:
    """Return a single expert by ID."""
    expert = or_404(db.query(Expert).filter(Expert.expert_id == expert_id).first())
    return _to_detail(expert)
