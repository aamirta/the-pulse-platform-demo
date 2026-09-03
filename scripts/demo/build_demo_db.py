"""Rebuild the SQLite database bundled with the demo deployment.

The Vercel demo has no Postgres attached: ``api/index.py`` copies
``backend/thepulse.db`` into /tmp and points the app at it. That file used to
hold a hand-written mock (8 startups, 0 incubators), which is why the demo
showed "0 structures d'accompagnement référencées" and empty analytics.

This script mirrors the real Postgres content into that SQLite file so the demo
serves the project's own data instead of a stub. The source connection is read
from DATABASE_URL in the project's .env, so no credentials are passed on the
command line. Run it whenever the source database changes:

    venv/bin/python scripts/demo/build_demo_db.py
"""

from __future__ import annotations

import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("PULSE_ALLOW_SQLITE_TESTING", "1")
os.environ.setdefault("PULSE_RUN_STARTUP_MIGRATIONS", "0")

from dotenv import load_dotenv  # noqa: E402
from sqlalchemy import create_engine, inspect, text  # noqa: E402

load_dotenv(ROOT / ".env")

from backend.models import Base  # noqa: E402

TARGET = ROOT / "backend" / "thepulse.db"

# The demo has to be signable-in -- admin and member access are part of what the
# supervisor reviews -- so the account tables travel with it. Every row is a
# @test.local QA account and passwords are stored as Argon2id hashes, never in
# clear. Private conversation content and generated artefacts stay behind.
EXCLUDED = {
    "direct_messages",
    "badge_generations",
    "alembic_version",
}


# Payloads left behind by the penetration test still sit in the source data --
# three Founders rows are named "<script>alert(1)</script>" and
# "Robert'); DROP TABLE members;--". They are escaped on render, so they are not
# an XSS risk, but they show up as founder names in the directory. They are
# filtered out of the demo build rather than deleted upstream.
_TEST_PAYLOAD_MARKERS = ("<script", "alert(", "drop table", "onerror=", "javascript:")


def _is_test_payload(row: object) -> bool:
    """True when any text field of the row carries a security-test payload."""
    return any(
        isinstance(value, str) and any(m in value.lower() for m in _TEST_PAYLOAD_MARKERS)
        for value in row
    )


def main() -> int:
    source_url = os.environ.get("DATABASE_URL", "")
    if not source_url or source_url.startswith("sqlite"):
        print("DATABASE_URL must point at the source Postgres database.")
        return 1

    src = create_engine(source_url)
    if TARGET.exists():
        TARGET.unlink()
    dst = create_engine(f"sqlite:///{TARGET}")

    Base.metadata.create_all(bind=dst)

    src_tables = set(inspect(src).get_table_names())
    copied: list[tuple[str, int]] = []

    with src.connect() as s, dst.begin() as d:
        for table in Base.metadata.sorted_tables:
            name = table.name
            if name in EXCLUDED or name not in src_tables:
                continue
            cols = [c.name for c in table.columns]
            quoted = ", ".join(f'"{c}"' for c in cols)
            rows = s.execute(text(f'SELECT {quoted} FROM "{name}"')).fetchall()
            skipped = [r for r in rows if _is_test_payload(r)]
            rows = [r for r in rows if r not in skipped]
            if skipped:
                print(f"  ! {name}: skipped {len(skipped)} security-test row(s)")
            if not rows:
                copied.append((name, 0))
                continue
            d.execute(table.insert(), [dict(zip(cols, r)) for r in rows])
            copied.append((name, len(rows)))

    with dst.begin() as d:
        d.execute(text("VACUUM"))

    for name, count in copied:
        if count:
            print(f"  {name:28s} {count}")
    size_mb = TARGET.stat().st_size / 1024 / 1024
    print(f"\nWrote {TARGET.relative_to(ROOT)} ({size_mb:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
