"""
NULL teaser_emails / teaser_personal_emails / teaser_professional_emails
for ALL founders. These scraped teaser fields expose domain-only fragments
(gmail.com, yolafresh.com) and occasional real private emails on public
profile pages — RGPD-unsafe and visually ugly.

Usage:
    python scripts/clear_all_emails.py            # dry-run (count only)
    python scripts/clear_all_emails.py --apply    # execute
"""
import os, sys, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ['DATABASE_URL'] = (
    'postgresql://postgres.lianafeunaxlzqfvslob:'
    'Habiba456!!!!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'
)
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
MODE = 'APPLY' if args.apply else 'DRY-RUN'
print(f"=== CLEAR ALL FOUNDER EMAILS — {MODE} ===\n")

with engine.connect() as conn:
    c1 = conn.execute(text('SELECT COUNT(*) FROM "Founders" WHERE teaser_emails              IS NOT NULL')).scalar()
    c2 = conn.execute(text('SELECT COUNT(*) FROM "Founders" WHERE teaser_personal_emails     IS NOT NULL')).scalar()
    c3 = conn.execute(text('SELECT COUNT(*) FROM "Founders" WHERE teaser_professional_emails IS NOT NULL')).scalar()
    cAny = conn.execute(text('''
        SELECT COUNT(*) FROM "Founders"
        WHERE teaser_emails IS NOT NULL
           OR teaser_personal_emails IS NOT NULL
           OR teaser_professional_emails IS NOT NULL
    ''')).scalar()
    # Count how many of those contain a real @ (not just domain fragments)
    cReal = conn.execute(text('''
        SELECT COUNT(*) FROM "Founders"
        WHERE teaser_emails              LIKE '%@%'
           OR teaser_personal_emails     LIKE '%@%'
           OR teaser_professional_emails LIKE '%@%'
    ''')).scalar()

print(f"teaser_emails              not NULL: {c1}")
print(f"teaser_personal_emails     not NULL: {c2}")
print(f"teaser_professional_emails not NULL: {c3}")
print(f"Founders with ≥1 email field set   : {cAny}")
print(f"  … of which contain a real @-mail : {cReal}")

if not args.apply:
    print("\n(dry-run — no changes applied. Run with --apply to execute.)")
    sys.exit(0)

with engine.begin() as tx:
    result = tx.execute(text('''
        UPDATE "Founders"
           SET teaser_emails              = NULL,
               teaser_personal_emails     = NULL,
               teaser_professional_emails = NULL
         WHERE teaser_emails              IS NOT NULL
            OR teaser_personal_emails     IS NOT NULL
            OR teaser_professional_emails IS NOT NULL
    '''))
    print(f"\n✓ {result.rowcount} rows cleared.")
