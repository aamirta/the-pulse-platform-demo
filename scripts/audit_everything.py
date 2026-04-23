"""
Broad audit of all secondary tables — looks for dupes, placeholders,
broken URLs, inconsistent casing, and other obvious smells.

SELECT-only.
"""
import os, sys, re
from collections import Counter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ['DATABASE_URL'] = (
    'postgresql://postgres.lianafeunaxlzqfvslob:'
    'Habiba456!!!!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'
)
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])


def section(title):
    print()
    print('=' * 72)
    print(title)
    print('=' * 72)


with engine.connect() as c:
    # ---------- STARTUPS — deeper ----------
    section('STARTUPS — deeper checks')

    # Contact email that's just a domain / looks bogus
    rows = c.execute(text('''
        SELECT COUNT(*) FROM "Startups"
        WHERE "contactEmail" IS NOT NULL
          AND TRIM("contactEmail") <> ''
          AND "contactEmail" NOT LIKE '%@%'
    ''')).scalar()
    print(f'  startups with contactEmail lacking "@": {rows}')

    # Very short descriptions (likely junk)
    rows = c.execute(text('''
        SELECT COUNT(*) FROM "Startups"
        WHERE description IS NOT NULL AND LENGTH(TRIM(description)) BETWEEN 1 AND 20
    ''')).scalar()
    print(f'  startups with very short description (1-20 chars): {rows}')

    # Description equals startup name
    rows = c.execute(text('''
        SELECT COUNT(*) FROM "Startups"
        WHERE description IS NOT NULL
          AND TRIM(LOWER(description)) = TRIM(LOWER("Startup name"))
    ''')).scalar()
    print(f'  startups where description == name (no real desc): {rows}')

    # Missing logo for well-funded startups (visible on vitrine)
    rows = c.execute(text('''
        SELECT COUNT(*) FROM "Startups"
        WHERE (logo_url IS NULL OR TRIM(logo_url) = '')
          AND total_funding_usd > 100000
    ''')).scalar()
    print(f'  well-funded (>100k) startups with NO logo: {rows}')

    # Stage distribution
    rows = c.execute(text('SELECT stage, COUNT(*) FROM "Startups" GROUP BY stage ORDER BY 2 DESC LIMIT 15')).fetchall()
    print(f'\n  Stage distribution (top 15):')
    for s, n in rows:
        print(f'    {n:<5}  {s!r}')

    # year_founded anomalies
    rows = c.execute(text('''
        SELECT "YearFounded", COUNT(*) FROM "Startups"
        WHERE "YearFounded" IS NOT NULL AND TRIM("YearFounded") <> ''
          AND NOT "YearFounded" ~ '^[12][0-9]{3}$'
        GROUP BY "YearFounded" ORDER BY 2 DESC LIMIT 10
    ''')).fetchall()
    print(f'\n  Weird year_founded values: {len(rows)}')
    for y, n in rows[:10]:
        print(f'    {n:<3}  {y!r}')

    # ---------- FOUNDING ROUND ----------
    section('FUNDING ROUNDS')
    n = c.execute(text('SELECT COUNT(*) FROM "FundingRounds"')).scalar()
    orph = c.execute(text('''
        SELECT COUNT(*) FROM "FundingRounds" fr
        LEFT JOIN "Startups" s ON s."Startup Id" = fr."Startup Id"
        WHERE fr."Startup Id" IS NOT NULL AND s."Startup Id" IS NULL
    ''')).scalar()
    print(f'  total rounds: {n}')
    print(f'  orphan rounds (FK to missing startup): {orph}')

    # Rounds with null startup_id AND null startup_name (pure junk)
    rows = c.execute(text('''
        SELECT COUNT(*) FROM "FundingRounds"
        WHERE "Startup Id" IS NULL
          AND ("Startup Name" IS NULL OR TRIM("Startup Name") = '')
    ''')).scalar()
    print(f'  fully-null rounds (no startup_id AND no startup_name): {rows}')

    # ---------- INCUBATORS ----------
    section('INCUBATORS')
    rows = c.execute(text('SELECT COUNT(*) FROM "Incubators"')).scalar()
    whitespace = c.execute(text('''
        SELECT COUNT(*) FROM "Incubators"
        WHERE "Incubator" IS NOT NULL AND "Incubator" <> TRIM("Incubator")
    ''')).scalar()
    print(f'  total: {rows}')
    print(f'  with leading/trailing whitespace: {whitespace}')

    # ---------- INVESTORS ----------
    section('INVESTORS')
    rows = c.execute(text('SELECT COUNT(*) FROM "Investors"')).scalar()
    print(f'  total: {rows}')

    # Malformed logo/linkedin on investors
    li_bad = c.execute(text('''
        SELECT COUNT(*) FROM "Investors"
        WHERE linkedin_url IS NOT NULL
          AND TRIM(linkedin_url) <> ''
          AND linkedin_url !~* 'linkedin\\.com/(company|school|showcase|in)/'
    ''')).scalar()
    print(f'  investors with malformed LinkedIn: {li_bad}')

    # ---------- CONTENT TABLES ----------
    section('CONTENT TABLES (posts / articles / resources)')
    for tbl in ('posts', 'articles', 'resources', 'direct_messages', 'pulse_members',
                'talents', 'experts', 'cofounder_projects'):
        n = c.execute(text(f'SELECT COUNT(*) FROM {tbl}')).scalar()
        print(f'  {tbl:<20}  rows={n}')

    # Unconfirmed pulse members beyond, say, 14 days
    stale = c.execute(text('''
        SELECT COUNT(*) FROM pulse_members
        WHERE is_confirmed = false
          AND created_at < NOW() - INTERVAL '14 days'
    ''')).scalar()
    print(f'  pulse_members unconfirmed > 14 days: {stale}')

    # Posts with null author or empty content
    bad_posts = c.execute(text('''
        SELECT COUNT(*) FROM posts
        WHERE content IS NULL OR TRIM(content) = ''
    ''')).scalar()
    print(f'  posts with empty content: {bad_posts}')

    # Articles with broken source_url (no http)
    bad_art = c.execute(text('''
        SELECT COUNT(*) FROM articles
        WHERE source_url IS NOT NULL AND TRIM(source_url) <> ''
          AND source_url NOT LIKE 'http%'
    ''')).scalar()
    print(f'  articles with source_url not starting with http: {bad_art}')

    # Resources with no URL at all
    bad_res = c.execute(text('''
        SELECT COUNT(*) FROM resources
        WHERE url IS NULL OR TRIM(url) = ''
    ''')).scalar()
    print(f'  resources with no URL: {bad_res}')

    # ---------- FOUNDERS — deeper ----------
    section('FOUNDERS — deeper')

    # location = city but employer is elsewhere (no easy automated fix; info only)
    bogus_title = c.execute(text('''
        SELECT COUNT(*) FROM "Founders"
        WHERE current_title IS NOT NULL
          AND LENGTH(current_title) > 120
    ''')).scalar()
    print(f'  founders with overly long current_title (>120ch): {bogus_title}')

    # literal "None" / "undefined" in free text
    weird = c.execute(text('''
        SELECT COUNT(*) FROM "Founders"
        WHERE LOWER(TRIM(current_employer)) IN ('none','null','undefined','n/a')
           OR LOWER(TRIM(location))         IN ('none','null','undefined','n/a')
    ''')).scalar()
    print(f'  founders with "None/Null/Undefined" in employer/location: {weird}')
