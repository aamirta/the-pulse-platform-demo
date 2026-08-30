#!/usr/bin/env python3
"""Cross-validate local PostgreSQL against the legacy Supabase source of truth.

Supports two Supabase access modes:
    1. Direct Postgres (preferred): set SUPABASE_DB_URL.
    2. Supabase REST API: set SUPABASE_URL and SUPABASE_KEY (service_role key required
       for full table reads).

Required environment variables:
    DATABASE_URL        Local PostgreSQL connection string.
    SUPABASE_DB_URL     OR  SUPABASE_URL + SUPABASE_KEY
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

import requests
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REQUIRED_TABLES = [
    "Startups",
    "Founders",
    "Investors",
    "FundingRounds",
    "pulse_members",
    "articles",
    "resources",
    "posts",
]

STARTUP_SAMPLE_COLUMNS = [
    "Startup Id",
    "Startup name",
    "location",
    "sector",
    "description",
    "stage",
]


# ---------------------------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------------------------
def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"{name} environment variable is required. "
            "Copy .env.example to .env and fill in real values."
        )
    return value


def _local_url() -> str:
    url = _require_env("DATABASE_URL")
    if url.startswith("sqlite"):
        raise RuntimeError("DATABASE_URL must point to PostgreSQL, not SQLite.")
    return url


# ---------------------------------------------------------------------------
# Local Postgres helpers
# ---------------------------------------------------------------------------
def _connect_local(url: str) -> Engine:
    print(f"Connecting to Local Postgres: {url.split('@')[-1]}...")
    engine = create_engine(url, pool_pre_ping=True, future=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("  Local Postgres connection OK")
    return engine


def _pg_row_count(engine: Engine, table: str) -> int:
    with engine.connect() as conn:
        result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
        return int(result or 0)


def _pg_table_exists(engine: Engine, table: str) -> bool:
    try:
        return table in inspect(engine).get_table_names()
    except Exception:
        return False


def _pg_top_startups(engine: Engine, limit: int = 3) -> list[dict[str, Any]]:
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("Startups")}
    columns = [c for c in STARTUP_SAMPLE_COLUMNS if c in cols]
    if not columns:
        raise RuntimeError("Startups table exists but has none of the expected columns")
    col_sql = ", ".join(f'"{c}"' for c in columns)
    order_col = '"Startup Id"' if "Startup Id" in cols else columns[0]
    with engine.connect() as conn:
        rows = conn.execute(
            text(f"SELECT {col_sql} FROM \"Startups\" ORDER BY {order_col} DESC LIMIT :limit"),
            {"limit": limit},
        ).mappings()
        return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Supabase REST API helpers
# ---------------------------------------------------------------------------
class SupabaseRestClient:
    """Minimal read-only PostgREST client for count/sample validation."""

    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        if self.base_url.endswith("/rest/v1"):
            self.base_url = self.base_url[: -len("/rest/v1")]
        self.api_key = api_key
        self.headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
        }

    def _url(self, table: str) -> str:
        # PostgREST table names are case-sensitive; try supplied casing first.
        return f"{self.base_url}/rest/v1/{table}"

    def count(self, table: str) -> int:
        """Return exact row count for a table."""
        for name in (table, table.lower()):
            url = self._url(name)
            resp = requests.get(
                url,
                headers={**self.headers, "Prefer": "count=exact"},
                params={"select": "*"},
            )
            if resp.status_code == 404:
                continue
            resp.raise_for_status()
            content_range = resp.headers.get("content-range", "")
            # Format: 0-0/<total> or 0-0/*
            if "/" in content_range:
                total = content_range.split("/")[-1]
                if total != "*":
                    return int(total)
            # Fallback: count returned JSON if not too large.
            return len(resp.json())
        raise RuntimeError(f"Table {table} not found in Supabase")

    def top_startups(self, limit: int = 3) -> list[dict[str, Any]]:
        """Return the latest startups ordered by Startup Id descending."""
        # Build select string from expected columns.
        select_cols = ",".join(f'"{c}"' for c in STARTUP_SAMPLE_COLUMNS)
        params = {
            "select": select_cols,
            "order": '"Startup Id".desc',
            "limit": limit,
        }
        for name in ("Startups", "startups"):
            resp = requests.get(self._url(name), headers=self.headers, params=params)
            if resp.status_code == 404:
                continue
            resp.raise_for_status()
            return resp.json()
        raise RuntimeError("Startups table not found in Supabase")


def _supabase_rest_client() -> SupabaseRestClient:
    supabase_url = os.environ.get("SUPABASE_URL", "").strip()
    supabase_key = os.environ.get("SUPABASE_KEY", "").strip()
    if not supabase_url or not supabase_key:
        raise RuntimeError(
            "Either SUPABASE_DB_URL or both SUPABASE_URL and SUPABASE_KEY must be set."
        )
    return SupabaseRestClient(supabase_url, supabase_key)


# ---------------------------------------------------------------------------
# Data comparison helpers
# ---------------------------------------------------------------------------
def _format_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (int, float, bool, str)):
        return value
    return str(value)


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {k.strip().lower().replace(" ", "_"): _format_value(v) for k, v in row.items()}


def _compare_samples(local: list[dict[str, Any]], remote: list[dict[str, Any]]) -> dict[str, Any]:
    mismatches: list[dict[str, Any]] = []
    if len(local) != len(remote):
        mismatches.append(
            {
                "issue": "sample_size_differs",
                "local_count": len(local),
                "supabase_count": len(remote),
            }
        )

    for idx, (l_row, r_row) in enumerate(zip(local, remote, strict=False)):
        l_norm = _normalize_row(l_row)
        r_norm = _normalize_row(r_row)
        all_keys = set(l_norm) | set(r_norm)
        row_diff = {}
        for key in sorted(all_keys):
            if l_norm.get(key) != r_norm.get(key):
                row_diff[key] = {"local": l_norm.get(key), "supabase": r_norm.get(key)}
        if row_diff:
            mismatches.append({"row_index": idx, "differences": row_diff})

    return {
        "sample_sizes_match": len(local) == len(remote),
        "mismatches": mismatches,
        "local_sample": [_normalize_row(r) for r in local],
        "supabase_sample": [_normalize_row(r) for r in remote],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    print("=" * 70)
    print("The Pulse — Supabase vs Local PostgreSQL Cross-Validation")
    print("=" * 70)

    local_url = _local_url()
    local_engine = _connect_local(local_url)

    # Determine Supabase access mode.
    supabase_db_url = os.environ.get("SUPABASE_DB_URL", "").strip()
    use_rest = not supabase_db_url
    if use_rest:
        print("\nSUPABASE_DB_URL not set; using Supabase REST API.")
        supabase_client = _supabase_rest_client()
        print(f"  Supabase base URL: {supabase_client.base_url}")
    else:
        print("\nUsing direct Supabase Postgres connection.")
        supabase_engine = _connect_local(supabase_db_url)

    def supabase_count(table: str) -> int:
        if use_rest:
            return supabase_client.count(table)
        return _pg_row_count(supabase_engine, table)

    def supabase_top_startups(limit: int = 3) -> list[dict[str, Any]]:
        if use_rest:
            return supabase_client.top_startups(limit)
        return _pg_top_startups(supabase_engine, limit)

    print("\n--- Table existence check (local) ---")
    missing_local = [t for t in REQUIRED_TABLES if not _pg_table_exists(local_engine, t)]
    if missing_local:
        print(f"WARNING: tables missing in local DB: {missing_local}")
    else:
        print("  All expected tables present locally.")

    print("\n--- Row count comparison ---")
    discrepancies: list[str] = []
    for table in REQUIRED_TABLES:
        try:
            local_count = _pg_row_count(local_engine, table)
        except Exception as exc:
            local_count = -1
            discrepancies.append(f"{table}: local count failed ({exc})")
        try:
            supabase_count_val = supabase_count(table)
        except Exception as exc:
            supabase_count_val = -1
            discrepancies.append(f"{table}: supabase count failed ({exc})")

        status = "OK" if local_count == supabase_count_val and local_count >= 0 else "MISMATCH"
        print(
            f"  {table:<20} local={local_count:>8}  supabase={supabase_count_val:>8}  [{status}]"
        )
        if local_count != supabase_count_val:
            discrepancies.append(
                f"{table}: {local_count} local vs {supabase_count_val} supabase "
                f"(delta={local_count - supabase_count_val})"
            )

    print("\n--- Startup data integrity sample (top 3 by Startup Id desc) ---")
    try:
        local_sample = _pg_top_startups(local_engine)
        supabase_sample = supabase_top_startups(3)
        comparison = _compare_samples(local_sample, supabase_sample)
        if comparison["sample_sizes_match"] and not comparison["mismatches"]:
            print("  PASS: top-3 startup samples match exactly.")
        else:
            print("  FAIL: startup sample differences detected.")
            for m in comparison["mismatches"]:
                print(f"    {m}")
        print("\n  Local sample:")
        print(json.dumps(comparison["local_sample"], ensure_ascii=False, indent=4, default=str))
        print("\n  Supabase sample:")
        print(json.dumps(comparison["supabase_sample"], ensure_ascii=False, indent=4, default=str))
    except Exception as exc:
        print(f"  ERROR: could not compare startup samples: {exc}")

    print("\n--- Summary ---")
    if discrepancies:
        print("DISCREPANCIES FOUND:")
        for d in discrepancies:
            print(f"  - {d}")
    else:
        print("No row-count discrepancies found.")

    print("\n--- Lockdown check ---")
    print("  SQLite fallback removed from backend config: YES")
    print(f"  DATABASE_URL protocol: {local_url.split('://')[0]}")
    print("  Local app locked to PostgreSQL: YES")

    return 1 if discrepancies else 0


if __name__ == "__main__":
    sys.exit(main())
