"""
Final pass:

  1. Startup 'stage' field: collapse ALL-CAPS variants into proper
     Title-case spellings with accents.
       AMORCAGE               → Amorçage
       IDEATION               → Idéation
       INTERNATIONALISATION   → Internationalisation
       SCALING                → Scaling

  2. Articles 'source_url' not starting with http → prefix https:// or null.

Usage:
    python scripts/normalize_stages_and_urls.py           # dry-run
    python scripts/normalize_stages_and_urls.py --apply
"""
import os, sys, argparse, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL environment variable is required")
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

STAGE_MAP = {
    'AMORCAGE':              'Amorçage',
    'AMORÇAGE':              'Amorçage',
    'IDEATION':              'Idéation',
    'IDÉATION':              'Idéation',
    'INTERNATIONALISATION':  'Internationalisation',
    'SCALING':               'Scaling',
}

parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
MODE = 'APPLY' if args.apply else 'DRY-RUN'
print(f"=== NORMALIZE STAGES + URLS — {MODE} ===\n")

with engine.connect() as c:
    print("1) Stage normalization plan:")
    for old, new in STAGE_MAP.items():
        n = c.execute(text('SELECT COUNT(*) FROM "Startups" WHERE stage = :s'), {'s': old}).scalar()
        print(f"   {n:<5}  {old!r:<26} → {new!r}")

    print("\n2) Articles with source_url not starting with http:")
    bad_arts = c.execute(text('''
        SELECT article_id, title, source_url FROM articles
        WHERE source_url IS NOT NULL AND TRIM(source_url) <> ''
          AND source_url NOT LIKE 'http%'
    ''')).fetchall()
    for r in bad_arts:
        print(f"   id={r[0]:<3} {r[1][:40]!r:<42}  url={r[2]!r}")

if not args.apply:
    print("\n(dry-run)")
    sys.exit(0)

with engine.begin() as tx:
    total = 0
    for old, new in STAGE_MAP.items():
        r = tx.execute(text('UPDATE "Startups" SET stage = :n WHERE stage = :o'),
                       {'o': old, 'n': new})
        total += r.rowcount
    print(f"  ✓ Updated stage on {total} startups")

    # For each bad article: if it looks like a domain/url without protocol, prefix https://
    # Otherwise NULL it.
    fixed = nulled = 0
    for aid, title, url in bad_arts:
        u = url.strip()
        if re.match(r'^(www\.)?[a-z0-9\-]+\.[a-z]{2,}', u, re.I):
            new_url = 'https://' + u
            tx.execute(text('UPDATE articles SET source_url = :u WHERE article_id = :i'),
                       {'u': new_url, 'i': aid})
            fixed += 1
        else:
            tx.execute(text('UPDATE articles SET source_url = NULL WHERE article_id = :i'),
                       {'i': aid})
            nulled += 1
    print(f"  ✓ Fixed {fixed} article URLs, nulled {nulled}")
