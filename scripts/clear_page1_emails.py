"""
Clear teaser_emails / teaser_personal_emails / teaser_professional_emails
for all founders shown on page 1 of /founders.

Those fields hold scraped domain-only teasers (e.g. "yolafresh.com, gmail.com")
that look bad on public profiles. This NULLs them — does not touch anything else.

Usage:
    python scripts/clear_page1_emails.py            # dry-run
    python scripts/clear_page1_emails.py --apply    # execute
"""
import os, sys, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL environment variable is required")
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

# Mimic the /founders route ordering to get the first 20 ids
PAGE1_IDS_SQL = text('''
WITH max_funding AS (
    SELECT sf."Founder Id" AS fid, MAX(s.total_funding_usd) AS mf
    FROM "StartupFounders" sf
    JOIN "Startups" s ON s."Startup Id" = sf."Startup Id"
    GROUP BY sf."Founder Id"
)
SELECT f."Founder Id", f.name
FROM "Founders" f
LEFT JOIN max_funding mf ON mf.fid = f."Founder Id"
WHERE f.name IS NOT NULL AND f.name <> ''
  AND (f.current_title IS NOT NULL
       OR f.profile_pic IS NOT NULL
       OR f.location IS NOT NULL
       OR f.company_details_name IS NOT NULL
       OR f.linkedin_url IS NOT NULL)
ORDER BY CASE WHEN mf.mf IS NOT NULL THEN 0 ELSE 1 END,
         mf.mf DESC NULLS LAST,
         f.name ASC
LIMIT 20
''')

parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
MODE = 'APPLY' if args.apply else 'DRY-RUN'
print(f"=== CLEAR PAGE-1 EMAILS — {MODE} ===\n")

with engine.connect() as conn:
    rows = conn.execute(PAGE1_IDS_SQL).fetchall()
    ids = [r[0] for r in rows]
    print(f"Page-1 founders ({len(ids)}):")
    for r in rows:
        print(f"  {r[0]:<8} {r[1]}")

    # Show current email values
    current = conn.execute(text('''
        SELECT "Founder Id", name,
               teaser_emails, teaser_personal_emails, teaser_professional_emails
        FROM "Founders"
        WHERE "Founder Id" = ANY(:ids)
          AND (teaser_emails IS NOT NULL
            OR teaser_personal_emails IS NOT NULL
            OR teaser_professional_emails IS NOT NULL)
        ORDER BY name
    '''), {'ids': ids}).fetchall()

    print(f"\nFounders with at least one email field set: {len(current)}")
    for r in current:
        print(f"  {r[0]:<8} {r[1]}")
        if r[2]: print(f"    teaser_emails              = {r[2]!r}")
        if r[3]: print(f"    teaser_personal_emails     = {r[3]!r}")
        if r[4]: print(f"    teaser_professional_emails = {r[4]!r}")

if not args.apply:
    print("\n(dry-run — no changes applied. Run with --apply to execute.)")
    sys.exit(0)

with engine.begin() as tx:
    result = tx.execute(text('''
        UPDATE "Founders"
           SET teaser_emails              = NULL,
               teaser_personal_emails     = NULL,
               teaser_professional_emails = NULL
         WHERE "Founder Id" = ANY(:ids)
    '''), {'ids': ids})
    print(f"\n✓ {result.rowcount} rows touched.")
