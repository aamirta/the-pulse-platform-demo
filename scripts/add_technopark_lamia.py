"""
Add 'Technopark Maroc' incubator + Lamia Benmakhlouf (CEO) + link.
Also remove the misclassified Startup row #1901 (TECHNOPARK MOROCCO).

Usage:
    python scripts/add_technopark_lamia.py            # dry-run
    python scripts/add_technopark_lamia.py --apply
"""
import os, sys, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL environment variable is required")
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

INCUBATOR = {
    'name':        'Technopark Maroc',
    'type':        'Technopark',
    'statut':      'Actif',
    'phases':      'Pre-seed, Seed, Early-stage',
    'ville':       'Casablanca',
    'ville_organ': 'Casablanca, Rabat, Tanger, Tétouan, Agadir, Oujda',
    'date':        '2001',
    'description': (
        "Le Technopark, opéré par MITC (Moroccan Information Technopark Company), "
        "est le premier hub d'innovation et d'incubation du Royaume. Lancé en 2001 "
        "à Casablanca dans le cadre d'un partenariat public-privé, il accueille "
        "aujourd'hui plus de 350 startups et PME marocaines à travers ses sites de "
        "Casablanca, Rabat, Tanger, Tétouan, Agadir et Oujda. Il offre des bureaux, "
        "des programmes d'accompagnement, du mentorat, et un accès privilégié aux "
        "investisseurs et aux donneurs d'ordre. Secteurs phares : TIC, GreenTech, "
        "Industries Culturelles et Créatives."
    ),
    'email':       'contact@technopark.ma',
    'secteurs':    'TIC, ICT, GreenTech, CleanTech, FinTech, EdTech, Industries culturelles',
    'image_url':   'https://www.technopark.ma/wp-content/uploads/2020/01/logo-technopark.png',
    'linkedin':    'https://www.linkedin.com/company/technopark-maroc/',
    'partners':    'MITC, Ministère de l\'Industrie, Bank Al-Maghrib, BMCE Bank, BCP, CDG, Maroc Telecom',
}

FOUNDER = {
    'name':        'Lamia Benmakhlouf',
    'first_name':  'Lamia',
    'last_name':   'Benmakhlouf',
    'title':       'CEO',
    'employer':    'MITC — Technopark Maroc',
    'company':     'Technopark Maroc',
    'location':    'Casablanca, Morocco',
    'linkedin':    'https://www.linkedin.com/in/lamia-benmakhlouf-92a38b16/',
    'profile_pic': '/static/images/founders/lamia_benmakhlouf.jpeg',  # to be saved separately
}


parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
MODE = 'APPLY' if args.apply else 'DRY-RUN'
print(f"=== ADD TECHNOPARK + LAMIA — {MODE} ===\n")

with engine.connect() as c:
    # Sanity checks for duplicates
    inc_exists = c.execute(text(
        'SELECT "Incubator Id" FROM "Incubators" WHERE "Incubator" ILIKE :n'
    ), {'n': '%technopark%'}).fetchone()
    f_exists = c.execute(text(
        'SELECT "Founder Id" FROM "Founders" WHERE name ILIKE :n'
    ), {'n': '%benmakhlouf%lamia%'}).fetchone()
    f_exists2 = c.execute(text(
        'SELECT "Founder Id" FROM "Founders" WHERE name ILIKE :n'
    ), {'n': '%lamia%benmakhlouf%'}).fetchone()
    misclassified_startup = c.execute(text(
        'SELECT "Startup Id", "Startup name" FROM "Startups" WHERE "Startup Id" = 1901'
    )).fetchone()

    next_inc_id = c.execute(text(
        'SELECT COALESCE(MAX("Incubator Id"), 0) + 1 FROM "Incubators"'
    )).scalar()
    next_f_id = str(c.execute(text('''
        SELECT COALESCE(MAX(CAST("Founder Id" AS INTEGER)), 0) + 1
        FROM "Founders" WHERE "Founder Id" ~ '^[0-9]+$'
    ''')).scalar())

print(f"Existing incubator match : {inc_exists}")
print(f"Existing founder match   : {f_exists or f_exists2}")
print(f"Startup #1901 to remove  : {misclassified_startup}")
print(f"Next Incubator Id        : {next_inc_id}")
print(f"Next Founder Id          : {next_f_id}")
print()
print("--- Incubator preview ---")
for k, v in INCUBATOR.items():
    print(f"  {k:<12} = {(str(v) or '')[:80]}")
print()
print("--- Founder preview ---")
for k, v in FOUNDER.items():
    print(f"  {k:<12} = {(str(v) or '')[:80]}")

# Photo file check
pic_path = os.path.join(os.path.dirname(__file__), '..', FOUNDER['profile_pic'].lstrip('/'))
pic_ok = os.path.exists(pic_path)
print(f"\nLamia photo on disk : {pic_ok}  ({pic_path})")
if not pic_ok:
    print("  (sauvegarde la photo à ce chemin pour qu'elle s'affiche ; on garde le path en base de toute façon)")

if not args.apply:
    print("\n(dry-run)")
    sys.exit(0)

if inc_exists or f_exists or f_exists2:
    print("\n✗ Existing record found — abort.")
    sys.exit(1)

with engine.begin() as tx:
    # 1. Remove misclassified startup
    if misclassified_startup:
        tx.execute(text('DELETE FROM "StartupFounders" WHERE "Startup Id" = 1901'))
        tx.execute(text('DELETE FROM "StartupIncubators" WHERE "Startup Id" = 1901'))
        tx.execute(text('DELETE FROM "FundingRounds" WHERE "Startup Id" = 1901'))
        tx.execute(text('DELETE FROM "Startups" WHERE "Startup Id" = 1901'))
        print("✓ removed misclassified startup row 1901")

    # 2. Insert incubator
    tx.execute(text('''
        INSERT INTO "Incubators" ("Incubator Id", "Incubator", type_organisme, statut,
                                  phases_investissement, ville_organisme, ville,
                                  date_creation, description, email, secteurs,
                                  image_url, linkedin, partners_or_sponsors)
        VALUES (:iid, :name, :type, :statut, :phases, :ville_organ, :ville,
                :date, :description, :email, :secteurs, :image, :linkedin, :partners)
    '''), {
        'iid': next_inc_id, 'name': INCUBATOR['name'], 'type': INCUBATOR['type'],
        'statut': INCUBATOR['statut'], 'phases': INCUBATOR['phases'],
        'ville_organ': INCUBATOR['ville_organ'], 'ville': INCUBATOR['ville'],
        'date': INCUBATOR['date'], 'description': INCUBATOR['description'],
        'email': INCUBATOR['email'], 'secteurs': INCUBATOR['secteurs'],
        'image': INCUBATOR['image_url'], 'linkedin': INCUBATOR['linkedin'],
        'partners': INCUBATOR['partners'],
    })
    print(f"✓ inserted incubator '{INCUBATOR['name']}' (id={next_inc_id})")

    # 3. Insert founder
    tx.execute(text('''
        INSERT INTO "Founders" ("Founder Id", name, first_name, last_name,
                                current_title, current_employer, location,
                                linkedin_url, profile_pic, company_details_name)
        VALUES (:fid, :name, :first, :last, :title, :employer, :location,
                :linkedin, :pic, :company)
    '''), {
        'fid': next_f_id, 'name': FOUNDER['name'],
        'first': FOUNDER['first_name'], 'last': FOUNDER['last_name'],
        'title': FOUNDER['title'], 'employer': FOUNDER['employer'],
        'location': FOUNDER['location'], 'linkedin': FOUNDER['linkedin'],
        'pic': FOUNDER['profile_pic'], 'company': FOUNDER['company'],
    })
    print(f"✓ inserted founder '{FOUNDER['name']}' (id={next_f_id})")

    # 4. Link
    tx.execute(text('''
        INSERT INTO "IncubatorFounders" ("Incubator Id", "Founder Id")
        VALUES (:iid, :fid)
    '''), {'iid': next_inc_id, 'fid': next_f_id})
    print("✓ linked Lamia ↔ Technopark Maroc")
