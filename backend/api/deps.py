"""FastAPI dependency helpers for database sessions and authentication."""

from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.security import decode_token
from backend.database import get_db
from backend.models import PulseMember, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


DbDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


def _token_version_matches(payload: dict[str, Any], account: User | PulseMember) -> bool:
    """Return True if the token was minted before the account's sessions were ended.

    Tokens issued before this claim existed carry no ``tv`` and read as 0, which
    matches the column default — so adding session invalidation did not sign
    everyone out on deploy.
    """
    return int(payload.get("tv", 0)) == int(getattr(account, "token_version", 0) or 0)


def get_current_user(
    db: DbDep,
    token: TokenDep,
) -> User:
    """Dependency that returns the currently authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        username: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")
        if username is None or token_type != "access":
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = db.query(User).filter(User.username == username).first()
    if user is None or not _token_version_matches(payload, user):
        raise credentials_exception
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def get_current_active_user(
    current_user: CurrentUserDep,
) -> User:
    """Ensure the authenticated user is active.

    Currently all users are considered active; the check is kept as a hook
    for future activation status columns.
    """
    return current_user


ActiveUserDep = Annotated[User, Depends(get_current_active_user)]


def require_admin(
    current_user: ActiveUserDep,
) -> User:
    """Dependency that restricts access to the admin user."""
    if current_user.username != settings.ADMIN_USERNAME:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


AdminUserDep = Annotated[User, Depends(require_admin)]


def optional_current_user(
    db: DbDep,
    authorization: Annotated[str | None, Header()] = None,
) -> User | None:
    """Return the current user if a valid bearer token is provided, else None."""
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    try:
        payload = decode_token(token)
        username: str | None = payload.get("sub")
        if username is None or payload.get("type") != "access":
            return None
    except JWTError:
        return None
    user = db.query(User).filter(User.username == username).first()
    if user is None or not _token_version_matches(payload, user):
        return None
    return user


OptionalUserDep = Annotated[User | None, Depends(optional_current_user)]


def get_current_user_or_member(
    db: DbDep,
    authorization: Annotated[str | None, Header()] = None,
) -> tuple[User | None, PulseMember | None]:
    """Return the authenticated user or member, or raise 401 if neither is valid.

    Admin tokens are validated first; member tokens are validated as a fallback.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    token_type = payload.get("type")
    sub = payload.get("sub")

    if token_type == "access" and sub:
        user = db.query(User).filter(User.username == sub).first()
        if user and _token_version_matches(payload, user):
            return user, None

    if token_type == "member_access" and sub and sub.startswith("member:"):
        try:
            member_id = int(sub.split(":", 1)[1])
        except ValueError:
            pass
        else:
            member = db.query(PulseMember).filter(PulseMember.id == member_id).first()
            if member and _token_version_matches(payload, member):
                return None, member

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )


UserOrMemberDep = Annotated[
    tuple[User | None, PulseMember | None],
    Depends(get_current_user_or_member),
]


def optional_user_or_member(
    db: DbDep,
    authorization: Annotated[str | None, Header()] = None,
) -> tuple[User | None, PulseMember | None]:
    """Return the authenticated actor if there is one, else ``(None, None)``.

    For endpoints that are public but answer *better* when they know who is
    asking — a public list that also reports which rows the caller has already
    interacted with. A missing or invalid token is not an error here, so an
    anonymous visitor still gets the public view.
    """
    if not authorization:
        return None, None
    try:
        return get_current_user_or_member(db, authorization)
    except HTTPException:
        return None, None


OptionalUserOrMemberDep = Annotated[
    tuple[User | None, PulseMember | None],
    Depends(optional_user_or_member),
]
