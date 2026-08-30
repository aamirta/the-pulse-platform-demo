"""Incubator API routes."""

import csv
import io
from typing import cast

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from backend.api.common import apply_search_filter, or_404, split_tags
from backend.api.deps import AdminUserDep, get_db
from backend.api.limiter import limiter
from backend.core.config import settings
from backend.models import Incubator
from backend.schemas import (
    IncubatorDetail,
    IncubatorListItem,
    PaginatedResponse,
)

router = APIRouter(prefix="/incubators", tags=["incubators"])


# Priority ordering copied from the legacy Flask app so the most prominent
# Moroccan incubators appear first when no explicit sort is requested.
_PRIORITY_INCUBATORS = [
    "212 Founders",
    "Flat6Labs",
    "Technopark",
    "Endeavor",
    "StartGate",
    "LaStartupFactory",
    "La Startup Factory",
    "Plug Play",
    "Orange Corners",
    "Hseven",
    "UM6P",
    "Emerging Business Factory",
    "Bidaya",
    "Accelab",
    "New Work Lab",
    "Enactus",
    "Impact Lab",
    "StartUp Maroc",
    "Climate Launchpad",
    "CEED",
    "Open Startup",
]


def _priority_score(incubator: Incubator) -> int:
    """Return the legacy priority rank for a given incubator name."""
    name = (incubator.incubator or "").lower()
    for idx, candidate in enumerate(_PRIORITY_INCUBATORS):
        if candidate.lower() in name:
            return idx
    return len(_PRIORITY_INCUBATORS)


# The source data spells the same organisation type several ways
# ("Incubateur" / "Incubateurs" / "incubateur"), which surfaced as three
# separate filter chips. Canonicalise on read so every consumer agrees;
# the stored values are left untouched.
_TYPE_ALIASES = {
    "incubateur": "Incubateur",
    "incubateurs": "Incubateur",
    "accelerateur": "Accélérateur",
    "accélérateur": "Accélérateur",
    "accélérateurs": "Accélérateur",
}

_STATUS_ALIASES = {
    "actif": "En activité",
    "active": "En activité",
    "en activité": "En activité",
    "inactif": "Inactif",
}


def _canonical(value: str | None, aliases: dict[str, str]) -> str:
    """Return the canonical spelling for a free-text label."""
    if not value:
        return ""
    return aliases.get(value.strip().lower(), value.strip())


def _to_list_item(incubator: Incubator) -> IncubatorListItem:
    """Map an Incubator ORM instance to the list schema."""
    return IncubatorListItem(
        id=incubator.incubator_id,
        name=incubator.incubator or "",
        type=_canonical(incubator.type_organisme, _TYPE_ALIASES),
        status=_canonical(incubator.statut, _STATUS_ALIASES),
        city=incubator.ville_organisme or incubator.ville or "",
        investmentPhases=split_tags(incubator.phases_investissement),
        image=incubator.image_url or "",
        sectors=split_tags(incubator.secteurs),
        linkedin=incubator.linkedin,
    )


def _to_detail(incubator: Incubator) -> IncubatorDetail:
    """Map an Incubator ORM instance to the full detail schema."""
    base = _to_list_item(incubator).model_dump()
    base["incubator_id"] = incubator.incubator_id
    detail = IncubatorDetail(**base)
    detail.description = incubator.description
    detail.email = incubator.email
    detail.telephone = incubator.telephone
    detail.ville_organisme = incubator.ville_organisme
    detail.date_creation = incubator.date_creation
    detail.partners_or_sponsors = incubator.partners_or_sponsors
    return detail


@router.get(
    "/",
    response_model=PaginatedResponse[IncubatorListItem],
    summary="List incubators",
    description="Paginated list of incubators with optional filtering by city, phase, type, and search.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def list_incubators(
    request: Request,
    db: Session = Depends(get_db),
    city: str | None = None,
    phase: str | None = None,
    type: str | None = None,
    search: str | None = None,
    sort_by: str = Query("priority", description="Column to sort by"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginatedResponse[IncubatorListItem]:
    """Return a paginated list of incubators."""
    query = db.query(Incubator)
    if city:
        query = query.filter(
            (Incubator.ville_organisme.ilike(f"%{city}%")) | (Incubator.ville.ilike(f"%{city}%"))
        )
    if phase:
        query = query.filter(Incubator.phases_investissement.ilike(f"%{phase}%"))
    if type:
        query = query.filter(Incubator.type_organisme.ilike(f"%{type}%"))
    if search:
        query = apply_search_filter(
            query, Incubator, search, "incubator", "ville_organisme", "description", "secteurs"
        )

    rows = query.all()
    if sort_by == "priority":
        rows.sort(key=lambda i: (_priority_score(i), i.incubator or ""), reverse=(order == "desc"))
    else:
        getattr(Incubator, sort_by, Incubator.incubator)
        rows.sort(
            key=lambda i: getattr(i, sort_by, i.incubator) or "",
            reverse=(order == "desc"),
        )

    total = len(rows)
    start = (page - 1) * page_size
    end = start + page_size
    page_rows = rows[start:end]
    return PaginatedResponse(
        items=[_to_list_item(i) for i in page_rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


@router.get(
    "/filters",
    response_model=dict,
    summary="Incubator filter options",
    description="Return available cities, phases, and types for filtering.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def incubator_filters(request: Request, db: Session = Depends(get_db)) -> dict[str, list[str]]:
    """Return distinct filter values for incubators."""
    rows = db.query(Incubator).all()
    cities = sorted({cast(str, i.ville_organisme or i.ville) for i in rows if i.ville_organisme or i.ville})
    phases = sorted(
        {tag.strip() for i in rows for tag in split_tags(i.phases_investissement) if tag}
    )
    types = sorted({i.type_organisme for i in rows if i.type_organisme})
    return {"cities": cities, "phases": phases, "types": types}


@router.get(
    "/export",
    summary="Export incubators as CSV",
    description="Download the current incubator directory as a CSV file (admin only).",
)
@limiter.limit("10/minute")
def export_incubators(
    request: Request,
    admin: AdminUserDep,
    db: Session = Depends(get_db),
    city: str | None = None,
    phase: str | None = None,
    type: str | None = None,
    search: str | None = None,
) -> Response:
    """Export filtered incubators as a CSV download."""
    query = db.query(Incubator)
    if city:
        query = query.filter(
            (Incubator.ville_organisme.ilike(f"%{city}%")) | (Incubator.ville.ilike(f"%{city}%"))
        )
    if phase:
        query = query.filter(Incubator.phases_investissement.ilike(f"%{phase}%"))
    if type:
        query = query.filter(Incubator.type_organisme.ilike(f"%{type}%"))
    if search:
        query = apply_search_filter(
            query, Incubator, search, "incubator", "ville_organisme", "description", "secteurs"
        )

    rows = query.order_by(Incubator.incubator).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Type", "Status", "City", "Phases", "Sectors", "Email"])
    for i in rows:
        writer.writerow(
            [
                i.incubator or "",
                i.type_organisme or "",
                i.statut or "",
                i.ville_organisme or i.ville or "",
                i.phases_investissement or "",
                i.secteurs or "",
                i.email or "",
            ]
        )

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=incubators_export.csv"},
    )


@router.get(
    "/{incubator_id}",
    response_model=IncubatorDetail,
    summary="Incubator detail",
    description="Return detailed information for a single incubator.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def get_incubator(request: Request, incubator_id: int, db: Session = Depends(get_db)) -> IncubatorDetail:
    """Return a single incubator by ID."""
    incubator = or_404(db.query(Incubator).filter(Incubator.incubator_id == incubator_id).first())
    return _to_detail(incubator)
