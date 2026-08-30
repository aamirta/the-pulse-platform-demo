"""
Merge duplicate Founder records.

For each (keep_id, delete_id) pair:
  1. Copy StartupFounders rows from delete_id → keep_id (skipping existing links).
  2. Delete remaining StartupFounders rows for delete_id.
  3. Delete the duplicate Founder row.

Usage:
    python scripts/merge_duplicate_founders.py            # dry-run
    python scripts/merge_duplicate_founders.py --apply    # execute
"""
import os, sys, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL environment variable is required")
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

# (keep_id, delete_id, label)
MERGES = [
    # Already applied — kept for audit trail
    # ('65811', '100069', 'Larbi Belrhiti (YoLa Fresh)'),
    # ('27805', '100137', 'Mehdi Alami  (Freterium)'),
    # Applied — kept for audit trail
    # ('62283', '100138', 'Omar Kouhene    (Freterium)'),
    # ('11514', '100157', 'El Aboussoror   (konta)'),
    # ('74797', '100146', 'Imad Zekri      (Cathedis)'),
    # ('28862', '100116', 'Amine Houssaini (kwiks)'),
    ('96915', '100088', 'Nizar Maane     (kifal)'),
]

parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
MODE = 'APPLY' if args.apply else 'DRY-RUN'
print(f"=== MERGE FOUNDERS — {MODE} ===\n")

with engine.connect() as conn:
    for keep_id, del_id, label in MERGES:
        print(f"— {label}")
        # What links does the delete row have that the keep row does NOT?
        transfer_rows = conn.execute(text('''
            SELECT sf_del."Startup Id", s."Startup name"
            FROM "StartupFounders" sf_del
            LEFT JOIN "Startups" s ON s."Startup Id" = sf_del."Startup Id"
            WHERE sf_del."Founder Id" = :d
              AND NOT EXISTS (
                  SELECT 1 FROM "StartupFounders" sf_keep
                  WHERE sf_keep."Founder Id" = :k
                    AND sf_keep."Startup Id" = sf_del."Startup Id"
              )
        '''), {'d': del_id, 'k': keep_id}).fetchall()
        print(f"    keep {keep_id}   delete {del_id}")
        print(f"    startup links to transfer: {len(transfer_rows)}")
        for sid, sname in transfer_rows:
            print(f"      → ({sid}) {sname}")

        # Rows that will simply be dropped (shared links, so founder disappears from that join)
        drop_rows = conn.execute(text('''
            SELECT sf."Startup Id", s."Startup name"
            FROM "StartupFounders" sf
            LEFT JOIN "Startups" s ON s."Startup Id" = sf."Startup Id"
            WHERE sf."Founder Id" = :d
              AND EXISTS (
                  SELECT 1 FROM "StartupFounders" sfk
                  WHERE sfk."Founder Id" = :k AND sfk."Startup Id" = sf."Startup Id"
              )
        '''), {'d': del_id, 'k': keep_id}).fetchall()
        print(f"    redundant links to drop: {len(drop_rows)}")
        for sid, sname in drop_rows:
            print(f"      × ({sid}) {sname}")
        print()

        if args.apply:
            with engine.begin() as tx:
                # 1) transfer new links
                if transfer_rows:
                    tx.execute(text('''
                        INSERT INTO "StartupFounders" ("Startup Id", "Founder Id")
                        SELECT sf."Startup Id", :k
                        FROM "StartupFounders" sf
                        WHERE sf."Founder Id" = :d
                          AND NOT EXISTS (
                              SELECT 1 FROM "StartupFounders" sfk
                              WHERE sfk."Founder Id" = :k
                                AND sfk."Startup Id" = sf."Startup Id"
                          )
                    '''), {'k': keep_id, 'd': del_id})
                # 2) remove all links from delete row
                tx.execute(
                    text('DELETE FROM "StartupFounders" WHERE "Founder Id" = :d'),
                    {'d': del_id}
                )
                # 3) delete the duplicate founder
                tx.execute(
                    text('DELETE FROM "Founders" WHERE "Founder Id" = :d'),
                    {'d': del_id}
                )
            print(f"    ✓ applied\n")

if not args.apply:
    print("(dry-run — no changes applied. Run with --apply to execute.)")
