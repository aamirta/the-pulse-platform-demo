"""Stats API routes."""

from collections import Counter
from typing import Any, cast

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.api.common import split_tags
from backend.api.deps import get_db
from backend.api.limiter import limiter
from backend.core.config import settings
from backend.models import Founder, FundingRound, Incubator, Investor, Resource, Startup
from backend.schemas import ChartSeries, EcosystemStatItem, HomeStats, StatsResponse, TrendItem

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get(
    "/home",
    response_model=HomeStats,
    summary="Home page stats",
    description="Return aggregated counts for the home page.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def home_stats(request: Request, db: Session = Depends(get_db)) -> HomeStats:
    """Return home page statistics."""
    startups = db.query(Startup).count()
    founders = db.query(Founder).count()
    investors = db.query(Investor).count()
    # Count incubator records. This previously counted distinct
    # ``Startup.incubated_by`` strings, which disagreed with every other surface
    # (the ecosystem graph counts Incubators rows) and under-reported the total.
    incubators = db.query(Incubator).count()
    funding_rounds = db.query(FundingRound).count()
    total_funding = db.query(func.sum(FundingRound.raised_amount_usd)).scalar() or 0
    # Opportunities live in the resources catalogue, not articles, and its
    # categories are French — the previous filter counted the wrong table with an
    # English-only term and always returned 0.
    from backend.api.routes.resources import _OPPORTUNITY_MARKERS, _category_filter

    opportunities = db.query(Resource).filter(_category_filter(_OPPORTUNITY_MARKERS)).count()

    sectors = set()
    for row in db.query(Startup.sector).filter(Startup.sector.isnot(None)).all():
        sectors.update(split_tags(row[0]))

    cities = set()
    for row in db.query(Startup.location).filter(Startup.location.isnot(None)).distinct().all():
        if row[0]:
            cities.add(row[0].split(",")[0].strip())

    return HomeStats(
        startups=startups,
        founders=founders,
        investors=investors,
        incubators=incubators,
        totalFunding=f"${total_funding / 1_000_000:.1f}M" if total_funding else "$0",
        opportunities=opportunities,
        sectors=len(sectors),
        cities=len(cities),
        fundingRounds=funding_rounds,
    )


@router.get(
    "/charts",
    response_model=StatsResponse,
    summary="Stats and charts",
    description="Return home stats plus trends, funding by stage, funding by year, and top sectors.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def charts(request: Request, db: Session = Depends(get_db)) -> StatsResponse:
    """Return aggregated charts and trends."""
    counts = home_stats(request, db)

    # Top sectors by startup count
    sector_counts: Counter[str] = Counter()
    for row in db.query(Startup.sector).filter(Startup.sector.isnot(None)).all():
        sector_counts.update(split_tags(row[0]))
    top_sectors = sector_counts.most_common(10)

    # Funding by stage (normalize round names like "Pre Seed Round - Startup" to "Pre Seed Round")
    stage_totals: dict[str, float] = {}
    for fr in db.query(FundingRound).filter(FundingRound.round_name.isnot(None)).all():
        amount = float(cast(Any, fr.raised_amount_usd) or 0)
        if amount <= 0:
            continue
        normalized = cast(str, fr.round_name).split(" - ", 1)[0].strip()
        stage_totals[normalized] = stage_totals.get(normalized, 0.0) + amount
    sorted_stages = sorted(stage_totals.items(), key=lambda x: x[1], reverse=True)
    stage_labels = [s[0] for s in sorted_stages]
    stage_values = [s[1] for s in sorted_stages]

    # Funding by year (extracted from date string)
    year_totals: dict[str, float] = {}
    for fr in db.query(FundingRound).filter(FundingRound.date.isnot(None)).all():
        year = cast(str, fr.date)[:4]
        if year.isdigit():
            year_totals[year] = year_totals.get(year, 0) + float(cast(Any, fr.raised_amount_usd) or 0)
    sorted_years = sorted(year_totals.keys())

    trends = [TrendItem(tag=tag, count=count) for tag, count in top_sectors]

    return StatsResponse(
        counts=counts,
        trends=trends,
        fundingByStage=ChartSeries(labels=stage_labels, values=stage_values),
        fundingByYear=ChartSeries(
            labels=sorted_years, values=[year_totals[y] for y in sorted_years]
        ),
        topSectors=ChartSeries(
            labels=[item.tag for item in trends],
            values=[item.count for item in trends],
        ),
        topFundedStartups=_top_funded_startups(db),
        fundingBySector=_funding_by_sector(db),
        startupsByCity=_startups_by_city(db),
    )


# `location` mostly holds a city, but a few rows carry a country instead. Those
# would sit at the top of a "startups by city" chart without naming a city.
_NON_CITY_LOCATIONS = {"morocco", "maroc"}


def _startups_by_city(db: Session, limit: int = 5) -> ChartSeries:
    """Top cities by startup count, with the remainder grouped together."""
    counts: Counter[str] = Counter()
    for (location,) in db.query(Startup.location).filter(Startup.location.isnot(None)).all():
        city = (location or "").strip()
        if not city or city.lower() in _NON_CITY_LOCATIONS:
            continue
        counts[city] += 1

    top = counts.most_common(limit)
    labels = [city for city, _ in top]
    values: list[float] = [float(count) for _, count in top]

    remainder = sum(counts.values()) - sum(int(v) for v in values)
    if remainder > 0:
        labels.append("Autres")
        values.append(float(remainder))

    return ChartSeries(labels=labels, values=values)


# Aggregate roll-ups that distort the per-startup chart; excluded by name.
_FUNDING_CHART_EXCLUDED = ("Argan Infrastructure Fund", "chari")


def _top_funded_startups(db: Session, n: int = 7) -> ChartSeries:
    """Return top startups by total raised funding (legacy toptotalfundingByStartup).

    Rounds are summed in the database. Iterating startups and touching the lazy
    ``funding_rounds`` relationship instead issued one query per startup — 1109
    queries against production data.
    """
    rounds_total = (
        db.query(
            FundingRound.startup_id.label("startup_id"),
            func.sum(FundingRound.raised_amount_usd).label("rounds_total"),
        )
        .filter(FundingRound.startup_id.isnot(None))
        .group_by(FundingRound.startup_id)
        .subquery()
    )

    rows = (
        db.query(
            Startup.startup_name,
            Startup.total_funding_usd,
            rounds_total.c.rounds_total,
        )
        .outerjoin(rounds_total, rounds_total.c.startup_id == Startup.startup_id)
        .filter(Startup.startup_name.isnot(None))
        .filter(Startup.startup_name.notin_(_FUNDING_CHART_EXCLUDED))
        .all()
    )

    # The larger of the two funding sources is picked in Python: SQL GREATEST is
    # not portable to the SQLite database the test suite runs against.
    totals: list[tuple[str, float]] = []
    for name, total_field, total_rounds in rows:
        total_funding = max(float(total_rounds or 0), float(total_field or 0))
        if total_funding > 0:
            totals.append((cast(str, name), total_funding / 1_000_000))

    sorted_items = sorted(totals, key=lambda x: x[1], reverse=True)[:n]
    return ChartSeries(
        labels=[item[0] for item in sorted_items],
        values=[item[1] for item in sorted_items],
    )


def _funding_by_sector(db: Session, n: int = 10) -> ChartSeries:
    """Return total funding grouped by startup sector (legacy get_total_funding_by_sector).

    Joins to Startup up front; the previous version resolved ``fr.startup``
    lazily inside the loop, costing one query per funding round.
    """
    rows = (
        db.query(Startup.sector, FundingRound.raised_amount_usd)
        .join(Startup, Startup.startup_id == FundingRound.startup_id)
        .filter(FundingRound.raised_amount_usd.isnot(None))
        .filter(Startup.sector.isnot(None))
        .all()
    )

    sector_totals: dict[str, float] = {}
    for sector_field, raised in rows:
        amount = float(raised or 0) / 1_000_000
        for sector in split_tags(sector_field):
            sector_totals[sector] = sector_totals.get(sector, 0.0) + amount

    sorted_items = sorted(sector_totals.items(), key=lambda x: x[1], reverse=True)[:n]
    return ChartSeries(
        labels=[item[0] for item in sorted_items],
        values=[item[1] for item in sorted_items],
    )


@router.get(
    "/trends",
    response_model=list[TrendItem],
    summary="Top sector trends",
    description="Return the most common startup sectors as trend items.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def trends(request: Request, db: Session = Depends(get_db)) -> list[TrendItem]:
    """Return trending sectors."""
    counter: Counter[str] = Counter()
    for row in db.query(Startup.sector).filter(Startup.sector.isnot(None)).all():
        counter.update(split_tags(row[0]))
    return [TrendItem(tag=tag, count=count) for tag, count in counter.most_common(20)]


@router.get(
    "/ecosystem",
    response_model=list[EcosystemStatItem],
    summary="Ecosystem stats cards",
    description="Return stats formatted as ecosystem stat cards for the frontend.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def ecosystem_cards(request: Request, db: Session = Depends(get_db)) -> list[EcosystemStatItem]:
    """Return ecosystem stat cards."""
    stats = home_stats(request, db)
    return [
        EcosystemStatItem(label="Startups", value=str(stats.startups), icon="Rocket"),
        EcosystemStatItem(label="Founders", value=str(stats.founders), icon="Users"),
        EcosystemStatItem(label="Investors", value=str(stats.investors), icon="Landmark"),
        EcosystemStatItem(label="Incubators", value=str(stats.incubators), icon="Building"),
        EcosystemStatItem(label="Funding", value=stats.totalFunding, icon="TrendingUp"),
    ]


@router.get(
    "/top-funded-startups",
    response_model=ChartSeries,
    summary="Top funded startups",
    description="Return the top startups by total raised funding, in millions USD.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def top_funded_startups(
    request: Request, db: Session = Depends(get_db), limit: int = Query(7, ge=1, le=50)
) -> ChartSeries:
    """Return top funded startups chart."""
    return _top_funded_startups(db, n=limit)


@router.get(
    "/funding-by-sector",
    response_model=ChartSeries,
    summary="Funding by sector",
    description="Return total raised funding grouped by startup sector, in millions USD.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def funding_by_sector(
    request: Request, db: Session = Depends(get_db), limit: int = Query(10, ge=1, le=50)
) -> ChartSeries:
    """Return funding by sector chart."""
    return _funding_by_sector(db, n=limit)
