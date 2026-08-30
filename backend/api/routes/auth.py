"""Authentication API routes."""

from datetime import datetime, timedelta
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.api.deps import UserOrMemberDep, get_current_user, get_db
from backend.api.limiter import limiter
from backend.core.config import settings
from backend.core.email import send_password_reset_email
from backend.core.security import (
    create_access_token,
    create_member_access_token,
    create_member_refresh_token,
    create_refresh_token,
    decode_token,
    generate_secure_token,
    hash_password,
    needs_rehash,
    verify_password,
)
from backend.models import PulseMember, User
from backend.schemas import (
    ForgotPasswordRequest,
    MemberLogin,
    MemberToken,
    PasswordChangeRequest,
    RefreshTokenResponse,
    ResetPasswordRequest,
    Token,
    UserMe,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=Token,
    summary="Login",
    description="Obtain an access token and refresh token by providing admin credentials.",
)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def login(
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> dict[str, Any]:
    """Authenticate a user and return JWT tokens."""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Transparently upgrade credentials still stored with legacy (or absent)
    # hashing now that we hold the verified plaintext.
    if needs_rehash(user.password):
        user.password = hash_password(form_data.password)
        db.commit()
    claims = {"sub": user.username, "tv": user.token_version}
    access_token = create_access_token(claims)
    refresh_token = create_refresh_token(claims)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Refresh tokens",
    description=(
        "Exchange a valid admin or member refresh token for a new access/refresh token pair."
    ),
)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def refresh_token(
    request: Request,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Validate a refresh token and issue a new token pair.

    Handles both admin (``refresh``) and community member (``member_refresh``)
    tokens. Member tokens used to be rejected here, which left members with no
    way to renew a session once the access token expired.
    """
    invalid_token = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )
    refresh_token_value = payload.get("refresh_token")
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="refresh_token is required",
        )
    try:
        token_data = decode_token(refresh_token_value)
    except Exception as exc:
        raise invalid_token from exc

    token_type = token_data.get("type")
    subject = token_data.get("sub")
    if not subject:
        raise invalid_token

    if token_type == "refresh":
        # The account must still exist, and the token must not predate a logout.
        user = db.query(User).filter(User.username == subject).first()
        if not user or int(token_data.get("tv", 0)) != int(user.token_version or 0):
            raise invalid_token
        claims = {"sub": subject, "tv": user.token_version}
        return {
            "access_token": create_access_token(claims),
            "refresh_token": create_refresh_token(claims),
            "token_type": "bearer",
        }

    if token_type == "member_refresh" and subject.startswith("member:"):
        try:
            member_id = int(subject.split(":", 1)[1])
        except ValueError as exc:
            raise invalid_token from exc
        member = db.query(PulseMember).filter(PulseMember.id == member_id).first()
        if not member or int(token_data.get("tv", 0)) != int(member.token_version or 0):
            raise invalid_token
        claims = {"sub": subject, "email": member.email, "tv": member.token_version}
        return {
            "access_token": create_member_access_token(claims),
            "refresh_token": create_member_refresh_token(claims),
            "token_type": "bearer",
            "member_id": member.id,
            "full_name": member.full_name,
            "role": member.role,
            "email": member.email,
        }

    raise invalid_token


@router.get(
    "/me",
    response_model=UserMe,
    summary="Current user",
    description="Return the currently authenticated user.",
)
@limiter.limit(settings.RATE_LIMIT_DATA)
def me(request: Request, current_user: User = Depends(get_current_user)) -> User:
    """Return the current authenticated user."""
    return current_user


@router.post(
    "/logout",
    summary="Sign out everywhere",
    description=(
        "Invalidates every access and refresh token already issued to the caller's account. "
        "Tokens are stateless, so this is what makes signing out mean something on the server "
        "rather than only in the browser."
    ),
)
@limiter.limit("20/minute")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    user_or_member: UserOrMemberDep = (None, None),
) -> dict[str, str]:
    """Bump the caller's token version, ending all of their sessions.

    Clearing localStorage alone left a refresh token valid for its full lifetime,
    so a token captured before sign-out kept working for days — on a shared
    machine, or after an XSS, that is the whole session handed over. Bumping the
    counter makes every previously minted token fail validation on its next use.
    """
    current_user, current_member = user_or_member
    account = current_member or current_user
    if account is None:  # pragma: no cover - the dependency raises first
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    account.token_version = (account.token_version or 0) + 1
    db.commit()
    return {"message": "Signed out"}


@router.post(
    "/change-password",
    summary="Change password",
    description=(
        "Change the authenticated account's password. Works for both administrator "
        "and community-member sessions."
    ),
)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def change_password(
    request: Request,
    data: PasswordChangeRequest,
    db: Session = Depends(get_db),
    user_or_member: UserOrMemberDep = (None, None),
) -> dict[str, str]:
    """Verify the current password and store a new Argon2id hash.

    This is the supported way to rotate a credential that was previously stored
    in plaintext, without going through the email reset flow.
    """
    current_user, current_member = user_or_member

    if data.new_password == data.current_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The new password must differ from the current one",
        )

    if current_user is not None:
        if not verify_password(data.current_password, current_user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect",
            )
        current_user.password = hash_password(data.new_password)
        current_user.token_version = (current_user.token_version or 0) + 1
    elif current_member is not None:
        if not current_member.password_hash or not verify_password(
            data.current_password, current_member.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect",
            )
        current_member.password_hash = hash_password(data.new_password)
        current_member.token_version = (current_member.token_version or 0) + 1
    else:  # pragma: no cover - the dependency raises before this is reachable
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    db.commit()
    # Every session opened with the old credential is now invalid, including
    # this one: the caller must sign in again with the new password.
    return {"message": "Password changed successfully. Please sign in again."}


@router.post(
    "/member-login",
    response_model=MemberToken,
    summary="Pulse member login",
    description="Authenticate a community member by email and password and return a JWT pair.",
)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def member_login(
    request: Request,
    data: MemberLogin,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Authenticate a PulseMember and return member-scoped JWT tokens."""
    email = data.email.strip().lower()
    member = db.query(PulseMember).filter(PulseMember.email == email).first()
    if (
        not member
        or not member.password_hash
        or not verify_password(data.password, member.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not member.is_confirmed:
        # Email verification is only meaningful if it actually gates login.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please confirm your email address before signing in.",
        )
    claims = {"sub": f"member:{member.id}", "email": member.email, "tv": member.token_version}
    access_token = create_member_access_token(claims)
    refresh_token = create_member_refresh_token(claims)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "member_id": member.id,
        "full_name": member.full_name,
        "role": member.role,
    }


@router.post(
    "/forgot-password",
    summary="Request password reset",
    description="Request a password reset link for a member account.",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("5/minute")
def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Generate a password reset token and email it to the member if found."""
    email = data.email.strip().lower()
    member = db.query(PulseMember).filter(PulseMember.email == email).first()
    if member:
        member.reset_token = generate_secure_token()
        member.reset_token_expires_at = cast(Any, datetime.utcnow() + timedelta(hours=1))
        db.commit()
        send_password_reset_email(member.email, member.reset_token)
    # Always return the same response to avoid email enumeration.
    return {"message": "If an account exists, a reset link has been sent."}


@router.post(
    "/reset-password",
    summary="Reset password",
    description="Reset a member password using a valid reset token.",
)
@limiter.limit("5/minute")
def reset_password(
    request: Request,
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Validate a reset token and update the member's password."""
    member = db.query(PulseMember).filter(PulseMember.reset_token == data.token).first()
    if not member or not member.reset_token_expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    expires_at = cast(datetime, member.reset_token_expires_at)
    if datetime.utcnow() > expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )
    member.password_hash = hash_password(data.new_password)
    member.reset_token = None
    member.reset_token_expires_at = None
    # A reset is the recovery path for a compromised account, so any session an
    # attacker already holds has to stop working.
    member.token_version = (member.token_version or 0) + 1
    db.commit()
    return {"message": "Password reset successfully"}
