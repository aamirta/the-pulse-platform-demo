"""
Normalize location + region fields on Startups.

Morocco redrew its administrative map in 2015: 16 regions → 12. The DB
has a mix of old and new names. Plus various typos and encoding glitches.

This pass:
  1. Collapses all variants of city names (CASABLANCA → Casablanca, etc.)
  2. Maps old regions to the 12 current ones.

Usage:
    python scripts/normalize_locations.py           # dry-run
    python scripts/normalize_locations.py --apply
"""
import os, sys, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL environment variable is required")
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])


# City-name canonical mapping (case-insensitive lookup → Canonical)
CITY_MAP = {
    # Canonical French/Moroccan spelling
    'casablanca':    'Casablanca',
    'rabat':         'Rabat',
    'marrakech':     'Marrakech',
    'marrakesh':     'Marrakech',
    'tanger':        'Tanger',
    'tangier':       'Tanger',
    'tanger-assilah':'Tanger',
    'fes':           'Fès',
    'fès':           'Fès',
    'meknes':        'Meknès',
    'meknès':        'Meknès',
    'agadir':        'Agadir',
    'kenitra':       'Kénitra',
    'kénitra':       'Kénitra',
    'safi':          'Safi',
    'essaouira':     'Essaouira',
    'mohammedia':    'Mohammedia',
    'khouribga':     'Khouribga',
    'temara':        'Témara',
    'témara':        'Témara',
    'nador':         'Nador',
    'ben guerir':    'Ben Guérir',
    'settat':        'Settat',
    'tetouan':       'Tétouan',
    'tétouan':       'Tétouan',
}

# Morocco's 12 current regions (post-2015)
REGION_MAP = {
    # Casablanca-Settat
    'casablanca-settat': 'Casablanca-Settat',
    'grand casablanca':  'Casablanca-Settat',
    'casablanca settat': 'Casablanca-Settat',
    'doukkala-abda':     'Casablanca-Settat',  # old — actually split between C-S and M-S
    # Rabat-Salé-Kénitra
    'rabat-salé-kénitra':      'Rabat-Salé-Kénitra',
    'rabat-sale-kenitra':      'Rabat-Salé-Kénitra',
    'rabat sale kenitra':      'Rabat-Salé-Kénitra',
    'rabat-sale-zemmour-zaer': 'Rabat-Salé-Kénitra',
    'gharb-chrarda-beni hssen':'Rabat-Salé-Kénitra',  # old, merged in
    # Marrakech-Safi
    'marrakech-safi':             'Marrakech-Safi',
    'marrakech -safi':            'Marrakech-Safi',
    'marrakesh-safi':             'Marrakech-Safi',
    'marrakech-tensift-al haouz': 'Marrakech-Safi',
    # Tanger-Tétouan-Al Hoceïma
    'tanger-tétouan-al hoceïma': 'Tanger-Tétouan-Al Hoceïma',
    'tanger-tetouan-al hoceima': 'Tanger-Tétouan-Al Hoceïma',
    'tanger-tetouan':            'Tanger-Tétouan-Al Hoceïma',
    # Fès-Meknès
    'fès-meknès':         'Fès-Meknès',
    'fes-meknes':         'Fès-Meknès',
    'meknes-tafilalet':   'Fès-Meknès',       # split, mostly here
    'fes-boulemane':      'Fès-Meknès',
    # Souss-Massa
    'souss-massa':       'Souss-Massa',
    'souss-massa-dr,a':  'Souss-Massa',       # encoding glitch
    'souss-massa-draa':  'Souss-Massa',
    # Béni Mellal-Khénifra
    'béni mellal-khénifra': 'Béni Mellal-Khénifra',
    'beni mellal-khenifra': 'Béni Mellal-Khénifra',
    # Drâa-Tafilalet
    'drâa-tafilalet':    'Drâa-Tafilalet',
    'draa-tafilalet':    'Drâa-Tafilalet',
    # Oriental
    'oriental':          'Oriental',
    'region oriental':   'Oriental',
    # South regions
    'laâyoune-sakia el hamra': 'Laâyoune-Sakia El Hamra',
    'laayoune-sakia el hamra': 'Laâyoune-Sakia El Hamra',
    'dakhla-oued ed-dahab':    'Dakhla-Oued Ed-Dahab',
    'guelmim-oued noun':       'Guelmim-Oued Noun',
}


def plan_updates(conn):
    """Return two lists of (id, old_value, new_value) tuples."""
    city_updates = []
    rows = conn.execute(text('''
        SELECT "Startup Id", location FROM "Startups"
        WHERE location IS NOT NULL AND TRIM(location) <> ''
    ''')).fetchall()
    for sid, loc in rows:
        key = loc.strip().lower()
        if key in CITY_MAP and CITY_MAP[key] != loc:
            city_updates.append((sid, loc, CITY_MAP[key]))

    region_updates = []
    rows = conn.execute(text('''
        SELECT "Startup Id", region FROM "Startups"
        WHERE region IS NOT NULL AND TRIM(region) <> ''
    ''')).fetchall()
    for sid, reg in rows:
        key = reg.strip().lower()
        if key in REGION_MAP and REGION_MAP[key] != reg:
            region_updates.append((sid, reg, REGION_MAP[key]))

    return city_updates, region_updates


parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
MODE = 'APPLY' if args.apply else 'DRY-RUN'
print(f"=== NORMALIZE LOCATIONS — {MODE} ===\n")

with engine.connect() as conn:
    city_ups, region_ups = plan_updates(conn)

# Aggregate for a compact preview
from collections import Counter
city_ch = Counter((o, n) for _, o, n in city_ups)
region_ch = Counter((o, n) for _, o, n in region_ups)

print(f"City updates: {len(city_ups)}")
for (o, n), c in city_ch.most_common():
    print(f"  {c:<4}  {o!r}  →  {n!r}")

print(f"\nRegion updates: {len(region_ups)}")
for (o, n), c in region_ch.most_common():
    print(f"  {c:<4}  {o!r}  →  {n!r}")

if not args.apply:
    print("\n(dry-run — no changes applied.)")
    sys.exit(0)

with engine.begin() as tx:
    for sid, _, new in city_ups:
        tx.execute(text('UPDATE "Startups" SET location = :v WHERE "Startup Id" = :s'),
                   {'v': new, 's': sid})
    for sid, _, new in region_ups:
        tx.execute(text('UPDATE "Startups" SET region = :v WHERE "Startup Id" = :s'),
                   {'v': new, 's': sid})
print(f"\n✓ Updated {len(city_ups)} cities and {len(region_ups)} regions.")
