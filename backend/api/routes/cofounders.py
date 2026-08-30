"""Co-founder search posting API routes.

The `cofounder_projects` table held real postings with no route exposing them,
so the frontend's "Co-founders Needed" section had nothing to call and fell back
to filtering the founders list against hardcoded mock IDs.

Note these are *projects* seeking co-founders, not people — the frontend renders
them as posting cards rather than profile cards.
"""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from backend.api.common import apply_search_filter, or_404, split_tags
from backend.api.deps import get_db
from backend.api.limiter import limiter
from backend.core.config import settings
from backend.models import CofounderProject
from backend.schemas import (
    CofounderProjectDetail,
    CofounderProjectListItem,
    PaginatedResponse,
)

router = APIRouter(prefix="/cofounders", tags=["cofounders"])


def _to_list_item(project: CofounderProject) -> CofounderProjectListItem:
    """Map a CofounderProject ORM instance to the frontend list schema."""
    return CofounderProjectListItem(
        id=str(project.project_id),
        title=project.project_title or "",
        domain=project.domain,
        stage=project.project_stage,
        description=project.description,
        rolesNeeded=split_tags(project.roles_needed),
        skillsNeeded=split_tags(project.skills_needed),
        authorName=project.author_name,
        authorAffiliation=project.author_affiliation,
        authorLinkedin=project.author_linkedin,
        commitmentType=project.commitment_type,
        locationPreference=project.location_preference,
        equityOffered=project.equity_offered,
    )


def _to_detail(project: CofounderProject) -> CofounderProjectDetail:
    """Map a CofounderProject ORM instance to the full detail schema."""
    detail = CofounderProjectDetail(**_to_list_item(project).model_dump())
    detail.contactInfo = project.contact_info
    detail.createdAt = project.created_at
    return detail


@router.get(
    "/",
    response_model=PaginatedResponse[CofounderProjectListItem],
    summary="List co-founder postings",
    description="Paginated list of projects seeking co-founders, filterable by domain, stage, role, and search.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_cofounder_projects(
    request: Request,
    db: Session = Depends(get_db),
    domain: str | None = None,
    stage: str | None = None,
    role: str | None = None,
    search: str | None = None,
    sort_by: str = Query("created_at", description="Column to sort by"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginatedResponse[CofounderProjectListItem]:
    """Return a paginated list of co-founder postings."""
    query = db.query(CofounderProject)
    if domain:
        query = query.filter(CofounderProject.domain.ilike(f"%{domain}%"))
    if stage:
        query = query.filter(CofounderProject.project_stage.ilike(f"%{stage}%"))
    if role:
        query = query.filter(
            (CofounderProject.roles_needed.ilike(f"%{role}%"))
            | (CofounderProject.skills_needed.ilike(f"%{role}%"))
        )
    if search:
        query = apply_search_filter(
            query,
            CofounderProject,
            search,
            "project_title",
            "description",
            "domain",
            "roles_needed",
            "author_name",
        )

    sort_column = getattr(CofounderProject, sort_by, CofounderProject.created_at)
    query = query.order_by(desc(sort_column).nullslast() if order == "desc" else asc(sort_column))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[_to_list_item(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get(
    "/filters",
    response_model=dict,
    summary="Co-founder posting filter options",
    description="Return available domains, stages, and roles for filtering.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def cofounder_filters(request: Request, db: Session = Depends(get_db)) -> dict[str, list[str]]:
    """Return distinct filter values for co-founder postings."""
    rows = db.query(CofounderProject).all()
    return {
        "domains": sorted({p.domain for p in rows if p.domain}),
        "stages": sorted({p.project_stage for p in rows if p.project_stage}),
        "roles": sorted({tag for p in rows for tag in split_tags(p.roles_needed) if tag}),
    }


@router.get(
    "/{project_id}",
    response_model=CofounderProjectDetail,
    summary="Co-founder posting detail",
    description="Return detailed information for a single co-founder posting.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def get_cofounder_project(
    request: Request, project_id: int, db: Session = Depends(get_db)
) -> CofounderProjectDetail:
    """Return a single co-founder posting by ID."""
    project = or_404(
        db.query(CofounderProject).filter(CofounderProject.project_id == project_id).first()
    )
    return _to_detail(project)
