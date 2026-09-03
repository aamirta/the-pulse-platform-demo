"""Repair text that was stored as UTF-8 but read back as Latin-1/cp1252.

A handful of rows carry the classic signature of that mistake: an institute is
stored as ``UniversitÃ© Ibn Tofail``, and four startup names came
through as ``sixiã¨mehomme`` and friends. They are visible to users --
those names sort to the end of the Z->A list and read as gibberish.

Two wrinkles the naive fix gets wrong:

* Some rows were lower-cased *after* the corruption, so the leading capital of
  each mojibake pair arrives lower-cased too. It has to be restored first.
* Some rows mix corrupted and correct characters -- one name holds a genuine en
  dash. Round-tripping the whole string destroys it, so each mojibake run is
  decoded on its own.

Run against the demo build (default) or the Postgres source:

    venv/bin/python scripts/demo/fix_mojibake.py             # dry run
    venv/bin/python scripts/demo/fix_mojibake.py --apply
    venv/bin/python scripts/demo/fix_mojibake.py --postgres --apply
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

load_dotenv(ROOT / ".env")

DEMO_DB = ROOT / "backend" / "thepulse.db"

# Columns that hold prose a reader actually sees.
TARGETS: tuple[tuple[str, str], ...] = (
    ("Institutes", "Institute Name"),
    ("Startups", "Startup name"),
    ("Founders", "skills"),
    ("Founders", "name"),
    ("Founders", "bio"),
    ("Investors", "Investor Name"),
)

# A mojibake run is the Latin-1/cp1252 view of a UTF-8 sequence: one lead
# character in C2-F4 followed by one to three continuation bytes in 80-BF.
# Bytes 80-9F have no Latin-1 glyph, so a cp1252 reader turned them into
# typographic characters instead -- 0x89 became a per-mille sign, which is why
# "sant\xc3\x89" arrives as "sant\u00e3\u2030". Those are mapped back, but only
# inside a candidate run: an en dash elsewhere in the string is genuine text.
_CP1252_HIGH = {bytes([b]).decode("cp1252"): b for b in range(0x80, 0xA0)
                if bytes([b]).decode("cp1252", "ignore")}
_LEAD = "".join(chr(b) for b in range(0xC2, 0xF5))
_CONT = "".join(chr(b) for b in range(0x80, 0xC0)) + "".join(_CP1252_HIGH)
RUN = re.compile(f"[{re.escape(_LEAD)}][{re.escape(_CONT)}]{{1,3}}")

# ZWJ (200D) is deliberately absent: it is meaningful inside emoji sequences.
ZERO_WIDTH = dict.fromkeys((0x200B, 0x200C, 0xFEFF))


def repair(value: str) -> str:
    """Return the repaired string, or the original when nothing decodes."""
    cleaned = value.translate(ZERO_WIDTH).strip()

    # Restore the lead character of each pair on rows lower-cased after the fact.
    restored = "".join(
        ("Ã" if ch == "ã" else "Â")
        if (
            ch in ("ã", "â")
            and i + 1 < len(cleaned)
            and (0x80 <= ord(cleaned[i + 1]) <= 0xBF
                 or cleaned[i + 1] in _CP1252_HIGH)
        )
        else ch
        for i, ch in enumerate(cleaned)
    )

    def decode_run(match: re.Match[str]) -> str:
        run = match.group(0)
        try:
            raw = bytes(_CP1252_HIGH.get(ch, ord(ch)) for ch in run)
            decoded = raw.decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return run
        return decoded if "�" not in decoded else run

    fixed = RUN.sub(decode_run, restored)
    if fixed == restored:
        return value  # nothing decoded: not a mojibake row

    # A row with no capital ASCII letters had been lower-cased wholesale, so the
    # recovered accents follow suit rather than reintroducing stray capitals.
    if not any(ch.isupper() for ch in cleaned if ch.isascii()):
        fixed = fixed.lower()
    return fixed


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair mis-decoded text.")
    parser.add_argument("--apply", action="store_true", help="write the repairs")
    parser.add_argument(
        "--postgres", action="store_true", help="target DATABASE_URL instead of the demo build"
    )
    args = parser.parse_args()

    if args.postgres:
        url = os.environ.get("DATABASE_URL", "")
        if not url or url.startswith("sqlite"):
            print("DATABASE_URL must point at the Postgres source.")
            return 1
    else:
        url = f"sqlite:///{DEMO_DB}"

    engine = create_engine(url)
    repaired = unresolved = 0

    # One transaction per column. A missing column raises, and on Postgres a
    # failed statement poisons the whole transaction -- sharing one would roll
    # back every repair made before it. SQLite is forgiving here, which is why
    # this only ever showed up against Postgres.
    for table, column in TARGETS:
        with engine.begin() as conn:
            try:
                rows = conn.execute(
                    text(f'SELECT DISTINCT "{column}" AS val FROM "{table}" WHERE "{column}" IS NOT NULL')
                ).fetchall()
            except Exception:
                continue  # column absent in this schema

            for (value,) in rows:
                if not isinstance(value, str):
                    continue
                fixed = repair(value)
                if fixed == value:
                    continue
                print(f"  {table}.{column}")
                print(f"     - {value!r}")
                print(f"     + {fixed!r}")
                if args.apply:
                    result = conn.execute(
                        text(f'UPDATE "{table}" SET "{column}" = :v WHERE "{column}" = :old'),
                        {"v": fixed, "old": value},
                    )
                    if result.rowcount < 1:
                        unresolved += 1
                        print("       !! UPDATE matched no rows")
                        continue
                repaired += 1

    where = "Postgres" if args.postgres else DEMO_DB.relative_to(ROOT)
    mode = "APPLIED to" if args.apply else "DRY RUN against"
    print(f"\n{mode} {where}: {repaired} repaired, {unresolved} unresolved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
