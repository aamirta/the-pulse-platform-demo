"""
Generate an 'I'm in the pulse' badge by compositing a user's photo
into the template's circular placeholder + overlaying name & role.

Usage:
    python generate_badge.py <photo> <out> "<full name>" "<role>"
    Defaults to Simohammed Damiri / Founder & CEO, Nessiam.
"""
import sys, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(ROOT, 'template.png')

FONT_DIR = (
    '/Users/damirimohamed/Library/Application Support/Claude/'
    'local-agent-mode-sessions/skills-plugin/'
    'b8cb25d5-c215-4108-b879-6d249e22f86b/'
    '6d7cd525-1eac-4142-8a35-df9b90bd1ea1/skills/canvas-design/canvas-fonts'
)
FONT_BOLD = os.path.join(FONT_DIR, 'BricolageGrotesque-Bold.ttf')
FONT_REG  = os.path.join(FONT_DIR, 'Outfit-Regular.ttf')

# Accent colour per the pulse member category
CATEGORY_COLORS = {
    'entrepreneur': (0, 214, 143),     # mint #00D68F
    'startup':      (0, 214, 143),
    'investisseur': (99, 102, 241),    # indigo #6366F1
    'vc':           (99, 102, 241),
    'amic':         (99, 102, 241),
    'président':    (99, 102, 241),    # presidents of associations / VCs
    'president':    (99, 102, 241),
    'programme':    (245, 158, 11),    # amber  #F59E0B
    'incubateur':   (249, 115, 22),    # orange #F97316
    'accelerateur': (249, 115, 22),
    'talent':       (139, 92, 246),    # purple #8B5CF6
    'professionnel':(139, 92, 246),
    'expert':       (234, 88, 12),     # dark orange #EA580C
    'mentor':       (234, 88, 12),
}

def accent_for(role):
    """Map a role string to its category accent colour."""
    key = (role or '').lower()
    for tok, col in CATEGORY_COLORS.items():
        if tok in key:
            return col
    return (0, 214, 143)  # fallback mint


def detect_circle(template_img):
    """
    Coordinates calibrated for the 1250×1250 marketing template.
    If the template is swapped, re-measure once and update.
    """
    w, h = template_img.size
    if (w, h) == (1250, 1250):
        # cx, cy, inner radius — circle is smaller so name/role sit below it
        return (796, 555, 268)
    # Fallback proportional guess
    return (int(w * 0.70), int(h * 0.47), int(min(w, h) * 0.27))


def crop_square_center(img):
    w, h = img.size
    s = min(w, h)
    left = (w - s) // 2
    top  = (h - s) // 2
    return img.crop((left, top, left + s, top + s))


def fit_font_size(text, font_path, max_width, start=60, min_size=20):
    """Binary-searchless: shrink font until text fits max_width."""
    for size in range(start, min_size - 1, -2):
        f = ImageFont.truetype(font_path, size)
        bbox = f.getbbox(text)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            return f
    return ImageFont.truetype(font_path, min_size)


def compose(photo_path, out_path, full_name, role):
    accent = accent_for(role)
    accent_rgba = accent + (255,)
    template = Image.open(TEMPLATE).convert('RGBA')
    W, H = template.size

    # New (smaller) circle position — leaves room for text below
    cx, cy, r = detect_circle(template)
    print(f"Using circle: center=({cx},{cy})  radius={r}")

    # Also need the ORIGINAL template circle so we can mask out its
    # landscape illustration (which would otherwise leak around our
    # smaller photo).
    ORIG_CX, ORIG_CY, ORIG_R = 796, 627, 363

    # --- Step 1: Mask out the original landscape --------------------
    # Paint the original circle area with the background colour, so the
    # sky / grass / original border ring all disappear.
    BG = (7, 11, 18, 255)  # --bg-primary from the site
    cover = Image.new('RGBA', template.size, (0, 0, 0, 0))
    ImageDraw.Draw(cover).ellipse(
        (ORIG_CX - ORIG_R - 4, ORIG_CY - ORIG_R - 4,
         ORIG_CX + ORIG_R + 4, ORIG_CY + ORIG_R + 4),
        fill=BG,
    )
    out = Image.alpha_composite(template, cover)

    # --- Step 2: Prepare photo → circular crop --------------------------
    photo = Image.open(photo_path).convert('RGBA')
    photo = crop_square_center(photo)
    d = r * 2
    photo = photo.resize((d, d), Image.LANCZOS)
    mask = Image.new('L', (d, d), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, d, d), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(0.8))
    photo_layer = Image.new('RGBA', template.size, (0, 0, 0, 0))
    photo_layer.paste(photo, (cx - r, cy - r), mask)
    out = Image.alpha_composite(out, photo_layer)

    # --- Step 3: Redraw border ring around new circle (category color)-
    ring = Image.new('RGBA', template.size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    for i, alpha in [(7, 40), (5, 80), (3, 140), (1, 220)]:
        rd.ellipse((cx - r - i, cy - r - i, cx + r + i, cy + r + i),
                   outline=accent + (alpha,), width=2)
    rd.ellipse((cx - r, cy - r, cx + r, cy + r),
               outline=accent_rgba, width=3)
    out = Image.alpha_composite(out, ring)

    # --- Step 4: Text BELOW the circle ---------------------------------
    draw = ImageDraw.Draw(out)
    max_text_w = int(d * 1.0)
    name_font = fit_font_size(full_name, FONT_BOLD, max_text_w, start=64, min_size=28)
    role_font = fit_font_size(role,       FONT_REG,  max_text_w, start=34, min_size=18)

    nb = name_font.getbbox(full_name)
    rb = role_font.getbbox(role)
    name_h = nb[3] - nb[1]
    role_h = rb[3] - rb[1]
    gap = 14

    # Anchor: 28px below the circle bottom
    circle_bottom = cy + r
    name_y = circle_bottom + 28
    role_y = name_y + name_h + gap

    name_x = cx - (nb[2] - nb[0]) // 2 - nb[0]
    role_x = cx - (rb[2] - rb[0]) // 2 - rb[0]

    draw.text((name_x, name_y), full_name, font=name_font, fill=(238, 242, 255, 255))
    draw.text((role_x, role_y), role, font=role_font, fill=accent_rgba)

    out.convert('RGB').save(out_path, 'PNG', optimize=True)
    print(f"Wrote {out_path}")
    return out_path


def _pad_to(img, W, H, offset_x, offset_y):
    """Place a smaller image onto a transparent canvas of size (W, H)."""
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    canvas.paste(img, (offset_x, offset_y), img)
    return canvas


if __name__ == '__main__':
    if len(sys.argv) >= 5:
        photo, out, name, role = sys.argv[1:5]
    else:
        photo = '/Users/damirimohamed/Desktop/Github/ThePulsePlateform/static/images/founders/SimoDamiri.jpeg'
        out   = os.path.join(ROOT, 'badge_simo.png')
        name  = 'Simohammed Damiri'
        role  = 'Founder & CEO, Nessiam'
    compose(photo, out, name, role)
