"""Vocabulary for Deal Room marketplace posts.

Pure data with no database or request dependency, so the validators, the filter
endpoint and the tests all read the same lists. Keeping it here rather than in
the route module is what stops the UI's dropdown and the server's validation
drifting apart: ``/deal-room-posts/meta`` serves these exact tuples to the
client, so a value the client can pick is by construction a value the server
accepts.
"""

from __future__ import annotations

from typing import Final

# ---------------------------------------------------------------------------
# What kind of ask a post represents
# ---------------------------------------------------------------------------
POST_TYPE_RAISING: Final = "raising_capital"
POST_TYPE_OFFERING_CAPITAL: Final = "offering_capital"
POST_TYPE_COFOUNDER: Final = "seeking_cofounder"
POST_TYPE_ADVISOR: Final = "seeking_advisor"
POST_TYPE_TALENT: Final = "seeking_talent"
POST_TYPE_PARTNERSHIP: Final = "seeking_partnership"
POST_TYPE_SERVICE: Final = "offering_service"
POST_TYPE_MENTORSHIP: Final = "offering_mentorship"

POST_TYPES: Final[tuple[str, ...]] = (
    POST_TYPE_RAISING,
    POST_TYPE_OFFERING_CAPITAL,
    POST_TYPE_COFOUNDER,
    POST_TYPE_ADVISOR,
    POST_TYPE_TALENT,
    POST_TYPE_PARTNERSHIP,
    POST_TYPE_SERVICE,
    POST_TYPE_MENTORSHIP,
)

# Which post types are only meaningful with a money figure attached. Used to
# decide whether an empty amount range is worth warning about, never to reject.
CAPITAL_POST_TYPES: Final[frozenset[str]] = frozenset(
    {POST_TYPE_RAISING, POST_TYPE_OFFERING_CAPITAL}
)

# ---------------------------------------------------------------------------
# Who the author wants to hear from
# ---------------------------------------------------------------------------
COUNTERPARTY_TYPES: Final[tuple[str, ...]] = (
    "any",
    "investor",
    "founder",
    "startup",
    "expert",
    "incubator",
    "service_provider",
    "talent",
)

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
STATUS_DRAFT: Final = "draft"
STATUS_PUBLISHED: Final = "published"
STATUS_CLOSED: Final = "closed"
STATUS_ARCHIVED: Final = "archived"

POST_STATUSES: Final[tuple[str, ...]] = (
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    STATUS_CLOSED,
    STATUS_ARCHIVED,
)

# Only these appear on the public board. A closed post stays readable through
# its own URL — the author's counterparties may still be mid-conversation — but
# it is not surfaced to new browsers.
BOARD_STATUSES: Final[frozenset[str]] = frozenset({STATUS_PUBLISHED})

# Transitions the author may drive. Anything absent here is refused, so an
# archived post cannot be quietly resurrected into the board.
ALLOWED_TRANSITIONS: Final[dict[str, frozenset[str]]] = {
    STATUS_DRAFT: frozenset({STATUS_PUBLISHED, STATUS_ARCHIVED}),
    STATUS_PUBLISHED: frozenset({STATUS_CLOSED, STATUS_ARCHIVED}),
    STATUS_CLOSED: frozenset({STATUS_PUBLISHED, STATUS_ARCHIVED}),
    STATUS_ARCHIVED: frozenset(),
}

# ---------------------------------------------------------------------------
# Moderation
# ---------------------------------------------------------------------------
MODERATION_VISIBLE: Final = "visible"
MODERATION_FLAGGED: Final = "flagged"
MODERATION_REMOVED: Final = "removed"

MODERATION_STATUSES: Final[tuple[str, ...]] = (
    MODERATION_VISIBLE,
    MODERATION_FLAGGED,
    MODERATION_REMOVED,
)

# A flagged post is still readable: flagging marks it for a human to look at,
# and hiding it on suspicion alone would make reporting a censorship button.
# Only "removed" takes a post off the board.
HIDDEN_MODERATION_STATUSES: Final[frozenset[str]] = frozenset({MODERATION_REMOVED})

REPORT_REASONS: Final[tuple[str, ...]] = (
    "spam",
    "misleading",
    "offensive",
    "scam",
    "off_topic",
    "other",
)

REPORT_STATUSES: Final[tuple[str, ...]] = ("open", "actioned", "dismissed")

RESPONSE_STATUSES: Final[tuple[str, ...]] = ("pending", "accepted", "declined")

# ---------------------------------------------------------------------------
# Descriptive facets
# ---------------------------------------------------------------------------
COMMITMENT_LEVELS: Final[tuple[str, ...]] = (
    "full_time",
    "part_time",
    "advisory",
    "one_off",
    "equity_only",
)

# Suggested stages. The column is free text so an unlisted stage still saves;
# these drive the dropdown and the board's filter chips.
SUGGESTED_STAGES: Final[tuple[str, ...]] = (
    "idea",
    "pre_seed",
    "seed",
    "series_a",
    "series_b",
    "growth",
    "not_applicable",
)


def is_valid_post_type(value: str | None) -> bool:
    return value in POST_TYPES


def is_valid_counterparty(value: str | None) -> bool:
    return value in COUNTERPARTY_TYPES


def is_valid_status(value: str | None) -> bool:
    return value in POST_STATUSES


def can_transition(current: str, target: str) -> bool:
    """Return True if the author may move a post from ``current`` to ``target``."""
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())


def is_publicly_listed(status: str, moderation_status: str) -> bool:
    """Return True if a post belongs on the public board."""
    return status in BOARD_STATUSES and moderation_status not in HIDDEN_MODERATION_STATUSES


__all__ = [
    "ALLOWED_TRANSITIONS",
    "BOARD_STATUSES",
    "CAPITAL_POST_TYPES",
    "COMMITMENT_LEVELS",
    "COUNTERPARTY_TYPES",
    "HIDDEN_MODERATION_STATUSES",
    "MODERATION_FLAGGED",
    "MODERATION_REMOVED",
    "MODERATION_STATUSES",
    "MODERATION_VISIBLE",
    "POST_STATUSES",
    "POST_TYPES",
    "REPORT_REASONS",
    "REPORT_STATUSES",
    "RESPONSE_STATUSES",
    "STATUS_ARCHIVED",
    "STATUS_CLOSED",
    "STATUS_DRAFT",
    "STATUS_PUBLISHED",
    "SUGGESTED_STAGES",
    "can_transition",
    "is_publicly_listed",
    "is_valid_counterparty",
    "is_valid_post_type",
    "is_valid_status",
]
