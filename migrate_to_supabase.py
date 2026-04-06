"""Migrate all data from SQLite to Supabase PostgreSQL."""
import sqlite3
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'thepulse.db')

# Use session pooler (port 5432) for migration — supports longer sessions
DATABASE_URL = os.environ.get("DATABASE_URL", "").replace(":6543/", ":5432/")

TABLE_ORDER = [
    'User', 'Institutes', 'Incubators', 'Startups', 'Founders',
    'Investors', 'Funds', 'LimitedPartner', 'ServiceProvider',
    'Education', 'Experiences', 'FundingRounds', 'articles',
    'resources', 'posts', 'talents', 'cofounder_projects',
    'direct_messages', 'StartupFounders', 'StartupIncubators',
    'IncubatorFounders', 'FundInvestors', 'Investements',
    'LPFunds', 'SPFunds', 'SPInvestor',
]

BATCH_SIZE = 50

def get_pg_column_types(pg_conn, table):
    cur = pg_conn.cursor()
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns WHERE table_name = %s
    """, (table,))
    return {col: {'type': dtype, 'maxlen': maxlen} for col, dtype, maxlen in cur.fetchall()}

def coerce(val, info):
    if val is None:
        return None
    dtype = info.get('type', '')
    maxlen = info.get('maxlen')
    if dtype == 'boolean':
        if isinstance(val, int):
            return bool(val)
        if isinstance(val, str):
            return val.lower() in ('true', '1', 'yes')
        return bool(val)
    if isinstance(val, str) and maxlen:
        return val[:maxlen]
    return val

def fresh_conn():
    return psycopg2.connect(DATABASE_URL, keepalives=1, keepalives_idle=30,
                            keepalives_interval=10, keepalives_count=5)

def migrate():
    print(f"SQLite: {SQLITE_PATH}", flush=True)
    print(f"PG: {DATABASE_URL[:60]}...", flush=True)

    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row

    existing_sqlite = {
        t[0] for t in sqlite_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }

    # Delete in reverse order to handle FK constraints
    print("\nClearing PG tables...", flush=True)
    pg = fresh_conn()
    for table in reversed(TABLE_ORDER):
        if table not in existing_sqlite:
            continue
        try:
            cur = pg.cursor()
            cur.execute(f'DELETE FROM "{table}"')
            pg.commit()
            print(f"  Cleared {table}", flush=True)
        except Exception as e:
            pg.rollback()
            print(f"  Could not clear {table}: {e}", flush=True)
    pg.close()

    # Insert table by table, reconnecting each time
    print("\nInserting data...", flush=True)
    for table in TABLE_ORDER:
        if table not in existing_sqlite:
            print(f"  SKIP {table}", flush=True)
            continue

        rows = sqlite_conn.execute(f'SELECT * FROM "{table}"').fetchall()
        if not rows:
            print(f"  SKIP {table} (empty)", flush=True)
            continue

        columns = list(rows[0].keys())
        pg = fresh_conn()
        col_types = get_pg_column_types(pg, table)

        quoted_cols = ', '.join(f'"{c}"' for c in columns)
        placeholders = ', '.join(['%s'] * len(columns))
        sql = f'INSERT INTO "{table}" ({quoted_cols}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'

        inserted = 0
        errors = 0
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            data = [
                tuple(coerce(row[c], col_types.get(c, {})) for c in columns)
                for row in batch
            ]
            try:
                cur = pg.cursor()
                cur.executemany(sql, data)
                pg.commit()
                inserted += len(batch)
                print(f"  {table}: {inserted}/{len(rows)}...", end='\r', flush=True)
            except Exception as e:
                pg.rollback()
                errors += 1
                print(f"\n    Batch error {table} [{i}:{i+BATCH_SIZE}]: {str(e)[:120]}", flush=True)

        pg.close()
        status = "OK" if errors == 0 else "PARTIAL"
        print(f"  {status} {table}: {inserted}/{len(rows)} rows ({errors} errors)      ", flush=True)

    sqlite_conn.close()
    print("\nMigration complete.", flush=True)

if __name__ == '__main__':
    migrate()
