"""
Miscellaneous cleanup pass:

  1. Delete 2 founders that are actually organisations (null-name + CEED GROW).
  2. Title-case 3 ALL-CAPS founder names.
  3. NULL 15 startup linkedin fields that hold invalid URLs
     (search results, /in/ personal profiles, /add, bare domain, etc).

Usage:
    python scripts/misc_cleanups.py            # dry-run
    python scripts/misc_cleanups.py --apply
"""
import os, sys, argparse, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL environment variable is required")
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

# Organisations wrongly stored as founders — delete them
NON_PERSON_IDS = ['23538', '27707']

# ALL-CAPS names to title-case
ALLCAPS_FIX = {
    '99954':  'Zouhair Brouzi',
    '32477':  'Younes Boumalek',
    '100048': 'Ilyas El Aouad',
}

# Startups whose linkedin field is garbage → NULL
BAD_STARTUP_LI_IDS = [1047, 59, 1040, 1050, 358, 296, 676, 65, 272, 295, 353, 373, 449, 450, 1015]

parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
MODE = 'APPLY' if args.apply else 'DRY-RUN'
print(f"=== MISC CLEANUPS — {MODE} ===\n")

with engine.connect() as conn:
    print("1) Non-person founders to delete:")
    rows = conn.execute(text('''
        SELECT "Founder Id", name, current_title, linkedin_url
        FROM "Founders" WHERE "Founder Id" = ANY(:ids)
    '''), {'ids': NON_PERSON_IDS}).fetchall()
    for r in rows:
        print(f"  {r[0]:<8} {r[1]!r:<30} title={r[2]!r}  li={r[3]}")

    print("\n2) ALL-CAPS names to title-case:")
    rows = conn.execute(text('''
        SELECT "Founder Id", name FROM "Founders"
        WHERE "Founder Id" = ANY(:ids)
    '''), {'ids': list(ALLCAPS_FIX.keys())}).fetchall()
    for r in rows:
        new = ALLCAPS_FIX.get(r[0], '—')
        print(f"  {r[0]:<8} {r[1]!r}  →  {new!r}")

    print("\n3) Startups with bad LinkedIn to NULL:")
    rows = conn.execute(text('''
        SELECT "Startup Id", "Startup name", linkedin FROM "Startups"
        WHERE "Startup Id" = ANY(:ids)
    '''), {'ids': BAD_STARTUP_LI_IDS}).fetchall()
    for r in rows:
        li_s = (r[2] or '')[:80]
        print(f"  {r[0]:<5} {r[1]:<30} {li_s}")

if not args.apply:
    print("\n(dry-run — no changes applied. Run with --apply to execute.)")
    sys.exit(0)

with engine.begin() as tx:
    # 1) Delete non-person founders (safe: neither has startup/education links)
    r1 = tx.execute(text('DELETE FROM "StartupFounders"   WHERE "Founder Id" = ANY(:ids)'),
                    {'ids': NON_PERSON_IDS})
    r2 = tx.execute(text('DELETE FROM "IncubatorFounders" WHERE "Founder Id" = ANY(:ids)'),
                    {'ids': NON_PERSON_IDS})
    r3 = tx.execute(text('DELETE FROM "Education"         WHERE "Founder Id" = ANY(:ids)'),
                    {'ids': NON_PERSON_IDS})
    r4 = tx.execute(text('DELETE FROM "Experiences"       WHERE "Founder Id" = ANY(:ids)'),
                    {'ids': NON_PERSON_IDS})
    r5 = tx.execute(text('DELETE FROM "Founders"          WHERE "Founder Id" = ANY(:ids)'),
                    {'ids': NON_PERSON_IDS})
    print(f"  ✓ Deleted {r5.rowcount} founder rows (and {r1.rowcount + r2.rowcount + r3.rowcount + r4.rowcount} FK rows)")

    # 2) Title-case names
    for fid, new in ALLCAPS_FIX.items():
        tx.execute(text('UPDATE "Founders" SET name = :n WHERE "Founder Id" = :i'),
                   {'n': new, 'i': fid})
    print(f"  ✓ Title-cased {len(ALLCAPS_FIX)} names")

    # 3) Null bad startup linkedin
    r6 = tx.execute(text('UPDATE "Startups" SET linkedin = NULL WHERE "Startup Id" = ANY(:ids)'),
                    {'ids': BAD_STARTUP_LI_IDS})
    print(f"  ✓ Nulled LinkedIn on {r6.rowcount} startups")
