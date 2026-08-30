"""Deal Room permission algebra.

The seven permission levels the product exposes are not a single ladder:
``view_watermark`` is *more* restrictive than ``view``, not a rung above it. So
each level is decomposed into a capability rank plus a watermark requirement,
and comparisons are made on the rank while the watermark flag travels alongside.

Nothing in this module touches the database or the request; it is pure so the
rules can be unit-tested in isolation from FastAPI.
"""

from __future__ import annotations

from typing import Final

PERMISSION_NONE: Final = "none"
PERMISSION_VIEW: Final = "view"
PERMISSION_VIEW_WATERMARK: Final = "view_watermark"
PERMISSION_DOWNLOAD: Final = "download"
PERMISSION_DOWNLOAD_WATERMARK: Final = "download_watermark"
PERMISSION_UPLOAD: Final = "upload"
PERMISSION_MANAGE: Final = "manage"

ALL_PERMISSIONS: Final[tuple[str, ...]] = (
    PERMISSION_NONE,
    PERMISSION_VIEW,
    PERMISSION_VIEW_WATERMARK,
    PERMISSION_DOWNLOAD,
    PERMISSION_DOWNLOAD_WATERMARK,
    PERMISSION_UPLOAD,
    PERMISSION_MANAGE,
)

# Capability rank. Watermarked variants share the rank of their plain
# counterpart because watermarking restricts *how* content is delivered, not
# *what* the holder may do.
RANK_NONE: Final = 0
RANK_VIEW: Final = 1
RANK_DOWNLOAD: Final = 2
RANK_UPLOAD: Final = 3
RANK_MANAGE: Final = 4

_RANK: Final[dict[str, int]] = {
    PERMISSION_NONE: RANK_NONE,
    PERMISSION_VIEW: RANK_VIEW,
    PERMISSION_VIEW_WATERMARK: RANK_VIEW,
    PERMISSION_DOWNLOAD: RANK_DOWNLOAD,
    PERMISSION_DOWNLOAD_WATERMARK: RANK_DOWNLOAD,
    PERMISSION_UPLOAD: RANK_UPLOAD,
    PERMISSION_MANAGE: RANK_MANAGE,
}

_WATERMARKED: Final[frozenset[str]] = frozenset(
    {PERMISSION_VIEW_WATERMARK, PERMISSION_DOWNLOAD_WATERMARK}
)

# Deal room document categories offered in the UI.
DEAL_ROOM_CATEGORIES: Final[tuple[str, ...]] = (
    "company_overview",
    "pitch_deck",
    "business_model",
    "market",
    "traction",
    "financials",
    "legal",
    "team",
    "cap_table",
    "product",
    "other",
)

# Participant lifecycle states that permit any access at all.
ACTIVE_PARTICIPANT_STATUSES: Final[frozenset[str]] = frozenset({"active"})


def is_valid_permission(permission: str | None) -> bool:
    """Return True if ``permission`` is one of the seven supported levels."""
    return permission in _RANK


def rank(permission: str | None) -> int:
    """Return the capability rank of a permission; unknown values rank as none.

    Defaulting unknown input to ``RANK_NONE`` means a typo or a value injected
    into the database can only ever *reduce* access, never widen it.
    """
    if permission is None:
        return RANK_NONE
    return _RANK.get(permission, RANK_NONE)


def requires_watermark(permission: str | None) -> bool:
    """Return True if this permission level mandates a watermarked rendition."""
    return permission in _WATERMARKED


def can_view(permission: str | None) -> bool:
    """Return True if the permission allows reading a document at all."""
    return rank(permission) >= RANK_VIEW


def can_download(permission: str | None) -> bool:
    """Return True if the permission allows retrieving the file itself."""
    return rank(permission) >= RANK_DOWNLOAD


def can_upload(permission: str | None) -> bool:
    """Return True if the permission allows adding or replacing documents."""
    return rank(permission) >= RANK_UPLOAD


def can_manage(permission: str | None) -> bool:
    """Return True if the permission allows administering the room."""
    return rank(permission) >= RANK_MANAGE


def most_restrictive(*permissions: str | None) -> str:
    """Return the lowest-ranked permission, preserving any watermark requirement.

    Used when several constraints apply at once (for example a room that forbids
    downloads combined with a grant that allows them): the tightest one wins.
    """
    candidates = [p for p in permissions if p is not None]
    if not candidates:
        return PERMISSION_NONE
    winner = min(candidates, key=rank)
    # A watermark demanded anywhere in the set survives the narrowing, so
    # combining "download" with "view_watermark" yields a watermarked view.
    if rank(winner) > RANK_NONE and any(requires_watermark(p) for p in candidates):
        return with_watermark(winner)
    return winner


def with_watermark(permission: str) -> str:
    """Return the watermarked equivalent of a permission, if one exists."""
    if permission == PERMISSION_VIEW:
        return PERMISSION_VIEW_WATERMARK
    if permission == PERMISSION_DOWNLOAD:
        return PERMISSION_DOWNLOAD_WATERMARK
    return permission


def cap_downloads(permission: str, *, allow_downloads: bool) -> str:
    """Reduce a download-capable permission to view-only when the room forbids downloads.

    ``upload`` and ``manage`` belong to the startup side and are left intact:
    the room-level download switch governs what *investors* may take away.
    """
    if allow_downloads or rank(permission) != RANK_DOWNLOAD:
        return permission
    return (
        PERMISSION_VIEW_WATERMARK
        if requires_watermark(permission)
        else PERMISSION_VIEW
    )
