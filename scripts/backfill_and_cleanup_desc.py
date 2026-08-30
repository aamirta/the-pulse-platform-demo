"""
  1. Backfill founders' current_employer from their linked startup name
     when the employer is NULL/empty (33 rows).
  2. NULL obvious junk startup descriptions (INDH=URL, startup6=placeholder).
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL environment variable is required")
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

with engine.begin() as tx:
    r1 = tx.execute(text("""
        UPDATE "Founders" f
           SET current_employer = s."Startup name"
          FROM "StartupFounders" sf
          JOIN "Startups" s ON s."Startup Id" = sf."Startup Id"
         WHERE f."Founder Id" = sf."Founder Id"
           AND (f.current_employer IS NULL OR TRIM(f.current_employer) = '')
           AND s."Startup name" IS NOT NULL
           AND TRIM(s."Startup name") <> ''
    """))
    print(f"✓ Backfilled employer on {r1.rowcount} founders")

    r2 = tx.execute(text(
        'UPDATE "Startups" SET description = NULL WHERE "Startup Id" IN (1742, 450)'
    ))
    print(f"✓ Nulled {r2.rowcount} junk descriptions (INDH, startup6)")
