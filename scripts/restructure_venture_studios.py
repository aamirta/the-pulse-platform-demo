"""
Restructure venture-studio data:

  - Restore Asmae Berrada's pulse_member (id=59) to her original
    person profile (was overwritten as 'The Foundry' in the previous run).
  - Create Amine Jouahri as a pulse_member (the person).
  - Create / refresh two venture-studio entities (separate pulse_members
    with role='venture_studio') and link each to its CEO via
    form_data['ceo_member_id'].
       * The Foundry  → CEO id 59 (Asmae)
       * 34 Ventures  → CEO id of new Amine Jouahri row
  - Use a short description for The Foundry; rich one for 34 Ventures.

Idempotent — re-runnable safely.

Usage:
    python scripts/restructure_venture_studios.py            # dry-run
    python scripts/restructure_venture_studios.py --apply
"""
import os, sys, json, uuid, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ['DATABASE_URL'] = (
    'postgresql://postgres.lianafeunaxlzqfvslob:'
    'Habiba456!!!!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'
)
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])


parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true')
args = parser.parse_args()
print(f"=== RESTRUCTURE VENTURE STUDIOS — {'APPLY' if args.apply else 'DRY-RUN'} ===\n")


def upsert_pulse_member(tx, *, email, full_name, role, linkedin=None,
                        form_data=None):
    """Insert or update a pulse_member by email; return its id."""
    fd_json = json.dumps(form_data or {}, ensure_ascii=False)
    existing = tx.execute(
        text("SELECT id FROM pulse_members WHERE LOWER(email) = LOWER(:e)"),
        {'e': email}
    ).fetchone()
    if existing:
        tx.execute(text("""
            UPDATE pulse_members
               SET full_name = :n, role = :r, is_confirmed = TRUE,
                   linkedin = COALESCE(:li, linkedin), form_data = :fd
             WHERE id = :i
        """), {'n': full_name, 'r': role, 'li': linkedin,
               'fd': fd_json, 'i': existing[0]})
        return existing[0], 'updated'
    r = tx.execute(text("""
        INSERT INTO pulse_members (email, full_name, role, confirmation_token,
                                    is_confirmed, linkedin, form_data)
        VALUES (:e, :n, :r, :tok, TRUE, :li, :fd)
        RETURNING id
    """), {'e': email, 'n': full_name, 'r': role, 'tok': str(uuid.uuid4()),
           'li': linkedin, 'fd': fd_json})
    return r.scalar(), 'inserted'


# Email aliases for the venture studio entities (separate from CEO mailboxes)
FOUNDRY_STUDIO_EMAIL = 'studio@um6pfoundry.com'
VENTURES34_STUDIO_EMAIL = 'hello@34stud.io'
AMINE_EMAIL = 'amine@34stud.io'  # placeholder; update when you have it

with engine.begin() if args.apply else engine.connect() as tx:
    # 1. Restore Asmae Berrada's person record
    asmae_id, action = upsert_pulse_member(
        tx,
        email='Asmae.berrada@um6pfoundry.com',
        full_name='Asmae Berrada',
        role='program',  # her original role
        linkedin=None,
        form_data={'organization': 'The Foundry — UM6P', 'role_at_foundry': 'CEO'},
    ) if args.apply else (59, 'would-update')
    print(f"  Asmae Berrada      : id={asmae_id}  ({action})")

    # 2. Create Amine Jouahri (the person)
    amine_id, action = upsert_pulse_member(
        tx,
        email=AMINE_EMAIL,
        full_name='Amine Jouahri',
        role='entrepreneur',
        linkedin='https://www.linkedin.com/in/amine-jouahri/',
        form_data={'organization': '34 Ventures', 'role_at_studio': 'CEO'},
    ) if args.apply else (None, 'would-insert')
    print(f"  Amine Jouahri      : id={amine_id}  ({action})")

    # 3. The Foundry — venture studio
    foundry_id, action = upsert_pulse_member(
        tx,
        email=FOUNDRY_STUDIO_EMAIL,
        full_name='The Foundry',
        role='venture_studio',
        linkedin='https://www.linkedin.com/company/the-foundry-ma/',
        form_data={
            'investor_name': 'The Foundry',
            'website':       'https://www.um6pfoundry.com/',
            'homepage_url':  'https://www.um6pfoundry.com/',
            'location':      'Benguerir, Morocco',
            'hq_location':   'Benguerir, Morocco',
            'description':   "The Foundry, le venture studio de l'UM6P, transforme "
                             "la recherche scientifique en startups deeptech.",
            'about':         "The Foundry, le venture studio de l'UM6P, transforme "
                             "la recherche scientifique en startups deeptech.",
            'ceo':           'Asmae Berrada',
            'ceo_member_id': asmae_id,
        },
    ) if args.apply else (None, 'would-insert')
    print(f"  The Foundry        : id={foundry_id}  ({action})")

    # 4. 34 Ventures — venture studio (rich data scraped from 34stud.io)
    v34_desc = (
        "34 Ventures est un AI Studio et venture builder marocain qui accompagne "
        "des fondateurs en deeptech et IA — financement, expertise, accès aux "
        "marchés globaux. Portefeuille : DEEPECHO, TOUMAI, TALATY, INVirtus, VIOO. "
        "« We help bold minds build AI & deeptech ventures with funding, hands-on "
        "support, and global reach. »"
    )
    ventures34_id, action = upsert_pulse_member(
        tx,
        email=VENTURES34_STUDIO_EMAIL,
        full_name='34 Ventures',
        role='venture_studio',
        linkedin='https://www.linkedin.com/company/34ventures/',
        form_data={
            'investor_name': '34 Ventures',
            'website':       'https://www.34stud.io/',
            'homepage_url':  'https://www.34stud.io/',
            'location':      'Casablanca, Morocco',
            'hq_location':   'Casablanca, Morocco',
            'description':   v34_desc,
            'about':         v34_desc,
            'tagline':       'Fueling founders, building ventures.',
            'portfolio':     'DEEPECHO, TOUMAI, TALATY, INVirtus, VIOO',
            'sectors':       'AI, Deeptech',
            'ceo':           'Amine Jouahri',
            'ceo_member_id': amine_id,
        },
    ) if args.apply else (None, 'would-insert')
    print(f"  34 Ventures        : id={ventures34_id}  ({action})")

    # 5. Clean up the orphaned VS rows from the previous bad run
    if args.apply:
        deleted = tx.execute(text("""
            DELETE FROM pulse_members
            WHERE role = 'venture_studio'
              AND email NOT IN (:e1, :e2)
        """), {'e1': FOUNDRY_STUDIO_EMAIL, 'e2': VENTURES34_STUDIO_EMAIL}).rowcount
        if deleted:
            print(f"  Removed {deleted} stale venture_studio rows")

if not args.apply:
    print("\n(dry-run)")
