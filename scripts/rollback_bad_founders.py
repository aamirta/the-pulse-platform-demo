"""
Rollback the garbage founders inserted by the last enrich_founders.py run.

Usage:
    python scripts/rollback_bad_founders.py            # dry-run (default)
    python scripts/rollback_bad_founders.py --apply    # really delete

Deletes from StartupFounders first (FK), then Founders.
Prints every row it would touch.
"""
import os, sys, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ['DATABASE_URL'] = (
    'postgresql://postgres.lianafeunaxlzqfvslob:'
    'Habiba456!!!!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'
)
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

# Obvious garbage — phrase fragments, newspaper prefixes, company names,
# or rows with a LinkedIn URL that belongs to someone else.
GARBAGE_IDS = [
    '100251',   # Douja Gharbi — wrongly linked to Patricia del Rio's LinkedIn
    '100270',   # The Hindu Suchana Seth
    '100274',   # Ajit Anand- Co
    '100275',   # Fashion Forward We are
    '100278',   # as the Co
    '100279',   # Maxson Lewis — discovery garbage at BIRDEV
    '100280',   # Magenta Mobility — company name, not a person
    '100287',   # Replit Tournament Tasneem Sabri
]

parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true', help='Actually perform DELETE')
args = parser.parse_args()

MODE = 'APPLY' if args.apply else 'DRY-RUN'
print(f"=== ROLLBACK — {MODE} ===\n")

with engine.connect() as conn:
    # Preview what will be deleted
    preview_sql = text('''
        SELECT f."Founder Id", f.name, s."Startup name", s."Startup Id"
        FROM "Founders" f
        LEFT JOIN "StartupFounders" sf ON sf."Founder Id" = f."Founder Id"
        LEFT JOIN "Startups" s ON s."Startup Id" = sf."Startup Id"
        WHERE f."Founder Id" = ANY(:ids)
        ORDER BY CAST(f."Founder Id" AS INTEGER)
    ''')
    rows = conn.execute(preview_sql, {'ids': GARBAGE_IDS}).fetchall()
    print(f"Rows to delete: {len(rows)}")
    for r in rows:
        print(f"  founder {r[0]:<8} name='{r[1]}' → startup='{r[2]}' (id={r[3]})")

    if not args.apply:
        print("\n(dry-run — no changes applied. Run with --apply to execute.)")
        sys.exit(0)

with engine.begin() as tx:
    r1 = tx.execute(
        text('DELETE FROM "StartupFounders" WHERE "Founder Id" = ANY(:ids)'),
        {'ids': GARBAGE_IDS}
    )
    print(f"\nDeleted {r1.rowcount} rows from StartupFounders")
    r2 = tx.execute(
        text('DELETE FROM "IncubatorFounders" WHERE "Founder Id" = ANY(:ids)'),
        {'ids': GARBAGE_IDS}
    )
    print(f"Deleted {r2.rowcount} rows from IncubatorFounders")
    r3 = tx.execute(
        text('DELETE FROM "Education" WHERE "Founder Id" = ANY(:ids)'),
        {'ids': GARBAGE_IDS}
    )
    print(f"Deleted {r3.rowcount} rows from Education")
    r4 = tx.execute(
        text('DELETE FROM "Experiences" WHERE "Founder Id" = ANY(:ids)'),
        {'ids': GARBAGE_IDS}
    )
    print(f"Deleted {r4.rowcount} rows from Experiences")
    r5 = tx.execute(
        text('DELETE FROM "Founders" WHERE "Founder Id" = ANY(:ids)'),
        {'ids': GARBAGE_IDS}
    )
    print(f"Deleted {r5.rowcount} rows from Founders")

print("\n=== DONE ===")
