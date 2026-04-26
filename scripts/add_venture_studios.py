"""
Seed two venture studios:
  - The Foundry  (CEO: Asmae Berrada — already in pulse_members as 'program')
  - 34Studio     (CEO: Amine Jouahri — has a Founder row, no pulse_member yet)

Usage:
    python scripts/add_venture_studios.py            # dry-run
    python scripts/add_venture_studios.py --apply
"""
import os, sys, json, argparse, uuid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ['DATABASE_URL'] = (
    'postgresql://postgres.lianafeunaxlzqfvslob:'
    'Habiba456!!!!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'
)
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

FOUNDRY = {
    'full_name': 'The Foundry',
    'email':     'Asmae.berrada@um6pfoundry.com',
    'website':   'https://www.um6pfoundry.com/',
    'linkedin':  'https://www.linkedin.com/company/the-foundry-ma/',
    'ceo':       'Asmae Berrada',
    'location':  'Benguerir, Morocco',
    'description': (
        "The Foundry, le venture studio de l'UM6P, transforme la recherche "
        "scientifique en startups deeptech. Implanté à Benguerir, il accompagne "
        "les chercheurs et entrepreneurs dans la création, le financement et "
        "le scale-up d'entreprises issues du laboratoire."
    ),
}

STUDIO34 = {
    'full_name': '34Studio',
    # Placeholder email — update once you have Amine's contact.
    'email':     'contact@34stud.io',
    'website':   'https://www.34stud.io/',
    'linkedin':  'https://www.linkedin.com/company/34studio/',
    'ceo':       'Amine Jouahri',
    'location':  'Casablanca, Morocco',
    'description': (
        "34Studio est un venture studio basé au Maroc qui co-construit des "
        "startups tech avec des founders ambitieux : idéation, MVP, levée de "
        "fonds et go-to-market."
    ),
}


def upsert_studio(tx, s):
    """Insert or update a venture-studio pulse_member.

    If a member with the same email already exists, switch their role to
    venture_studio and refresh form_data; otherwise create a new row.
    """
    fd = {
        'investor_name': s['full_name'],
        'website':       s['website'],
        'homepage_url':  s['website'],
        'location':      s['location'],
        'hq_location':   s['location'],
        'description':   s['description'],
        'about':         s['description'],
        'ceo':           s['ceo'],
    }
    fd_json = json.dumps(fd, ensure_ascii=False)

    existing = tx.execute(
        text("SELECT id FROM pulse_members WHERE LOWER(email) = LOWER(:e)"),
        {'e': s['email']}
    ).fetchone()

    if existing:
        tx.execute(text("""
            UPDATE pulse_members
               SET full_name = :n, role = 'venture_studio', is_confirmed = TRUE,
                   linkedin = :li, form_data = :fd
             WHERE id = :i
        """), {'n': s['full_name'], 'li': s['linkedin'], 'fd': fd_json, 'i': existing[0]})
        return f"updated id={existing[0]}"
    else:
        r = tx.execute(text("""
            INSERT INTO pulse_members (email, full_name, role, confirmation_token,
                                        is_confirmed, linkedin, form_data)
            VALUES (:e, :n, 'venture_studio', :tok, TRUE, :li, :fd)
            RETURNING id
        """), {
            'e': s['email'], 'n': s['full_name'], 'tok': str(uuid.uuid4()),
            'li': s['linkedin'], 'fd': fd_json,
        })
        return f"inserted id={r.scalar()}"


parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
print(f"=== ADD VENTURE STUDIOS — {'APPLY' if args.apply else 'DRY-RUN'} ===\n")

for s in [FOUNDRY, STUDIO34]:
    print(f"-- {s['full_name']} (CEO: {s['ceo']}) --")
    for k, v in s.items():
        if k == 'description':
            print(f"  {k}: {v[:80]}...")
        else:
            print(f"  {k}: {v}")
    print()

if not args.apply:
    print("(dry-run)")
    sys.exit(0)

with engine.begin() as tx:
    for s in [FOUNDRY, STUDIO34]:
        msg = upsert_studio(tx, s)
        print(f"  ✓ {s['full_name']}: {msg}")
