"""
Seed venture studios into the Investors directory.

The frontend's "Venture Studios & Builders" section reads the investor
directory (`GET /investors/?type=venture+studio`), which filters on
`PrimaryInvestorType`. An earlier version of this script seeded studios into
`pulse_members` with `role = 'venture_studio'` instead — a table that section
never reads — so the section rendered empty. Studios now go into `Investors`
with `PrimaryInvestorType = 'Venture Studio'`, which is what the filter matches.

Sources:
  - The Foundry (UM6P), 34Studio — curated, CEOs confirmed
  - Alfia — data/gitex_africa_2026_morocco_exhibitors.csv (GITEX Africa 2026)

Usage:
    python scripts/add_venture_studios.py            # dry-run
    python scripts/add_venture_studios.py --apply
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL environment variable is required")
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

# The value the API's ?type= filter matches on. Keep in sync with the frontend
# constant in new_design/src/hooks/useVentureStudios.ts.
VENTURE_STUDIO_TYPE = 'Venture Studio'

FOUNDRY = {
    'name':        'The Foundry',
    'email':       'Asmae.berrada@um6pfoundry.com',
    'domain':      'um6pfoundry.com',
    'linkedin':    'https://www.linkedin.com/company/the-foundry-ma/',
    'ceo':         'Asmae Berrada',
    'location':    'Benguerir, Morocco',
    'city':        'Benguerir',
    'focus':       'DeepTech, Research Spinoffs, Science',
    'description': (
        "The Foundry, le venture studio de l'UM6P, transforme la recherche "
        "scientifique en startups deeptech. Implanté à Benguerir, il accompagne "
        "les chercheurs et entrepreneurs dans la création, le financement et "
        "le scale-up d'entreprises issues du laboratoire."
    ),
}

STUDIO34 = {
    'name':        '34Studio',
    # Placeholder email — update once Amine's contact is confirmed.
    'email':       'contact@34stud.io',
    'domain':      '34stud.io',
    'linkedin':    'https://www.linkedin.com/company/34studio/',
    'ceo':         'Amine Jouahri',
    'location':    'Casablanca, Morocco',
    'city':        'Casablanca',
    'focus':       'Tech, SaaS, Go-to-Market',
    'description': (
        "34Studio est un venture studio basé au Maroc qui co-construit des "
        "startups tech avec des founders ambitieux : idéation, MVP, levée de "
        "fonds et go-to-market."
    ),
}

# From the GITEX Africa 2026 exhibitor list. That CSV carries no website,
# LinkedIn, or contact email for Alfia, so those stay NULL rather than guessed.
ALFIA = {
    'name':        'Alfia',
    'email':       None,
    'domain':      None,
    'linkedin':    None,
    'ceo':         None,
    'location':    'Oujda, Morocco',
    'city':        'Oujda',
    'focus':       'Platform Infrastructure, MENA Ecosystem',
    'description': (
        "ALFIA is a venture builder and platform infrastructure company serving "
        "the MENA startup ecosystem, headquartered in Oujda, Morocco with "
        "operations in Riyadh, KSA."
    ),
}

STUDIOS = [FOUNDRY, STUDIO34, ALFIA]


def upsert_studio(tx, s):
    """Insert or update an Investors row for one venture studio.

    Matched on investor name so re-running is idempotent: an existing row is
    retyped and refreshed rather than duplicated.
    """
    params = {
        'n':  s['name'],
        't':  VENTURE_STUDIO_TYPE,
        'loc': s['location'],
        'city': s['city'],
        'desc': s['description'],
        'focus': s['focus'],
        'dom': s['domain'],
        'li': s['linkedin'],
        'em': s['email'],
    }

    existing = tx.execute(
        text('SELECT "Investor Id" FROM "Investors" WHERE LOWER("Investor Name") = LOWER(:n)'),
        {'n': s['name']},
    ).fetchone()

    if existing:
        tx.execute(text("""
            UPDATE "Investors"
               SET "PrimaryInvestorType" = :t,
                   "HQLocation" = :loc,
                   city = :city,
                   "Description" = :desc,
                   "PreferredIndustry" = :focus,
                   domain = COALESCE(:dom, domain),
                   linkedin_url = COALESCE(:li, linkedin_url),
                   "HQEmail" = COALESCE(:em, "HQEmail")
             WHERE "Investor Id" = :i
        """), {**params, 'i': existing[0]})
        return f"updated id={existing[0]}"

    r = tx.execute(text("""
        INSERT INTO "Investors" ("Investor Name", "PrimaryInvestorType", "InvestorStatus",
                                 "HQLocation", city, region, "Country Code",
                                 "Description", "PreferredIndustry",
                                 domain, linkedin_url, "HQEmail")
        VALUES (:n, :t, 'En activité', :loc, :city, 'Morocco', 'MA',
                :desc, :focus, :dom, :li, :em)
        RETURNING "Investor Id"
    """), params)
    return f"inserted id={r.scalar()}"


parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
print(f"=== SEED VENTURE STUDIOS INTO Investors — {'APPLY' if args.apply else 'DRY-RUN'} ===\n")

for s in STUDIOS:
    print(f"-- {s['name']} (CEO: {s['ceo'] or 'unknown'}) --")
    print(f"  PrimaryInvestorType: {VENTURE_STUDIO_TYPE}")
    for k in ('location', 'focus', 'domain', 'linkedin', 'email'):
        print(f"  {k}: {s[k]}")
    print(f"  description: {s['description'][:80]}...")
    print()

if not args.apply:
    print("(dry-run — re-run with --apply to write)")
    sys.exit(0)

with engine.begin() as tx:
    for s in STUDIOS:
        print(f"  ✓ {s['name']}: {upsert_studio(tx, s)}")
