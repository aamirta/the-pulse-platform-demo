"""
Rapport J+8 - The Pulse
Bilan de lancement - Rapport partenaires
Généré le 13 avril 2026
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

W, H = A4  # 595 x 842

# ── Colors ──
ACCENT = HexColor("#00d4aa")
DARK = HexColor("#0f172a")
DARK2 = HexColor("#1e293b")
MUTED = HexColor("#64748b")
ORANGE = HexColor("#f97316")
PURPLE = HexColor("#8B5CF6")
BLUE = HexColor("#3B82F6")
RED = HexColor("#ef4444")
GREEN = HexColor("#22c55e")
WHITE = white
LIGHT_BG = HexColor("#f8fafc")
CARD_BG = HexColor("#f1f5f9")

IMG_DIR = os.path.join(os.path.dirname(__file__), "static", "images")
LOGO_DARK = os.path.join(IMG_DIR, "thepulse-noir.png")
LOGO_WHITE = os.path.join(IMG_DIR, "thepulse-blanc.png")
OUTPUT = os.path.join(os.path.dirname(__file__), "Rapport_J7_ThePulse_Partenaires.pdf")

# Partner logos
PARTNER_LOGOS = [
    (os.path.join(IMG_DIR, "um6p_logo.png"), "UM6P"),
    (os.path.join(IMG_DIR, "logo_omtpme-13.png"), "OMTPME"),
    (os.path.join(IMG_DIR, "tamwilcom_logo.png"), "Tamwilcom"),
    (os.path.join(IMG_DIR, "amic_logo.png"), "AMIC"),
    (os.path.join(IMG_DIR, "MTN LOGO.svg"), "MTN"),
]


def draw_rounded_rect(c, x, y, w, h, r, fill_color=None, stroke_color=None):
    """Draw a rounded rectangle."""
    p = c.beginPath()
    p.roundRect(x, y, w, h, r)
    p.close()
    if fill_color:
        c.setFillColor(fill_color)
    if stroke_color:
        c.setStrokeColor(stroke_color)
        c.setLineWidth(0.5)
        c.drawPath(p, fill=1 if fill_color else 0, stroke=1 if stroke_color else 0)
    else:
        c.drawPath(p, fill=1 if fill_color else 0, stroke=0)


def draw_kpi_card(c, x, y, w, h, value, label, color=ACCENT):
    """Draw a KPI card. y = bottom of card."""
    draw_rounded_rect(c, x, y, w, h, 8, fill_color=CARD_BG)
    # Accent bar top
    draw_rounded_rect(c, x, y + h - 4, w, 4, 2, fill_color=color)
    # Value
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(x + w/2, y + h - 35, str(value))
    # Label
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8.5)
    c.drawCentredString(x + w/2, y + 10, label)


def draw_table(c, x, y, headers, rows, col_widths, header_color=DARK):
    """Draw a styled table. Returns y position after table."""
    row_h = 20
    header_h = 24
    total_w = sum(col_widths)

    # Header
    draw_rounded_rect(c, x, y - header_h, total_w, header_h, 4, fill_color=header_color)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 8)
    cx = x
    for i, h in enumerate(headers):
        c.drawString(cx + 6, y - header_h + 8, h)
        cx += col_widths[i]

    # Rows
    ry = y - header_h
    for ri, row in enumerate(rows):
        ry -= row_h
        if ri % 2 == 0:
            draw_rounded_rect(c, x, ry, total_w, row_h, 0, fill_color=HexColor("#f8fafc"))
        c.setFillColor(DARK)
        c.setFont("Helvetica", 8)
        cx = x
        for i, cell in enumerate(row):
            if i == 0:
                c.setFont("Helvetica-Bold", 8)
            else:
                c.setFont("Helvetica", 8)
            c.drawString(cx + 6, ry + 6, str(cell))
            cx += col_widths[i]

    return ry


def draw_bar(c, x, y, w, h, pct, color=ACCENT, bg=CARD_BG):
    """Draw a progress bar."""
    draw_rounded_rect(c, x, y, w, h, h/2, fill_color=bg)
    if pct > 0:
        bar_w = max(h, w * pct)
        draw_rounded_rect(c, x, y, bar_w, h, h/2, fill_color=color)


def draw_page_header(c, title, right_text, margin=40):
    """Draw standard page header with logo and title bar."""
    # Header bar
    c.setFillColor(DARK)
    c.rect(0, H - 50, W, 50, fill=1, stroke=0)
    c.setFillColor(ACCENT)
    c.rect(0, H - 54, W, 4, fill=1, stroke=0)
    # Small logo in header
    try:
        logo = ImageReader(LOGO_DARK)
        c.drawImage(logo, margin, H - 42, width=60, height=21, mask='auto', preserveAspectRatio=True)
    except Exception:
        pass
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin + 70, H - 35, title)
    c.setFillColor(HexColor("#94a3b8"))
    c.setFont("Helvetica", 9)
    c.drawRightString(W - margin, H - 35, right_text)


def build_report():
    c = canvas.Canvas(OUTPUT, pagesize=A4)
    c.setTitle("The Pulse - Rapport J+8 Lancement")
    c.setAuthor("The Pulse - UM6P")
    c.setSubject("Bilan de lancement J+8 - Rapport partenaires")

    margin = 40
    content_w = W - 2 * margin

    # ══════════════════════════════════════════════════════════════════
    # PAGE 1 - COVER
    # ══════════════════════════════════════════════════════════════════
    c.setFillColor(DARK)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Accent line top
    c.setFillColor(ACCENT)
    c.rect(0, H - 6, W, 6, fill=1, stroke=0)

    # Logo - big centered
    try:
        logo = ImageReader(LOGO_WHITE)
        logo_w, logo_h = 260, 92
        c.drawImage(logo, (W - logo_w) / 2, H - 150, width=logo_w, height=logo_h, mask='auto', preserveAspectRatio=True)
    except Exception:
        pass

    # Title block
    y = H - 220
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 36)
    c.drawString(margin, y, "Rapport J+8")

    y -= 50
    c.setFont("Helvetica-Bold", 28)
    c.drawString(margin, y, "Bilan de Lancement")

    # Accent underline
    y -= 20
    c.setFillColor(ACCENT)
    c.rect(margin, y, 80, 4, fill=1, stroke=0)

    # Subtitle
    y -= 45
    c.setFillColor(HexColor("#94a3b8"))
    c.setFont("Helvetica", 14)
    c.drawString(margin, y, u"Plateforme de donn\u00e9es de l\u2019\u00e9cosyst\u00e8me startup marocain")

    # Date block
    y -= 60
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin, y, u"P\u00e9riode : 6 - 13 avril 2026")
    y -= 22
    c.setFillColor(HexColor("#94a3b8"))
    c.setFont("Helvetica", 11)
    c.drawString(margin, y, u"8 jours apr\u00e8s le lancement officiel")

    # ── Partner logos section ──
    y -= 60
    c.setFillColor(HexColor("#475569"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "Rapport partenaires")
    y -= 10
    c.setStrokeColor(HexColor("#1e293b"))
    c.setLineWidth(0.5)
    c.line(margin, y, W - margin, y)
    y -= 55

    # Draw partner logos in a row
    n_partners = len(PARTNER_LOGOS)
    logo_size = 40
    total_items = n_partners + 1  # +1 for MESC
    spacing = (content_w - total_items * logo_size) / (total_items - 1) if total_items > 1 else 0
    for i, (logo_path, name) in enumerate(PARTNER_LOGOS):
        lx = margin + i * (logo_size + spacing)
        try:
            plogo = ImageReader(logo_path)
            c.drawImage(plogo, lx, y, width=logo_size, height=logo_size, mask='auto', preserveAspectRatio=True)
        except Exception:
            c.setFillColor(HexColor("#94a3b8"))
            c.setFont("Helvetica-Bold", 7)
            c.drawString(lx, y + 15, name)
        c.setFillColor(HexColor("#64748b"))
        c.setFont("Helvetica", 6.5)
        c.drawCentredString(lx + logo_size / 2, y - 12, name)

    # MESC (no logo file, draw as styled box)
    mesc_x = margin + n_partners * (logo_size + spacing)
    draw_rounded_rect(c, mesc_x, y, logo_size, logo_size, 6, fill_color=PURPLE)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(mesc_x + logo_size / 2, y + 14, "M")
    c.setFillColor(HexColor("#64748b"))
    c.setFont("Helvetica", 6.5)
    c.drawCentredString(mesc_x + logo_size / 2, y - 12, "MESC")

    # Footer on cover
    c.setFillColor(HexColor("#475569"))
    c.setFont("Helvetica", 9)
    c.drawString(margin, 60, "The Pulse  |  UM6P  |  thepulse.ma")
    c.drawString(margin, 45, "Document confidentiel - Rapport partenaires")

    c.setStrokeColor(HexColor("#1e293b"))
    c.setLineWidth(0.5)
    c.line(margin, 80, W - margin, 80)

    c.showPage()

    # ══════════════════════════════════════════════════════════════════
    # PAGE 2 - VUE D'ENSEMBLE & BASE DE DONNÉES
    # ══════════════════════════════════════════════════════════════════
    c.setFillColor(LIGHT_BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    draw_page_header(c, u"1.  Vue d\u2019ensemble de la plateforme", "The Pulse  |  J+8", margin)

    y = H - 72

    # Section title
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, u"Base de donn\u00e9es \u00e9cosyst\u00e8me")
    y -= 14
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(margin, y, u"Donn\u00e9es collect\u00e9es, structur\u00e9es et mises en ligne sur thepulse.ma")

    y -= 20

    # KPI Cards - Row 1 (y = top of cards area, cards drawn below)
    card_w = (content_w - 3*12) / 4
    card_h = 58
    card_y = y - card_h  # bottom of cards
    draw_kpi_card(c, margin, card_y, card_w, card_h, "2 014", "STARTUPS", ACCENT)
    draw_kpi_card(c, margin + card_w + 12, card_y, card_w, card_h, "1 333", "FONDATEURS", PURPLE)
    draw_kpi_card(c, margin + 2*(card_w+12), card_y, card_w, card_h, "51", "INVESTISSEURS", BLUE)
    draw_kpi_card(c, margin + 3*(card_w+12), card_y, card_w, card_h, "$226.8M", u"FONDS LEV\u00c9S", ORANGE)

    y = card_y - 14

    # KPI Cards - Row 2
    card_y2 = y - card_h
    draw_kpi_card(c, margin, card_y2, card_w, card_h, "171", "TOURS DE TABLE", GREEN)
    draw_kpi_card(c, margin + card_w + 12, card_y2, card_w, card_h, "45", "INCUBATEURS", BLUE)
    draw_kpi_card(c, margin + 2*(card_w+12), card_y2, card_w, card_h, "1 265", "LIENS STARTUP-FONDATEUR", PURPLE)
    draw_kpi_card(c, margin + 3*(card_w+12), card_y2, card_w, card_h, "21", "RESSOURCES", MUTED)

    y = card_y2 - 25

    # Section: Données détaillées
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, u"D\u00e9tail de la base de donn\u00e9es")
    y -= 25

    headers = [u"CAT\u00c9GORIE", "NOMBRE", u"D\u00c9TAIL"]
    col_widths = [180, 80, content_w - 260]
    rows = [
        ["Startups", "2 014", u"R\u00e9pertoire complet des startups marocaines"],
        ["Fondateurs", "1 333", u"948 startups avec fondateur(s) identifi\u00e9(s)"],
        ["Investisseurs", "51", "Fonds d\u2019investissement actifs au Maroc"],
        [u"Incubateurs / Acc\u00e9l\u00e9rateurs", "45", "Programmes d\u2019accompagnement"],
        ["Tours de financement", "171", u"Lev\u00e9es de fonds document\u00e9es ($226.8M total)"],
        [u"Experts r\u00e9f\u00e9renc\u00e9s", "8", "Consultants et mentors"],
        ["Ressources", "21", "Guides, rapports, outils"],
        [u"Articles / Actualit\u00e9s", "9", u"Contenu \u00e9ditorial"],
        [u"Membres inscrits", "48", u"Entrepreneurs, investisseurs, experts, programmes"],
    ]
    y = draw_table(c, margin, y, headers, rows, col_widths)

    y -= 30
    c.setFillColor(MUTED)
    c.setFont("Helvetica-Oblique", 8.5)
    c.drawString(margin, y, u"* Enrichissement continu : scraping multi-sources + validation manuelle. Objectif : 100% des startups avec fondateur(s) identifi\u00e9(s).")

    c.showPage()

    # ══════════════════════════════════════════════════════════════════
    # PAGE 3 - ANALYTICS & TRAFIC
    # ══════════════════════════════════════════════════════════════════
    c.setFillColor(LIGHT_BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    draw_page_header(c, u"2.  Trafic & Audience  (Google Analytics)", "6 - 13 avril 2026", margin)

    y = H - 90

    # KPI row - Traffic
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, u"Indicateurs cl\u00e9s de trafic  (7 jours)")
    y -= 20

    card_w3 = (content_w - 2*12) / 3
    card_y = y - card_h
    draw_kpi_card(c, margin, card_y, card_w3, card_h, "2 665", "SESSIONS", ACCENT)
    draw_kpi_card(c, margin + card_w3 + 12, card_y, card_w3, card_h, "1 855", "UTILISATEURS ACTIFS", PURPLE)
    draw_kpi_card(c, margin + 2*(card_w3+12), card_y, card_w3, card_h, "1 748", "NOUVEAUX UTILISATEURS", BLUE)

    y = card_y - 14

    card_y2 = y - card_h
    draw_kpi_card(c, margin, card_y2, card_w3, card_h, "57,7%", "TAUX D\u2019ENGAGEMENT", GREEN)
    draw_kpi_card(c, margin + card_w3 + 12, card_y2, card_w3, card_h, "1m 34s", u"DUR\u00c9E MOY. SESSION", ORANGE)
    draw_kpi_card(c, margin + 2*(card_w3+12), card_y2, card_w3, card_h, "30 683", u"\u00c9V\u00c9NEMENTS", MUTED)

    y = card_y2 - 25

    # Sources d'acquisition
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Sources d\u2019acquisition")
    y -= 25

    channels = [
        ("Direct", 1378, 51.7, ACCENT),
        ("Recherche organique (Google)", 1063, 39.9, PURPLE),
        (u"R\u00e9seaux sociaux (LinkedIn)", 114, 4.3, BLUE),
        ("Referrals (Medias24, etc.)", 63, 2.4, ORANGE),
        ("Autres", 47, 1.8, MUTED),
    ]
    bar_w = content_w - 200
    for label, count, pct, color in channels:
        c.setFillColor(DARK)
        c.setFont("Helvetica", 9)
        c.drawString(margin, y + 2, label)
        draw_bar(c, margin + 180, y, bar_w, 14, pct / 100, color)
        c.setFillColor(MUTED)
        c.setFont("Helvetica-Bold", 8)
        c.drawRightString(W - margin, y + 2, f"{count} ({pct}%)")
        y -= 22

    y -= 20

    # Géographie
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, u"R\u00e9partition g\u00e9ographique des utilisateurs")
    y -= 25

    headers = ["PAYS", "UTILISATEURS", "PART", "TAUX ENGAGEMENT", u"DUR\u00c9E MOY."]
    col_widths = [140, 90, 70, 110, content_w - 410]
    rows = [
        ["Maroc", "1 440", "77,6%", "55,2%", "2m 18s"],
        ["France", "151", "8,1%", "61,5%", "1m 42s"],
        [u"\u00c9tats-Unis", "56", "3,0%", "35,8%", "36s"],
        ["Canada", "33", "1,8%", "59,4%", "1m 04s"],
        ["Pays-Bas", "19", "1,0%", "76,1%", "3m 10s"],
        ["Royaume-Uni", "14", "0,8%", "56,3%", "33s"],
        ["Allemagne", "11", "0,6%", "60,0%", "1m 51s"],
        ["Espagne", "3", "0,2%", "50,0%", "45s"],
    ]
    y = draw_table(c, margin, y, headers, rows, col_widths)

    y -= 25
    c.setFillColor(MUTED)
    c.setFont("Helvetica-Oblique", 8.5)
    c.drawString(margin, y, u"Source : Google Analytics (G-9TTHWMF6L0) - P\u00e9riode du 6 au 13 avril 2026")

    c.showPage()

    # ══════════════════════════════════════════════════════════════════
    # PAGE 4 - PAGES & ENGAGEMENT
    # ══════════════════════════════════════════════════════════════════
    c.setFillColor(LIGHT_BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    draw_page_header(c, u"3.  Pages les plus visit\u00e9es & Engagement", "6 - 13 avril 2026", margin)

    y = H - 85

    # Top Pages
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, u"Pages les plus consult\u00e9es")
    y -= 25

    headers = ["PAGE", "VUES", "UTILISATEURS", "REBOND", "VS MOYENNE*"]
    col_widths = [170, 60, 80, 70, content_w - 380]
    rows = [
        [u"R\u00e9pertoire Startups", "3 067", "690", "18,5%", u"\u25b2 Page #1"],
        ["Page d\u2019accueil", "1 892", "1 310", "35,2%", "Rebond moyen"],
        ["Rejoindre The Pulse", "1 010", "725", "17,9%", u"\u25b2 Fort int\u00e9r\u00eat"],
        [u"R\u00e9pertoire Fondateurs", "576", "215", "11,0%", u"\u25b2 Tr\u00e8s engag\u00e9"],
        [u"R\u00e9pertoire Investisseurs", "403", "176", "10,1%", u"\u25b2 Tr\u00e8s engag\u00e9"],
        ["Se connecter", "302", "240", "12,8%", u"\u25b2 Engag\u00e9"],
        ["Co-Fondateurs", "282", "195", "9,2%", u"\u25b2\u25b2 Excellent"],
    ]
    y = draw_table(c, margin, y, headers, rows, col_widths)

    y -= 8
    c.setFillColor(MUTED)
    c.setFont("Helvetica-Oblique", 7)
    c.drawString(margin, y, u"* Moyenne taux de rebond SaaS B2B : 40-60% (source : CXL / Contentsquare 2025). The Pulse est largement en dessous.")

    y -= 25

    # Tendance des visites (J1→J7)
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, u"Tendance des visites (J1 \u2192 J8)")
    y -= 22

    trend_days = [
        ("J1 (6 avr)", 180, MUTED),
        ("J2 (7 avr)", 220, MUTED),
        ("J3 (8 avr)", 290, BLUE),
        ("J4 (9 avr)", 520, ACCENT),
        ("J5 (10 avr)", 480, ACCENT),
        ("J6 (11 avr)", 410, BLUE),
        ("J7 (12 avr)", 341, BLUE),
        ("J8 (13 avr)", 224, MUTED),
    ]
    bar_max_val = 520
    bar_w_trend = content_w - 180
    for label, sessions, clr in trend_days:
        c.setFillColor(DARK)
        c.setFont("Helvetica", 8)
        c.drawString(margin, y + 2, label)
        ratio = sessions / bar_max_val
        draw_bar(c, margin + 90, y, bar_w_trend, 13, ratio, clr)
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawRightString(W - margin, y + 2, f"{sessions} sess.")
        y -= 19

    y -= 8
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin, y, u"\u25b2 Pic J4 (9 avril) : +189% vs J1 \u2014 effet du lancement LinkedIn + partage communaut\u00e9")

    y -= 20

    # Key insight box
    draw_rounded_rect(c, margin, y - 46, content_w, 46, 8, fill_color=HexColor("#ecfdf5"))
    draw_rounded_rect(c, margin, y - 46, 4, 46, 2, fill_color=ACCENT)
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin + 16, y - 15, u"Point cl\u00e9")
    c.setFont("Helvetica", 8.5)
    c.setFillColor(HexColor("#334155"))
    c.drawString(margin + 16, y - 30, u"Taux de rebond moyen de 16,6% vs 40-60% pour un SaaS B2B \u2014 les visiteurs explorent activement.")
    c.drawString(margin + 16, y - 42, u"48 inscriptions en 8 jours avec un pic \u00e0 J4. Le r\u00e9pertoire Startups concentre 36% des vues.")

    c.showPage()

    # ══════════════════════════════════════════════════════════════════
    # PAGE 5 - COMMUNAUTÉ & INSCRITS
    # ══════════════════════════════════════════════════════════════════
    c.setFillColor(LIGHT_BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    draw_page_header(c, u"4.  Communaut\u00e9 & Membres inscrits", "Au 13 avril 2026", margin)

    y = H - 90

    # KPIs inscrits
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, u"Inscriptions \u00e0 la plateforme")
    y -= 20

    card_w4 = (content_w - 3*12) / 4
    card_y = y - card_h
    draw_kpi_card(c, margin, card_y, card_w4, card_h, "48", "INSCRITS TOTAL", ACCENT)
    draw_kpi_card(c, margin + card_w4 + 12, card_y, card_w4, card_h, "22", u"CONFIRM\u00c9S", GREEN)
    draw_kpi_card(c, margin + 2*(card_w4+12), card_y, card_w4, card_h, "26", "EN ATTENTE", ORANGE)
    draw_kpi_card(c, margin + 3*(card_w4+12), card_y, card_w4, card_h, "11", "AVEC PHOTO", PURPLE)

    y = card_y - 25

    # Répartition par rôle
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, u"R\u00e9partition par r\u00f4le")
    y -= 25

    roles = [
        ("Entrepreneurs", 35, 72.9, ACCENT),
        ("Investisseurs", 5, 10.4, BLUE),
        ("Experts", 5, 10.4, PURPLE),
        ("Programmes / Incubateurs", 3, 6.3, ORANGE),
    ]
    bar_w = content_w - 220
    for label, count, pct, color in roles:
        c.setFillColor(DARK)
        c.setFont("Helvetica", 9.5)
        c.drawString(margin, y + 2, label)
        draw_bar(c, margin + 180, y, bar_w, 14, pct / 100, color)
        c.setFillColor(MUTED)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawRightString(W - margin, y + 2, f"{count} ({pct}%)")
        y -= 24

    y -= 20

    # Inscriptions par jour
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Inscriptions par jour")
    y -= 25

    days = [
        ("6 avril (lancement)", 0),
        ("7 avril", 0),
        ("8 avril", 0),
        ("9 avril", 29),
        ("10 avril", 8),
        ("11 avril", 4),
        ("12 avril", 3),
        ("13 avril", 4),
    ]
    max_val = max(d[1] for d in days)
    bar_w = content_w - 200
    for label, count in days:
        c.setFillColor(DARK)
        c.setFont("Helvetica", 9)
        c.drawString(margin, y + 2, label)
        pct = count / max_val if max_val > 0 else 0
        color = ACCENT if count > 0 else CARD_BG
        draw_bar(c, margin + 160, y, bar_w, 14, pct, color)
        if count > 0:
            c.setFillColor(DARK)
            c.setFont("Helvetica-Bold", 8.5)
            c.drawRightString(W - margin, y + 2, str(count))
        y -= 20

    y -= 25

    # Engagement communautaire
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Engagement communautaire")
    y -= 25

    headers = ["INDICATEUR", "VALEUR", "COMMENTAIRE"]
    col_widths = [180, 80, content_w - 260]
    rows = [
        [u"Messages directs \u00e9chang\u00e9s", "10", "Messagerie interne entre membres"],
        ["Publications newsfeed", "14", u"Posts de la communaut\u00e9"],
        ["Projets co-fondateur", "6", "Recherches de co-fondateurs actives"],
        ["Membres avec mot de passe", "8", u"Comptes pleinement activ\u00e9s"],
    ]
    y = draw_table(c, margin, y, headers, rows, col_widths)

    y -= 20

    # CTA box for partners
    draw_rounded_rect(c, margin, y - 42, content_w, 42, 8, fill_color=PURPLE)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin + 16, y - 16, u"\U0001f91d  Appel aux partenaires")
    c.setFillColor(HexColor("#e8daff"))
    c.setFont("Helvetica", 9)
    c.drawString(margin + 16, y - 32, u"Aidez-nous \u00e0 promouvoir The Pulse ! Partagez la plateforme avec vos r\u00e9seaux, startups et communaut\u00e9s.")

    c.showPage()

    # ══════════════════════════════════════════════════════════════════
    # PAGE 6 - FONCTIONNALITÉS DÉPLOYÉES DEPUIS LE LANCEMENT
    # ══════════════════════════════════════════════════════════════════
    c.setFillColor(LIGHT_BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    draw_page_header(c, u"5.  Fonctionnalit\u00e9s d\u00e9ploy\u00e9es depuis le lancement", "6 - 13 avril 2026", margin)

    y = H - 80

    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, u"Nouvelles fonctionnalit\u00e9s mises en production")
    y -= 14
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(margin, y, u"Plus de 15 fonctionnalit\u00e9s majeures livr\u00e9es en 8 jours pour transformer la plateforme en r\u00e9seau actif.")
    y -= 22

    # Feature categories
    features = [
        (u"Comptes & Profils membres", PURPLE, [
            (u"Cr\u00e9ation de compte", u"Inscription via formulaires d\u00e9di\u00e9s (entrepreneurs, investisseurs, experts, programmes)."),
            (u"Profils enrichis", u"Photo, bio, LinkedIn, comp\u00e9tences, disponibilit\u00e9, langues, r\u00e9alisations."),
            (u"\u00c9dition & mot de passe", u"Modification des infos, changement de photo, gestion du mot de passe."),
            (u"Badge \u00ab New Pulser \u00bb", u"Badge visuel sur les nouveaux membres pour dynamiser la communaut\u00e9."),
        ]),
        (u"Interactions & Communaut\u00e9", ACCENT, [
            (u"Envoi de Pulses", u"Bouton \u00ab Envoyer un Pulse \u00bb pour initier un contact avec un autre membre."),
            (u"Messagerie instantan\u00e9e (Inbox)", u"Conversations 1-to-1 entre membres, avec compteur de messages non lus."),
            (u"Newsfeed communautaire", u"Publications, annonces, opportunit\u00e9s \u2014 posts avec images, likes et commentaires."),
            (u"Projets co-fondateur", u"Espace d\u00e9di\u00e9 pour publier et trouver des opportunit\u00e9s de co-fondation."),
        ]),
        (u"R\u00e9pertoires & D\u00e9couverte", BLUE, [
            (u"Talent Marketplace", u"Nouveau r\u00e9pertoire des talents et professionnels disponibles pour les startups."),
            (u"R\u00e9pertoire Experts", u"Consultants et mentors r\u00e9f\u00e9renc\u00e9s avec domaines d\u2019expertise."),
            (u"Filtres avanc\u00e9s", u"Secteur, stade, g\u00e9ographie, disponibilit\u00e9 \u2014 applicables \u00e0 tous les r\u00e9pertoires."),
            (u"Toolbox IA", u"Suite d\u2019outils IA pour les entrepreneurs (analyses, rapports, aide \u00e0 la d\u00e9cision)."),
        ]),
        (u"Administration & Op\u00e9rations", ORANGE, [
            (u"Dashboard admin Pulsers", u"Gestion compl\u00e8te des membres : recherche, filtres, \u00e9dition, confirmation, suppression."),
            (u"Actions en masse", u"Confirmer ou supprimer plusieurs comptes en une action."),
            (u"Statistiques temps r\u00e9el", u"Barre de stats (total, confirm\u00e9s, en attente, avec photo) mise \u00e0 jour dynamiquement."),
            (u"Scrapers d\u2019enrichissement", u"Scripts automatis\u00e9s (DuckDuckGo, LinkedIn) pour enrichir la base fondateurs."),
        ]),
    ]

    col_w = (content_w - 16) / 2
    col_positions = [margin, margin + col_w + 16]
    col_y = [y, y]

    for idx, (cat_title, cat_color, items) in enumerate(features):
        col = idx % 2
        cx = col_positions[col]
        cy = col_y[col]

        # Category header
        draw_rounded_rect(c, cx, cy - 22, col_w, 22, 4, fill_color=cat_color)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawString(cx + 10, cy - 15, cat_title)
        cy -= 30

        # Items
        for title, desc in items:
            # Bullet
            c.setFillColor(cat_color)
            c.circle(cx + 6, cy + 4, 2.5, fill=1, stroke=0)
            c.setFillColor(DARK)
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(cx + 14, cy, title)
            cy -= 11
            # Description (wrapped)
            c.setFillColor(HexColor("#475569"))
            c.setFont("Helvetica", 7.5)
            text = desc
            max_chars = 58
            while text:
                if len(text) <= max_chars:
                    c.drawString(cx + 14, cy, text)
                    cy -= 10
                    break
                cut = text[:max_chars].rfind(' ')
                if cut == -1:
                    cut = max_chars
                c.drawString(cx + 14, cy, text[:cut])
                cy -= 10
                text = text[cut:].strip()
            cy -= 4

        col_y[col] = cy - 10

    # Footer note
    y = min(col_y) - 10
    if y < 80:
        y = 80
    draw_rounded_rect(c, margin, y - 36, content_w, 36, 6, fill_color=HexColor("#ecfdf5"))
    draw_rounded_rect(c, margin, y - 36, 4, 36, 2, fill_color=ACCENT)
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin + 16, y - 14, u"Roadmap J+30")
    c.setFillColor(HexColor("#334155"))
    c.setFont("Helvetica", 8.5)
    c.drawString(margin + 16, y - 28, u"Notifications push, v\u00e9rification LinkedIn automatique, matching intelligent fondateurs \u2194 investisseurs, rapports publics.")

    c.showPage()

    # ══════════════════════════════════════════════════════════════════
    # PAGE 7 - SYNTHÈSE & PROCHAINES ÉTAPES
    # ══════════════════════════════════════════════════════════════════
    c.setFillColor(LIGHT_BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    draw_page_header(c, u"6.  Synth\u00e8se & Prochaines \u00e9tapes", "Perspectives J+30", margin)


    y = H - 90

    # Synthèse
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, u"Synth\u00e8se J+8")
    y -= 25

    highlights = [
        ("Audience forte", u"1 855 utilisateurs actifs et 2 665 sessions en 8 jours, principalement depuis le Maroc (78%)."),
        ("Acquisition organique", u"39,6% du trafic provient de la recherche Google, signe d\u2019un bon r\u00e9f\u00e9rencement naturel."),
        (u"Engagement \u00e9lev\u00e9", u"57,7% de taux d\u2019engagement (vs. 40% moyenne secteur) et 48 inscriptions effectives en 8 jours."),
        (u"Communaut\u00e9 naissante", u"48 membres inscrits dont 35 entrepreneurs, 5 investisseurs, 5 experts et 3 programmes."),
        (u"Base de donn\u00e9es riche", u"2 014 startups, 1 333 fondateurs, 51 investisseurs, 171 tours de financement document\u00e9s."),
        ("Rayonnement international", u"Visiteurs de 8+ pays, avec une diaspora active (France 8,5%, USA 3,2%, Canada 1,8%)."),
    ]
    for title, desc in highlights:
        c.setFillColor(ACCENT)
        c.circle(margin + 6, y + 4, 3, fill=1, stroke=0)
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawString(margin + 18, y, title)
        c.setFillColor(HexColor("#475569"))
        c.setFont("Helvetica", 8.5)
        text = desc
        max_chars = 95
        lines = []
        while text:
            if len(text) <= max_chars:
                lines.append(text)
                break
            idx = text[:max_chars].rfind(' ')
            if idx == -1:
                idx = max_chars
            lines.append(text[:idx])
            text = text[idx:].strip()
        for line in lines:
            y -= 14
            c.drawString(margin + 18, y, line)
        y -= 22

    y -= 10

    # Axes d'amélioration
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, u"Axes d\u2019am\u00e9lioration identifi\u00e9s")
    y -= 25

    improvements = [
        u"Activation des 26 comptes en attente de confirmation (54% des inscrits)",
        u"Enrichissement fondateurs : 1 068 startups sans fondateur identifi\u00e9 (objectif : -50% \u00e0 J+30)",
        u"Augmentation du contenu \u00e9ditorial et des publications communautaires",
        u"D\u00e9ploiement d\u2019une strat\u00e9gie d\u2019acquisition sur LinkedIn et les r\u00e9seaux sociaux",
    ]
    for imp in improvements:
        c.setFillColor(ORANGE)
        c.circle(margin + 6, y + 4, 3, fill=1, stroke=0)
        c.setFillColor(HexColor("#475569"))
        c.setFont("Helvetica", 9)
        lines = []
        text = imp
        max_chars = 100
        while text:
            if len(text) <= max_chars:
                lines.append(text)
                break
            idx = text[:max_chars].rfind(' ')
            if idx == -1:
                idx = max_chars
            lines.append(text[:idx])
            text = text[idx:].strip()
        for i, line in enumerate(lines):
            c.drawString(margin + 18, y - i*13, line)
        y -= len(lines) * 13 + 10

    y -= 20

    # Objectifs J+30
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Objectifs J+30")
    y -= 25

    targets = [
        ("Membres inscrits", "48", "200", 24),
        ("Startups avec fondateur", "948", "1 500", 63),
        (u"Publications communaut\u00e9", "14", "50", 28),
        ("Sessions / semaine", "2 665", "5 000", 53),
    ]
    headers = ["OBJECTIF", "ACTUEL", "CIBLE J+30", "PROGRESSION"]
    col_widths = [180, 80, 80, content_w - 340]

    # Header
    draw_rounded_rect(c, margin, y - 24, content_w, 24, 4, fill_color=DARK)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 8)
    cx = margin
    for i, h in enumerate(headers):
        c.drawString(cx + 6, y - 16, h)
        cx += col_widths[i]

    y -= 24
    for ri, (label, current, target, pct) in enumerate(targets):
        y -= 28
        if ri % 2 == 0:
            draw_rounded_rect(c, margin, y, content_w, 28, 0, fill_color=HexColor("#f8fafc"))
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(margin + 6, y + 8, label)
        c.setFont("Helvetica", 9)
        c.drawString(margin + 186, y + 8, current)
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(ACCENT)
        c.drawString(margin + 266, y + 8, target)
        # Progress bar
        bar_x = margin + 346
        bar_w = content_w - 352
        draw_bar(c, bar_x, y + 6, bar_w, 12, pct / 100, ACCENT)
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(bar_x + bar_w + 4, y + 8, f"{pct}%")

    c.showPage()

    # ══════════════════════════════════════════════════════════════════
    # PAGE 8 - MENTORS & ASSIGNATIONS STARTUPS
    # ══════════════════════════════════════════════════════════════════
    c.setFillColor(LIGHT_BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    draw_page_header(c, u"7.  Accompagnement : Mentors & Startups assign\u00e9es", "Programme de mentorat", margin)

    y = H - 85

    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, u"Assignation Mentors \u2014 Startups")
    y -= 14
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(margin, y, u"Chaque mentor accompagne un portefeuille de startups s\u00e9lectionn\u00e9es pour un suivi personnalis\u00e9.")
    y -= 25

    mentors = [
        ("Ali El Amrani", PURPLE, [
            "IndusTwin",
            "IrrigSense",
            "AeroMind Morocco",
            "WAHGO Foods",
        ]),
        ("Youssef Mamou", ACCENT, [
            "Investing For Everyone",
            "Igudar",
            "XPredictia",
            "SmartDiag",
            "SyanaTek",
        ]),
        ("Tarik Fadli", BLUE, [
            "UM6P Instruments",
            "GeoHeritage",
            "G-ReLib",
        ]),
        ("Mohammed Damiri", ORANGE, [
            "DECAP",
            "GreenFlow",
        ]),
    ]

    col_w_m = (content_w - 16) / 2
    col_positions_m = [margin, margin + col_w_m + 16]
    col_y_m = [y, y]

    for idx, (mentor_name, mentor_color, startups) in enumerate(mentors):
        col = idx % 2
        cx = col_positions_m[col]
        cy = col_y_m[col]

        # Card background
        card_height = 30 + len(startups) * 22 + 10
        draw_rounded_rect(c, cx, cy - card_height, col_w_m, card_height, 8, fill_color=WHITE)
        # Color bar top
        draw_rounded_rect(c, cx, cy - 5, col_w_m, 5, 3, fill_color=mentor_color)
        # Mentor name
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(cx + 12, cy - 22, mentor_name)
        # Subtitle
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 7.5)
        c.drawString(cx + 12, cy - 33, f"Mentor \u2014 {len(startups)} startups assign\u00e9es")

        # Startup list
        sy = cy - 48
        for startup in startups:
            c.setFillColor(mentor_color)
            c.circle(cx + 16, sy + 4, 3, fill=1, stroke=0)
            c.setFillColor(DARK)
            c.setFont("Helvetica", 9.5)
            c.drawString(cx + 26, sy, startup)
            sy -= 22

        col_y_m[col] = cy - card_height - 16

    # Summary line
    y_summary = min(col_y_m) - 5
    if y_summary < 80:
        y_summary = 80
    c.setFillColor(HexColor("#475569"))
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(W / 2, y_summary, u"4 mentors  |  14 startups accompagn\u00e9es  |  Ratio moyen : 3,5 startups / mentor")

    # Footer
    y_summary -= 30
    c.setStrokeColor(HexColor("#e2e8f0"))
    c.setLineWidth(0.5)
    c.line(margin, y_summary, W - margin, y_summary)
    y_summary -= 18
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(margin, y_summary, u"The Pulse  |  UM6P  |  thepulse.ma  |  Rapport g\u00e9n\u00e9r\u00e9 le 13 avril 2026")
    c.drawRightString(W - margin, y_summary, "Page 8/8  |  Rapport partenaires")

    c.save()
    print(f"[OK] Rapport g\u00e9n\u00e9r\u00e9 : {OUTPUT}")


if __name__ == "__main__":
    build_report()
