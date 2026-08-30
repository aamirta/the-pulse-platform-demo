"""
SELECT-only audit of data-quality issues in Founders + Startups.
Safe to run while enrichment agents are writing.

Writes findings to logs/audit_report.txt — no UPDATE/DELETE.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL environment variable is required")
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

OUT = []
def w(msg=''):
    print(msg)
    OUT.append(msg)

def section(title):
    w()
    w('=' * 70)
    w(title)
    w('=' * 70)


with engine.connect() as conn:
    # ---------- FOUNDERS ----------
    section('FOUNDERS')

    total_f = conn.execute(text('SELECT COUNT(*) FROM "Founders"')).scalar()
    w(f'Total founders: {total_f}')

    # Null / empty name
    null_name = conn.execute(text(
        'SELECT COUNT(*) FROM "Founders" '
        "WHERE name IS NULL OR TRIM(name) = ''"
    )).scalar()
    w(f'Founders with null/empty name: {null_name}')

    # Whitespace issues
    whitespace = conn.execute(text(
        'SELECT COUNT(*) FROM "Founders" '
        'WHERE name IS NOT NULL AND name <> TRIM(name)'
    )).scalar()
    w(f'Founders with leading/trailing whitespace in name: {whitespace}')

    # ALL CAPS last names (common in this dataset)
    allcaps = conn.execute(text(
        'SELECT COUNT(*) FROM "Founders" '
        "WHERE name IS NOT NULL AND name = UPPER(name) AND name ~ '[A-Z]{3,}'"
    )).scalar()
    w(f'Founders with ALL-CAPS name: {allcaps}')

    # Duplicate by normalized name + employer
    dup_name = conn.execute(text('''
        SELECT LOWER(TRIM(name)) AS nkey,
               COUNT(*) AS c
        FROM "Founders"
        WHERE name IS NOT NULL AND TRIM(name) <> ''
        GROUP BY LOWER(TRIM(name))
        HAVING COUNT(*) > 1
        ORDER BY c DESC
        LIMIT 20
    ''')).fetchall()
    w(f'\nDuplicate founder names (top 20, same normalized name):')
    for row in dup_name:
        w(f'  {row.c}×  {row.nkey}')
    total_dup_name = conn.execute(text('''
        SELECT COALESCE(SUM(c - 1), 0) FROM (
            SELECT COUNT(*) AS c FROM "Founders"
            WHERE name IS NOT NULL AND TRIM(name) <> ''
            GROUP BY LOWER(TRIM(name))
            HAVING COUNT(*) > 1
        ) x
    ''')).scalar()
    w(f'Total duplicate rows (all name-duplicates): {total_dup_name}')

    # Duplicate by linkedin_url
    dup_li = conn.execute(text('''
        SELECT linkedin_url, COUNT(*) AS c
        FROM "Founders"
        WHERE linkedin_url IS NOT NULL AND TRIM(linkedin_url) <> ''
        GROUP BY linkedin_url
        HAVING COUNT(*) > 1
        ORDER BY c DESC
        LIMIT 20
    ''')).fetchall()
    w(f'\nDuplicate LinkedIn URLs in Founders (top 20):')
    for row in dup_li:
        w(f'  {row.c}×  {row.linkedin_url}')
    total_dup_li = conn.execute(text('''
        SELECT COALESCE(SUM(c - 1), 0) FROM (
            SELECT COUNT(*) AS c FROM "Founders"
            WHERE linkedin_url IS NOT NULL AND TRIM(linkedin_url) <> ''
            GROUP BY linkedin_url
            HAVING COUNT(*) > 1
        ) x
    ''')).scalar()
    w(f'Total duplicate rows (all LinkedIn-duplicates): {total_dup_li}')

    # Malformed LinkedIn URLs
    malformed_li = conn.execute(text('''
        SELECT "Founder Id", name, linkedin_url FROM "Founders"
        WHERE linkedin_url IS NOT NULL
          AND TRIM(linkedin_url) <> ''
          AND linkedin_url !~* '^https?://([a-z]{2,3}\\.)?linkedin\\.com/in/'
        LIMIT 15
    ''')).fetchall()
    count_malformed_li = conn.execute(text('''
        SELECT COUNT(*) FROM "Founders"
        WHERE linkedin_url IS NOT NULL
          AND TRIM(linkedin_url) <> ''
          AND linkedin_url !~* '^https?://([a-z]{2,3}\\.)?linkedin\\.com/in/'
    ''')).scalar()
    w(f'\nFounders with malformed LinkedIn URL (not matching linkedin.com/in/): {count_malformed_li}')
    for row in malformed_li:
        w(f'  [{row[0]}] {row[1]}  →  {row[2]}')

    # ---------- STARTUPS ----------
    section('STARTUPS')

    total_s = conn.execute(text('SELECT COUNT(*) FROM "Startups"')).scalar()
    w(f'Total startups: {total_s}')

    null_sname = conn.execute(text(
        'SELECT COUNT(*) FROM "Startups" '
        "WHERE \"Startup name\" IS NULL OR TRIM(\"Startup name\") = ''"
    )).scalar()
    w(f'Startups with null/empty name: {null_sname}')

    whitespace_s = conn.execute(text(
        'SELECT COUNT(*) FROM "Startups" '
        'WHERE "Startup name" IS NOT NULL AND "Startup name" <> TRIM("Startup name")'
    )).scalar()
    w(f'Startups with leading/trailing whitespace in name: {whitespace_s}')

    # Duplicate startup names
    dup_sname = conn.execute(text('''
        SELECT LOWER(TRIM("Startup name")) AS nkey, COUNT(*) AS c
        FROM "Startups"
        WHERE "Startup name" IS NOT NULL AND TRIM("Startup name") <> ''
        GROUP BY LOWER(TRIM("Startup name"))
        HAVING COUNT(*) > 1
        ORDER BY c DESC
        LIMIT 20
    ''')).fetchall()
    w(f'\nDuplicate startup names (top 20):')
    for row in dup_sname:
        w(f'  {row.c}×  {row.nkey}')
    total_dup_sname = conn.execute(text('''
        SELECT COALESCE(SUM(c - 1), 0) FROM (
            SELECT COUNT(*) AS c FROM "Startups"
            WHERE "Startup name" IS NOT NULL AND TRIM("Startup name") <> ''
            GROUP BY LOWER(TRIM("Startup name"))
            HAVING COUNT(*) > 1
        ) x
    ''')).scalar()
    w(f'Total duplicate rows (all name-duplicates): {total_dup_sname}')

    # Duplicate LinkedIn URLs in Startups
    dup_sli = conn.execute(text('''
        SELECT linkedin, COUNT(*) AS c
        FROM "Startups"
        WHERE linkedin IS NOT NULL AND TRIM(linkedin) <> ''
        GROUP BY linkedin
        HAVING COUNT(*) > 1
        ORDER BY c DESC
        LIMIT 15
    ''')).fetchall()
    w(f'\nDuplicate LinkedIn company URLs in Startups (top 15):')
    for row in dup_sli:
        w(f'  {row.c}×  {row.linkedin}')

    # Malformed startup LinkedIn
    mal_sli = conn.execute(text('''
        SELECT COUNT(*) FROM "Startups"
        WHERE linkedin IS NOT NULL
          AND TRIM(linkedin) <> ''
          AND linkedin !~* 'linkedin\\.com/(company|school|showcase)/'
    ''')).scalar()
    w(f'\nStartups with malformed LinkedIn (not /company/, /school/, /showcase/): {mal_sli}')

    # Sector token analysis
    w(f'\nSector token distribution:')
    sectors_rows = conn.execute(text(
        'SELECT sector FROM "Startups" WHERE sector IS NOT NULL AND TRIM(sector) <> \'\''
    )).fetchall()
    tokens = Counter()
    for (s,) in sectors_rows:
        for tok in s.split(','):
            tk = tok.strip()
            if tk:
                tokens[tk] += 1
    w(f'  Distinct sector tokens: {len(tokens)}')
    # Case-insensitive duplicates (e.g., "FinTech" vs "fintech")
    ci_groups = {}
    for tok, c in tokens.items():
        ci_groups.setdefault(tok.lower(), []).append((tok, c))
    case_dupes = [(k, v) for k, v in ci_groups.items() if len(v) > 1]
    w(f'  Case-variant duplicate tokens: {len(case_dupes)}')
    for k, variants in case_dupes[:10]:
        w(f'    {k!r}: {variants}')

    # ---------- ORPHANS / FK INTEGRITY ----------
    section('ORPHANS & FK INTEGRITY')

    orphan_sf_s = conn.execute(text('''
        SELECT COUNT(*) FROM "StartupFounders" sf
        LEFT JOIN "Startups" s ON s."Startup Id" = sf."Startup Id"
        WHERE s."Startup Id" IS NULL
    ''')).scalar()
    w(f'StartupFounders rows pointing to missing Startup: {orphan_sf_s}')

    orphan_sf_f = conn.execute(text('''
        SELECT COUNT(*) FROM "StartupFounders" sf
        LEFT JOIN "Founders" f ON f."Founder Id" = sf."Founder Id"
        WHERE f."Founder Id" IS NULL
    ''')).scalar()
    w(f'StartupFounders rows pointing to missing Founder: {orphan_sf_f}')

    # Founders not linked to any startup
    unlinked_f = conn.execute(text('''
        SELECT COUNT(*) FROM "Founders" f
        LEFT JOIN "StartupFounders" sf ON sf."Founder Id" = f."Founder Id"
        WHERE sf."Founder Id" IS NULL
    ''')).scalar()
    w(f'Founders with zero startup link: {unlinked_f}')

    section('END')

# Write report
os.makedirs('logs', exist_ok=True)
with open('logs/audit_report.txt', 'w') as f:
    f.write('\n'.join(OUT))
print('\nWrote logs/audit_report.txt')
