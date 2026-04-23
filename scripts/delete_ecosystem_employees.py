"""
Delete orphan 'founders' that are actually employees of ecosystem
organisations (incubators, clusters, universities, foreign employers),
not founders of Moroccan startups.

Criteria for deletion:
  • No StartupFounders link
  • AND current_employer matches a known ecosystem-org pattern
  • AND founder_id NOT in WHITELIST (actual founders we want to keep)

Usage:
    python scripts/delete_ecosystem_employees.py           # dry-run
    python scripts/delete_ecosystem_employees.py --apply
"""
import os, sys, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ['DATABASE_URL'] = (
    'postgresql://postgres.lianafeunaxlzqfvslob:'
    'Habiba456!!!!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'
)
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

# Case-insensitive substrings that identify ecosystem-org employers
ECOSYSTEM_PATTERNS = [
    'mcise',
    'réseau entreprendre', 'reseau entreprendre',
    'emerging business factory',
    'media digital invest', 'média digital invest',
    'r&d maroc', 'r & d maroc', 'r&d mraoc',
    'accelab',
    'hseven', 'h-seven', ' h7',
    'new work lab', 'net work marketing',
    'impact lab', 'impactlab',
    'cluster ',
    'bidaya',
    'lastartupfactory', 'la startup factory',
    'startup maroc',
    'ceed mo', 'ceed maroc',
    'cdg invest',
    'orange corners', 'orange fab',
    'génération entrepreneurs', 'generation entrepreneurs',
    'plug and play',
    'instiglio',
    'groupe iscae',
    'hec paris',
    'ebrd',
    'alx_africa', 'alx africa',
    'um6p', 'mohammed vi polytechnic', 'african academy',
    'entrepreneur academy',
    'lafactory',
    'mfounders',
    'incubooster',
    'meratus',
    ' rem',           # REM as a word (trailing word)
    'euromed innovation',
    'académie hassan', 'academie hassan',
    'skytrend',
    'ariej',
]

# Founders we want to KEEP (they're legit founders of actual startups)
KEEP_WHITELIST = {
    '42080',  # Ahmed Larouz     → Bridgizz (Amsterdam)
    '36990',  # Anas Khatim      → Skills & Smart groupe
    '17685',  # El-aichaoui Samir→ Happy Ventures
    '44072',  # Larbi Laraki     → Impact Lab Agency (Agency distinct from incubator)
    '73905',  # Mohamed Anmanari → DIGITAL STARTUP MAROC
    '64853',  # Olivier Tarbes   → Tractr
    '83409',  # Salma Kabbaj     → IMPACT Lab (co-founder of the org)
    '85355',  # Zineb RHARRASSE  → StartUp Maroc (co-founder of the org)
}

parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
MODE = 'APPLY' if args.apply else 'DRY-RUN'
print(f"=== DELETE ECOSYSTEM-ORG EMPLOYEES — {MODE} ===\n")

# Build the WHERE clause for pattern matching
conditions = " OR ".join(f"LOWER(f.current_employer) LIKE :p{i}" for i, _ in enumerate(ECOSYSTEM_PATTERNS))
params = {f'p{i}': f'%{p}%' for i, p in enumerate(ECOSYSTEM_PATTERNS)}

SQL = text(f'''
    SELECT f."Founder Id", f.name, f.current_employer, f.current_title
    FROM "Founders" f
    LEFT JOIN "StartupFounders" sf ON sf."Founder Id" = f."Founder Id"
    WHERE sf."Founder Id" IS NULL
      AND f.current_employer IS NOT NULL
      AND TRIM(f.current_employer) <> ''
      AND ({conditions})
    ORDER BY f.name
''')

with engine.connect() as conn:
    rows = conn.execute(SQL, params).fetchall()

to_delete = [r for r in rows if r[0] not in KEEP_WHITELIST]
kept      = [r for r in rows if r[0] in KEEP_WHITELIST]

print(f"Candidates matched by ecosystem patterns: {len(rows)}")
print(f"Kept (whitelist):                         {len(kept)}")
print(f"To delete:                                {len(to_delete)}\n")

if kept:
    print("--- KEPT (whitelist) ---")
    for r in kept:
        print(f"  {r[0]:<8} {r[1]!r:<30} emp={r[2]!r}")
    print()

print("--- TO DELETE ---")
for r in to_delete:
    print(f"  {r[0]:<8} {r[1]!r:<35} emp={r[2]!r}")

if not args.apply:
    print("\n(dry-run — no changes applied. Run with --apply to execute.)")
    sys.exit(0)

ids = [r[0] for r in to_delete]
with engine.begin() as tx:
    for tbl in ['StartupFounders', 'IncubatorFounders', 'Education', 'Experiences', 'Founders']:
        r = tx.execute(
            text(f'DELETE FROM "{tbl}" WHERE "Founder Id" = ANY(:ids)'),
            {'ids': ids}
        )
        print(f"  ✓ {r.rowcount} rows deleted from {tbl}")
