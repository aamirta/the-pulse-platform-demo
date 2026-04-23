"""
Auto-merge duplicate founders that share the same LinkedIn /in/ slug.

For each LinkedIn-slug group with >1 founder id:
  1. Compute phonetic similarity between the names.
  2. If names are compatible (likely same person): keep the richer row,
     merge StartupFounders links, delete the duplicate.
  3. If names diverge (likely bad LinkedIn association): skip + flag.

Optional cleanup: rename a few known mangled kept-rows (Sali Ma → Salima HDA, etc.)

Usage:
    python scripts/merge_all_founders_auto.py            # dry-run
    python scripts/merge_all_founders_auto.py --apply
"""
import os, sys, re, argparse
from collections import defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ['DATABASE_URL'] = (
    'postgresql://postgres.lianafeunaxlzqfvslob:'
    'Habiba456!!!!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'
)
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])


# ----- Utilities --------------------------------------------------------
def norm_li(url):
    if not url:
        return None
    u = url.lower().strip().rstrip('/').split('?')[0]
    m = re.search(r'linkedin\.com/in/([a-z0-9\-_%\.]+)', u)
    return m.group(1) if m else None


NAME_NOISE = {
    'el', 'al', 'le', 'la', 'de', 'du', 'the', 'and', 'co', 'founder', 'fondateur',
    'ait', 'ben', 'bin',  # Moroccan name particles (optional in slugs)
    # NOTE: 'aziz' is a real given name — NEVER add it here.
}


def name_tokens(name):
    if not name:
        return set()
    # strip emoji / non-latin
    s = re.sub(r'[^\w\s\-]', ' ', name.lower(), flags=re.UNICODE)
    # drop diacritics
    s = s.replace('é', 'e').replace('è', 'e').replace('ê', 'e').replace('â', 'a') \
         .replace('ç', 'c').replace('ô', 'o').replace('î', 'i').replace('ï', 'i')
    return {t for t in re.split(r'[\s\-_]+', s) if t and t not in NAME_NOISE and len(t) >= 2}


def compact(s):
    """Lowercased, letter-only, no whitespace — e.g. 'Sali Ma' → 'salima'."""
    return re.sub(r'[^a-z]', '', (s or '').lower())


def names_compatible(a, b):
    """True if the two names likely refer to the same person."""
    ta, tb = name_tokens(a), name_tokens(b)
    if ta and tb:
        if ta & tb:               return True
        if ta <= tb or tb <= ta:  return True
    # Fallback: compact-substring (handles 'Sali Ma' vs 'Salima HDA',
    # 'Aziz Elyaagoubi' vs 'Aziz EL YAAGOUBI', etc.)
    ca, cb = compact(a), compact(b)
    if ca and cb and (ca in cb or cb in ca):
        return True
    return False


def richness(r):
    _, name, ct, loc, pic, emp, li = r
    s = 0
    if pic:  s += 15
    if ct:   s += 6
    if loc:  s += 5
    if emp:  s += 3
    if li:   s += 4
    # prefer shorter display names
    if name: s += max(0, 6 - len(name.split()))
    return s


# Known mangled kept-row names — rewrite after merge
NAME_FIX = {
    38463: 'Salima HDA',            # was 'Sali Ma'
    85076: 'Mohamed Khachani',       # was 'M Khachani'
    68683: 'Diego Ganeo',            # strip Chinese 迭戈 prefix
    42886: 'Aya Bakahoui',           # strip emoji
    57466: 'Fatine Wahid',           # was 'Wahid F.' — full legal per del row 'WAHID Fatine'
}


parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
MODE = 'APPLY' if args.apply else 'DRY-RUN'
print(f"=== MERGE ALL FOUNDERS (via LinkedIn slug) — {MODE} ===\n")


with engine.connect() as conn:
    rows = conn.execute(text('''
        SELECT "Founder Id", name, current_title, location,
               profile_pic IS NOT NULL AS has_pic,
               current_employer, linkedin_url
        FROM "Founders"
        WHERE name IS NOT NULL AND TRIM(name) <> ''
          AND linkedin_url IS NOT NULL AND TRIM(linkedin_url) <> ''
    ''')).fetchall()

groups = defaultdict(list)
for r in rows:
    slug = norm_li(r[6])
    if slug:
        groups[slug].append(r)

# Fallback: also group by normalized name when no LinkedIn or when the
# founder lacks a shared slug. This catches duplicates that don't share
# a LinkedIn URL but have the same display name.
name_rows = [r for r in rows]  # already filtered on name above? no, include no-linkedin too
from collections import defaultdict as _dd
# Re-query — include founders without linkedin, too
with engine.connect() as conn2:
    all_rows = conn2.execute(text('''
        SELECT "Founder Id", name, current_title, location,
               profile_pic IS NOT NULL AS has_pic,
               current_employer, linkedin_url
        FROM "Founders"
        WHERE name IS NOT NULL AND TRIM(name) <> ''
    ''')).fetchall()

name_groups = _dd(list)
for r in all_rows:
    nm = re.sub(r'[^a-z0-9]', '', (r[1] or '').lower())
    if nm and len(nm) >= 6:
        name_groups[f"name:{nm}"].append(r)

# Merge name_groups into groups only where each row isn't already part of a
# LinkedIn-based group pair.
already_in_li_group_ids = {r[0] for g in groups.values() if len({x[0] for x in g}) > 1 for r in g}
for k, g in name_groups.items():
    ids = {r[0] for r in g}
    if len(ids) > 1 and not (ids & already_in_li_group_ids):
        groups[k] = g

auto_merges = []   # list of (keep_id, del_id, slug, keep_name, del_name)
flagged   = []     # pairs where names don't match

for slug, g in groups.items():
    ids = {r[0] for r in g}
    if len(ids) < 2:
        continue
    g_unique = list({r[0]: r for r in g}.values())
    g_sorted = sorted(g_unique, key=richness, reverse=True)
    keep = g_sorted[0]
    for other in g_sorted[1:]:
        if names_compatible(keep[1], other[1]):
            auto_merges.append((keep[0], other[0], slug, keep[1], other[1]))
        else:
            flagged.append((keep[0], other[0], slug, keep[1], other[1]))

print(f"LinkedIn slug groups with >1 founder: {sum(1 for g in groups.values() if len({r[0] for r in g}) > 1)}")
print(f"Auto-mergeable pairs (names compatible): {len(auto_merges)}")
print(f"Flagged pairs (names diverge — MANUAL REVIEW):  {len(flagged)}\n")

if flagged:
    print("--- FLAGGED for manual review ---")
    for keep_id, del_id, slug, kn, dn in flagged:
        print(f"  slug={slug}")
        print(f"    keep {keep_id:<8} {kn!r}")
        print(f"    del? {del_id:<8} {dn!r}")
    print()

print("--- Auto-merge plan ---")
for keep_id, del_id, slug, kn, dn in auto_merges[:50]:
    print(f"  keep {keep_id:<8} {kn!r:<38} ← del {del_id:<8} {dn!r}")
if len(auto_merges) > 50:
    print(f"  … and {len(auto_merges) - 50} more")

if NAME_FIX:
    print("\n--- Name fixes (kept rows with mangled display names) ---")
    for fid, new in NAME_FIX.items():
        print(f"  id={fid} → {new!r}")

if not args.apply:
    print("\n(dry-run — no changes applied. Run with --apply to execute.)")
    sys.exit(0)

# ---- Apply merges ------------------------------------------------------
print("\nApplying…")
success = 0
for keep_id, del_id, slug, kn, dn in auto_merges:
    with engine.begin() as tx:
        # 1) StartupFounders — transfer missing, then drop remainder
        tx.execute(text('''
            INSERT INTO "StartupFounders" ("Startup Id", "Founder Id")
            SELECT sf."Startup Id", :k FROM "StartupFounders" sf
            WHERE sf."Founder Id" = :d
              AND NOT EXISTS (SELECT 1 FROM "StartupFounders" sk
                              WHERE sk."Founder Id" = :k
                                AND sk."Startup Id" = sf."Startup Id")
        '''), {'k': keep_id, 'd': del_id})
        tx.execute(text('DELETE FROM "StartupFounders" WHERE "Founder Id" = :d'), {'d': del_id})

        # 2) IncubatorFounders — same pattern
        tx.execute(text('''
            INSERT INTO "IncubatorFounders" ("Incubator Id", "Founder Id")
            SELECT i."Incubator Id", :k FROM "IncubatorFounders" i
            WHERE i."Founder Id" = :d
              AND NOT EXISTS (SELECT 1 FROM "IncubatorFounders" ik
                              WHERE ik."Founder Id" = :k
                                AND ik."Incubator Id" = i."Incubator Id")
        '''), {'k': keep_id, 'd': del_id})
        tx.execute(text('DELETE FROM "IncubatorFounders" WHERE "Founder Id" = :d'), {'d': del_id})

        # 3) Education / Experience — repoint founder_id
        tx.execute(text('UPDATE "Education"   SET "Founder Id" = :k WHERE "Founder Id" = :d'),
                   {'k': keep_id, 'd': del_id})
        tx.execute(text('UPDATE "Experiences" SET "Founder Id" = :k WHERE "Founder Id" = :d'),
                   {'k': keep_id, 'd': del_id})

        # 4) Finally delete the duplicate founder
        tx.execute(text('DELETE FROM "Founders" WHERE "Founder Id" = :d'), {'d': del_id})
    success += 1

print(f"  ✓ merged {success} founder pairs")

# Name fixes
if NAME_FIX:
    with engine.begin() as tx:
        for fid, new in NAME_FIX.items():
            tx.execute(text('UPDATE "Founders" SET name = :n WHERE "Founder Id" = :i'),
                       {'n': new, 'i': str(fid)})
    print(f"  ✓ renamed {len(NAME_FIX)} mangled display names")
