"""
Compare duplicate Startup records side by side so we can pick
which to keep before merging.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL environment variable is required")
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

PAIRS = [
    (565, 1220, 'YoLa Fresh'),
    (103, 1276, 'Freterium'),
    (299, 476,  'kifal'),
]

FIELDS = [
    ('Startup Id',     '"Startup Id"'),
    ('Startup name',   '"Startup name"'),
    ('sector',         'sector'),
    ('location',       'location'),
    ('region',         'region'),
    ('linkedin',       'linkedin'),
    ('homepage_url',   'homepage_url'),
    ('entreprise_contact_site_web', '"EntrepriseContactSiteWeb"'),
    ('logo_url',       'logo_url'),
    ('description',    'description'),
    ('total_funding_usd', 'total_funding_usd'),
    ('year_founded',   '"YearFounded"'),
    ('numeroRC',       '"numeroRC"'),
    ('numeroICE',      '"numeroICE"'),
]
select_cols = ', '.join(col for _, col in FIELDS)

with engine.connect() as c:
    for a, b, label in PAIRS:
        print(f"\n========== {label}  —  {a} vs {b} ==========")
        rows = c.execute(text(
            f'SELECT {select_cols} FROM "Startups" WHERE "Startup Id" IN ({a},{b}) ORDER BY "Startup Id"'
        )).fetchall()
        data = {r[0]: r for r in rows}

        for fname, _ in FIELDS:
            i = [f for f, _ in FIELDS].index(fname)
            va = (data.get(a) or (None,)*len(FIELDS))[i]
            vb = (data.get(b) or (None,)*len(FIELDS))[i]
            va_s = str(va)[:45] if va is not None else '—'
            vb_s = str(vb)[:45] if vb is not None else '—'
            print(f"  {fname:<28}  A={va_s:<48}  B={vb_s}")

        # Count related rows on each side
        for table, col in [
            ('StartupFounders', '"Startup Id"'),
            ('FundingRounds',   '"Startup Id"'),
            ('StartupIncubators', '"Startup Id"'),
        ]:
            ra = c.execute(text(f'SELECT COUNT(*) FROM "{table}" WHERE {col} = :x'), {'x': a}).scalar()
            rb = c.execute(text(f'SELECT COUNT(*) FROM "{table}" WHERE {col} = :x'), {'x': b}).scalar()
            print(f"  rel: {table:<22}  A={ra}   B={rb}")
