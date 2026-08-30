"""Resources / opportunities API routes."""

from datetime import datetime
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session

from backend.api.common import apply_search_filter, or_404
from backend.api.deps import AdminUserDep, UserOrMemberDep, get_db
from backend.api.limiter import limiter
from backend.core.config import settings
from backend.models import Resource, ResourceApplication
from backend.schemas import (
    OpportunityItem,
    PaginatedResponse,
    ResourceApplicationCreate,
    ResourceApplicationItem,
    ResourceApplicationResponse,
    ResourceCreate,
    ResourceDetail,
    ResourceListItem,
)

router = APIRouter(prefix="/resources", tags=["resources"])

# The seeded resource catalogue is in French ("Appels à projets", "Dispositifs
# d'appui"), while the UI asks for "opportunity" and "event". Matching only the
# English words returned zero rows, so both pages rendered permanently empty.
# These markers bridge the two vocabularies.
_OPPORTUNITY_MARKERS = ("opportunity", "opportunit", "appel", "dispositif", "financement", "concours")
_EVENT_MARKERS = ("event", "évén", "even", "rencontre", "salon", "conf", "meetup", "hackathon")


def _category_filter(markers: tuple[str, ...]) -> Any:
    """Build an OR filter matching any marker against category or resource_type."""
    clauses = []
    for marker in markers:
        clauses.append(Resource.category.ilike(f"%{marker}%"))
        clauses.append(Resource.resource_type.ilike(f"%{marker}%"))
    return or_(*clauses)


@router.get(
    "/",
    response_model=PaginatedResponse[ResourceListItem],
    summary="List resources",
    description="Paginated list of resources with optional filtering by category, type, search, and featured flag.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_resources(
    request: Request,
    db: Session = Depends(get_db),
    category: str | None = None,
    resource_type: str | None = None,
    search: str | None = None,
    is_featured: bool | None = None,
    sort_by: str = Query("published_at", description="Column to sort by"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginatedResponse[ResourceListItem]:
    """Return a paginated list of resources."""
    query = db.query(Resource)
    if category:
        # "event"/"opportunity" are treated as intents rather than literal
        # category names so the French catalogue still matches.
        lowered = category.strip().lower()
        if any(marker in lowered for marker in ("event", "évén", "even")):
            query = query.filter(_category_filter(_EVENT_MARKERS))
        elif "opportun" in lowered:
            query = query.filter(_category_filter(_OPPORTUNITY_MARKERS))
        else:
            query = query.filter(Resource.category.ilike(f"%{category}%"))
    if resource_type:
        query = query.filter(Resource.resource_type.ilike(f"%{resource_type}%"))
    if is_featured is not None:
        query = query.filter(Resource.is_featured == is_featured)
    if search:
        query = apply_search_filter(
            query, Resource, search, "title", "description", "organization", "category"
        )
    sort_column = getattr(Resource, sort_by, Resource.published_at)
    query = query.order_by(desc(sort_column) if order == "desc" else asc(sort_column))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[ResourceListItem.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get(
    "/opportunities",
    response_model=PaginatedResponse[OpportunityItem],
    summary="List opportunities",
    description="Return resources formatted as opportunities for the frontend.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_opportunities(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginatedResponse[OpportunityItem]:
    """Return resources as opportunities."""
    query = (
        db.query(Resource)
        .filter(_category_filter(_OPPORTUNITY_MARKERS))
        .order_by(desc(Resource.published_at))
    )
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(
        items=[
            OpportunityItem(
                id=str(r.resource_id),
                title=r.title,
                organization=r.organization or "",
                deadline=cast(datetime, r.published_at).strftime("%Y-%m-%d") if r.published_at else "",
                category=r.category or "",
                description=r.description or "",
            )
            for r in items
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get(
    "/{resource_id}",
    response_model=ResourceDetail,
    summary="Resource detail",
    description="Return detailed information for a single resource.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def get_resource(request: Request, resource_id: int, db: Session = Depends(get_db)) -> ResourceDetail:
    """Return a single resource by ID."""
    resource = or_404(db.query(Resource).filter(Resource.resource_id == resource_id).first())
    return ResourceDetail.model_validate(resource)


@router.post(
    "/",
    response_model=ResourceDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create resource",
    description="Create a new resource (admin only).",
)
@limiter.limit("10/minute")
def create_resource(
    request: Request,
    data: ResourceCreate,
    admin: AdminUserDep,
    db: Session = Depends(get_db),
) -> ResourceDetail:
    """Create a new resource."""
    resource = Resource(
        title=data.title,
        description=data.description,
        category=data.category,
        resource_type=data.resource_type,
        url=data.url,
        organization=data.organization,
        tags=data.tags,
        is_featured=data.is_featured,
        published_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return ResourceDetail.model_validate(resource)


# ---------------------------------------------------------------------------
# Registrations and applications
#
# Events and opportunities are both rows in ``resources``; the submission kind is
# derived from the resource's own category so a client cannot mislabel it.
# ---------------------------------------------------------------------------
def _application_kind(resource: Resource) -> str:
    """Return the submission kind implied by the resource's category/type."""
    marker = f"{resource.category or ''} {resource.resource_type or ''}".lower()
    return "registration" if "event" in marker else "application"


def _require_member(user_or_member: tuple[object | None, object | None]) -> int:
    """Return the authenticated member's id, or 403 for admin-only sessions."""
    _, current_member = user_or_member
    if current_member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only community members can register or apply",
        )
    return cast(int, current_member.id)


@router.post(
    "/{resource_id}/apply",
    response_model=ResourceApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register for an event or apply to an opportunity",
    description=(
        "Persist the authenticated member's registration (events) or application "
        "(opportunities). Re-submitting updates the existing entry rather than duplicating it."
    ),
)
@limiter.limit("10/minute")
def apply_to_resource(
    request: Request,
    resource_id: int,
    data: ResourceApplicationCreate,
    db: Session = Depends(get_db),
    user_or_member: UserOrMemberDep = (None, None),
) -> ResourceApplicationResponse:
    """Create or update the member's submission for a resource."""
    member_id = _require_member(user_or_member)
    resource = or_404(db.query(Resource).filter(Resource.resource_id == resource_id).first())

    existing = (
        db.query(ResourceApplication)
        .filter(
            ResourceApplication.resource_id == resource_id,
            ResourceApplication.member_id == member_id,
        )
        .first()
    )
    if existing:
        # Idempotent: a second submit edits the message instead of erroring or
        # silently creating a duplicate row.
        existing.message = data.message
        db.commit()
        db.refresh(existing)
        return ResourceApplicationResponse.model_validate(existing)

    application = ResourceApplication(
        resource_id=resource_id,
        member_id=member_id,
        kind=_application_kind(resource),
        message=data.message,
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return ResourceApplicationResponse.model_validate(application)


@router.get(
    "/applications/mine",
    response_model=list[ResourceApplicationItem],
    summary="My registrations and applications",
    description="Return the authenticated member's submissions, newest first.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def my_applications(
    request: Request,
    db: Session = Depends(get_db),
    user_or_member: UserOrMemberDep = (None, None),
) -> list[ResourceApplicationItem]:
    """Return the current member's registrations and applications."""
    member_id = _require_member(user_or_member)

    # Joined up front so the resource titles do not cost one query per row.
    rows = (
        db.query(ResourceApplication, Resource)
        .join(Resource, Resource.resource_id == ResourceApplication.resource_id)
        .filter(ResourceApplication.member_id == member_id)
        .order_by(desc(ResourceApplication.created_at))
        .all()
    )
    return [
        ResourceApplicationItem(
            **ResourceApplicationResponse.model_validate(application).model_dump(),
            resource_title=resource.title,
            resource_category=resource.category,
        )
        for application, resource in rows
    ]
