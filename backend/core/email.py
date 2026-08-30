"""Email helpers for The Pulse.

Production deployments should configure RESEND_API_KEY (or SMTP) to send real
confirmation and password-reset emails. When no sender is configured, the
helpers return the rendered URL so callers can log it during development.
"""

import logging
import os
from typing import Any, cast

from backend.core.config import settings

logger = logging.getLogger(__name__)


def _api_base_url() -> str:
    """Return the public base URL of this API (for server-handled links)."""
    return os.environ.get("PUBLIC_BASE_URL") or settings.PUBLIC_API_BASE_URL


def _app_base_url() -> str:
    """Return the public base URL of the React SPA (for user-facing pages)."""
    return settings.PUBLIC_APP_BASE_URL.rstrip("/")


def _send_with_resend(to: str, subject: str, html: str) -> bool:
    """Attempt to send an email via Resend if an API key is configured."""
    if not settings.RESEND_API_KEY:
        return False
    try:
        import resend

        resend.api_key = settings.RESEND_API_KEY
        params: dict[str, Any] = {
            "from": settings.GMAIL_USER,
            "to": [to],
            "subject": subject,
            "html": html,
        }
        resend.Emails.send(cast(Any, params))
        return True
    except Exception as exc:
        logger.warning("Failed to send email via Resend: %s", exc)
        return False


def send_confirmation_email(to: str, token: str, base_url: str | None = None) -> str | None:
    """Send a confirmation email. Returns the confirmation URL."""
    base = base_url or _api_base_url()
    url = f"{base}/api/v1/members/confirm/{token}"
    subject = "Confirmez votre compte The Pulse"
    html = f"""
    <p>Bonjour,</p>
    <p>Cliquez sur le lien ci-dessous pour confirmer votre compte The Pulse :</p>
    <p><a href="{url}">{url}</a></p>
    <p>Si vous n'avez pas demandé ce compte, ignorez cet email.</p>
    """
    if not _send_with_resend(to, subject, html):
        logger.info("No email provider configured; confirmation URL: %s", url)
    return url


def send_password_reset_email(to: str, token: str, base_url: str | None = None) -> str | None:
    """Send a password reset email. Returns the reset URL."""
    # The SPA uses a hash router, so the reset page lives behind "/#/".
    base = base_url or _app_base_url()
    url = f"{base}/#/reset-password?token={token}"
    subject = "Réinitialisation de votre mot de passe The Pulse"
    html = f"""
    <p>Bonjour,</p>
    <p>Cliquez sur le lien ci-dessous pour réinitialiser votre mot de passe :</p>
    <p><a href="{url}">{url}</a></p>
    <p>Ce lien expire dans une heure.</p>
    """
    if not _send_with_resend(to, subject, html):
        logger.info("No email provider configured; reset URL: %s", url)
    return url
