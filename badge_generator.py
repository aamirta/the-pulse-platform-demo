"""
Badge composition module — used by the Flask /badge route.

Public API:
    generate(photo_stream_or_path, full_name, role, *, out=None) -> BytesIO
        Returns an in-memory PNG (or writes to `out` if given).
"""
import os, io, re
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(ROOT, 'static', 'badge', 'template.png')

# Fonts — fallback list in case one is missing
FONT_DIRS = [
    os.path.join(os.path.expanduser('~'),
                 'Library', 'Application Support', 'Claude',
                 'local-agent-mode-sessions', 'skills-plugin',
                 'b8cb25d5-c215-4108-b879-6d249e22f86b',
                 '6d7cd525-1eac-4142-8a35-df9b90bd1ea1',
                 'skills', 'canvas-design', 'canvas-fonts'),
    os.path.join(ROOT, 'static', 'fonts'),
]


def _font_path(name):
    for d in FONT_DIRS:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    return None


FONT_BOLD = _font_path('BricolageGrotesque-Bold.ttf') or _font_path('Outfit-Bold.ttf')
FONT_REG  = _font_path('Outfit-Regular.ttf')

# Category accent colours
CATEGORY_COLORS = {
    'entrepreneur': (0, 214, 143),     # mint
    'startup':      (0, 214, 143),
    'investisseur': (99, 102, 241),    # indigo
    'vc':           (99, 102, 241),
    'amic':         (99, 102, 241),
    'président':    (99, 102, 241),
    'president':    (99, 102, 241),
    'programme':    (245, 158, 11),    # amber
    'incubateur':   (249, 115, 22),    # orange
    'accelerateur': (249, 115, 22),
    'accélérateur': (249, 115, 22),
    'talent':       (139, 92, 246),    # purple
    'professionnel':(139, 92, 246),
    'expert':       (234, 88, 12),     # dark orange
    'mentor':       (234, 88, 12),
}

CATEGORIES = [
    ('entrepreneur', 'Entrepreneur / Startup'),
    ('investisseur', 'Investisseur / VC'),
    ('programme',    "Programme d'accompagnement"),
    ('incubateur',   'Incubateur / Accélérateur'),
    ('talent',       'Talent / Professionnel'),
    ('expert',       'Expert / Mentor'),
]


def accent_for(role):
    key = (role or '').lower()
    for tok, col in CATEGORY_COLORS.items():
        if tok in key:
            return col
    return (0, 214, 143)


def _detect_circle(template_img):
    w, h = template_img.size
    if (w, h) == (1250, 1250):
        return (796, 555, 268)
    return (int(w * 0.64), int(h * 0.44), int(min(w, h) * 0.21))


def _crop_square_center(img):
    w, h = img.size
    s = min(w, h)
    return img.crop(((w - s) // 2, (h - s) // 2,
                     (w - s) // 2 + s, (h - s) // 2 + s))


def _fit_font(text, font_path, max_width, start=64, min_size=26):
    for size in range(start, min_size - 1, -2):
        f = ImageFont.truetype(font_path, size)
        bbox = f.getbbox(text)
        if bbox[2] - bbox[0] <= max_width:
            return f
    return ImageFont.truetype(font_path, min_size)


def _pad_to(img, W, H, x, y):
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    canvas.paste(img, (x, y), img)
    return canvas


def generate(photo_src, full_name, role, out=None, category=None):
    """
    photo_src:  path to file OR a file-like object (e.g. Flask's FileStorage).
    full_name:  person's display name.
    role:       label shown under the name.
    category:   optional explicit category slug (entrepreneur / investisseur /
                programme / incubateur / talent / expert). If provided, drives
                the accent colour. Otherwise keywords in `role` are scanned.
    out:        optional file path; if None, returns a BytesIO.
    """
    if category and category.lower() in CATEGORY_COLORS:
        accent = CATEGORY_COLORS[category.lower()]
    else:
        accent = accent_for(role)
    accent_rgba = accent + (255,)

    template = Image.open(TEMPLATE).convert('RGBA')
    W, H = template.size
    cx, cy, r = _detect_circle(template)
    ORIG_CX, ORIG_CY, ORIG_R = 796, 627, 363
    BG = (7, 11, 18, 255)

    # 1. Mask out the template's original landscape
    cover = Image.new('RGBA', template.size, (0, 0, 0, 0))
    ImageDraw.Draw(cover).ellipse(
        (ORIG_CX - ORIG_R - 4, ORIG_CY - ORIG_R - 4,
         ORIG_CX + ORIG_R + 4, ORIG_CY + ORIG_R + 4),
        fill=BG,
    )
    img = Image.alpha_composite(template, cover)

    # 2. Photo -> circle
    if hasattr(photo_src, 'read'):
        photo = Image.open(photo_src).convert('RGBA')
    else:
        photo = Image.open(photo_src).convert('RGBA')
    photo = _crop_square_center(photo)
    d = r * 2
    photo = photo.resize((d, d), Image.LANCZOS)
    mask = Image.new('L', (d, d), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, d, d), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(0.8))
    photo_layer = Image.new('RGBA', template.size, (0, 0, 0, 0))
    photo_layer.paste(photo, (cx - r, cy - r), mask)
    img = Image.alpha_composite(img, photo_layer)

    # 3. Border ring in category accent
    ring = Image.new('RGBA', template.size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    for i, alpha in [(7, 40), (5, 80), (3, 140), (1, 220)]:
        rd.ellipse((cx - r - i, cy - r - i, cx + r + i, cy + r + i),
                   outline=accent + (alpha,), width=2)
    rd.ellipse((cx - r, cy - r, cx + r, cy + r),
               outline=accent_rgba, width=3)
    img = Image.alpha_composite(img, ring)

    # 4. Text below circle
    draw = ImageDraw.Draw(img)
    max_text_w = int(d * 1.0)
    name_font = _fit_font(full_name, FONT_BOLD, max_text_w, start=64, min_size=28)
    role_font = _fit_font(role,      FONT_REG,  max_text_w, start=34, min_size=18)
    nb = name_font.getbbox(full_name)
    rb = role_font.getbbox(role)
    name_h = nb[3] - nb[1]
    role_h = rb[3] - rb[1]
    gap = 14
    circle_bottom = cy + r
    name_y = circle_bottom + 28
    role_y = name_y + name_h + gap
    name_x = cx - (nb[2] - nb[0]) // 2 - nb[0]
    role_x = cx - (rb[2] - rb[0]) // 2 - rb[0]

    draw.text((name_x, name_y), full_name, font=name_font,
              fill=(238, 242, 255, 255))
    draw.text((role_x, role_y), role, font=role_font, fill=accent_rgba)

    # Output
    final = img.convert('RGB')
    if out:
        final.save(out, 'PNG', optimize=True)
        return out
    buf = io.BytesIO()
    final.save(buf, 'PNG', optimize=True)
    buf.seek(0)
    return buf
