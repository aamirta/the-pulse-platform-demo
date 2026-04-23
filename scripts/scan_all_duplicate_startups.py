"""
Scan the whole Startups table for probable duplicate pairs.
Detection layers:
  (A) same normalized name (lowercase, stripped of punctuation / spaces)
  (B) same linkedin URL (case- / trailing-slash-insensitive)
  (C) same homepage_url (root domain, insensitive)
SELECT-only.
"""
import os, sys, re
from collections import defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ['DATABASE_URL'] = (
    'postgresql://postgres.lianafeunaxlzqfvslob:'
    'Habiba456!!!!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'
)
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])


def norm_name(s):
    if not s:
        return None
    # lowercase, drop legal suffixes, drop all non-alphanumerics
    s = s.lower()
    s = re.sub(r'\b(s\.?a\.?r\.?l\.?|sarl|sa|sas|ltd|inc|llc|s\.?a\.?|group|groupe)\b', ' ', s)
    s = re.sub(r'[^a-z0-9]', '', s)
    return s or None


def norm_li(url):
    if not url:
        return None
    u = url.lower().strip().rstrip('/')
    u = u.split('?')[0]
    # only keep the /company/slug part
    m = re.search(r'linkedin\.com/(company|school|showcase)/([a-z0-9\-_%\.]+)', u)
    if not m:
        return None
    return m.group(2)


def norm_host(url):
    if not url:
        return None
    u = url.lower().strip()
    m = re.search(r'https?://(?:www\.)?([a-z0-9\-\.]+)', u)
    return m.group(1) if m else None


with engine.connect() as c:
    rows = c.execute(text('''
        SELECT "Startup Id", "Startup name", linkedin, homepage_url,
               total_funding_usd, logo_url, description, sector
        FROM "Startups"
        WHERE "Startup name" IS NOT NULL AND TRIM("Startup name") <> ''
    ''')).fetchall()

print(f"Total startups: {len(rows)}\n")

by_name = defaultdict(list)
by_li = defaultdict(list)
by_host = defaultdict(list)

for r in rows:
    sid, name, li, hp, funding, logo, desc, sector = r
    n = norm_name(name)
    if n:
        by_name[n].append(r)
    l = norm_li(li)
    if l:
        by_li[l].append(r)
    h = norm_host(hp)
    if h:
        by_host[h].append(r)


def richness_score(r):
    """Higher = richer. Used to recommend which to keep."""
    sid, name, li, hp, funding, logo, desc, sector = r
    s = 0
    if funding: s += 20
    if li:      s += 6
    if hp:      s += 6
    if logo:    s += 4
    if desc and len(desc) > 80: s += 3
    if sector and ',' in sector: s += 2
    return s


def print_groups(groups, label):
    print(f"\n{'=' * 72}")
    print(f"{label}")
    print('=' * 72)
    dupes = {k: g for k, g in groups.items() if len({r[0] for r in g}) > 1}
    print(f"Groups with >1 id: {len(dupes)}")
    for k, g in sorted(dupes.items()):
        g = sorted({r[0]: r for r in g}.values(), key=richness_score, reverse=True)
        print(f"\n  key: {k!r}")
        for r in g:
            sid, name, li, hp, funding, logo, desc, sector = r
            fund_s = f"${int(funding):,}" if funding else '—'
            pic = 'pic' if logo else '---'
            lid = 'li ' if li else '---'
            hpd = 'web' if hp else '---'
            print(f"    id={sid:<5} score={richness_score(r):<3}  [{pic}|{lid}|{hpd}|{fund_s:<12}]  name={name!r}")

print_groups(by_name, 'BY NORMALIZED NAME (strip legal suffixes, punctuation)')
print_groups(by_li,   'BY LINKEDIN COMPANY SLUG')
print_groups(by_host, 'BY HOMEPAGE ROOT HOST')
