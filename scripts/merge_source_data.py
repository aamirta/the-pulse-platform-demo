"""Union-merge the Pulse_Data_Insertion CSVs into the current database.

The goal is a true union, not a replacement:

    FINAL = CURRENT DB  UNION  ORIGINAL CSV SOURCE

Guarantees
----------
* Never deletes, truncates, or drops anything.
* Never overwrites a non-empty production value with a CSV value; a differing
  value is recorded as a conflict and production wins (it is the newer source).
* Fills NULL/empty production columns from the CSV (that is the actual gain).
* Resolves entities by primary key first, then by natural keys with an explicit
  confidence level. LOW-confidence matches are never merged automatically.
* Maps old source ids to current ids so foreign keys are never broken.
* Idempotent: a second run inserts nothing and reports zero changes.

Usage
-----
    python scripts/merge_source_data.py --report   # analyse only, no writes
    python scripts/merge_source_data.py --apply    # perform the merge
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

CSV_DIR = PROJECT_ROOT / "datab" / "data"

# Columns that are spreadsheet artefacts rather than data.
JUNK_COLUMNS = {"", "Unnamed: 0", "﻿", "index"}

NULL_TOKENS = {"", "nan", "NaN", "none", "None", "null", "NULL", "NaT", "<NA>"}


@dataclass
class TableSpec:
    """How one CSV maps onto one database table."""

    csv_name: str
    table: str
    pk: list[str]
    #: CSV column -> DB column, for genuinely renamed fields.
    rename: dict[str, str] = field(default_factory=dict)
    #: Natural keys tried in order; each is (columns, confidence).
    natural_keys: list[tuple[tuple[str, ...], str]] = field(default_factory=list)
    #: For association tables: {db_column: (parent_table, parent_pk)}.
    fks: dict[str, tuple[str, str]] = field(default_factory=dict)
    #: Association tables have no surrogate id and are matched purely on the pair.
    association: bool = False


# Parents first, then dependants, then association tables: FK-safe ordering.
SPECS: list[TableSpec] = [
    TableSpec("CompleteInstitutes.csv", "Institutes", ["Institute Id"],
              natural_keys=[(("Institute Name",), "MEDIUM")]),
    TableSpec("CompleteIncubators.csv", "Incubators", ["Incubator Id"],
              rename={"ville": "ville_organisme", "ville.1": "ville"},
              natural_keys=[(("Incubator",), "MEDIUM")]),
    TableSpec("Startups__Cleaned.csv", "Startups", ["Startup Id"],
              natural_keys=[(("numeroICE",), "HIGH"), (("numeroRC",), "HIGH"),
                            (("Startup name", "location"), "MEDIUM")]),
    TableSpec("CompleteFounders.csv", "Founders", ["Founder Id"],
              natural_keys=[(("linkedin_url",), "HIGH"),
                            (("name", "location"), "MEDIUM")]),
    TableSpec("InvestorsCleaned.csv", "Investors", ["Investor Id"],
              natural_keys=[(("domain",), "HIGH"), (("Investor Name",), "MEDIUM")]),
    TableSpec("FundsCleaned.csv", "Funds", ["Fund Id"],
              natural_keys=[(("FundName",), "MEDIUM")]),
    TableSpec("LimitedPartnersCleaned.csv", "LimitedPartner", ["LimitedPartner Id"],
              natural_keys=[(("LimitedPartnerName",), "MEDIUM")]),
    TableSpec("ServiceProvidersCleaned.csv", "ServiceProvider", ["ServiceProvider Id"],
              natural_keys=[(("ServiceProviderName",), "MEDIUM")]),
    TableSpec("FundingRoundsCleaned.csv", "FundingRounds", ["Funding_Round_Id"],
              natural_keys=[(("Uuid",), "HIGH"), (("Dealid",), "HIGH")],
              fks={"Startup Id": ("Startups", "Startup Id")}),
    # The production rows all carry uuid = NULL, so uuid can never match and
    # matching on it alone would duplicate 24 investments that already exist.
    # An investment is identified by which investor funded which round.
    TableSpec("investementsRaw.csv", "Investements", ["Investement Id"],
              natural_keys=[(("Funding_Round_Id", "Investor Id"), "HIGH"),
                            (("uuid",), "HIGH")],
              fks={"Funding_Round_Id": ("FundingRounds", "Funding_Round_Id"),
                   "Investor Id": ("Investors", "Investor Id")}),
    TableSpec("CompleteEducation.csv", "Education", ["Education Id"],
              natural_keys=[(("Founder Id", "Institute Id", "degree"), "MEDIUM")],
              fks={"Founder Id": ("Founders", "Founder Id"),
                   "Institute Id": ("Institutes", "Institute Id")}),
    TableSpec("CompleteExperiences.csv", "Experiences", ["Experience Id"],
              natural_keys=[(("Founder Id", "Role", "Company"), "MEDIUM")],
              fks={"Founder Id": ("Founders", "Founder Id")}),
    # ---- association tables ----
    TableSpec("CompleteStartupFounder.csv", "StartupFounders", ["Startup Id", "Founder Id"],
              association=True,
              fks={"Startup Id": ("Startups", "Startup Id"),
                   "Founder Id": ("Founders", "Founder Id")}),
    TableSpec("CompleteStartupIncubator.csv", "StartupIncubators", ["Startup Id", "Incubator Id"],
              association=True,
              fks={"Startup Id": ("Startups", "Startup Id"),
                   "Incubator Id": ("Incubators", "Incubator Id")}),
    TableSpec("IncubatorFounders.csv", "IncubatorFounders", ["Incubator Id", "Founder Id"],
              association=True,
              fks={"Incubator Id": ("Incubators", "Incubator Id"),
                   "Founder Id": ("Founders", "Founder Id")}),
    TableSpec("FundInvestors.csv", "FundInvestors", ["Fund Id", "Investor Id"],
              association=True,
              fks={"Fund Id": ("Funds", "Fund Id"),
                   "Investor Id": ("Investors", "Investor Id")}),
    TableSpec("LPFundsCleaned.csv", "LPFunds", ["Fund Id", "LimitedPartner Id"],
              association=True,
              fks={"Fund Id": ("Funds", "Fund Id"),
                   "LimitedPartner Id": ("LimitedPartner", "LimitedPartner Id")}),
    TableSpec("SPFundsCleaned.csv", "SPFunds", ["Fund Id", "ServiceProvider Id"],
              association=True,
              fks={"Fund Id": ("Funds", "Fund Id"),
                   "ServiceProvider Id": ("ServiceProvider", "ServiceProvider Id")}),
    TableSpec("SPInvestorsCleaned.csv", "SPInvestor", ["Investor Id", "ServiceProvider Id"],
              association=True,
              fks={"Investor Id": ("Investors", "Investor Id"),
                   "ServiceProvider Id": ("ServiceProvider", "ServiceProvider Id")}),
]


def clean(value: Any) -> Any:
    """Normalise a raw CSV value, mapping placeholder tokens to NULL."""
    if value is None:
        return None
    text = str(value).strip()
    if text in NULL_TOKENS:
        return None
    return text


def is_empty(value: Any) -> bool:
    """True when a database value carries no information."""
    return value is None or (isinstance(value, str) and value.strip() == "")


def coerce(value: Any, sa_type: Any) -> Any:
    """Cast a cleaned CSV string to something the column will accept."""
    if value is None:
        return None
    text = str(value)
    try:
        python_type = sa_type.python_type
    except (NotImplementedError, AttributeError):
        return text

    if python_type is bool:
        return text.lower() in {"true", "1", "yes", "y", "t"}
    if python_type is int:
        try:
            return int(float(text))
        except (ValueError, OverflowError):
            return None
    if python_type is float:
        try:
            return float(text)
        except ValueError:
            return None
    if python_type is Decimal:
        try:
            return Decimal(text)
        except (InvalidOperation, ValueError):
            return None
    if python_type is datetime:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(text[:19], fmt)
            except ValueError:
                continue
        return None
    return text


class MergeStats:
    """Per-table reconciliation counters."""

    def __init__(self, table: str) -> None:
        self.table = table
        self.source_rows = 0
        self.db_before = 0
        self.matched_pk = 0
        self.matched_natural = 0
        self.inserted = 0
        self.field_fills = 0
        self.conflicts: list[dict[str, Any]] = []
        self.orphans: list[dict[str, Any]] = []
        self.ambiguous: list[dict[str, Any]] = []
        self.id_remaps: dict[str, Any] = {}
        self.duplicates_prevented = 0
        self.db_after = 0

    def as_row(self) -> dict[str, Any]:
        return {
            "table": self.table,
            "source_rows": self.source_rows,
            "db_before": self.db_before,
            "matched": self.matched_pk + self.matched_natural,
            "inserted": self.inserted,
            "field_fills": self.field_fills,
            "duplicates_prevented": self.duplicates_prevented,
            "conflicts": len(self.conflicts),
            "orphans": len(self.orphans),
            "ambiguous": len(self.ambiguous),
            "db_after": self.db_after,
        }


class Merger:
    def __init__(self, engine: sa.Engine, apply: bool) -> None:
        self.engine = engine
        self.apply = apply
        self.meta = sa.MetaData()
        self.stats: list[MergeStats] = []
        # {table: {old_id: current_id}} so association rows can be remapped.
        self.id_map: dict[str, dict[str, Any]] = {}

    def table(self, name: str) -> sa.Table:
        if name not in self.meta.tables:
            sa.Table(name, self.meta, autoload_with=self.engine)
        return self.meta.tables[name]

    def count(self, conn: sa.Connection, name: str) -> int:
        return conn.execute(sa.text(f'select count(*) from "{name}"')).scalar() or 0

    # -- entity resolution -------------------------------------------------
    def find_by_natural_key(
        self, conn: sa.Connection, tbl: sa.Table, row: dict[str, Any],
        keys: list[tuple[tuple[str, ...], str]], stats: MergeStats,
    ) -> tuple[Any | None, str | None]:
        """Return (existing_row, confidence) for the first natural key that hits."""
        for cols, confidence in keys:
            if not all(c in tbl.c for c in cols):
                continue
            values = [row.get(c) for c in cols]
            if any(is_empty(v) for v in values):
                continue
            where = sa.and_(*[tbl.c[c] == v for c, v in zip(cols, values, strict=True)])
            hits = conn.execute(sa.select(tbl).where(where).limit(3)).mappings().all()
            if len(hits) == 1:
                return hits[0], confidence
            if len(hits) > 1:
                # Several production rows share this key: merging would pick one
                # arbitrarily, so leave it for a human.
                stats.ambiguous.append(
                    {"natural_key": list(cols), "values": [str(v) for v in values],
                     "candidates": len(hits)}
                )
                return None, "LOW"
        return None, None

    def merge_fields(
        self, existing: dict[str, Any], incoming: dict[str, Any], tbl: sa.Table,
        stats: MergeStats, pk_repr: str,
    ) -> dict[str, Any]:
        """Fill blank production columns from the source; log real conflicts."""
        updates: dict[str, Any] = {}
        pk_names = [c.name for c in tbl.primary_key]
        for col, new_value in incoming.items():
            if col not in tbl.c or new_value is None:
                continue
            if col in pk_names:
                continue
            current = existing.get(col)
            if is_empty(current):
                updates[col] = new_value
                stats.field_fills += 1
            elif str(current).strip() != str(new_value).strip():
                stats.conflicts.append(
                    {"pk": pk_repr, "column": col,
                     "db_value": str(current)[:120], "csv_value": str(new_value)[:120],
                     "resolution": "kept_db (production is the newer source)"}
                )
        return updates

    # -- main --------------------------------------------------------------
    def process(self, spec: TableSpec) -> MergeStats:
        stats = MergeStats(spec.table)
        path = CSV_DIR / spec.csv_name
        tbl = self.table(spec.table)
        col_types = {c.name: c.type for c in tbl.c}

        with self.engine.begin() as conn:
            stats.db_before = self.count(conn, spec.table)

            if not path.exists():
                stats.db_after = stats.db_before
                self.stats.append(stats)
                return stats

            with path.open(encoding="utf-8", errors="replace", newline="") as fh:
                reader = csv.DictReader(fh)
                raw_rows = list(reader)
            stats.source_rows = len(raw_rows)

            self.id_map.setdefault(spec.table, {})

            for raw in raw_rows:
                row: dict[str, Any] = {}
                for key, value in raw.items():
                    if key is None:
                        continue
                    name = key.lstrip("﻿").strip()
                    if name in JUNK_COLUMNS:
                        continue
                    name = spec.rename.get(name, name)
                    if name not in col_types:
                        continue  # obsolete/derived source column
                    row[name] = coerce(clean(value), col_types[name])

                if not row:
                    continue

                # Remap foreign keys through previously merged parents, and drop
                # rows whose parent genuinely does not exist.
                orphan = False
                for fk_col, (parent_table, _parent_pk) in spec.fks.items():
                    if fk_col not in row or row[fk_col] is None:
                        continue
                    mapped = self.id_map.get(parent_table, {}).get(str(row[fk_col]))
                    if mapped is not None:
                        row[fk_col] = mapped
                    parent = self.table(parent_table)
                    parent_pk_col = next(iter(parent.primary_key))
                    exists = conn.execute(
                        sa.select(parent_pk_col).where(parent_pk_col == row[fk_col]).limit(1)
                    ).first()
                    if not exists:
                        stats.orphans.append(
                            {"column": fk_col, "value": str(row[fk_col]),
                             "parent": parent_table, "reason": "parent row absent"}
                        )
                        orphan = True
                        break
                if orphan:
                    continue

                # An association row is nothing but its pair, so a NULL member
                # makes it meaningless and it would violate NOT NULL anyway.
                if spec.association and any(row.get(c) is None for c in spec.pk):
                    stats.orphans.append(
                        {"column": ",".join(spec.pk), "value": None,
                         "parent": spec.table,
                         "reason": "null key member in source row"}
                    )
                    continue

                pk_values = {c: row.get(c) for c in spec.pk if c in row}
                pk_repr = ",".join(f"{k}={v}" for k, v in pk_values.items())

                existing = None
                if len(pk_values) == len(spec.pk) and all(
                    v is not None for v in pk_values.values()
                ):
                    where = sa.and_(*[tbl.c[k] == v for k, v in pk_values.items()])
                    existing = conn.execute(sa.select(tbl).where(where)).mappings().first()
                    if existing is not None:
                        stats.matched_pk += 1

                if spec.association:
                    # The pair itself is the identity; nothing to merge into.
                    if existing is not None:
                        stats.duplicates_prevented += 1
                        continue
                    if self.apply:
                        conn.execute(sa.insert(tbl).values(**row))
                    stats.inserted += 1
                    continue

                confidence = None
                if existing is None and spec.natural_keys:
                    existing, confidence = self.find_by_natural_key(
                        conn, tbl, row, spec.natural_keys, stats
                    )
                    if existing is not None:
                        stats.matched_natural += 1

                if existing is not None:
                    if confidence == "LOW":
                        continue
                    updates = self.merge_fields(dict(existing), row, tbl, stats, pk_repr)
                    if updates and self.apply:
                        where = sa.and_(
                            *[tbl.c[c.name] == existing[c.name] for c in tbl.primary_key]
                        )
                        conn.execute(sa.update(tbl).where(where).values(**updates))
                    # Remember how the source id maps onto the surviving row.
                    if len(spec.pk) == 1:
                        source_id = raw.get(spec.pk[0])
                        current_id = existing[spec.pk[0]]
                        if source_id is not None and str(source_id) != str(current_id):
                            self.id_map[spec.table][str(source_id)] = current_id
                            stats.id_remaps[str(source_id)] = current_id
                    stats.duplicates_prevented += 1
                    continue

                # Genuinely new entity.
                if self.apply:
                    conn.execute(sa.insert(tbl).values(**row))
                stats.inserted += 1

            stats.db_after = self.count(conn, spec.table)

        self.stats.append(stats)
        return stats


def resync_sequences(engine: sa.Engine, tables: list[str]) -> list[str]:
    """Push identity sequences past the highest id so future inserts succeed."""
    done = []
    with engine.begin() as conn:
        for name in tables:
            tbl = sa.Table(name, sa.MetaData(), autoload_with=engine)
            pks = list(tbl.primary_key)
            if len(pks) != 1:
                continue
            col = pks[0]
            try:
                if col.type.python_type is not int:
                    continue
            except (NotImplementedError, AttributeError):
                continue
            seq = conn.execute(
                sa.text("select pg_get_serial_sequence(:t, :c)"),
                {"t": f'"{name}"', "c": col.name},
            ).scalar()
            if not seq:
                continue
            conn.execute(
                sa.text(
                    f'select setval(:seq, coalesce((select max("{col.name}") '
                    f'from "{name}"), 0) + 1, false)'
                ),
                {"seq": seq},
            )
            done.append(name)
    return done


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--report", action="store_true", help="analyse only, no writes")
    group.add_argument("--apply", action="store_true", help="perform the merge")
    parser.add_argument("--out", default="backups/merge_report.json")
    args = parser.parse_args()

    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 2

    engine = sa.create_engine(url)
    merger = Merger(engine, apply=args.apply)

    mode = "APPLY" if args.apply else "REPORT (no writes)"
    print(f"=== Pulse source merge — {mode} ===\n")
    header = (
        f"{'table':22}{'src':>6}{'before':>8}{'match':>7}{'ins':>6}"
        f"{'fills':>7}{'dupPrev':>9}{'confl':>7}{'orph':>6}{'after':>8}"
    )
    print(header)
    print("-" * len(header))

    for spec in SPECS:
        st = merger.process(spec)
        r = st.as_row()
        print(
            f"{r['table']:22}{r['source_rows']:>6}{r['db_before']:>8}{r['matched']:>7}"
            f"{r['inserted']:>6}{r['field_fills']:>7}{r['duplicates_prevented']:>9}"
            f"{r['conflicts']:>7}{r['orphans']:>6}{r['db_after']:>8}"
        )

    resynced: list[str] = []
    if args.apply:
        resynced = resync_sequences(engine, [s.table for s in SPECS])

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": mode,
        "tables": [s.as_row() for s in merger.stats],
        "conflicts": {s.table: s.conflicts for s in merger.stats if s.conflicts},
        "orphans": {s.table: s.orphans for s in merger.stats if s.orphans},
        "ambiguous": {s.table: s.ambiguous for s in merger.stats if s.ambiguous},
        "id_remaps": {s.table: s.id_remaps for s in merger.stats if s.id_remaps},
        "sequences_resynced": resynced,
    }
    out = PROJECT_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str))

    totals = {
        "inserted": sum(s.inserted for s in merger.stats),
        "field_fills": sum(s.field_fills for s in merger.stats),
        "conflicts": sum(len(s.conflicts) for s in merger.stats),
        "orphans": sum(len(s.orphans) for s in merger.stats),
        "ambiguous": sum(len(s.ambiguous) for s in merger.stats),
    }
    print(
        f"\ninserted={totals['inserted']}  field_fills={totals['field_fills']}  "
        f"conflicts={totals['conflicts']}  orphans={totals['orphans']}  "
        f"ambiguous={totals['ambiguous']}"
    )
    print(f"report -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
