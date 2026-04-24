"""
Insert 'Revolut Maroc' startup + Yacine Faqir (CEO) founder + link.

Usage:
    python scripts/add_revolut_maroc.py            # dry-run
    python scripts/add_revolut_maroc.py --apply
"""
import os, sys, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ['DATABASE_URL'] = (
    'postgresql://postgres.lianafeunaxlzqfvslob:'
    'Habiba456!!!!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'
)
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

STARTUP = {
    'name':        'Revolut Maroc',
    'sector':      'FinTech',
    'location':    'Casablanca',
    'region':      'Casablanca-Settat',
    'country':     'Morocco',
    'logo_url':    '/static/images/revolut_logo.png',
    'linkedin':    'https://www.linkedin.com/company/revolut/',
    'homepage':    'https://www.revolut.com/',
    'description': ("Revolut Maroc — filiale marocaine de Revolut, la superapp "
                    "financière globale fondée en 2015 (Londres). Services "
                    "bancaires, paiements internationaux, crypto, investissement."),
}

FOUNDER = {
    'name':        'Yacine Faqir',
    'first_name':  'Yacine',
    'last_name':   'Faqir',
    'title':       'CEO',
    'employer':    'Revolut Maroc',
    'location':    'Casablanca, Morocco',
    'linkedin':    None,                                            # fill if you have it
    'profile_pic': '/static/images/founders/yacine_faqir.jpeg',     # expected path
}


parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
MODE = 'APPLY' if args.apply else 'DRY-RUN'
print(f"=== ADD REVOLUT MAROC — {MODE} ===\n")

with engine.connect() as c:
    # Find next available startup id
    max_sid = c.execute(text('SELECT COALESCE(MAX("Startup Id"), 0) FROM "Startups"')).scalar()
    sid = max_sid + 1

    # Find next available founder id (numeric-like)
    max_fid = c.execute(text('''
        SELECT COALESCE(MAX(CAST("Founder Id" AS INTEGER)), 0)
        FROM "Founders"
        WHERE "Founder Id" ~ '^[0-9]+$'
    ''')).scalar()
    fid = str(max_fid + 1)

    # Check for existing rows — don't double-insert
    existing_s = c.execute(text('SELECT "Startup Id" FROM "Startups" WHERE "Startup name" = :n'),
                           {'n': STARTUP['name']}).fetchone()
    existing_f = c.execute(text('SELECT "Founder Id" FROM "Founders" WHERE name = :n'),
                           {'n': FOUNDER['name']}).fetchone()

print(f"Next startup id: {sid}" + ("  (already exists: "+str(existing_s[0])+")" if existing_s else ""))
print(f"Next founder id: {fid}" + ("  (already exists: "+str(existing_f[0])+")" if existing_f else ""))

for k, v in STARTUP.items():
    val = (v or '—')[:70]
    print(f"  startup.{k:<12} = {val}")
print()
for k, v in FOUNDER.items():
    val = (v or '—')[:70]
    print(f"  founder.{k:<12} = {val}")

# Verify the founder's pic file exists on disk (warn if not)
pic_path = os.path.join(os.path.dirname(__file__), '..', FOUNDER['profile_pic'].lstrip('/'))
pic_exists = os.path.exists(pic_path)
print(f"\nPhoto de Yacine trouvée sur disque : {pic_exists}  ({pic_path})")
if not pic_exists:
    print("  ⚠ Sauvegarde la photo à ce chemin avant --apply, sinon profile_pic restera cassé.")

if not args.apply:
    print("\n(dry-run)")
    sys.exit(0)

if existing_s or existing_f:
    print("\n✗ Abandon — des lignes existent déjà. Supprime-les d'abord si tu veux forcer.")
    sys.exit(1)

with engine.begin() as tx:
    tx.execute(text('''
        INSERT INTO "Startups" ("Startup Id", "Startup name", sector, location, region,
                                 country_code, logo_url, linkedin, homepage_url,
                                 "EntrepriseContactSiteWeb", description, stage)
        VALUES (:sid, :name, :sector, :location, :region, :country,
                :logo, :linkedin, :homepage, :homepage, :description, 'SCALING')
    '''), {
        'sid': sid, 'name': STARTUP['name'], 'sector': STARTUP['sector'],
        'location': STARTUP['location'], 'region': STARTUP['region'],
        'country': STARTUP['country'], 'logo': STARTUP['logo_url'],
        'linkedin': STARTUP['linkedin'], 'homepage': STARTUP['homepage'],
        'description': STARTUP['description'],
    })
    tx.execute(text('''
        INSERT INTO "Founders" ("Founder Id", name, first_name, last_name,
                                current_title, current_employer, location,
                                linkedin_url, profile_pic, company_details_name)
        VALUES (:fid, :name, :first, :last, :title, :employer,
                :location, :linkedin, :pic, :employer)
    '''), {
        'fid': fid, 'name': FOUNDER['name'],
        'first': FOUNDER['first_name'], 'last': FOUNDER['last_name'],
        'title': FOUNDER['title'], 'employer': FOUNDER['employer'],
        'location': FOUNDER['location'], 'linkedin': FOUNDER['linkedin'],
        'pic': FOUNDER['profile_pic'],
    })
    tx.execute(text('INSERT INTO "StartupFounders" ("Startup Id", "Founder Id") VALUES (:s, :f)'),
               {'s': sid, 'f': fid})

print(f"\n✓ Inserted: startup {sid} 'Revolut Maroc' + founder {fid} 'Yacine Faqir' + link.")