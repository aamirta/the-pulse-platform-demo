"""Maps / visualizer API routes."""

from collections import defaultdict

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.api.limiter import limiter
from backend.core.config import settings
from backend.models import Founder, Investor, Startup
from backend.schemas import CityAggregation, MapDataResponse, MapPoint

router = APIRouter(prefix="/maps", tags=["maps"])


def _normalize_city(location: str | None) -> tuple[str, str]:
    """Extract city and country from a location string."""
    if not location:
        return ("", "")
    parts = [p.strip() for p in location.split(",")]
    city = parts[0] if parts else ""
    country = parts[-1] if len(parts) > 1 else ""
    return city, country


@router.get(
    "/",
    response_model=MapDataResponse,
    summary="Map visualizer data",
    description="Return aggregated ecosystem points by city for map visualization.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def map_data(
    request: Request,
    db: Session = Depends(get_db),
    type: str | None = Query(None, description="Filter by type: startup, founder, investor"),
) -> MapDataResponse:
    """Return map visualizer data aggregated by city."""
    points: list[MapPoint] = []
    city_counts: dict[tuple[str, str, str], int] = defaultdict(int)

    if type is None or type == "startup":
        for s in db.query(Startup).filter(Startup.location.isnot(None)).all():
            city, country = _normalize_city(s.location)
            if city:
                city_counts[(city, country, "startup")] += 1

    if type is None or type == "founder":
        for f in db.query(Founder).filter(Founder.location.isnot(None)).all():
            city, country = _normalize_city(f.location)
            if city:
                city_counts[(city, country, "founder")] += 1

    if type is None or type == "investor":
        for i in (
            db.query(Investor)
            .filter((Investor.hq_location.isnot(None)) | (Investor.city.isnot(None)))
            .all()
        ):
            location = i.hq_location or i.city or ""
            city, country = _normalize_city(location)
            if city:
                city_counts[(city, country, "investor")] += 1

    for idx, ((city, country, entity_type), count) in enumerate(city_counts.items()):
        points.append(
            MapPoint(
                id=str(idx),
                type=entity_type,
                name=city,
                latitude=None,
                longitude=None,
                city=city,
                country=country,
                count=count,
            )
        )

    return MapDataResponse(points=points, total=len(points))


@router.get(
    "/cities",
    response_model=list[CityAggregation],
    summary="City aggregation",
    description="Return ecosystem counts aggregated by city.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def city_aggregation(request: Request, db: Session = Depends(get_db)) -> list[CityAggregation]:
    """Return city-level ecosystem aggregation."""
    agg: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"startups": 0, "founders": 0, "investors": 0}
    )

    for s in db.query(Startup).filter(Startup.location.isnot(None)).all():
        city, country = _normalize_city(s.location)
        if city:
            agg[(city, country)]["startups"] += 1

    for f in db.query(Founder).filter(Founder.location.isnot(None)).all():
        city, country = _normalize_city(f.location)
        if city:
            agg[(city, country)]["founders"] += 1

    for i in (
        db.query(Investor)
        .filter((Investor.hq_location.isnot(None)) | (Investor.city.isnot(None)))
        .all()
    ):
        location = i.hq_location or i.city or ""
        city, country = _normalize_city(location)
        if city:
            agg[(city, country)]["investors"] += 1

    return [
        CityAggregation(
            city=city,
            country=country,
            startups=counts["startups"],
            founders=counts["founders"],
            investors=counts["investors"],
        )
        for (city, country), counts in sorted(agg.items())
    ]
