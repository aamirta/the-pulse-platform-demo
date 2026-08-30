"""
Merge duplicate Startup records.

For each (keep_id, delete_id) pair:
  1. Transfer StartupFounders rows (insert missing, delete rest for del).
  2. Re-point FundingRounds.startup_id to keep_id.
  3. Transfer StartupIncubators (insert missing, delete rest).
  4. Optionally enrich keep row with a handful of fields from delete
     (currently: company_legal_name, numeroRC, numeroICE — only if keep's
     version is NULL/empty).
  5. Delete the duplicate Startup row.

Usage:
    python scripts/merge_duplicate_startups.py           # dry-run
    python scripts/merge_duplicate_startups.py --apply   # execute
"""
import os, sys, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL environment variable is required")
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

# (keep_id, delete_id, label)
MERGES = [
    # Already applied — kept for audit trail:
    # (565, 1220, 'YoLa Fresh ← YolaFresh'),
    # (103, 1276, 'Freterium ← Freterium SARL'),
    # (299, 476,  'kifal auto ← kifal services [+ backfill RC/ICE]'),

    # === Rich vs SARL-twin / name variant — picked the richer side ===
    (506,  1107, 'Inyad ← Inyad'),
    (801,  1747, 'ipdis sarl ← IP DIS'),
    (430,  1547, 'kenjanoishi ← KENJANOISHI SARL'),
    (807,  1502, "kenz'up ← Kenzup"),
    (141,  1764, 'la startup station ← LaStartupStation'),
    (459,   941, 'lnko ← lnko sarl'),
    (1176, 1404, 'Magna Worldwide SARL ← Magna Worldwide'),
    (328,  1237, 'minthr ← Mint HR'),
    (413,   909, 'mymarket.ma ← mymarket.ma sarl'),
    (90,   1273, 'nextwi ← NEXTWI SARL'),
    (446,    15, 'nowedge ← nowedge sarl'),
    (969,  1188, 'pcs agri. ← PCS AGRI'),
    (538,   143, 'positeams ← positeams sarl'),
    (279,  1199, 'sandtogreen ← Sand to Green'),
    (1235, 1393, 'snazzy marketplace ← SNAZZY Market place'),
    (866,  1420, 'sowit ← SOWIT GROUP'),
    (1095, 2002, 'Spore.bio ← Spore Bio'),
    (179,  1439, 'ta7alil2.0 ← TA7ALIL 2.0'),
    (147,  1361, 'tec forge sarl ← TEC FORGE'),
    (879,   920, 'velo volt sarl ← velo volt'),
    (2019, 1223, 'Virtual Building Solution ← Virtual Building Solution SA'),
    (246,  1219, 'vitalscan ← Vital Scan'),
    (139,  1921, 'wash-minute ← Washminute'),
    (567,  1294, 'weego mobility lab ← WEEGOMOBILITYLAB'),
    (408,   455, 'ostadi.ma ← ostadi ma'),

    # === Triples — two deletes each (chain) ===
    (361,  2003, "l'workshop ← L'Workshop"),
    (361,   699, "l'workshop ← l'workshop (3rd)"),
    (220,  1998, 'OMNIDOC SANTÉ ← (proper casing)  [+ fix encoding]'),
    (220,  1833, 'OMNIDOC SANTÉ ← Omnidoc Sant (truncated)'),

    # === Shared LinkedIn slug ===
    (330,  1310, 'ailab ← AI LAB'),
    (233,  1633, 'betterfly ← Betterfly solutions'),
    (291,   443, 'dr stone.ma ← dr stone'),
    (127,  1488, 'defendis ← Defendis (SARL)'),
    (473,   510, 'aiox_labs ← aiox labs'),
    (1075,  274, 'Jobop ← jobop.co'),
    (461,   395, 'mastery ← mastery gps'),
    (300,  2017, 'Mubawab ← Mubawab.ma'),
    (106,   399, 'pip pip yalah ← … covoiturage maroc'),
    (560,  2006, 'wafr ← WafR (Mobile Payment System)'),
]

# Encoding-broken names that need to be rewritten AFTER merge:
# keep_id → corrected name
NAME_FIX = {
    230:  "\u200bProCrèche",       # was "procrã¨che"
    40:   "\u200bSixièmeHomme",     # was "sixiã¨mehomme"
    220:  "OMNIDOC SANTÉ",           # was "omnidoc santã‰"
}

# Also merge the encoding-fix pairs:
MERGES.append((230, 1996, 'ProCrèche ← ProCrèche  [+ fix encoding]'))
MERGES.append((40,  1997, 'SixièmeHomme ← SixièmeHomme  [+ fix encoding]'))

# Second wave (detected after first merge ran) — keep richest, lower id on tie
MERGES = [
    (723,  1585, 'africtrust ← Afric TRUST'),
    (238,  1537, 'agrolora ← AGRO LORA'),
    (341,  1989, 'alg uno ← ALGUNO'),
    (1991,  989, 'Ardisplay ← ar display'),
    (356,   576, 'bluedove ← bluedove sarl'),
    (403,  1432, 'cardiag ← Car Diag'),
    (930,  1319, 'cinetique 360 ← CINETIQUE 360°  [tie, lower id]'),
    (932,  1240, 'data pathology ← DataPathology'),
    (1999,  963, 'Ecodome Maroc ← eco-dome maroc'),
    (389,  1282, 'epicerie verte ← E-PICERIE VERTE'),
    (778,  1154, 'fantastic app ← Fantastic.app'),
    (666,  1470, 'fellahtech ← FELLAH TECH'),
    (1221, 1412, 'GOOD FELLOWS SARL ← GOOD FELLOWS  [tie, lower id]'),
    (2001,  970, 'IDA Tech ← id&a tech'),
    (505,  1290, 'innovdom ← INNOVDOM SARL  [tie, lower id]'),
]

# Only backfill these fields on keep if keep's value is NULL/empty.
BACKFILL_FIELDS = [
    ('CompanyLegalName', '"CompanyLegalName"'),
    ('numeroRC',         '"numeroRC"'),
    ('numeroICE',        '"numeroICE"'),
]

parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
MODE = 'APPLY' if args.apply else 'DRY-RUN'
print(f"=== MERGE STARTUPS — {MODE} ===\n")


def preview(conn, keep_id, del_id, label):
    print(f"— {label}")

    # StartupFounders to transfer
    sf_transfer = conn.execute(text('''
        SELECT sf."Founder Id", f.name
        FROM "StartupFounders" sf
        LEFT JOIN "Founders" f ON f."Founder Id" = sf."Founder Id"
        WHERE sf."Startup Id" = :d
          AND NOT EXISTS (SELECT 1 FROM "StartupFounders" sk
                          WHERE sk."Startup Id" = :k
                            AND sk."Founder Id" = sf."Founder Id")
    '''), {'k': keep_id, 'd': del_id}).fetchall()
    sf_drop = conn.execute(text('''
        SELECT sf."Founder Id", f.name
        FROM "StartupFounders" sf
        LEFT JOIN "Founders" f ON f."Founder Id" = sf."Founder Id"
        WHERE sf."Startup Id" = :d
          AND EXISTS (SELECT 1 FROM "StartupFounders" sk
                      WHERE sk."Startup Id" = :k
                        AND sk."Founder Id" = sf."Founder Id")
    '''), {'k': keep_id, 'd': del_id}).fetchall()
    print(f"    StartupFounders — transfer: {len(sf_transfer)}, drop redundant: {len(sf_drop)}")
    for r in sf_transfer:
        print(f"      → founder {r[0]}  ({r[1]})")
    for r in sf_drop:
        print(f"      × redundant founder {r[0]}  ({r[1]})")

    # FundingRounds to repoint
    fr = conn.execute(
        text('SELECT "Funding_Round_Id", "Round Name" FROM "FundingRounds" WHERE "Startup Id" = :d'),
        {'d': del_id}
    ).fetchall()
    print(f"    FundingRounds to repoint: {len(fr)}")
    for r in fr:
        print(f"      → FR {r[0]}  ({r[1]})")

    # StartupIncubators
    si_transfer = conn.execute(text('''
        SELECT si."Incubator Id" FROM "StartupIncubators" si
        WHERE si."Startup Id" = :d
          AND NOT EXISTS (SELECT 1 FROM "StartupIncubators" sk
                          WHERE sk."Startup Id" = :k
                            AND sk."Incubator Id" = si."Incubator Id")
    '''), {'k': keep_id, 'd': del_id}).fetchall()
    si_drop = conn.execute(text('''
        SELECT si."Incubator Id" FROM "StartupIncubators" si
        WHERE si."Startup Id" = :d
          AND EXISTS (SELECT 1 FROM "StartupIncubators" sk
                      WHERE sk."Startup Id" = :k
                        AND sk."Incubator Id" = si."Incubator Id")
    '''), {'k': keep_id, 'd': del_id}).fetchall()
    print(f"    StartupIncubators — transfer: {len(si_transfer)}, drop: {len(si_drop)}")

    # Fields to backfill (where keep is NULL/empty and delete has a value)
    select_cols = ', '.join(col for _, col in BACKFILL_FIELDS)
    keep_row = conn.execute(text(
        f'SELECT {select_cols} FROM "Startups" WHERE "Startup Id" = :k'
    ), {'k': keep_id}).fetchone()
    del_row = conn.execute(text(
        f'SELECT {select_cols} FROM "Startups" WHERE "Startup Id" = :d'
    ), {'d': del_id}).fetchone()
    backfill = []
    for i, (fname, col) in enumerate(BACKFILL_FIELDS):
        kv, dv = keep_row[i] if keep_row else None, del_row[i] if del_row else None
        kv_empty = (kv is None) or (isinstance(kv, str) and kv.strip() == '')
        dv_val = (dv is not None) and not (isinstance(dv, str) and dv.strip() == '')
        if kv_empty and dv_val:
            backfill.append((col, fname, dv))
    print(f"    Fields to backfill: {len(backfill)}")
    for col, fname, v in backfill:
        print(f"      ← {fname} = {v!r}")

    return {
        'transfer_sf': bool(sf_transfer),
        'fr_count': len(fr),
        'transfer_si': bool(si_transfer),
        'backfill': backfill,
    }


with engine.connect() as conn:
    plans = []
    for keep_id, del_id, label in MERGES:
        plans.append((keep_id, del_id, label, preview(conn, keep_id, del_id, label)))
        print()

if not args.apply:
    print("(dry-run — no changes applied. Run with --apply to execute.)")
    sys.exit(0)

# Apply
for keep_id, del_id, label, plan in plans:
    print(f"\nApplying {label}...")
    with engine.begin() as tx:
        # 1. Backfill
        if plan['backfill']:
            sets = ', '.join(f"{col} = :v_{i}" for i, (col, _, _) in enumerate(plan['backfill']))
            params = {f'v_{i}': v for i, (_, _, v) in enumerate(plan['backfill'])}
            params['k'] = keep_id
            tx.execute(
                text(f'UPDATE "Startups" SET {sets} WHERE "Startup Id" = :k'),
                params
            )
        # 2. Transfer StartupFounders
        tx.execute(text('''
            INSERT INTO "StartupFounders" ("Startup Id", "Founder Id")
            SELECT :k, sf."Founder Id" FROM "StartupFounders" sf
            WHERE sf."Startup Id" = :d
              AND NOT EXISTS (SELECT 1 FROM "StartupFounders" sk
                              WHERE sk."Startup Id" = :k
                                AND sk."Founder Id" = sf."Founder Id")
        '''), {'k': keep_id, 'd': del_id})
        tx.execute(text('DELETE FROM "StartupFounders" WHERE "Startup Id" = :d'), {'d': del_id})

        # 3. Re-point FundingRounds
        tx.execute(text('UPDATE "FundingRounds" SET "Startup Id" = :k WHERE "Startup Id" = :d'),
                   {'k': keep_id, 'd': del_id})

        # 4. Transfer StartupIncubators
        tx.execute(text('''
            INSERT INTO "StartupIncubators" ("Startup Id", "Incubator Id")
            SELECT :k, si."Incubator Id" FROM "StartupIncubators" si
            WHERE si."Startup Id" = :d
              AND NOT EXISTS (SELECT 1 FROM "StartupIncubators" sk
                              WHERE sk."Startup Id" = :k
                                AND sk."Incubator Id" = si."Incubator Id")
        '''), {'k': keep_id, 'd': del_id})
        tx.execute(text('DELETE FROM "StartupIncubators" WHERE "Startup Id" = :d'), {'d': del_id})

        # 5. Delete the duplicate startup
        tx.execute(text('DELETE FROM "Startups" WHERE "Startup Id" = :d'), {'d': del_id})

    print(f"  ✓ applied")

# Fix encoding-broken names on kept rows
if NAME_FIX:
    print("\n--- Encoding fixes ---")
    with engine.begin() as tx:
        for sid, new_name in NAME_FIX.items():
            tx.execute(
                text('UPDATE "Startups" SET "Startup name" = :n WHERE "Startup Id" = :s'),
                {'n': new_name, 's': sid}
            )
            print(f"  ✓ id={sid}  →  name={new_name!r}")
