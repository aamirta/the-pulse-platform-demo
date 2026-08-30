"""Seed the database with mock data from new_design/src/data/*.ts.

Usage:
    venv/bin/python scripts/seed/seed_mock_data.py

Environment:
    DATABASE_URL (optional) - defaults to thepulse_v2.db SQLite file
"""

from __future__ import annotations

import json5
import os
import re
import sys
from pathlib import Path
from typing import Any

from passlib.context import CryptContext
from sqlalchemy import func


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Add backend to path so we can import models/config
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.orm import Session  # noqa: E402

from backend.core.config import settings  # noqa: E402
from backend.database import engine, SessionLocal  # noqa: E402
from backend.models import (  # noqa: E402
    Base,
    Article,
    Founder,
    Investor,
    Startup,
    StartupFounder,
    User,
)


# Argon2id password hashing (OWASP recommended)
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__time_cost=settings.ARGON2_TIME_COST,
    argon2__memory_cost=settings.ARGON2_MEMORY_COST,
    argon2__parallelism=settings.ARGON2_PARALLELISM,
    argon2__hash_len=32,
    argon2__salt_len=16,
)


def _extract_ts_array(file_path: Path, var_name: str) -> list[dict[str, Any]]:
    """Extract a TypeScript array of objects into Python dicts using JSON5."""
    text = file_path.read_text(encoding="utf-8")
    # Find the array assignment: export const NAME: TYPE = [...];
    match = re.search(
        rf"export const {var_name}\s*:\s*[^=]+=\s*(\[.*?\]);\s*$",
        text,
        re.DOTALL | re.MULTILINE,
    )
    if not match:
        raise ValueError(f"Could not find array {var_name} in {file_path}")
    array_text = match.group(1)
    # JSON5 handles single quotes, unquoted keys, trailing commas, comments
    return json5.loads(array_text)


def _seed_startups(db: Session) -> dict[str, int]:
    """Seed startups and return a mapping of slug -> integer startup_id."""
    data_path = PROJECT_ROOT / "new_design" / "src" / "data" / "startups.ts"
    startups = _extract_ts_array(data_path, "startups")
    slug_to_id: dict[str, int] = {}

    for idx, item in enumerate(startups, start=1):
        slug = item["id"]
        # Parse year founded
        year_founded = None
        try:
            year_founded = int(item.get("yearFounded")) if item.get("yearFounded") else None
        except (ValueError, TypeError):
            pass

        # Parse funding amount
        funding = item.get("funding")
        total_funding_usd = None
        if isinstance(funding, (int, float)):
            total_funding_usd = funding

        # Stage/status mapping
        stage = item.get("stage")
        status = item.get("status")

        startup = Startup(
            startup_id=idx,
            startup_name=item.get("name"),
            sector=", ".join(item.get("sector", [])) if isinstance(item.get("sector"), list) else item.get("sector"),
            stage=stage,
            status_startup=status,
            location=item.get("location"),
            description=item.get("description"),
            total_funding_usd=total_funding_usd,
            year_founded=str(year_founded) if year_founded else None,
            homepage_url=item.get("website"),
            logo_url=item.get("logo"),
            uuid=slug,
            country_code="MA" if "Morocco" in (item.get("location") or "") else None,
        )
        db.add(startup)
        slug_to_id[slug] = idx

    db.commit()
    print(f"Seeded {len(startups)} startups")
    return slug_to_id


def _seed_founders(db: Session, startup_slug_to_id: dict[str, int]) -> None:
    """Seed founders and link them to startups."""
    data_path = PROJECT_ROOT / "new_design" / "src" / "data" / "founders.ts"
    founders = _extract_ts_array(data_path, "founders")

    for item in founders:
        founder_id = item["id"]
        name = item.get("name", "")
        first_name, last_name = _split_name(name)

        founder = Founder(
            founder_id=founder_id,
            name=name,
            first_name=first_name,
            last_name=last_name,
            current_title=item.get("role"),
            location=item.get("location"),
            profile_pic=item.get("avatar"),
            linkedin_url=item.get("linkedin"),
            skills=item.get("experience"),
        )
        db.add(founder)

        # Link to startup via association table
        startup_slug = item.get("startupId")
        if startup_slug and startup_slug in startup_slug_to_id:
            assoc = StartupFounder(
                startup_id=startup_slug_to_id[startup_slug],
                founder_id=founder_id,
            )
            db.add(assoc)

    db.commit()
    print(f"Seeded {len(founders)} founders")


def _split_name(full_name: str) -> tuple[str, str]:
    """Split a full name into first/last name."""
    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _seed_investors(db: Session) -> None:
    """Seed investors from the mock data."""
    data_path = PROJECT_ROOT / "new_design" / "src" / "data" / "investors.ts"
    investors = _extract_ts_array(data_path, "investors")

    for idx, item in enumerate(investors, start=1):
        slug = item["id"]
        investor_type = item.get("type")
        portfolio = item.get("portfolio")
        investments = item.get("investments")

        investor = Investor(
            investor_id=idx,
            investor_name=item.get("name"),
            primary_investor_type=investor_type,
            city=item.get("location"),
            preferred_industry=", ".join(item.get("focus", [])) if isinstance(item.get("focus"), list) else item.get("focus"),
            logo_url=item.get("logo"),
            domain=item.get("website"),
            uuid=slug,
            total_active_portfolio=portfolio if isinstance(portfolio, int) else None,
            total_investments=investments if isinstance(investments, int) else None,
        )
        db.add(investor)

    db.commit()
    print(f"Seeded {len(investors)} investors")


def _seed_articles(db: Session) -> None:
    """Seed articles from the news mock data."""
    data_path = PROJECT_ROOT / "new_design" / "src" / "data" / "news.ts"
    news_items = _extract_ts_array(data_path, "newsItems")

    category_map = {
        "funding": "Funding",
        "news": "News",
        "event": "Event",
    }

    for item in news_items:
        article = Article(
            title=item.get("title"),
            content=item.get("description"),
            summary=item.get("description"),
            category=category_map.get(item.get("type"), "News"),
            source=item.get("source"),
            source_url=None,
            author=item.get("source"),
            image_url=item.get("image"),
            tags=", ".join(item.get("tags", [])) if item.get("tags") else None,
            is_featured=item.get("type") == "funding",
        )
        db.add(article)

    db.commit()
    print(f"Seeded {len(news_items)} articles")


def _seed_secure_admin(db: Session) -> None:
    """Replace legacy plaintext admin with a securely hashed user.

    Safety gate: destructive admin replacement is only allowed on SQLite
    dev databases, or when PULSE_SEED_ALLOW_DESTRUCTIVE=1 is explicitly set.
    """
    allow_destructive = (
        settings.DATABASE_URL.startswith("sqlite")
        or os.environ.get("PULSE_SEED_ALLOW_DESTRUCTIVE") == "1"
    )
    if not allow_destructive:
        raise RuntimeError(
            "Refusing to seed admin user on a non-SQLite database without "
            "PULSE_SEED_ALLOW_DESTRUCTIVE=1. This protects production data."
        )

    # Remove any existing admin rows (dev-only)
    db.query(User).filter(User.username == "admin").delete()
    db.commit()

    hashed = pwd_context.hash("admin")
    admin = User(
        username="admin",
        password=hashed,
    )
    db.add(admin)
    db.commit()
    print("Seeded secure admin user (password hashed with Argon2id)")


def seed_all() -> None:
    """Run all seeding steps idempotently."""
    print(f"Seeding database: {settings.DATABASE_URL}")

    # Ensure tables exist before querying/inserting
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Safety check: refuse to seed if mock data already exists
        existing_startups = db.query(func.count(Startup.startup_id)).scalar()
        existing_articles = db.query(func.count(Article.article_id)).scalar()
        if existing_startups > 0 or existing_articles > 0:
            print(
                f"SKIP: database already contains mock data "
                f"({existing_startups} startups, {existing_articles} articles). "
                f"To re-seed, truncate the tables or use a fresh database."
            )
            return

        _seed_secure_admin(db)
        startup_slug_to_id = _seed_startups(db)
        _seed_founders(db, startup_slug_to_id)
        _seed_investors(db)
        _seed_articles(db)
        print("Seeding complete.")
    except Exception as exc:
        db.rollback()
        print(f"ERROR: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
