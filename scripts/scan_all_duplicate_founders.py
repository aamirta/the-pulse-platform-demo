"""
Find ALL duplicate Founder records across the DB.
Detection: same linkedin_url (case- and trailing-slash-insensitive).
Also tries exact normalized name as a fallback.
For each group, recommends which row to keep (richest score).
"""
import os, sys, re
from collections import defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL environment variable is required")
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])


def norm_li(url):
    if not url:
        return None
    u = url.lower().strip().rstrip('/').split('?')[0]
    m = re.search(r'linkedin\.com/in/([a-z0-9\-_%\.]+)', u)
    return m.group(1) if m else None


def norm_name(s):
    if not s:
        return None
    s = s.lower()
    s = re.sub(r'[^a-z0-9]', '', s)
    return s or None


def richness(r):
    """Higher = richer — used to pick which row to keep."""
    _, name, ct, loc, pic, emp, li = r
    s = 0
    if pic:  s += 15
    if ct:   s += 6
    if loc:  s += 5
    if emp:  s += 3
    if li:   s += 4
    # prefer shorter display names (usually the original 'Mehdi Alami' not 'Mehdi CHERIF ALAMI')
    if name: s += max(0, 6 - len(name.split()))
    return s


with engine.connect() as conn:
    rows = conn.execute(text('''
        SELECT "Founder Id", name, current_title, location,
               profile_pic IS NOT NULL AS has_pic,
               current_employer, linkedin_url
        FROM "Founders"
        WHERE name IS NOT NULL AND TRIM(name) <> ''
    ''')).fetchall()

print(f"Total founders: {len(rows)}\n")

by_li = defaultdict(list)
by_name = defaultdict(list)

for r in rows:
    li = norm_li(r[6])
    if li:
        by_li[li].append(r)
    nm = norm_name(r[1])
    if nm:
        by_name[nm].append(r)


def print_groups(groups, label):
    dupes = [(k, g) for k, g in groups.items() if len({r[0] for r in g}) > 1]
    print(f"\n{'=' * 72}")
    print(f"{label} — groups with >1 id: {len(dupes)}")
    print('=' * 72)
    for k, g in sorted(dupes):
        g_unique = list({r[0]: r for r in g}.values())
        g_sorted = sorted(g_unique, key=richness, reverse=True)
        print(f"\n  key: {k!r}")
        for i, r in enumerate(g_sorted):
            marker = 'KEEP' if i == 0 else 'del '
            print(f"    [{marker}] id={r[0]:<8} score={richness(r):<3} "
                  f"pic={'Y' if r[4] else '-'} "
                  f"name={r[1]!r:<40} title={r[2]!r}")


print_groups(by_li, 'BY LINKEDIN URL SLUG')
print_groups(by_name, 'BY NORMALIZED NAME')
