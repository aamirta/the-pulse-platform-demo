"""Talent marketplace API routes.

The `talents` table and its ORM model existed with no route exposing them, so
the sidebar's "Talent Marketplace" entry had nothing to call and was wired to
`/opportunities?type=talent` instead -- which is why the page rendered the
Opportunities content.

The rows are profiles of people available to join startups (title, skills,
availability), not job adverts, and the responses are shaped accordingly.
Contact fields (email, phone) are never returned: reaching someone goes through
the platform's messaging rather than a scrapeable directory.
"""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from backend.api.common import apply_search_filter, or_404, split_tags
from backend.api.deps import get_db
from backend.api.limiter import limiter
from backend.core.config import settings
from backend.models import Talent
from backend.schemas import PaginatedResponse, TalentDetail, TalentListItem

router = APIRouter(prefix="/talents", tags=["talents"])


def _to_list_item(talent: Talent) -> TalentListItem:
    """Map a Talent ORM instance to the frontend list schema."""
    return TalentListItem(
        id=str(talent.talent_id),
        name=talent.full_name or "",
        title=talent.current_title,
        location=talent.location,
        yearsExperience=talent.years_experience,
        roleType=talent.role_type,
        workFormat=talent.work_format,
        availability=talent.availability,
        skills=split_tags(talent.skills),
        industries=split_tags(talent.industries_of_interest),
        profilePic=talent.profile_pic,
    )


def _to_detail(talent: Talent) -> TalentDetail:
    """Map a Talent ORM instance to the full detail schema."""
    detail = TalentDetail(**_to_list_item(talent).model_dump())
    detail.professionalBio = talent.professional_bio
    detail.lookingFor = talent.looking_for
    detail.education = talent.education
    detail.achievements = talent.achievements
    detail.languages = talent.languages
    detail.linkedin = talent.linkedin_url
    detail.portfolioWebsite = talent.portfolio_website
    detail.githubProfile = talent.github_profile
    detail.createdAt = talent.created_at
    return detail


@router.get(
    "/",
    response_model=PaginatedResponse[TalentListItem],
    summary="List talent profiles",
    description=(
        "Paginated list of people available to join startups, filterable by "
        "role, work format, location and availability."
    ),
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_talents(
    request: Request,
    db: Session = Depends(get_db),
    role_type: str | None = None,
    work_format: str | None = None,
    location: str | None = None,
    availability: str | None = None,
    search: str | None = None,
    sort_by: str = Query("full_name", description="Column to sort by"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginatedResponse[TalentListItem]:
    """Return a paginated list of talent profiles."""
    query = db.query(Talent)
    if role_type:
        query = query.filter(Talent.role_type.ilike(f"%{role_type}%"))
    if work_format:
        query = query.filter(Talent.work_format.ilike(f"%{work_format}%"))
    if location:
        query = query.filter(Talent.location.ilike(f"%{location}%"))
    if availability:
        query = query.filter(Talent.availability.ilike(f"%{availability}%"))
    if search:
        query = apply_search_filter(
            query, Talent, search, "full_name", "current_title", "skills", "looking_for"
        )

    sort_column = getattr(Talent, sort_by, Talent.full_name)
    query = query.order_by(desc(sort_column) if order == "desc" else asc(sort_column))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[_to_list_item(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get(
    "/filters",
    response_model=dict,
    summary="Talent filter options",
    description="Return available role types, work formats, locations and availabilities.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def talent_filters(request: Request, db: Session = Depends(get_db)) -> dict[str, list[str]]:
    """Return distinct filter values for talents."""
    rows = db.query(Talent).all()
    return {
        "roleTypes": sorted({t.role_type for t in rows if t.role_type}),
        "workFormats": sorted({t.work_format for t in rows if t.work_format}),
        "locations": sorted({t.location for t in rows if t.location}),
        "availabilities": sorted({t.availability for t in rows if t.availability}),
    }


@router.get(
    "/{talent_id}",
    response_model=TalentDetail,
    summary="Talent detail",
    description="Return the full profile for a single talent.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def get_talent(request: Request, talent_id: int, db: Session = Depends(get_db)) -> TalentDetail:
    """Return a single talent profile by ID."""
    talent = or_404(db.query(Talent).filter(Talent.talent_id == talent_id).first())
    return _to_detail(talent)
