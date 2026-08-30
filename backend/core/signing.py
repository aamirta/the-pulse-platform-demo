"""Short-lived signed tokens for Deal Room document delivery.

A signed token is *not* a substitute for authorization. It binds a delivery URL
to one document version, one viewer and one intent, and expires quickly; the
handler that redeems it still re-runs the full permission check against live
database state, so revoking access takes effect immediately rather than when the
token happens to expire.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.core.config import settings
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

# Namespaced so a token minted here can never be replayed against another
# itsdangerous consumer that happens to share the application secret.
_SALT = "deal-room-document-access-v1"

# Deliberately short: long enough to load a viewer, too short to pass around.
DEFAULT_TTL_SECONDS = 300


class InvalidAccessToken(Exception):
    """Raised when a document access token is missing, tampered with, or expired."""


@dataclass(frozen=True)
class DocumentAccessClaims:
    """The identity and intent a document token asserts."""

    document_id: int
    version_id: int
    member_id: int | None
    user_id: int | None
    deal_room_id: int
    # "preview" | "download"
    intent: str
    watermark: bool


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.SECRET_KEY, salt=_SALT)


def issue_document_token(claims: DocumentAccessClaims) -> str:
    """Return a signed, expiring token that names exactly what may be delivered."""
    payload: dict[str, Any] = {
        "d": claims.document_id,
        "v": claims.version_id,
        "m": claims.member_id,
        "u": claims.user_id,
        "r": claims.deal_room_id,
        "i": claims.intent,
        "w": claims.watermark,
    }
    return _serializer().dumps(payload)


def read_document_token(token: str, max_age: int = DEFAULT_TTL_SECONDS) -> DocumentAccessClaims:
    """Validate a token and return its claims, or raise :class:`InvalidAccessToken`."""
    try:
        payload = _serializer().loads(token, max_age=max_age)
    except SignatureExpired as exc:
        raise InvalidAccessToken("This document link has expired") from exc
    except BadSignature as exc:
        raise InvalidAccessToken("This document link is not valid") from exc

    if not isinstance(payload, dict):
        raise InvalidAccessToken("This document link is not valid")

    try:
        return DocumentAccessClaims(
            document_id=int(payload["d"]),
            version_id=int(payload["v"]),
            member_id=payload["m"] if payload["m"] is None else int(payload["m"]),
            user_id=payload["u"] if payload["u"] is None else int(payload["u"]),
            deal_room_id=int(payload["r"]),
            intent=str(payload["i"]),
            watermark=bool(payload["w"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidAccessToken("This document link is not valid") from exc


def hash_invite_token(token: str) -> str:
    """Return a storable digest of an invitation token.

    Invitations are bearer credentials, so only the digest is persisted; a
    database leak then yields nothing an attacker can present.
    """
    import hashlib

    return hashlib.sha256(token.encode("utf-8")).hexdigest()
