"""
Final cleanup pass:

  1. Merge the 4 rebrand startup pairs (pick the richer side; rename/update
     description where the brand has shifted).
  2. Delete 7 non-Moroccan founders wrongly attached to Moroccan startups
     by the discovery agent.
  3. Hygiene: trim + collapse whitespace in founder name fields.
  4. Hygiene: normalize trailing/leading whitespace on sector tokens.

Usage:
    python scripts/final_cleanup.py           # dry-run
    python scripts/final_cleanup.py --apply
"""
import os, sys, argparse, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL environment variable is required")
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

# Non-Moroccan founders wrongly attached by the discovery agent
SUSPICIOUS_FOUNDER_IDS = [
    '100269',  # Suchana Seth          → ailab    (Indian AI researcher, not MA)
    '100271',  # Gay Gaddis            → AMEE     (US founder of T3)
    '100272',  # Zankruti Raj Gaglani  → AMEE     (Indian name)
    '100273',  # Ajit Anand            → aptus software (Indian)
    '100281',  # Nathan Sudds          → Activelabs
    '100284',  # Daniel Hu             → aicademy (asian, unverifiable)
    '100286',  # Sheikha Reem Amjad Masad → Alif Invest (Jordanian Replit family)
]

# Rebrand startup merges
STARTUP_MERGES = [
    (89,  1070, 'allo garant ← To the Garant',      None),
    (62,   294, 'brostech ← hoota.ma  [rename+desc]', 'hoota'),
    (210,  217, 'alya pay ← alya',                   None),
    (509,  815, 'kwiks ← kwirks frc',                None),
]

# Special post-merge update for case 'hoota' — rename 62 and adopt hoota's description
POST_HOOTA = dict(
    id=62,
    new_name='hoota.ma',
    new_description_source_id=294,  # but 294 is gone after merge, so we snapshot first
)

BACKFILL_FIELDS = [
    ('CompanyLegalName', '"CompanyLegalName"'),
    ('numeroRC',         '"numeroRC"'),
    ('numeroICE',        '"numeroICE"'),
]

parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
MODE = 'APPLY' if args.apply else 'DRY-RUN'
print(f"=== FINAL CLEANUP — {MODE} ===\n")


def do_startup_merge(tx, keep_id, del_id):
    # backfill
    select_cols = ', '.join(col for _, col in BACKFILL_FIELDS)
    kr = tx.execute(text(f'SELECT {select_cols} FROM "Startups" WHERE "Startup Id" = :k'),
                    {'k': keep_id}).fetchone()
    dr = tx.execute(text(f'SELECT {select_cols} FROM "Startups" WHERE "Startup Id" = :d'),
                    {'d': del_id}).fetchone()
    if kr and dr:
        sets, params = [], {'k': keep_id}
        for i, (fname, col) in enumerate(BACKFILL_FIELDS):
            kv, dv = kr[i], dr[i]
            ke = (kv is None) or (isinstance(kv, str) and not kv.strip())
            dv_ok = (dv is not None) and not (isinstance(dv, str) and not dv.strip())
            if ke and dv_ok:
                sets.append(f"{col} = :v_{i}")
                params[f'v_{i}'] = dv
        if sets:
            tx.execute(text(f'UPDATE "Startups" SET {", ".join(sets)} WHERE "Startup Id" = :k'),
                       params)
    # StartupFounders
    tx.execute(text('''
        INSERT INTO "StartupFounders" ("Startup Id", "Founder Id")
        SELECT :k, sf."Founder Id" FROM "StartupFounders" sf
        WHERE sf."Startup Id" = :d
          AND NOT EXISTS (SELECT 1 FROM "StartupFounders" sk
                          WHERE sk."Startup Id" = :k
                            AND sk."Founder Id" = sf."Founder Id")
    '''), {'k': keep_id, 'd': del_id})
    tx.execute(text('DELETE FROM "StartupFounders" WHERE "Startup Id" = :d'), {'d': del_id})
    # FundingRounds
    tx.execute(text('UPDATE "FundingRounds" SET "Startup Id" = :k WHERE "Startup Id" = :d'),
               {'k': keep_id, 'd': del_id})
    # StartupIncubators
    tx.execute(text('''
        INSERT INTO "StartupIncubators" ("Startup Id", "Incubator Id")
        SELECT :k, si."Incubator Id" FROM "StartupIncubators" si
        WHERE si."Startup Id" = :d
          AND NOT EXISTS (SELECT 1 FROM "StartupIncubators" sk
                          WHERE sk."Startup Id" = :k
                            AND sk."Incubator Id" = si."Incubator Id")
    '''), {'k': keep_id, 'd': del_id})
    tx.execute(text('DELETE FROM "StartupIncubators" WHERE "Startup Id" = :d'), {'d': del_id})
    tx.execute(text('DELETE FROM "Startups" WHERE "Startup Id" = :d'), {'d': del_id})


def do_delete_founder(tx, fid):
    tx.execute(text('DELETE FROM "StartupFounders"   WHERE "Founder Id" = :i'), {'i': fid})
    tx.execute(text('DELETE FROM "IncubatorFounders" WHERE "Founder Id" = :i'), {'i': fid})
    tx.execute(text('DELETE FROM "Education"         WHERE "Founder Id" = :i'), {'i': fid})
    tx.execute(text('DELETE FROM "Experiences"       WHERE "Founder Id" = :i'), {'i': fid})
    tx.execute(text('DELETE FROM "Founders"          WHERE "Founder Id" = :i'), {'i': fid})


# ----- PREVIEW ----------------------------------------------------------
with engine.connect() as conn:
    print("1) Rebrand startup merges:")
    for k, d, label, _ in STARTUP_MERGES:
        print(f"  {label}  (keep {k}, del {d})")

    print("\n2) Suspicious non-Moroccan founders to delete:")
    rows = conn.execute(text('''
        SELECT f."Founder Id", f.name, s."Startup name"
        FROM "Founders" f
        LEFT JOIN "StartupFounders" sf ON sf."Founder Id" = f."Founder Id"
        LEFT JOIN "Startups" s ON s."Startup Id" = sf."Startup Id"
        WHERE f."Founder Id" = ANY(:ids)
        ORDER BY f."Founder Id"
    '''), {'ids': SUSPICIOUS_FOUNDER_IDS}).fetchall()
    for r in rows:
        print(f"  {r[0]:<8} {r[1]!r:<32} → {r[2]}")

    print("\n3) Founder names with whitespace to tidy:")
    ws = conn.execute(text('''
        SELECT COUNT(*) FROM "Founders"
        WHERE name IS NOT NULL
          AND (name <> TRIM(name)
               OR name ~ '\\s{2,}'
               OR first_name <> TRIM(COALESCE(first_name,''))
               OR last_name  <> TRIM(COALESCE(last_name,'')))
    ''')).scalar()
    print(f"  rows with leading/trailing or double spaces in name fields: {ws}")

    print("\n4) Sector tokens with leading/trailing whitespace:")
    sc = conn.execute(text('''
        SELECT COUNT(*) FROM "Startups"
        WHERE sector IS NOT NULL
          AND (sector LIKE ' %'
            OR sector LIKE '% '
            OR sector LIKE '%,  %'
            OR sector LIKE '%  ,%'
            OR sector LIKE '% ,%'
            OR sector ~ ',\\s{2,}')
    ''')).scalar()
    print(f"  rows with suspicious sector formatting: {sc}")

if not args.apply:
    print("\n(dry-run — no changes applied. Run with --apply to execute.)")
    sys.exit(0)

# ----- APPLY ------------------------------------------------------------
# 1. Snapshot hoota's description before merging
with engine.connect() as conn:
    hoota_desc = conn.execute(
        text('SELECT description FROM "Startups" WHERE "Startup Id" = :i'), {'i': 294}
    ).scalar()

# 2. Rebrand merges
for k, d, label, mark in STARTUP_MERGES:
    with engine.begin() as tx:
        do_startup_merge(tx, k, d)
    print(f"  ✓ merged {label}")

# 3. Special post-update for hoota: rename + adopt hoota's description
if hoota_desc:
    with engine.begin() as tx:
        tx.execute(
            text('UPDATE "Startups" SET "Startup name" = :n, description = :d WHERE "Startup Id" = :i'),
            {'n': 'hoota.ma', 'd': hoota_desc, 'i': 62}
        )
    print(f"  ✓ renamed 62 to 'hoota.ma' + adopted description")

# 4. Delete suspicious founders
for fid in SUSPICIOUS_FOUNDER_IDS:
    with engine.begin() as tx:
        do_delete_founder(tx, fid)
print(f"  ✓ deleted {len(SUSPICIOUS_FOUNDER_IDS)} suspicious founders")

# 5. Hygiene: trim whitespace in founder name/first_name/last_name
with engine.begin() as tx:
    r1 = tx.execute(text('''
        UPDATE "Founders"
           SET name       = REGEXP_REPLACE(TRIM(name),       '\\s+', ' ', 'g'),
               first_name = REGEXP_REPLACE(TRIM(first_name), '\\s+', ' ', 'g'),
               last_name  = REGEXP_REPLACE(TRIM(last_name),  '\\s+', ' ', 'g')
         WHERE name       IS NOT NULL AND (name       <> TRIM(name)       OR name       ~ '\\s{2,}')
            OR first_name IS NOT NULL AND (first_name <> TRIM(first_name) OR first_name ~ '\\s{2,}')
            OR last_name  IS NOT NULL AND (last_name  <> TRIM(last_name)  OR last_name  ~ '\\s{2,}')
    '''))
    print(f"  ✓ hygiene: tidied {r1.rowcount} founder name rows")

# 6. Hygiene: normalize sector tokens
with engine.begin() as tx:
    # For each row, split sector on ',', trim each, drop empties, join with ', '
    # PostgreSQL array_to_string(array_agg(...))
    r2 = tx.execute(text('''
        UPDATE "Startups" s
           SET sector = norm.new_sector
          FROM (
            SELECT "Startup Id" AS sid,
                   (SELECT string_agg(trim(tok), ', ')
                      FROM unnest(string_to_array(sector, ',')) AS tok
                     WHERE trim(tok) <> ''
                   ) AS new_sector
              FROM "Startups"
             WHERE sector IS NOT NULL AND TRIM(sector) <> ''
          ) norm
         WHERE s."Startup Id" = norm.sid
           AND s.sector <> norm.new_sector
    '''))
    print(f"  ✓ hygiene: normalized sector on {r2.rowcount} startups")
