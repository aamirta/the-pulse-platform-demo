"""Core configuration for the FastAPI backend."""

import os
from pathlib import Path
from typing import ClassVar

from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _require_postgres_url() -> str:
    """Return the DATABASE_URL, defaulting to SQLite if not provided."""
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        tmp_db = "/tmp/thepulse.db"
        return f"sqlite:///{tmp_db}"

    return database_url


class Settings:
    """Application settings loaded from environment variables."""

    # Database — PostgreSQL only. No SQLite fallback.
    DATABASE_URL: str = _require_postgres_url()

    # Security
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "pulse_secret_change_me_in_production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    REFRESH_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_MINUTES", "10080"))
    ALGORITHM: str = os.environ.get("ALGORITHM", "HS256")
    ADMIN_USERNAME: str = os.environ.get("ADMIN_USERNAME", "admin")

    # Public base URLs used to build links inside outgoing emails.
    # PUBLIC_API_BASE_URL points at this API (email confirmation is handled
    # server-side); PUBLIC_APP_BASE_URL points at the React SPA, which uses a
    # hash router, so links into it must go through "/#/".
    PUBLIC_API_BASE_URL: str = os.environ.get("PUBLIC_API_BASE_URL", "http://localhost:8001")
    PUBLIC_APP_BASE_URL: str = os.environ.get("PUBLIC_APP_BASE_URL", "http://localhost:5173")

    # Rate limiting (requests per window)
    RATE_LIMIT_AUTH: str = os.environ.get("RATE_LIMIT_AUTH", "5/minute")
    RATE_LIMIT_SEARCH: str = os.environ.get("RATE_LIMIT_SEARCH", "30/minute")
    RATE_LIMIT_DATA: str = os.environ.get("RATE_LIMIT_DATA", "60/minute")

    # Argon2id password hashing
    ARGON2_TIME_COST: int = int(os.environ.get("ARGON2_TIME_COST", "3"))
    ARGON2_MEMORY_COST: int = int(os.environ.get("ARGON2_MEMORY_COST", "65536"))  # 64 MB
    ARGON2_PARALLELISM: int = int(os.environ.get("ARGON2_PARALLELISM", "4"))

    # CORS (default covers common local dev ports for Vite and the legacy Flask dev server)
    CORS_ORIGINS: ClassVar[list[str]] = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:3002,http://127.0.0.1:3002,"
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5000,http://127.0.0.1:5000",
    ).split(",")

    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = int(os.environ.get("DEFAULT_PAGE_SIZE", "20"))
    MAX_PAGE_SIZE: int = int(os.environ.get("MAX_PAGE_SIZE", "100"))

    # Email
    RESEND_API_KEY: str = os.environ.get("RESEND_API_KEY", "")
    GMAIL_USER: str = os.environ.get("GMAIL_USER", "contact@thepulse.ma")
    GMAIL_APP_PASSWORD: str = os.environ.get("GMAIL_APP_PASSWORD", "")

    # Supabase (legacy source-of-truth, read from environment only)
    SUPABASE_URL: str | None = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY: str | None = os.environ.get("SUPABASE_KEY")
    SUPABASE_DB_URL: str | None = os.environ.get("SUPABASE_DB_URL")

    # Uploads
    UPLOAD_FOLDER: Path = PROJECT_ROOT / "static" / "uploads"

    # Private storage for confidential Deal Room documents. Deliberately outside
    # UPLOAD_FOLDER's parent, which main.py mounts with StaticFiles. Overridable
    # so tests and each deployment get their own tree rather than sharing one.
    PRIVATE_STORAGE_ROOT: Path = Path(
        os.environ.get("PRIVATE_STORAGE_ROOT", str(PROJECT_ROOT / "private_storage"))
    )
    ALLOWED_EXTENSIONS: ClassVar[set[str]] = {"png", "jpg", "jpeg", "gif", "webp"}


settings = Settings()
