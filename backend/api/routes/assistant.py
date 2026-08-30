"""Ecosystem assistant answering from the platform's own data.

The SPA previously shipped a hardcoded map of canned replies containing invented
figures ("1,951 indexed startups", "FinTech - 245 startups") that did not match
the database. This router answers the same questions from live aggregates, so
every number returned is real and every response names the tables it came from.

It is deliberately a retrieval endpoint, not a language model: it classifies the
question into a known intent and runs a real query. Unrecognised questions say so
rather than inventing an answer.
"""

import re

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.api.common import split_tags
from backend.api.deps import get_db
from backend.api.limiter import limiter
from backend.core.config import settings
from backend.models import Founder, FundingRound, Incubator, Investor, Startup
from backend.schemas import AssistantAnswer, AssistantQuery, TrendItem

router = APIRouter(prefix="/assistant", tags=["assistant"])

# Intent keywords, checked in order. French and English both occur in the UI.
_SECTOR_TERMS = ("secteur", "sector", "industrie", "industry", "domaine")
_FUNDING_TERMS = ("lev", "funding", "raise", "fund", "financement", "investissement")
_INVESTOR_TERMS = ("investisseur", "investor", "vc", "fond")
_INCUBATOR_TERMS = ("incubateur", "incubator", "accelerateur", "accélérateur", "programme")
_CITY_TERMS = ("ville", "city", "casablanca", "rabat", "marrakech", "tanger", "where")
_COUNT_TERMS = ("combien", "how many", "nombre", "total", "count")


def _top_sectors(db: Session, limit: int = 8) -> list[TrendItem]:
    """Return the most common startup sectors with real counts."""
    counts: dict[str, int] = {}
    for (sector_field,) in db.query(Startup.sector).filter(Startup.sector.isnot(None)):
        for sector in split_tags(sector_field):
            counts[sector] = counts.get(sector, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]
    return [TrendItem(tag=tag, count=count) for tag, count in ranked]


def _top_cities(db: Session, limit: int = 8) -> list[TrendItem]:
    """Return the cities with the most startups."""
    counts: dict[str, int] = {}
    for (location,) in db.query(Startup.location).filter(Startup.location.isnot(None)):
        city = (location or "").split(",")[0].strip()
        if city:
            counts[city] = counts.get(city, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]
    return [TrendItem(tag=tag, count=count) for tag, count in ranked]


def _recent_raises(db: Session, limit: int = 8) -> list[TrendItem]:
    """Return the largest recorded funding rounds, in whole USD."""
    rows = (
        db.query(FundingRound.startup_name, FundingRound.raised_amount_usd)
        .filter(FundingRound.raised_amount_usd.isnot(None))
        .filter(FundingRound.startup_name.isnot(None))
        .order_by(FundingRound.raised_amount_usd.desc())
        .limit(limit)
        .all()
    )
    return [TrendItem(tag=str(name), count=int(amount or 0)) for name, amount in rows]


def _top_investors(db: Session, limit: int = 8) -> list[TrendItem]:
    """Return referenced investors."""
    rows = (
        db.query(Investor.investor_name)
        .filter(Investor.investor_name.isnot(None))
        .limit(limit)
        .all()
    )
    return [TrendItem(tag=str(name), count=1) for (name,) in rows]


def _incubators(db: Session, limit: int = 8) -> list[TrendItem]:
    """Return incubators with their city."""
    rows = (
        db.query(Incubator.incubator, Incubator.ville_organisme)
        .filter(Incubator.incubator.isnot(None))
        .limit(limit)
        .all()
    )
    return [TrendItem(tag=f"{name} ({city or 'Maroc'})", count=1) for name, city in rows]


@router.post(
    "/query",
    response_model=AssistantAnswer,
    summary="Ask the ecosystem assistant",
    description=(
        "Answer a question using live aggregates from the platform database. "
        "Unrecognised questions return a capability list rather than a generated guess."
    ),
)
@limiter.limit(settings.RATE_LIMIT_SEARCH)
def query_assistant(
    request: Request,
    data: AssistantQuery,
    db: Session = Depends(get_db),
) -> AssistantAnswer:
    """Classify the question and answer it from real data."""
    question = data.question.strip().lower()
    # Normalise punctuation so keyword checks are not defeated by marks.
    normalised = re.sub(r"[^\w\sàâçéèêëîïôûùüÿñæœ]", " ", question)

    def has(terms: tuple[str, ...]) -> bool:
        return any(term in normalised for term in terms)

    total_startups = db.query(func.count(Startup.startup_id)).scalar() or 0

    if has(_SECTOR_TERMS):
        points = _top_sectors(db)
        listed = ", ".join(f"{item.tag} ({item.count})" for item in points)
        return AssistantAnswer(
            answer=(
                f"Les secteurs les plus représentés parmi les {total_startups} startups "
                f"indexées : {listed}."
            ),
            intent="top_sectors",
            data=points,
            sources=["Startups"],
        )

    if has(_FUNDING_TERMS):
        points = _recent_raises(db)
        total_rounds = db.query(func.count(FundingRound.funding_round_id)).scalar() or 0
        listed = ", ".join(f"{item.tag} (${item.count:,})" for item in points)
        return AssistantAnswer(
            answer=f"{total_rounds} levées sont enregistrées. Les plus importantes : {listed}.",
            intent="top_raises",
            data=points,
            sources=["FundingRounds"],
        )

    if has(_INVESTOR_TERMS):
        points = _top_investors(db)
        total_investors = db.query(func.count(Investor.investor_id)).scalar() or 0
        listed = ", ".join(item.tag for item in points)
        return AssistantAnswer(
            answer=f"{total_investors} investisseurs sont référencés, dont : {listed}.",
            intent="investors",
            data=points,
            sources=["Investors"],
        )

    if has(_INCUBATOR_TERMS):
        points = _incubators(db)
        total = db.query(func.count(Incubator.incubator_id)).scalar() or 0
        listed = ", ".join(item.tag for item in points)
        return AssistantAnswer(
            answer=f"{total} incubateurs et programmes sont référencés, dont : {listed}.",
            intent="incubators",
            data=points,
            sources=["Incubators"],
        )

    if has(_CITY_TERMS):
        points = _top_cities(db)
        listed = ", ".join(f"{item.tag} ({item.count})" for item in points)
        return AssistantAnswer(
            answer=f"Répartition des startups par ville : {listed}.",
            intent="cities",
            data=points,
            sources=["Startups"],
        )

    if has(_COUNT_TERMS):
        counts = [
            TrendItem(tag="Startups", count=total_startups),
            TrendItem(tag="Founders", count=db.query(func.count(Founder.founder_id)).scalar() or 0),
            TrendItem(
                tag="Investors", count=db.query(func.count(Investor.investor_id)).scalar() or 0
            ),
            TrendItem(
                tag="Incubators", count=db.query(func.count(Incubator.incubator_id)).scalar() or 0
            ),
        ]
        listed = ", ".join(f"{item.count} {item.tag.lower()}" for item in counts)
        return AssistantAnswer(
            answer=f"L'écosystème indexé compte {listed}.",
            intent="counts",
            data=counts,
            sources=["Startups", "Founders", "Investors", "Incubators"],
        )

    # No invented answer: state the real capabilities instead.
    return AssistantAnswer(
        answer=(
            "Je réponds à partir des données de la plateforme. Vous pouvez me demander : "
            "les secteurs les plus actifs, les dernières levées de fonds, les investisseurs "
            "référencés, les incubateurs, ou la répartition des startups par ville."
        ),
        intent="unknown",
        data=[],
        sources=[],
    )
