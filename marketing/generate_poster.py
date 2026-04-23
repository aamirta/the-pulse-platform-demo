"""
The Pulse — A4 marketing poster
Aligned with the site's existing brand system (dark mode palette):
  bg #070B12, text #EEF2FF, accent #00D68F (mint), secondary #6366F1, tertiary #F59E0B.
  Typography: BricolageGrotesque (≈ Syne), Outfit (≈ DM Sans), GeistMono.
  Wordmark: embedded thepulse-blanc.png (white logo on transparent).

Output: the_pulse_poster.pdf
"""
import math
import random
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import Color, HexColor
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

# --- Fonts --------------------------------------------------------------
FONT_DIR = (
    "/Users/damirimohamed/Library/Application Support/Claude/"
    "local-agent-mode-sessions/skills-plugin/"
    "b8cb25d5-c215-4108-b879-6d249e22f86b/"
    "6d7cd525-1eac-4142-8a35-df9b90bd1ea1/skills/canvas-design/canvas-fonts"
)

pdfmetrics.registerFont(TTFont("Bricolage",      f"{FONT_DIR}/BricolageGrotesque-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Bricolage-Bold", f"{FONT_DIR}/BricolageGrotesque-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Outfit",         f"{FONT_DIR}/Outfit-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Outfit-Bold",    f"{FONT_DIR}/Outfit-Bold.ttf"))
pdfmetrics.registerFont(TTFont("GeistMono",      f"{FONT_DIR}/GeistMono-Regular.ttf"))
pdfmetrics.registerFont(TTFont("GeistMono-Bold", f"{FONT_DIR}/GeistMono-Bold.ttf"))

# --- Palette (from static/css/base.css :root dark mode) -----------------
BG          = HexColor("#070B12")   # --bg-primary
BG_CARD     = HexColor("#0D1420")   # --bg-card
TEXT        = HexColor("#EEF2FF")   # --text-primary
TEXT_DIM    = HexColor("#7A90B0")   # --text-secondary
TEXT_MUTED  = HexColor("#3D5270")   # --text-muted
BORDER      = HexColor("#1A2535")   # --border-primary
ACCENT      = HexColor("#00D68F")   # --accent (mint)
ACCENT_SOFT = Color(0.0, 0.839, 0.561, alpha=0.25)
SECONDARY   = HexColor("#6366F1")   # --secondary (indigo)
TERTIARY    = HexColor("#F59E0B")   # --tertiary (amber)
TEXT_FAINT  = Color(0.933, 0.949, 1.0, alpha=0.10)
GRID        = Color(1, 1, 1, alpha=0.04)   # --chart-grid

# --- Canvas -------------------------------------------------------------
W, H = A4  # 595.28 × 841.89 pt
OUT = "/Users/damirimohamed/Desktop/Github/ThePulsePlateform/marketing/the_pulse_poster.pdf"
LOGO = "/Users/damirimohamed/Desktop/Github/ThePulsePlateform/static/images/thepulse-blanc.png"
c = canvas.Canvas(OUT, pagesize=A4)

# Background
c.setFillColor(BG)
c.rect(0, 0, W, H, fill=1, stroke=0)

# Subtle dot-matrix background (echoes the site's card pattern) ----------
c.setFillColor(BORDER)
dot_step = 22
r = 0.55
for y in range(20, int(H), dot_step):
    for x in range(20, int(W), dot_step):
        c.circle(x, y, r, stroke=0, fill=1)

# Subtle radial mint glow near top (like --gradient-mesh) ----------------
# reportlab has no true radial gradient; approximate with stacked discs.
for i, alpha in enumerate([0.05, 0.035, 0.022, 0.012]):
    c.setFillColor(Color(0, 0.839, 0.561, alpha=alpha))
    radius = 260 + i * 80
    c.circle(W / 2, H - 170, radius, stroke=0, fill=1)

# --- Margins ------------------------------------------------------------
MARGIN_X = 44
MARGIN_Y = 44
GUTTER = W - 2 * MARGIN_X

# --- Top rail -----------------------------------------------------------
c.setStrokeColor(BORDER)
c.setLineWidth(0.6)
c.line(MARGIN_X, H - 60, W - MARGIN_X, H - 60)

c.setFillColor(TEXT_DIM)
c.setFont("GeistMono", 7.5)
c.drawString(MARGIN_X, H - 52, "THEPULSE.MA / MARKETING")
c.drawRightString(W - MARGIN_X, H - 52, "ÉDITION 01  ·  AVRIL 2026")

# --- Logo ---------------------------------------------------------------
# thepulse-blanc.png is 1536×1024 (aspect 1.5:1). The wordmark occupies
# roughly the center ~60% of the image width. Place a generous version.
logo_img = ImageReader(LOGO)
iw, ih = logo_img.getSize()
target_w = 300  # pt
target_h = target_w * ih / iw
c.drawImage(
    LOGO,
    (W - target_w) / 2, H - 90 - target_h,
    width=target_w, height=target_h,
    mask="auto",
)

# --- Tagline ------------------------------------------------------------
c.setFillColor(TEXT)
c.setFont("Bricolage-Bold", 26)
tagline = "Le battement de l'écosystème"
t1w = pdfmetrics.stringWidth(tagline, "Bricolage-Bold", 26)
TAG_Y = H - 260
c.drawString((W - t1w) / 2, TAG_Y, tagline)

c.setFillColor(ACCENT)
tagline2 = "startup marocain."
t2w = pdfmetrics.stringWidth(tagline2, "Bricolage-Bold", 26)
c.drawString((W - t2w) / 2, TAG_Y - 30, tagline2)

# Tiny eyebrow label above the tagline
def draw_centered_tracked(text, cx, y, font, size, tracking, fill):
    c.setFont(font, size)
    c.setFillColor(fill)
    widths = [pdfmetrics.stringWidth(ch, font, size) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, widths):
        c.drawString(x, y, ch)
        x += w + tracking

draw_centered_tracked(
    "OBSERVATOIRE · FOUNDERS · STARTUPS · INVESTISSEURS",
    W / 2, H - 218, "GeistMono", 7.5, 1.8, TEXT_DIM
)

# --- Signal band --------------------------------------------------------
SIG_CENTER_Y = H - 432
SIG_LEFT = MARGIN_X + 4
SIG_RIGHT = W - MARGIN_X - 4
signal_span = SIG_RIGHT - SIG_LEFT
BASE = SIG_CENTER_Y

# Frame (thin top/bottom rules)
c.setStrokeColor(BORDER)
c.setLineWidth(0.5)
BAND_TOP = SIG_CENTER_Y + 90
BAND_BOT = SIG_CENTER_Y - 90
c.line(SIG_LEFT, BAND_TOP, SIG_RIGHT, BAND_TOP)
c.line(SIG_LEFT, BAND_BOT, SIG_RIGHT, BAND_BOT)

# Plate caption (top of band)
c.setFillColor(TEXT_DIM)
c.setFont("GeistMono", 6.8)
c.drawString(SIG_LEFT, BAND_TOP + 6, "FIG. 01")
c.drawRightString(SIG_RIGHT, BAND_TOP + 6, "RELEVÉ — ÉCHANTILLON T1 2026")

# Subtle dense tick grid on baseline
c.setStrokeColor(GRID)
c.setLineWidth(0.35)
x = SIG_LEFT
i = 0
tick_step = 6
while x <= SIG_RIGHT:
    major = (i % 10 == 0)
    h = 5 if major else 2
    c.line(x, BASE - h, x, BASE + h)
    x += tick_step
    i += 1

# Axis labels
c.setFillColor(TEXT_MUTED)
c.setFont("GeistMono", 6.2)
for yoff, lbl in [(62, "+σ"), (0, " 0"), (-62, "−σ")]:
    c.drawRightString(SIG_LEFT - 4, BASE + yoff - 2, lbl)

# --- Waveform ----------------------------------------------------------
random.seed(11)

def build_signal_points(peaks):
    pts = []
    n = 560
    peak_width = 0.022
    for i in range(n + 1):
        t = i / n
        xp = SIG_LEFT + t * signal_span
        # Baseline gentle wander
        y = BASE + math.sin(t * 18.0) * 2.2 + (random.random() - 0.5) * 1.5
        # Add peaks (ECG QRS-style)
        for pcx, ph in peaks:
            d = t - pcx
            if abs(d) < peak_width * 3:
                spike = math.exp(-(d * d) / (2 * (peak_width * 0.50) ** 2))
                y += spike * ph
                # small post-peak dip
                if d > peak_width * 0.6:
                    y -= math.exp(-((d - peak_width * 1.1) ** 2) / (2 * (peak_width * 0.5) ** 2)) * ph * 0.10
        pts.append((xp, y))
    return pts

# Three peaks at 22%, 50%, 78%, heights vary for visual rhythm
peaks = [(0.22, 56), (0.50, 74), (0.78, 60)]
pts = build_signal_points(peaks)

# Draw the pulse line — mint accent, matching the logo's ECG trail
c.setStrokeColor(ACCENT)
c.setLineWidth(1.4)
c.setLineCap(1)
c.setLineJoin(1)
p = c.beginPath()
p.moveTo(*pts[0])
for pt in pts[1:]:
    p.lineTo(*pt)
c.drawPath(p, stroke=1, fill=0)

# Soft glow — draw a second wider stroke at low alpha underneath
# (approximated by a few parallel strokes at decreasing opacity)
# reportlab lacks stroke alpha per-op, so we layered ACCENT_SOFT beforehand
# via a pre-pass:
# (we'll add the glow pass next — but rendered BEFORE the main line ideally)

# --- Peak metric pins ---------------------------------------------------
peak_positions = [0.22, 0.50, 0.78]
peak_labels = [
    ("2 014", "STARTUPS"),
    ("1 334", "FONDATEURS"),
    ("143",   "SECTEURS"),
]

for (tx, (num, lab)) in zip(peak_positions, peak_labels):
    xp = SIG_LEFT + tx * signal_span
    # get exact peak y by sampling
    idx = int(len(pts) * tx)
    window = pts[max(0, idx - 4): idx + 4]
    yp = max(window, key=lambda q: q[1])[1] if window else BASE

    # vertical tick under peak — thin mint dashed line
    c.setStrokeColor(ACCENT)
    c.setDash(1.6, 2.2)
    c.setLineWidth(0.7)
    c.line(xp, yp + 2, xp, BASE - 72)
    c.setDash()  # reset

    # dot at peak
    c.setFillColor(ACCENT)
    c.circle(xp, yp, 2.6, stroke=0, fill=1)

    # Mint halo ring
    c.setStrokeColor(ACCENT_SOFT)
    c.setLineWidth(1.2)
    c.circle(xp, yp, 7, stroke=1, fill=0)

    # Big metric number — Bricolage Bold
    c.setFillColor(TEXT)
    c.setFont("Bricolage-Bold", 38)
    nw = pdfmetrics.stringWidth(num, "Bricolage-Bold", 38)
    c.drawString(xp - nw / 2, BASE - 110, num)

    # Small label in mono
    draw_centered_tracked(lab, xp, BASE - 128, "GeistMono", 7.2, 2.0, ACCENT)

# --- Value props --------------------------------------------------------
VP_Y = BASE - 190

# divider line
c.setStrokeColor(BORDER)
c.setLineWidth(0.5)
c.line(MARGIN_X, VP_Y + 26, W - MARGIN_X, VP_Y + 26)

vp_cols = [
    ("01",  "CONNECTER",   "Fondateurs, investisseurs,\ntalents et experts — réunis."),
    ("02",  "DÉCOUVRIR",   "Cartographier startups,\nsecteurs et opportunités."),
    ("03",  "FAIRE CROÎTRE", "Lever, recruter, s'entourer.\nL'écosystème répond."),
]
col_w = GUTTER / 3
for i, (num, head, body) in enumerate(vp_cols):
    cx = MARGIN_X + col_w * (i + 0.5)

    # Number pill
    c.setFillColor(ACCENT)
    c.setFont("GeistMono-Bold", 9)
    c.drawString(cx - pdfmetrics.stringWidth(num, "GeistMono-Bold", 9) / 2, VP_Y + 6, num)

    # Head (tracked uppercase)
    draw_centered_tracked(head, cx, VP_Y - 14, "Bricolage-Bold", 13, 1.4, TEXT)

    # Body (two short lines)
    c.setFillColor(TEXT_DIM)
    c.setFont("Outfit", 10)
    for j, line in enumerate(body.split("\n")):
        lw = pdfmetrics.stringWidth(line, "Outfit", 10)
        c.drawString(cx - lw / 2, VP_Y - 32 - j * 13, line)

# vertical micro-dividers
for i in (1, 2):
    xv = MARGIN_X + col_w * i
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.4)
    c.line(xv, VP_Y + 20, xv, VP_Y - 60)

# --- CTA ---------------------------------------------------------------
CTA_Y = 118
c.setStrokeColor(BORDER)
c.setLineWidth(0.5)
c.line(MARGIN_X, CTA_Y + 40, W - MARGIN_X, CTA_Y + 40)

# Left side
c.setFillColor(TEXT_DIM)
c.setFont("GeistMono", 7.5)
c.drawString(MARGIN_X, CTA_Y + 26, "REJOIGNEZ L'OBSERVATOIRE →")

# thepulse.ma pill-button
button_text = "thepulse.ma"
c.setFont("Bricolage-Bold", 24)
btw = pdfmetrics.stringWidth(button_text, "Bricolage-Bold", 24)
pad_x = 18
pad_y = 10
box_w = btw + pad_x * 2
box_h = 28 + pad_y
box_x = W - MARGIN_X - box_w
box_y = CTA_Y + 14

# Mint filled pill
c.setFillColor(ACCENT)
c.roundRect(box_x, box_y, box_w, box_h, 8, fill=1, stroke=0)

# Text on pill — use dark ink for contrast (brand accent on dark bg)
c.setFillColor(BG)
c.drawString(box_x + pad_x, box_y + pad_y + 4, button_text)

# Invitation line
c.setFillColor(TEXT)
c.setFont("Outfit", 12)
cta = "Inscrivez votre startup.  Enrichissez votre profil.  Entrez dans le signal."
cw = pdfmetrics.stringWidth(cta, "Outfit", 12)
c.drawString((W - cw) / 2, CTA_Y - 4, cta)

# --- Bottom colophon ---------------------------------------------------
c.setFillColor(TEXT_MUTED)
c.setFont("GeistMono", 6.5)
c.drawString(MARGIN_X, 46, "THE PULSE  ·  PLATEFORME DE L'ÉCOSYSTÈME STARTUP MAROCAIN")
c.drawRightString(W - MARGIN_X, 46, "RABAT — CASABLANCA — MARRAKECH   ·   MMXXVI")

# Bottom thin rule
c.setStrokeColor(BORDER)
c.setLineWidth(0.5)
c.line(MARGIN_X, 60, W - MARGIN_X, 60)

c.showPage()
c.save()
print(f"Wrote {OUT}")
