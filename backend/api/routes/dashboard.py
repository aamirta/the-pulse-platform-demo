"""Role-scoped dashboard API.

Backs the authenticated dashboard with real records. The role is taken from the
authenticated identity, never from a client-supplied parameter, so a member
cannot request the administrator view.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from backend.api.deps import UserOrMemberDep, get_db
from backend.api.limiter import limiter
from backend.core.config import settings
from backend.models import (
    DirectMessage,
    FundingRound,
    Incubator,
    Investor,
    Post,
    PulseMember,
    Startup,
    User,
)
from backend.schemas import (
    ChartSeries,
    DashboardModerationItem,
    DashboardResponse,
    DashboardStat,
    PostItem,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Profile fields that count toward the completeness indicator.
_PROFILE_FIELDS = ("full_name", "email", "role", "profile_pic", "linkedin", "form_data")

_INVESTOR_TERMS = ("investor", "investisseur", "vc", "angel", "fond")
_PARTNER_TERMS = (
    "incubateur",
    "accelerateur",
    "accélérateur",
    "programme",
    "partner",
    "partenaire",
    "studio",
)


def _resolve_role(current_user: User | None, member: PulseMember | None) -> str:
    """Return the dashboard role for the authenticated actor.

    Mirrors ``roleToDashboardRole`` in the SPA. Kept server-side so the view a
    caller receives is decided by their identity rather than by a query string.
    """
    if current_user and current_user.username == settings.ADMIN_USERNAME:
        return "admin"
    raw = (member.role if member else "").lower()
    if any(term in raw for term in _INVESTOR_TERMS):
        return "investor"
    if any(term in raw for term in _PARTNER_TERMS):
        return "partner"
    return "startup"


def _profile_completeness(member: PulseMember) -> int:
    """Return the percentage of profile fields the member has filled in."""
    filled = sum(1 for field in _PROFILE_FIELDS if getattr(member, field, None))
    return round(filled * 100 / len(_PROFILE_FIELDS))


def _funding_by_year(db: Session, limit: int = 6) -> ChartSeries:
    """Return total funding per year, in millions USD, for the ecosystem chart."""
    totals: dict[str, float] = {}
    rows = (
        db.query(FundingRound.date, FundingRound.raised_amount_usd)
        .filter(FundingRound.date.isnot(None))
        .all()
    )
    for date_value, raised in rows:
        year = str(date_value)[:4]
        if year.isdigit():
            totals[year] = totals.get(year, 0.0) + float(raised or 0) / 1_000_000
    years = sorted(totals)[-limit:]
    return ChartSeries(labels=years, values=[round(totals[year], 2) for year in years])


def _admin_dashboard(db: Session) -> tuple[list[DashboardStat], list[DashboardModerationItem]]:
    """Return administrator statistics and the real pending-confirmation queue."""
    pending_query = db.query(PulseMember).filter(PulseMember.is_confirmed.isnot(True))
    pending_count = pending_query.count()
    pending = pending_query.order_by(desc(PulseMember.created_at)).limit(10).all()

    stats = [
        DashboardStat(
            key="startups",
            label="Startups",
            value=str(db.query(func.count(Startup.startup_id)).scalar() or 0),
        ),
        DashboardStat(
            key="pending_members",
            label="Pending confirmation",
            value=str(pending_count),
            hint="Awaiting email confirmation",
        ),
        DashboardStat(
            key="members",
            label="Community members",
            value=str(db.query(func.count(PulseMember.id)).scalar() or 0),
        ),
        DashboardStat(
            key="posts",
            label="Published posts",
            value=str(
                db.query(func.count(Post.post_id)).filter(Post.is_published.is_(True)).scalar() or 0
            ),
        ),
    ]
    return stats, [DashboardModerationItem.model_validate(m) for m in pending]


def _member_dashboard(db: Session, member: PulseMember, role: str) -> list[DashboardStat]:
    """Return statistics scoped to a single community member."""
    actor_email = (member.email or "").strip().lower()

    unread = (
        db.query(func.count(DirectMessage.id))
        .filter(DirectMessage.to_email == actor_email, DirectMessage.is_read.isnot(True))
        .scalar()
        or 0
    )
    inbound = {
        row[0]
        for row in db.query(DirectMessage.from_email)
        .filter(DirectMessage.to_email == actor_email)
        .distinct()
        if row[0]
    }
    outbound = {
        row[0]
        for row in db.query(DirectMessage.to_email)
        .filter(DirectMessage.from_email == actor_email)
        .distinct()
        if row[0]
    }
    my_posts = (
        db.query(func.count(Post.post_id)).filter(Post.author_name == member.full_name).scalar() or 0
    )

    # The fourth card reflects the slice of the directory this role works with.
    if role == "investor":
        directory_label = "Startups in directory"
        directory_value = db.query(func.count(Startup.startup_id)).scalar() or 0
    elif role == "partner":
        directory_label = "Incubators & programmes"
        directory_value = db.query(func.count(Incubator.incubator_id)).scalar() or 0
    else:
        directory_label = "Investors to reach"
        directory_value = db.query(func.count(Investor.investor_id)).scalar() or 0

    return [
        DashboardStat(
            key="profile_completeness",
            label="Profile completeness",
            value=f"{_profile_completeness(member)}%",
            hint="Based on the fields on your member profile",
        ),
        DashboardStat(
            key="unread_messages",
            label="Unread messages",
            value=str(unread),
            hint=f"{len(inbound | outbound)} conversation(s)",
        ),
        DashboardStat(key="my_posts", label="Your posts", value=str(my_posts)),
        DashboardStat(key="directory", label=directory_label, value=str(directory_value)),
    ]


@router.get(
    "/",
    response_model=DashboardResponse,
    summary="Role-scoped dashboard",
    description=(
        "Return dashboard statistics for the authenticated actor. The role is derived "
        "from the caller's identity; it cannot be selected by the client."
    ),
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def get_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user_or_member: UserOrMemberDep = (None, None),
) -> DashboardResponse:
    """Return the dashboard payload for the authenticated user or member."""
    current_user, current_member = user_or_member
    role = _resolve_role(current_user, current_member)

    moderation_queue: list[DashboardModerationItem] = []
    if role == "admin":
        stats, moderation_queue = _admin_dashboard(db)
    elif current_member is not None:
        stats = _member_dashboard(db, current_member, role)
    else:
        # A non-admin User row has no member profile to summarise.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No dashboard is available for this account",
        )

    recent_posts = (
        db.query(Post)
        .filter(Post.is_published.is_(True))
        .order_by(desc(Post.created_at))
        .limit(5)
        .all()
    )

    return DashboardResponse(
        role=role,
        stats=stats,
        funding_by_year=_funding_by_year(db),
        moderation_queue=moderation_queue,
        recent_posts=[PostItem.model_validate(p) for p in recent_posts],
    )
