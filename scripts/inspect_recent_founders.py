"""
SELECT-only inspection of the 20 founders inserted by the last
enrich_founders.py run. Prints them with their startup link so we
can flag which ones are garbage and should be rolled back.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ['DATABASE_URL'] = (
    'postgresql://postgres.lianafeunaxlzqfvslob:'
    'Habiba456!!!!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'
)
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

# The log indicated inserts starting at founder_id 100268.
# Be conservative: look at all founders with Founder Id >= 100268.
SQL = '''
SELECT f."Founder Id", f.name, f.linkedin_url, f.current_employer,
       s."Startup name", s."Startup Id"
FROM "Founders" f
LEFT JOIN "StartupFounders" sf ON sf."Founder Id" = f."Founder Id"
LEFT JOIN "Startups" s ON s."Startup Id" = sf."Startup Id"
WHERE CAST(f."Founder Id" AS TEXT) ~ '^[0-9]+$'
  AND CAST(f."Founder Id" AS INTEGER) >= 100268
ORDER BY CAST(f."Founder Id" AS INTEGER)
'''

with engine.connect() as conn:
    rows = conn.execute(text(SQL)).fetchall()

print(f"Founders with id >= 100268: {len(rows)}\n")
print(f"{'ID':<8} {'NAME':<38} {'STARTUP':<28} LINKEDIN")
print('-' * 120)
for r in rows:
    fid, name, li, emp, sname, sid = r
    name_s = (name or '—')[:37]
    snm = (sname or '—')[:27]
    li_s = (li or '—')[:50]
    print(f"{fid:<8} {name_s:<38} {snm:<28} {li_s}")
