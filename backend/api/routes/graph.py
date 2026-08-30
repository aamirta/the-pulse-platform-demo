"""Ecosystem relationship graph routes.

Every edge returned here is read from a persisted join record:

* ``founded``   -- ``StartupFounders`` (startup <-> founder)
* ``invested``  -- ``Investements`` -> ``FundingRounds`` (investor -> startup)
* ``incubated`` -- ``StartupIncubators`` (incubator -> startup)

Nothing is inferred from sector overlap and nothing is randomised: an edge exists
in the response only when the corresponding row exists in the database.
"""

from collections.abc import Sequence

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import Row
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.api.limiter import limiter
from backend.core.config import settings
from backend.models import (
    Founder,
    FundingRound,
    Incubator,
    IncubatorFounder,
    Investment,
    Investor,
    Startup,
    StartupFounder,
    StartupIncubator,
)
from backend.schemas import EcosystemGraph, GraphLink, GraphNode, GraphTotals

router = APIRouter(prefix="/graph", tags=["graph"])

# Node-type prefixes keep ids unique across entity tables, since a startup and an
# investor can legitimately share the same numeric primary key.
STARTUP = "startup"
FOUNDER = "founder"
INVESTOR = "investor"
INCUBATOR = "incubator"


def _founder_name(founder: Founder) -> str:
    """Return the best available display name for a founder."""
    if founder.name:
        return founder.name
    parts = [founder.first_name or "", founder.last_name or ""]
    return " ".join(p for p in parts if p).strip()


def _primary_sector(raw: str | None) -> str | None:
    """Return the first sector tag from a delimited sector string."""
    if not raw:
        return None
    for separator in (",", ";", "|"):
        if separator in raw:
            first = raw.split(separator)[0].strip()
            return first or None
    return raw.strip() or None


@router.get(
    "/ecosystem",
    response_model=EcosystemGraph,
    summary="Ecosystem relationship graph",
    description=(
        "Return the real relationship graph between startups, founders, investors and "
        "incubators. Edges come from StartupFounders, Investements/FundingRounds and "
        "StartupIncubators join records only."
    ),
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def ecosystem_graph(
    request: Request,
    db: Session = Depends(get_db),
    limit: int = Query(
        260,
        ge=10,
        le=2000,
        description="Maximum number of nodes to return, selected by connection count.",
    ),
    include_incubators: bool = Query(
        True, description="Include incubator/accelerator relationships."
    ),
) -> EcosystemGraph:
    """Build the ecosystem relationship graph from persisted join records."""
    # ------------------------------------------------------------------
    # 1. Read every real edge.
    # ------------------------------------------------------------------
    founded_rows = db.query(StartupFounder.startup_id, StartupFounder.founder_id).all()

    # investor -> startup, resolved through the funding round that names the startup.
    invested_rows = (
        db.query(Investment.investor_id, FundingRound.startup_id)
        .join(FundingRound, Investment.funding_round_id == FundingRound.funding_round_id)
        .filter(Investment.investor_id.isnot(None))
        .filter(FundingRound.startup_id.isnot(None))
        .distinct()
        .all()
    )

    incubated_rows: Sequence[Row[tuple[int, int]]] = []
    supported_rows: Sequence[Row[tuple[int, str]]] = []
    if include_incubators:
        incubated_rows = db.query(
            StartupIncubator.incubator_id, StartupIncubator.startup_id
        ).all()
        # Incubator -> founder affiliations. These live in IncubatorFounders and
        # are the only edge type that does not terminate on a startup.
        supported_rows = db.query(
            IncubatorFounder.incubator_id, IncubatorFounder.founder_id
        ).all()

    # ------------------------------------------------------------------
    # 2. Keep only edges whose endpoints still exist, so the graph never
    #    references a deleted or unnamed record.
    # ------------------------------------------------------------------
    startup_rows = db.query(
        Startup.startup_id, Startup.startup_name, Startup.sector, Startup.location
    ).all()
    startups = {
        sid: (name, sector, location)
        for sid, name, sector, location in startup_rows
        if name and name.strip()
    }

    founders = {f.founder_id: f for f in db.query(Founder).all() if _founder_name(f)}

    investor_rows = db.query(
        Investor.investor_id, Investor.investor_name, Investor.hq_location
    ).all()
    investors = {
        iid: (name, location) for iid, name, location in investor_rows if name and name.strip()
    }

    incubators: dict[int, tuple[str, str | None]] = {}
    if include_incubators:
        incubator_rows = db.query(
            Incubator.incubator_id, Incubator.incubator, Incubator.ville_organisme
        ).all()
        incubators = {
            iid: (name, ville) for iid, name, ville in incubator_rows if name and name.strip()
        }

    # De-duplicate edges: the same pair can appear across several funding rounds.
    edges: set[tuple[str, str, str]] = set()

    for startup_id, founder_id in founded_rows:
        if startup_id in startups and founder_id in founders:
            edges.add((f"{FOUNDER}-{founder_id}", f"{STARTUP}-{startup_id}", "founded"))

    for investor_id, startup_id in invested_rows:
        if investor_id in investors and startup_id in startups:
            edges.add((f"{INVESTOR}-{investor_id}", f"{STARTUP}-{startup_id}", "invested"))

    for incubator_id, startup_id in incubated_rows:
        if incubator_id in incubators and startup_id in startups:
            edges.add((f"{INCUBATOR}-{incubator_id}", f"{STARTUP}-{startup_id}", "incubated"))

    for incubator_id, founder_id in supported_rows:
        if incubator_id in incubators and founder_id in founders:
            edges.add((f"{INCUBATOR}-{incubator_id}", f"{FOUNDER}-{founder_id}", "supported"))

    totals = GraphTotals(
        startups=len(startups),
        founders=len(founders),
        investors=len(investors),
        incubators=len(incubators),
        founded=sum(1 for e in edges if e[2] == "founded"),
        invested=sum(1 for e in edges if e[2] == "invested"),
        incubated=sum(1 for e in edges if e[2] == "incubated"),
        supported=sum(1 for e in edges if e[2] == "supported"),
    )

    # ------------------------------------------------------------------
    # 3. Select the densest connected slice that fits the node budget.
    #    Startups are the hubs, so we walk them by degree and pull in each
    #    hub together with its neighbours. Adding a node only alongside its
    #    hub guarantees every returned node keeps at least one visible edge.
    # ------------------------------------------------------------------
    neighbours: dict[str, list[tuple[str, str]]] = {}
    degree: dict[str, int] = {}
    for source, target, kind in edges:
        neighbours.setdefault(target, []).append((source, kind))
        degree[source] = degree.get(source, 0) + 1
        degree[target] = degree.get(target, 0) + 1

    ranked_hubs = sorted(
        neighbours.keys(), key=lambda node_id: (-degree.get(node_id, 0), node_id)
    )

    selected: set[str] = set()
    truncated = False
    for hub in ranked_hubs:
        group = {hub} | {peer for peer, _ in neighbours[hub]}
        if len(selected | group) > limit:
            # Stop at the first hub that would overflow the budget, rather than
            # skipping ahead, so the result stays the top-N densest cluster.
            truncated = True
            break
        selected |= group

    if not selected and ranked_hubs:
        # Budget too small for even the densest hub's full neighbourhood: keep
        # that hub plus as many neighbours as fit, so the caller still gets a
        # connected star rather than a single edgeless node.
        top = ranked_hubs[0]
        selected = {top}
        for peer, _ in neighbours[top]:
            if len(selected) >= limit:
                break
            selected.add(peer)
        truncated = True

    visible_links = [
        GraphLink(source=source, target=target, type=kind)
        for source, target, kind in sorted(edges)
        if source in selected and target in selected
    ]

    # Recount degrees against what is actually drawn, so the UI's
    # "N connection(s)" figure matches the visible edges.
    visible_degree: dict[str, int] = {}
    for link in visible_links:
        visible_degree[link.source] = visible_degree.get(link.source, 0) + 1
        visible_degree[link.target] = visible_degree.get(link.target, 0) + 1

    # ------------------------------------------------------------------
    # 4. Materialise the selected nodes.
    # ------------------------------------------------------------------
    nodes: list[GraphNode] = []
    for node_id in selected:
        kind, _, ref = node_id.partition("-")
        if kind == STARTUP:
            name, sector, location = startups[int(ref)]
            nodes.append(
                GraphNode(
                    id=node_id,
                    refId=ref,
                    name=name,
                    type=STARTUP,
                    sector=_primary_sector(sector),
                    location=location,
                    connections=visible_degree.get(node_id, 0),
                )
            )
        elif kind == FOUNDER:
            founder = founders[ref]
            nodes.append(
                GraphNode(
                    id=node_id,
                    refId=ref,
                    name=_founder_name(founder),
                    type=FOUNDER,
                    sector=founder.current_title or None,
                    location=founder.location,
                    connections=visible_degree.get(node_id, 0),
                )
            )
        elif kind == INVESTOR:
            name, location = investors[int(ref)]
            nodes.append(
                GraphNode(
                    id=node_id,
                    refId=ref,
                    name=name,
                    type=INVESTOR,
                    location=location,
                    connections=visible_degree.get(node_id, 0),
                )
            )
        else:
            name, ville = incubators[int(ref)]
            nodes.append(
                GraphNode(
                    id=node_id,
                    refId=ref,
                    name=name,
                    type=INCUBATOR,
                    location=ville,
                    connections=visible_degree.get(node_id, 0),
                )
            )

    nodes.sort(key=lambda n: (-n.connections, n.name))

    return EcosystemGraph(nodes=nodes, links=visible_links, totals=totals, truncated=truncated)
