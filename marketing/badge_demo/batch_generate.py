"""
Generate 6 badges — per user request:
  • 2 Experts  : Hamid Bouchikhi, Simohammed Damiri
  • 4 Startups : Youssef Mamou, Larbi Belrhiti (YoLa Fresh),
                 Ismail Belkhayat (Chari), Mehdi Alami (Freterium)

Handles three photo sources:
  - local file path (static/...)
  - remote http(s) URL (with a desktop UA to get through CDN)
  - data:image/...;base64 (stored inline on pulse_members)
"""
import os, sys, base64, re, shutil, urllib.request, ssl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['DATABASE_URL'] = (
    'postgresql://postgres.lianafeunaxlzqfvslob:'
    'Habiba456!!!!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'
)
from sqlalchemy import create_engine, text
from generate_badge import compose

engine = create_engine(os.environ['DATABASE_URL'])
ROOT   = os.path.dirname(os.path.abspath(__file__))
REPO   = os.path.abspath(os.path.join(ROOT, '..', '..'))
OUTDIR = os.path.join(ROOT, 'samples')
os.makedirs(OUTDIR, exist_ok=True)

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36')


def save_pic(src, out):
    if not src:
        return False
    # data URL
    m = re.match(r'data:image/[^;]+;base64,(.+)', src, re.DOTALL)
    if m:
        with open(out, 'wb') as f:
            f.write(base64.b64decode(m.group(1)))
        return True
    # local /static path
    if src.startswith('/static/'):
        p = os.path.join(REPO, src.lstrip('/'))
        if os.path.exists(p):
            shutil.copy(p, out)
            return True
        return False
    # remote URL
    if src.startswith('http'):
        try:
            req = urllib.request.Request(src, headers={'User-Agent': UA})
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                with open(out, 'wb') as f:
                    f.write(resp.read())
            return True
        except Exception as e:
            print(f"    ! download failed: {e}")
            return False
    return False


with engine.connect() as c:
    def founder(fid):
        r = c.execute(text('''SELECT "Founder Id", name, current_title, current_employer, profile_pic
                              FROM "Founders" WHERE "Founder Id" = :i'''), {'i': fid}).fetchone()
        return r

    def pulse(mid):
        r = c.execute(text('SELECT full_name, role, profile_pic FROM pulse_members WHERE id = :i'),
                      {'i': mid}).fetchone()
        return r

    PLAN = [
        # (slug,          source,               name,                 role-label)
        ('01_larbi',      founder('65811'),     'Larbi Belrhiti',     'Co-Founder, YoLa Fresh'),
        ('02_mamou',      founder('41790'),     'Youssef Mamou',      'Co-Founder, YoLa Fresh'),
        ('03_ismail',     founder('99893'),     'Ismail Belkhayat',   'Co-Founder & CEO, Chari'),
        ('04_mehdi',      founder('27805'),     'Mehdi Alami',        'Founder & CEO, Freterium'),
        ('05_hamid',      pulse(47),            'Hamid Bouchikhi',    'Expert / Mentor'),
        ('06_simo',       pulse(43),            'Simohammed Damiri',  'Expert / Mentor'),
    ]

    for slug, row, name, label in PLAN:
        if not row:
            print(f"[{slug}] no row for {name}")
            continue
        # Find the pic source in the row
        pic_src = row[-1]  # profile_pic is last in both shapes
        tmp = os.path.join(OUTDIR, f'_tmp_{slug}.jpg')
        ok = save_pic(pic_src, tmp)
        if not ok:
            print(f"[{slug}] pic download failed for {name}")
            continue
        out = os.path.join(OUTDIR, f'badge_{slug}.png')
        try:
            compose(tmp, out, name, label)
        except Exception as e:
            print(f"[{slug}] compose error: {e}")
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
