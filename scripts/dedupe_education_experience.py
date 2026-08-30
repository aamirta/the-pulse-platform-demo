"""
Dedupe Education and Experience rows that became duplicates after
founder merges (same founder + same content).

Strategy: keep the row with the smallest PK, delete the rest per group.

Usage:
    python scripts/dedupe_education_experience.py            # dry-run
    python scripts/dedupe_education_experience.py --apply
"""
import os, sys, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL environment variable is required")
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
MODE = 'APPLY' if args.apply else 'DRY-RUN'
print(f"=== DEDUPE EDUCATION + EXPERIENCES — {MODE} ===\n")

# CTE: for each group, get IDs sorted, keep the first, mark the rest for deletion.
EDU_DELETE_IDS_SQL = text('''
    WITH ranked AS (
        SELECT "Education Id",
               ROW_NUMBER() OVER (
                   PARTITION BY "Founder Id", "Institute Id", degree, start_date, end_date
                   ORDER BY "Education Id"
               ) AS rn
        FROM "Education"
        WHERE "Founder Id" IS NOT NULL
    )
    SELECT "Education Id" FROM ranked WHERE rn > 1
''')

EXP_DELETE_IDS_SQL = text('''
    WITH ranked AS (
        SELECT "Experience Id",
               ROW_NUMBER() OVER (
                   PARTITION BY "Founder Id", "Role", "Company"
                   ORDER BY "Experience Id"
               ) AS rn
        FROM "Experiences"
        WHERE "Founder Id" IS NOT NULL
    )
    SELECT "Experience Id" FROM ranked WHERE rn > 1
''')

with engine.connect() as c:
    edu_ids = [r[0] for r in c.execute(EDU_DELETE_IDS_SQL).fetchall()]
    exp_ids = [r[0] for r in c.execute(EXP_DELETE_IDS_SQL).fetchall()]
print(f"Education rows to delete: {len(edu_ids)}")
print(f"Experiences rows to delete: {len(exp_ids)}")

if not args.apply:
    print("\n(dry-run)")
    sys.exit(0)

with engine.begin() as tx:
    if edu_ids:
        r1 = tx.execute(
            text('DELETE FROM "Education" WHERE "Education Id" = ANY(:ids)'),
            {'ids': edu_ids}
        )
        print(f"✓ Deleted {r1.rowcount} duplicate Education rows")
    if exp_ids:
        r2 = tx.execute(
            text('DELETE FROM "Experiences" WHERE "Experience Id" = ANY(:ids)'),
            {'ids': exp_ids}
        )
        print(f"✓ Deleted {r2.rowcount} duplicate Experience rows")
