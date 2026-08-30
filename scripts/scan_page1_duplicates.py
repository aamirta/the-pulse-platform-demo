"""
Scan for duplicate founders among those visible on page 1 of the /founders
listing — i.e. the top 20 when sorted by startup funding DESC, name ASC.

Looks for:
  (a) same linkedin_url (case- and trailing-slash-insensitive)
  (b) same name (case-insensitive, trimmed)
  (c) different id pointing to same startup with overlapping first+last tokens

Also finds duplicate Startup records linked to these page-1 founders.

SELECT-only.
"""
import os, sys, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL environment variable is required")
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

# Mimic the /founders route ordering to grab the first 60 candidates
# (page size 20 × a bit of buffer to catch pair partners that may be on p.2)
PAGE1_SQL = text('''
WITH max_funding AS (
    SELECT sf."Founder Id" AS fid, MAX(s.total_funding_usd) AS mf
    FROM "StartupFounders" sf
    JOIN "Startups" s ON s."Startup Id" = sf."Startup Id"
    GROUP BY sf."Founder Id"
)
SELECT f."Founder Id", f.name, f.linkedin_url,
       COALESCE(mf.mf, 0) AS funding,
       array_agg(DISTINCT s."Startup name") FILTER (WHERE s."Startup name" IS NOT NULL) AS startups
FROM "Founders" f
LEFT JOIN max_funding mf ON mf.fid = f."Founder Id"
LEFT JOIN "StartupFounders" sf ON sf."Founder Id" = f."Founder Id"
LEFT JOIN "Startups" s ON s."Startup Id" = sf."Startup Id"
WHERE f.name IS NOT NULL AND f.name <> ''
  AND (f.current_title IS NOT NULL
       OR f.profile_pic IS NOT NULL
       OR f.location IS NOT NULL
       OR f.company_details_name IS NOT NULL
       OR f.linkedin_url IS NOT NULL)
GROUP BY f."Founder Id", f.name, f.linkedin_url, mf.mf
ORDER BY CASE WHEN mf.mf IS NOT NULL THEN 0 ELSE 1 END,
         mf.mf DESC NULLS LAST,
         f.name ASC
LIMIT 60
''')


def norm_name(s):
    s = (s or '').lower().strip()
    s = re.sub(r'[^\w\s]', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s


def norm_li(url):
    if not url:
        return None
    u = url.lower().strip().rstrip('/')
    # strip query
    u = u.split('?')[0]
    return u


def tokens(name):
    return set(norm_name(name).split())


with engine.connect() as conn:
    rows = conn.execute(PAGE1_SQL).fetchall()

print(f"Page-1 candidates scanned: {len(rows)}\n")

# Build lookup structures
by_li = {}
by_name = {}
by_tokens = []
for r in rows:
    fid, name, li, funding, startups = r
    li_n = norm_li(li)
    nm_n = norm_name(name)
    if li_n:
        by_li.setdefault(li_n, []).append(r)
    if nm_n:
        by_name.setdefault(nm_n, []).append(r)
    by_tokens.append((tokens(name), r))

print("=" * 60)
print("DUPLICATES BY LINKEDIN URL (case/trailing-slash insensitive)")
print("=" * 60)
for li_n, group in by_li.items():
    if len(group) > 1:
        print(f"\n  LinkedIn: {li_n}")
        for r in group:
            print(f"    id={r[0]}  name={r[1]!r}  startups={r[4]}")

print()
print("=" * 60)
print("DUPLICATES BY NORMALIZED NAME")
print("=" * 60)
for nm, group in by_name.items():
    if len(group) > 1:
        print(f"\n  name: {nm!r}")
        for r in group:
            print(f"    id={r[0]}  linkedin={r[2]}  startups={r[4]}")

print()
print("=" * 60)
print("POTENTIAL NEAR-MATCHES (shared ≥2 name tokens, different id)")
print("=" * 60)
seen_pairs = set()
for i, (tks_a, ra) in enumerate(by_tokens):
    for tks_b, rb in by_tokens[i + 1:]:
        if ra[0] == rb[0]:
            continue
        key = tuple(sorted([ra[0], rb[0]]))
        if key in seen_pairs:
            continue
        # skip if already flagged above
        if ra in by_li.get(norm_li(ra[2]), []) and rb in by_li.get(norm_li(ra[2]), []):
            continue
        if ra in by_name.get(norm_name(ra[1]), []) and rb in by_name.get(norm_name(ra[1]), []):
            continue
        common = tks_a & tks_b
        # Require 2 meaningful tokens (>= 3 chars, not generic)
        meaningful = {t for t in common if len(t) >= 3 and t not in {
            'the', 'and', 'des', 'les', 'une', 'mohamed', 'mohammed', 'ahmed', 'youssef'
        }}
        if len(meaningful) >= 2:
            seen_pairs.add(key)
            print(f"\n  shared tokens: {meaningful}")
            print(f"    id={ra[0]}  {ra[1]!r}  → {ra[4]}")
            print(f"    id={rb[0]}  {rb[1]!r}  → {rb[4]}")

# Now duplicate Startups among page-1 founder startups
print()
print("=" * 60)
print("DUPLICATE STARTUPS linked to page-1 founders")
print("=" * 60)
startup_ids = set()
for r in rows:
    for sn in (r[4] or []):
        pass  # already have names

# Get full (name, id) pairs for these founders
startup_info = conn.execute(text('''
    SELECT s."Startup Id", s."Startup name"
    FROM "Startups" s
    JOIN "StartupFounders" sf ON sf."Startup Id" = s."Startup Id"
    WHERE sf."Founder Id" = ANY(:ids)
'''), {'ids': [r[0] for r in rows]}).fetchall()

by_snorm = {}
for sid, sn in startup_info:
    k = re.sub(r'[^a-z0-9]', '', (sn or '').lower())
    if k:
        by_snorm.setdefault(k, set()).add((sid, sn))
for k, vs in by_snorm.items():
    if len({sid for sid, _ in vs}) > 1:
        print(f"\n  normalized: {k!r}")
        for sid, sn in sorted(vs):
            print(f"    id={sid}  name={sn!r}")
