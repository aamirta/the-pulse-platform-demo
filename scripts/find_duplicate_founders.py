"""
Find duplicate founder records for Larbi Belghiti and Mehdi Alami.
Shows all fields + startup links so we can decide which to keep.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ['DATABASE_URL'] = (
    'postgresql://postgres.lianafeunaxlzqfvslob:'
    'Habiba456!!!!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'
)
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

TARGETS = ['Larbi Belghiti', 'Mehdi Alami']

SQL = text('''
SELECT f."Founder Id", f.name, f.first_name, f.last_name, f.current_title,
       f.current_employer, f.location, f.linkedin_url, f.profile_pic,
       f.company_details_name,
       array_agg(DISTINCT s."Startup name") FILTER (WHERE s."Startup name" IS NOT NULL) AS startups,
       array_agg(DISTINCT s."Startup Id")    FILTER (WHERE s."Startup Id" IS NOT NULL) AS startup_ids,
       MAX(s.total_funding_usd) AS max_funding
FROM "Founders" f
LEFT JOIN "StartupFounders" sf ON sf."Founder Id" = f."Founder Id"
LEFT JOIN "Startups" s ON s."Startup Id" = sf."Startup Id"
WHERE f.name ILIKE :pattern
   OR (f.first_name ILIKE :first1 AND f.last_name ILIKE :last1)
   OR (f.first_name ILIKE :first2 AND f.last_name ILIKE :last2)
GROUP BY f."Founder Id", f.name, f.first_name, f.last_name, f.current_title,
         f.current_employer, f.location, f.linkedin_url, f.profile_pic,
         f.company_details_name
ORDER BY f.name, f."Founder Id"
''')

with engine.connect() as conn:
    for target in TARGETS:
        print(f"\n========== {target} ==========")
        parts = target.split(' ', 1)
        rows = conn.execute(SQL, {
            'pattern': f'%{target}%',
            'first1': f'%{parts[0]}%', 'last1': f'%{parts[1]}%',
            'first2': f'%{parts[1]}%', 'last2': f'%{parts[0]}%',
        }).fetchall()
        print(f"Records found: {len(rows)}\n")
        for r in rows:
            print(f"  ID: {r[0]}")
            print(f"    name            : {r[1]}")
            print(f"    first / last    : {r[2]} / {r[3]}")
            print(f"    current_title   : {r[4]}")
            print(f"    current_employer: {r[5]}")
            print(f"    location        : {r[6]}")
            print(f"    linkedin_url    : {r[7]}")
            print(f"    profile_pic     : {'yes' if r[8] else '—'}")
            print(f"    company_details : {r[9]}")
            print(f"    startups        : {r[10]}")
            print(f"    startup_ids     : {r[11]}")
            print(f"    max_funding_usd : {r[12]}")
            print()
