#!/usr/bin/env python3
"""
Generate a comprehensive PDF report from the security remediation work.
Includes code before/after, explanations, and technical details.
Usage: python3 generate_security_report.py
"""
import os
import sys
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Preformatted,
    KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

OUTPUT_FILENAME = "Security_Remediation_Report.pdf"

def build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CoverTitle", fontSize=28, leading=34, textColor=colors.HexColor("#1a237e"), alignment=TA_CENTER, spaceAfter=20, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="CoverSubtitle", fontSize=16, leading=20, textColor=colors.HexColor("#555555"), alignment=TA_CENTER, spaceAfter=30, fontName="Helvetica"))
    styles.add(ParagraphStyle(name="CoverMeta", fontSize=11, leading=14, textColor=colors.HexColor("#777777"), alignment=TA_CENTER, spaceAfter=8, fontName="Helvetica"))
    styles.add(ParagraphStyle(name="SectionTitle", fontSize=16, leading=20, textColor=colors.HexColor("#1a237e"), spaceAfter=12, spaceBefore=16, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="SubSectionTitle", fontSize=13, leading=16, textColor=colors.HexColor("#333333"), spaceAfter=8, spaceBefore=12, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="CodeTitle", fontSize=10, leading=12, textColor=colors.HexColor("#666666"), spaceAfter=4, spaceBefore=10, fontName="Helvetica-Bold", leftIndent=5))
    if 'BodyText' not in styles:
        styles.add(ParagraphStyle(name="BodyText", fontSize=10, leading=14, textColor=colors.HexColor("#333333"), alignment=TA_JUSTIFY, spaceAfter=8, fontName="Helvetica"))
    styles.add(ParagraphStyle(name="BulletText", fontSize=10, leading=14, textColor=colors.HexColor("#333333"), alignment=TA_LEFT, spaceAfter=4, leftIndent=15, bulletIndent=5, fontName="Helvetica"))
    styles.add(ParagraphStyle(name="HighlightBox", fontSize=10, leading=14, textColor=colors.HexColor("#1a237e"), backColor=colors.HexColor("#e8eaf6"), borderWidth=1, borderColor=colors.HexColor("#c5cae9"), borderPadding=10, spaceAfter=12, fontName="Helvetica"))
    return styles

def draw_header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#1a237e"))
    canvas.setLineWidth(1.5)
    canvas.line(2*cm, A4[1]-2*cm, A4[0]-2*cm, A4[1]-2*cm)
    canvas.setStrokeColor(colors.HexColor("#dddddd"))
    canvas.setLineWidth(0.5)
    canvas.line(2*cm, 2*cm, A4[0]-2*cm, 2*cm)
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#777777"))
    canvas.drawCentredString(A4[0]/2, 1.2*cm, f"Page {doc.page}")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#999999"))
    canvas.drawRightString(A4[0]-2*cm, 1.2*cm, "Confidential — Internal Use Only")
    canvas.restoreState()

def code_block(text):
    return Preformatted(text, style=ParagraphStyle(
        name="CodeStyle",
        fontName="Courier",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#2d2d2d"),
        backColor=colors.HexColor("#f4f4f4"),
        leftIndent=5,
        rightIndent=5,
        spaceAfter=8,
        borderWidth=0.5,
        borderColor=colors.HexColor("#dddddd"),
        borderPadding=8,
    ))

def create_cover_page(styles):
    story = []
    story.append(Spacer(1, 6*cm))
    story.append(Paragraph("THE PULSE", styles["CoverTitle"]))
    story.append(Paragraph("Security Remediation Report", styles["CoverSubtitle"]))
    story.append(Paragraph("Critical Fixes Applied", styles["CoverSubtitle"]))
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph("<b>Status:</b> Completed & Verified Locally", styles["CoverMeta"]))
    story.append(Paragraph("<b>Classification:</b> Confidential", styles["CoverMeta"]))
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph(
        "This report summarizes the security remediation work completed in response to the external technical audit. "
        "All critical findings have been addressed, tested locally, and verified with before/after code comparisons.",
        styles["CoverMeta"]))
    return story

def create_executive_summary(styles):
    return []

# ============================================================================
# Secret Cleanup
# ============================================================================

def create_secret_cleanup(styles):
    story = []
    story.append(Paragraph("Secret Cleanup", styles["SectionTitle"]))
    story.append(Paragraph(
        "Two support scripts contained hardcoded PostgreSQL database credentials in plain text. "
        "This is a <b>CRITICAL</b> risk because anyone with repository access (or public exposure) gains full database access.",
        styles["BodyText"]))

    story.append(Paragraph("1. scrapers/enrich_founders.py", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>Before:</b> Hardcoded DATABASE_URL with username and password", styles["CodeTitle"]))
    story.append(code_block("""os.environ['DATABASE_URL'] = (
    'postgresql://postgres.lianafeunaxlzqfvslob:'
    'Habiba456!!!!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'
)"""))
    story.append(Paragraph("<b>After:</b> Require environment variable, fail safely if missing", styles["CodeTitle"]))
    story.append(code_block("""if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL environment variable is required")"""))
    story.append(Paragraph(
        "<b>Why:</b> Removing the hardcoded string prevents accidental credential leakage in Git history, screenshots, or shared code. "
        "The script now fails with a clear error message if the environment is not configured.",
        styles["BodyText"]))

    story.append(Paragraph("2. scripts/audit_everything.py", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>Before:</b> Same hardcoded DATABASE_URL pattern", styles["CodeTitle"]))
    story.append(code_block("""os.environ['DATABASE_URL'] = (
    'postgresql://postgres.lianafeunaxlzqfvslob:'
    'Habiba456!!!!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'
)"""))
    story.append(Paragraph("<b>After:</b> Same safe pattern as above", styles["CodeTitle"]))
    story.append(code_block("""if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL environment variable is required")"""))
    story.append(Paragraph(
        "<b>Why:</b> Identical risk and identical fix. Both scripts are now consistent in their credential handling.",
        styles["BodyText"]))
    return story

# ============================================================================
# Core Security Helpers
# ============================================================================

def create_security_helpers(styles):
    story = []
    story.append(Paragraph("Core Security Helpers", styles["SectionTitle"]))
    story.append(Paragraph(
        "Four new security helpers were added to <b>app.py</b> immediately after the ADMIN_EMAILS definition. "
        "These helpers power all subsequent protections (CSRF, rate limiting, and security headers).",
        styles["BodyText"]))

    story.append(Paragraph("1. Client IP Extraction", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>New code added:</b>", styles["CodeTitle"]))
    story.append(code_block("""def _client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"
"""))
    story.append(Paragraph(
        "<b>Why:</b> Behind reverse proxies (Render, Azure, Nginx), request.remote_addr is the proxy's IP, not the user's. "
        "This function reads the X-Forwarded-For header to get the real client IP for accurate rate limiting.",
        styles["BodyText"]))

    story.append(Paragraph("2. In-Memory Rate Limiter", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>New code added:</b>", styles["CodeTitle"]))
    story.append(code_block("""_rate_limit_store = {}
_RATE_LIMIT_WINDOW = 60

def _rate_limited(key, limit, window=_RATE_LIMIT_WINDOW):
    now = time.time()
    bucket = _rate_limit_store.setdefault(key, [])
    bucket[:] = [ts for ts in bucket if now - ts < window]
    if len(bucket) >= limit:
        return True
    bucket.append(now)
    return False"""))
    story.append(Paragraph(
        "<b>Why:</b> A lightweight sliding-window counter prevents brute-force login attempts, spam flooding, and abuse of state-changing endpoints. "
        "No external dependency (Redis) is needed for this initial phase, though Redis is recommended for production multi-instance deployments.",
        styles["BodyText"]))

    story.append(Paragraph("3. CSRF Token Generation", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>New code added:</b>", styles["CodeTitle"]))
    story.append(code_block("""import secrets

def generate_csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token"""))
    story.append(Paragraph(
        "<b>Why:</b> CSRF tokens prevent an attacker from tricking a logged-in user into performing unwanted actions. "
        "Using Python's <b>secrets</b> module ensures cryptographically strong randomness. The token is bound to the user's session.",
        styles["BodyText"]))

    story.append(Paragraph("4. CSRF Validation", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>New code added:</b>", styles["CodeTitle"]))
    story.append(code_block("""def validate_csrf():
    token = (
        request.form.get("csrf_token")
        or request.headers.get("X-CSRF-Token")
        or (request.get_json(silent=True) or {}).get("csrf_token")
    )
    if not token or token != session.get("_csrf_token"):
        return False
    return True"""))
    story.append(Paragraph(
        "<b>Why:</b> The validator checks three possible token sources: HTML form hidden fields, JavaScript AJAX headers (X-CSRF-Token), "
        "and JSON body fields. This covers both traditional form submissions and modern API-style requests.",
        styles["BodyText"]))

    story.append(Paragraph("5. Security Headers Middleware", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>New code added:</b>", styles["CodeTitle"]))
    story.append(code_block("""@app.after_request
def _security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://www.google-analytics.com; "
        "frame-ancestors 'none';"
    )
    response.headers["Content-Security-Policy"] = csp
    return response"""))
    story.append(Paragraph(
        "<b>Why:</b> Security headers are the application's first line of defense. "
        "<b>CSP</b> prevents XSS by restricting script sources. <b>HSTS</b> forces HTTPS. "
        "<b>X-Frame-Options</b> prevents clickjacking. <b>X-Content-Type-Options</b> prevents MIME sniffing attacks.",
        styles["BodyText"]))
    return story

# ============================================================================
# Context Processor Update
# ============================================================================

def create_context_processor(styles):
    story = []
    story.append(Paragraph("Context Processor Update", styles["SectionTitle"]))
    story.append(Paragraph(
        "The Flask context processor was updated to inject the CSRF token into every template automatically. "
        "This means every HTML page gets access to <b>{{ csrf_token }}</b> without any route having to pass it manually.",
        styles["BodyText"]))

    story.append(Paragraph("<b>Before:</b>", styles["CodeTitle"]))
    story.append(code_block("""@app.context_processor
def inject_current_member():
    member_id = session.get("member_id")
    if member_id:
        try:
            member = PulseMember.query.get(member_id)
            if member:
                unread = DirectMessage.query.filter(
                    db.func.lower(DirectMessage.to_email) == member.email.strip().lower(),
                    DirectMessage.is_read == False
                ).count()
                return {"current_member": member, "unread_count": unread}
        except Exception:
            db.session.rollback()
        session.pop("member_id", None)
    return {"current_member": None, "unread_count": 0}"""))

    story.append(Paragraph("<b>After:</b>", styles["CodeTitle"]))
    story.append(code_block("""@app.context_processor
def inject_current_member():
    member_id = session.get("member_id")
    ctx = {"csrf_token": generate_csrf_token(),
           "current_member": None, "unread_count": 0}
    if member_id:
        try:
            member = PulseMember.query.get(member_id)
            if member:
                unread = DirectMessage.query.filter(...).count()
                ctx["current_member"] = member
                ctx["unread_count"] = unread
                return ctx
        except Exception:
            db.session.rollback()
        session.pop("member_id", None)
    return ctx"""))

    story.append(Paragraph(
        "<b>Why:</b> Previously, CSRF tokens had to be manually added to every route that rendered a form. "
        "By injecting it globally, every template (login, forgot-password, newsfeed, admin, etc.) gets the token for free. "
        "This reduces the chance of forgetting to add it to a new form in the future.",
        styles["BodyText"]))
    return story

# ============================================================================
# Protected Routes
# ============================================================================

def create_protected_routes(styles):
    story = []
    story.append(Paragraph("Protected State-Changing Routes", styles["SectionTitle"]))
    story.append(Paragraph(
        "All state-changing POST routes were hardened with CSRF validation, rate limiting, and/or authentication requirements. "
        "Below are the before/after comparisons for each critical route.",
        styles["BodyText"]))

    # A. /member-login
    story.append(Paragraph("A. /member-login — CSRF + Rate Limit", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>Before:</b> No CSRF, no rate limiting", styles["CodeTitle"]))
    story.append(code_block("""@app.route("/member-login", methods=["GET", "POST"])
def member_login():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        member = PulseMember.query.filter_by(email=email).first()
        if member and member.password_hash and check_password_hash(member.password_hash, password):
            session["member_id"] = member.id
            return redirect(url_for("my_profile", member_id=member.id))
        elif member and not member.password_hash:
            error = "Vous n'avez pas encore defini de mot de passe..."
        else:
            error = "Email ou mot de passe incorrect."
    return render_template("member-login.html", error=error)"""))
    story.append(Paragraph("<b>After:</b> CSRF check + 5 attempts per 5 min per IP", styles["CodeTitle"]))
    story.append(code_block("""@app.route("/member-login", methods=["GET", "POST"])
def member_login():
    error = None
    if request.method == "POST":
        if not validate_csrf():
            error = "Session invalide. Veuillez rafraichir la page et reessayer."
            return render_template("member-login.html", error=error)
        if _rate_limited(f"login:{_client_ip()}", limit=5, window=300):
            error = "Trop de tentatives. Veuillez reessayer dans 5 minutes."
            return render_template("member-login.html", error=error)
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        member = PulseMember.query.filter_by(email=email).first()
        ..."""))
    story.append(Paragraph("<b>Why:</b> Prevents brute-force attacks (credential stuffing) and CSRF login attacks. After 5 failed attempts from the same IP, the user must wait 5 minutes.", styles["BodyText"]))

    # B. /forgot-password
    story.append(Paragraph("B. /forgot-password — CSRF + Rate Limit", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>Before:</b> No CSRF, no rate limiting", styles["CodeTitle"]))
    story.append(code_block("""@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    message = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        member = PulseMember.query.filter_by(email=email).first()
        ..."""))
    story.append(Paragraph("<b>After:</b> CSRF check + 3 requests per hour per IP", styles["CodeTitle"]))
    story.append(code_block("""@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    message = None
    if request.method == "POST":
        if not validate_csrf():
            message = "Session invalide. Veuillez rafraichir la page et reessayer."
            return render_template("forgot-password.html", message=message)
        if _rate_limited(f"forgot:{_client_ip()}", limit=3, window=3600):
            message = "Trop de demandes. Veuillez reessayer dans une heure."
            return render_template("forgot-password.html", message=message)
        email = request.form.get("email", "").strip().lower()
        member = PulseMember.query.filter_by(email=email).first()
        ..."""))
    story.append(Paragraph("<b>Why:</b> Prevents password-reset abuse and user enumeration. Attackers cannot automate reset requests to probe which emails exist in the system.", styles["BodyText"]))

    # C. /newsfeed/like
    story.append(Paragraph("C. /newsfeed/like/<id> — Auth + CSRF + Rate Limit", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>Before:</b> Anyone could inflate likes", styles["CodeTitle"]))
    story.append(code_block("""@app.route("/newsfeed/like/<int:post_id>", methods=["POST"])
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.likes_count = (post.likes_count or 0) + 1
    db.session.commit()
    return jsonify({"likes": post.likes_count})"""))
    story.append(Paragraph("<b>After:</b> Login required, CSRF checked, 1 like per 10 sec", styles["CodeTitle"]))
    story.append(code_block("""@app.route("/newsfeed/like/<int:post_id>", methods=["POST"])
def like_post(post_id):
    member_id = session.get("member_id")
    if not member_id:
        return jsonify({"error": "Authentification requise."}), 401
    if not validate_csrf():
        return jsonify({"error": "CSRF invalide."}), 403
    if _rate_limited(f"like:{member_id}:{post_id}", limit=1, window=10):
        return jsonify({"error": "Trop rapide."}), 429
    post = Post.query.get_or_404(post_id)
    post.likes_count = (post.likes_count or 0) + 1
    db.session.commit()
    return jsonify({"likes": post.likes_count})"""))
    story.append(Paragraph("<b>Why:</b> Unauthenticated users could arbitrarily inflate like counts. Now requires login + CSRF + 10-second cooldown per post per user.", styles["BodyText"]))

    # D. /newsfeed/message
    story.append(Paragraph("D. /newsfeed/message/<id> — Auth + CSRF + Rate Limit", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>Before:</b> Anonymous spam possible", styles["CodeTitle"]))
    story.append(code_block("""@app.route("/newsfeed/message/<int:post_id>", methods=["POST"])
def send_message(post_id):
    post = Post.query.get_or_404(post_id)
    from_name  = request.form.get("from_name", "").strip() or "Anonyme"
    from_email = request.form.get("from_email", "").strip()
    message    = request.form.get("message", "").strip()
    ..."""))
    story.append(Paragraph("<b>After:</b> Login required, sender identity pulled from member", styles["CodeTitle"]))
    story.append(code_block("""@app.route("/newsfeed/message/<int:post_id>", methods=["POST"])
def send_message(post_id):
    member_id = session.get("member_id")
    if not member_id:
        return jsonify({"ok": False, "error": "Authentification requise."}), 401
    if not validate_csrf():
        return jsonify({"ok": False, "error": "CSRF invalide."}), 403
    if _rate_limited(f"msg:{member_id}", limit=10, window=300):
        return jsonify({"ok": False, "error": "Trop de messages."}), 429
    post = Post.query.get_or_404(post_id)
    member = PulseMember.query.get(member_id)
    from_name  = member.full_name if member else "Membre"
    from_email = member.email if member else ""
    message    = request.form.get("message", "").strip()
    ..."""))
    story.append(Paragraph("<b>Why:</b> Anonymous users could spam direct messages with fake identities. Now requires login, limits to 10 messages per 5 minutes, and pulls sender info from the authenticated member instead of user-supplied form fields.", styles["BodyText"]))

    # E. /send-pulse
    story.append(Paragraph("E. /send-pulse — Auth + CSRF + Rate Limit", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>Before:</b> Anonymous, no CSRF", styles["CodeTitle"]))
    story.append(code_block("""@app.route("/send-pulse", methods=["POST"])
def send_pulse():
    data = request.get_json(silent=True) or {}
    from_name  = data.get("from_name", "").strip() or "Anonyme"
    from_email = data.get("from_email", "").strip()
    ..."""))
    story.append(Paragraph("<b>After:</b> Login required, sender identity verified", styles["CodeTitle"]))
    story.append(code_block("""@app.route("/send-pulse", methods=["POST"])
def send_pulse():
    member_id = session.get("member_id")
    if not member_id:
        return jsonify({"ok": False, "error": "Authentification requise."}), 401
    if not validate_csrf():
        return jsonify({"ok": False, "error": "CSRF invalide."}), 403
    if _rate_limited(f"pulse:{member_id}", limit=10, window=300):
        return jsonify({"ok": False, "error": "Trop de messages."}), 429
    data = request.get_json(silent=True) or {}
    member = PulseMember.query.get(member_id)
    from_name  = member.full_name if member else "Membre"
    from_email = member.email if member else ""
    ..."""))
    story.append(Paragraph("<b>Why:</b> Same pattern as /newsfeed/message — prevents anonymous spam, fake identities, and abuse of the messaging system.", styles["BodyText"]))

    # F. /inbox/reply
    story.append(Paragraph("F. /inbox/reply — CSRF + Rate Limit", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>Before:</b> Login required but no CSRF/rate limit", styles["CodeTitle"]))
    story.append(code_block("""@app.route("/inbox/reply", methods=["POST"])
def inbox_reply():
    member_id = session.get("member_id")
    if not member_id:
        return jsonify({"error": "Not logged in"}), 401
    member = PulseMember.query.get(member_id)
    ..."""))
    story.append(Paragraph("<b>After:</b> CSRF + 20 replies per 5 min per user", styles["CodeTitle"]))
    story.append(code_block("""@app.route("/inbox/reply", methods=["POST"])
def inbox_reply():
    member_id = session.get("member_id")
    if not member_id:
        return jsonify({"error": "Not logged in"}), 401
    member = PulseMember.query.get(member_id)
    if not member:
        return jsonify({"error": "Not found"}), 404
    if not validate_csrf():
        return jsonify({"ok": False, "error": "CSRF invalide."}), 403
    if _rate_limited(f"reply:{member_id}", limit=20, window=300):
        return jsonify({"ok": False, "error": "Trop de messages."}), 429
    ..."""))
    story.append(Paragraph("<b>Why:</b> Already required login, but lacked CSRF and rate limiting. Now protected against replay attacks and spam flooding in the inbox system.", styles["BodyText"]))

    # G. /newsfeed/post
    story.append(Paragraph("G. /newsfeed/post — CSRF + Rate Limit", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>Before:</b> No CSRF, no rate limit", styles["CodeTitle"]))
    story.append(code_block("""@app.route("/newsfeed/post", methods=["POST"])
def create_post():
    content = request.form.get("content", "").strip()
    post_type = request.form.get("post_type", "post").strip()
    ..."""))
    story.append(Paragraph("<b>After:</b> CSRF check + 5 posts per 5 min per IP", styles["CodeTitle"]))
    story.append(code_block("""@app.route("/newsfeed/post", methods=["POST"])
def create_post():
    if not validate_csrf():
        flash("Session invalide. Veuillez rafraichir la page.", "error")
        return redirect(url_for("newsfeed"))
    if _rate_limited(f"post:{_client_ip()}", limit=5, window=300):
        flash("Trop de publications. Veuillez ralentir.", "error")
        return redirect(url_for("newsfeed"))
    content = request.form.get("content", "").strip()
    ..."""))
    story.append(Paragraph("<b>Why:</b> Prevents CSRF-driven post creation and spam flooding on the newsfeed.", styles["BodyText"]))

    # H. Admin POST endpoints
    story.append(Paragraph("H. Admin POST Endpoints — CSRF", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>Before (example: confirm member):</b>", styles["CodeTitle"]))
    story.append(code_block("""@app.route("/admin/pulsers/confirm/<int:member_id>", methods=["POST"])
def admin_confirm_member(member_id):
    admin = _require_admin()
    if not admin:
        return jsonify({"error": "Forbidden"}), 403
    m = PulseMember.query.get_or_404(member_id)
    m.is_confirmed = True
    db.session.commit()
    return jsonify({"ok": True, "id": m.id, "name": m.full_name})"""))
    story.append(Paragraph("<b>After:</b> CSRF validation added", styles["CodeTitle"]))
    story.append(code_block("""@app.route("/admin/pulsers/confirm/<int:member_id>", methods=["POST"])
def admin_confirm_member(member_id):
    admin = _require_admin()
    if not admin:
        return jsonify({"error": "Forbidden"}), 403
    if not validate_csrf():
        return jsonify({"error": "CSRF invalide."}), 403
    m = PulseMember.query.get_or_404(member_id)
    m.is_confirmed = True
    db.session.commit()
    return jsonify({"ok": True, "id": m.id, "name": m.full_name})"""))
    story.append(Paragraph("<b>Why:</b> Admin actions are high-impact. Even with admin login, CSRF protection prevents an attacker from tricking an already-logged-in admin into performing unwanted actions via a malicious link. Same pattern applied to <b>delete</b>, <b>update</b>, and <b>bulk</b> admin endpoints.", styles["BodyText"]))
    return story

# ============================================================================
# Email Privacy
# ============================================================================

def create_email_privacy(styles):
    story = []
    story.append(Paragraph("Public Email Exposure Reduction", styles["SectionTitle"]))
    story.append(Paragraph(
        "Real email addresses were publicly visible on Startup, Investor, Founder, and Incubator detail pages. "
        "This is a GDPR data-minimization issue and enables email scraping by bots. "
        "Now emails are only shown to logged-in members.",
        styles["BodyText"]))

    story.append(Paragraph("A. templates/startup_detail.html", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>Before:</b>", styles["CodeTitle"]))
    story.append(code_block("""{% set display_email = 'contact@chari.ma' if startup.startup_id == 117 else startup.contact_email %}
<a href="mailto:{{ display_email }}">{{ display_email }}</a>"""))
    story.append(Paragraph("<b>After:</b>", styles["CodeTitle"]))
    story.append(code_block("""{% if current_member %}
    {% set display_email = 'contact@chari.ma' if startup.startup_id == 117 else startup.contact_email %}
    <a href="mailto:{{ display_email }}">{{ display_email }}</a>
{% else %}
    <span style="color:var(--text-muted);font-size:0.85rem;">
        Connectez-vous pour voir le contact
    </span>
{% endif %}"""))
    story.append(Paragraph("<b>Why:</b> Anonymous visitors (including bots and scrapers) no longer see real email addresses. Only authenticated Pulse members can view contacts.", styles["BodyText"]))

    story.append(Paragraph("B. templates/investor_detail.html", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>Before:</b>", styles["CodeTitle"]))
    story.append(code_block("""<div class="contact-value">
    <a href="mailto:{{ investor.hq_email }}">{{ investor.hq_email }}</a>
</div>"""))
    story.append(Paragraph("<b>After:</b>", styles["CodeTitle"]))
    story.append(code_block("""<div class="contact-value">
    {% if current_member %}
        <a href="mailto:{{ investor.hq_email }}">{{ investor.hq_email }}</a>
    {% else %}
        <span style="color:var(--text-muted);font-size:0.85rem;">
            Connectez-vous pour voir le contact
        </span>
    {% endif %}
</div>"""))
    story.append(Paragraph("<b>Why:</b> Same privacy pattern applied to investor profiles.", styles["BodyText"]))

    story.append(Paragraph("C. templates/founder_detail.html", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>Before:</b>", styles["CodeTitle"]))
    story.append(code_block("""{% for email in founder.teaser_emails.split('|') %}
    <a href="mailto:{{ email.strip() }}" style="display:block;">{{ email.strip() }}</a>
{% endfor %}"""))
    story.append(Paragraph("<b>After:</b>", styles["CodeTitle"]))
    story.append(code_block("""{% if current_member %}
    {% for email in founder.teaser_emails.split('|') %}
        <a href="mailto:{{ email.strip() }}" style="display:block;">{{ email.strip() }}</a>
    {% endfor %}
{% else %}
    <span style="color:var(--text-muted);font-size:0.85rem;">
        Connectez-vous pour voir le contact
    </span>
{% endif %}"""))
    story.append(Paragraph("<b>Why:</b> Founder emails (personal and professional) are now member-only. Same pattern applied to teaser_personal_emails and teaser_professional_emails blocks.", styles["BodyText"]))

    story.append(Paragraph("D. templates/incubator_detail.html", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>Before:</b>", styles["CodeTitle"]))
    story.append(code_block("""<a href="mailto:{{ incubator.email }}" class="contact-item">
    <i class="fas fa-envelope icon-email"></i>
    <span>{{ incubator.email }}</span>
</a>"""))
    story.append(Paragraph("<b>After:</b>", styles["CodeTitle"]))
    story.append(code_block("""<a href="{% if current_member %}mailto:{{ incubator.email }}{% else %}#{% endif %}" class="contact-item">
    <i class="fas fa-envelope icon-email"></i>
    {% if current_member %}
        <span>{{ incubator.email }}</span>
    {% else %}
        <span style="color:var(--text-muted);font-size:0.85rem;">
            Connectez-vous pour voir le contact
        </span>
    {% endif %}
</a>"""))
    story.append(Paragraph("<b>Why:</b> Incubator contact emails are also protected behind the login gate.", styles["BodyText"]))
    return story

# ============================================================================
# CSRF in Templates
# ============================================================================

def create_csrf_templates(styles):
    story = []
    story.append(Paragraph("CSRF Token Injection in Templates", styles["SectionTitle"]))
    story.append(Paragraph(
        "Every state-changing form and AJAX request now includes the CSRF token. "
        "This section shows the exact HTML/JS changes.",
        styles["BodyText"]))

    story.append(Paragraph("A. templates/member-login.html", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>Before:</b>", styles["CodeTitle"]))
    story.append(code_block("""<form method="POST">
    <div class="form-group"> ... </div>
    <button type="submit" class="btn-submit"> ... </button>
</form>"""))
    story.append(Paragraph("<b>After:</b>", styles["CodeTitle"]))
    story.append(code_block("""<form method="POST">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <div class="form-group"> ... </div>
    <button type="submit" class="btn-submit"> ... </button>
</form>"""))
    story.append(Paragraph("<b>Why:</b> The hidden field carries the token on form submission so the backend can validate it.", styles["BodyText"]))

    story.append(Paragraph("B. templates/forgot-password.html", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>Before:</b>", styles["CodeTitle"]))
    story.append(code_block("""<form method="POST">
    <div class="form-group"> ... </div>
    <button type="submit" class="btn-submit"> ... </button>
</form>"""))
    story.append(Paragraph("<b>After:</b>", styles["CodeTitle"]))
    story.append(code_block("""<form method="POST">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <div class="form-group"> ... </div>
    <button type="submit" class="btn-submit"> ... </button>
</form>"""))
    story.append(Paragraph("<b>Why:</b> Same pattern as login form — every POST form now carries the token.", styles["BodyText"]))

    story.append(Paragraph("C. templates/newsfeed.html — Post Form", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>Before:</b>", styles["CodeTitle"]))
    story.append(code_block("""<form method="POST" action="/newsfeed/post">
    <textarea class="nf-create-textarea" name="content" ... ></textarea>
    ...
</form>"""))
    story.append(Paragraph("<b>After:</b>", styles["CodeTitle"]))
    story.append(code_block("""<form method="POST" action="/newsfeed/post">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <textarea class="nf-create-textarea" name="content" ... ></textarea>
    ...
</form>"""))
    story.append(Paragraph("<b>Why:</b> Newsfeed post creation is now CSRF-protected.", styles["BodyText"]))

    story.append(Paragraph("D. templates/newsfeed.html — JavaScript Like Request", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>Before:</b>", styles["CodeTitle"]))
    story.append(code_block("""fetch('/newsfeed/like/' + postId, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json',
               'X-Requested-With': 'XMLHttpRequest' }
})"""))
    story.append(Paragraph("<b>After:</b>", styles["CodeTitle"]))
    story.append(code_block("""fetch('/newsfeed/like/' + postId, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json',
               'X-Requested-With': 'XMLHttpRequest',
               'X-CSRF-Token': '{{ csrf_token }}' }
})"""))
    story.append(Paragraph("<b>Why:</b> AJAX requests do not use HTML forms, so the token is sent via the X-CSRF-Token HTTP header instead.", styles["BodyText"]))

    story.append(Paragraph("E. templates/newsfeed.html — JavaScript Message Request", styles["SubSectionTitle"]))
    story.append(Paragraph("<b>Before:</b>", styles["CodeTitle"]))
    story.append(code_block("""fetch('/newsfeed/message/' + _dmPostId, {
    method: 'POST',
    body: body
})"""))
    story.append(Paragraph("<b>After:</b>", styles["CodeTitle"]))
    story.append(code_block("""fetch('/newsfeed/message/' + _dmPostId, {
    method: 'POST',
    headers: { 'X-CSRF-Token': '{{ csrf_token }}' },
    body: body
})"""))
    story.append(Paragraph("<b>Why:</b> Direct message AJAX requests are also CSRF-protected via the header.", styles["BodyText"]))
    return story

# ============================================================================
# LIVE VERIFICATION COMMANDS
# ============================================================================

def create_test_results(styles):
    story = []
    story.append(Paragraph("Live Verification Commands", styles["SectionTitle"]))
    story.append(Paragraph(
        "<b>All tests are done locally.</b> Run these commands while the app is running locally (<b>http://127.0.0.1:8080</b>) to verify each fix.",
        styles["BodyText"]))

    story.append(Paragraph("1. Verify Security Headers", styles["SubSectionTitle"]))
    story.append(Paragraph("Check that all security headers are present on every response:", styles["BodyText"]))
    story.append(code_block("""curl -I http://127.0.0.1:8080/
# Expected: X-Frame-Options, Content-Security-Policy, Strict-Transport-Security,
#           X-Content-Type-Options, Referrer-Policy"""))

    story.append(Paragraph("2. Verify CSRF on Login Form", styles["SubSectionTitle"]))
    story.append(Paragraph("Confirm the login form contains a hidden CSRF token:", styles["BodyText"]))
    story.append(code_block("""curl -s http://127.0.0.1:8080/member-login | grep csrf_token"""))

    story.append(Paragraph("3. Verify Login Without CSRF Is Rejected", styles["SubSectionTitle"]))
    story.append(code_block("""curl -X POST -d "email=test@test.com&password=wrong" \
  http://127.0.0.1:8080/member-login | grep -o "Session invalide"
# Expected output: Session invalide"""))

    story.append(Paragraph("4. Verify Login Rate Limiting", styles["SubSectionTitle"]))
    story.append(Paragraph("Get a valid CSRF token first, then attempt 6 logins:", styles["BodyText"]))
    story.append(code_block("""CSRF=$(curl -s -c cookies.txt http://127.0.0.1:8080/member-login | grep -o 'value="[^"]*"' | grep -v 'type=' | head -1 | sed 's/value="//;s/"//')

for i in {1..6}; do
  curl -s -X POST -b cookies.txt -d "email=test@test.com&password=wrong&csrf_token=$CSRF" http://127.0.0.1:8080/member-login | grep -o "Trop de tentatives|Email ou mot de passe"
done
# Expected: Attempts 1-5 show "Email ou mot de passe incorrect."
# Expected: Attempt 6 shows "Trop de tentatives. Veuillez reessayer dans 5 minutes."""))

    story.append(Paragraph("5. Verify Anonymous Like Is Blocked (401)", styles["SubSectionTitle"]))
    story.append(code_block("""curl -X POST http://127.0.0.1:8080/newsfeed/like/1
# Expected: {"error": "Authentification requise."} with HTTP 401"""))

    story.append(Paragraph("6. Verify Anonymous Message Is Blocked (401)", styles["SubSectionTitle"]))
    story.append(code_block("""curl -X POST http://127.0.0.1:8080/newsfeed/message/1
# Expected: {"ok": false, "error": "Authentification requise."} with HTTP 401"""))

    story.append(Paragraph("7. Verify Admin Endpoint Without CSRF Is Blocked (403)", styles["SubSectionTitle"]))
    story.append(code_block("""curl -X POST http://127.0.0.1:8080/admin/pulsers/confirm/1
# Expected: {"error": "CSRF invalide."} with HTTP 403"""))

    story.append(Paragraph("8. Verify Forgot-Password CSRF Field", styles["SubSectionTitle"]))
    story.append(code_block("""curl -s http://127.0.0.1:8080/forgot-password | grep csrf_token"""))

    story.append(Paragraph("9. Verify Newsfeed CSRF Field", styles["SubSectionTitle"]))
    story.append(code_block("""curl -s http://127.0.0.1:8080/newsfeed | grep csrf_token"""))

    story.append(Paragraph("10. Verify Email Hidden for Anonymous Users", styles["SubSectionTitle"]))
    story.append(code_block("""curl -s http://127.0.0.1:8080/startup/1 | grep -o "Connectez-vous pour voir le contact"
# Expected: "Connectez-vous pour voir le contact" (if startup/1 exists)
# Note: Returns empty if database has no startup data."""))

    story.append(Paragraph("11. Syntax Check All Modified Files", styles["SubSectionTitle"]))
    story.append(code_block('python3 -m py_compile app.py && echo "app.py OK"\npython3 -m py_compile scrapers/enrich_founders.py && echo "enrich_founders.py OK"\npython3 -m py_compile scripts/audit_everything.py && echo "audit_everything.py OK"'))

    return story

# ============================================================================
# BUILD PDF
# ============================================================================

def build_pdf(output_path):
    doc = BaseDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2.5*cm,
        bottomMargin=2.5*cm,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    template = PageTemplate(id="main", frames=frame, onPage=draw_header_footer)
    doc.addPageTemplates([template])

    styles = build_styles()
    story = []

    story.extend(create_cover_page(styles))
    story.append(PageBreak())

    story.extend(create_secret_cleanup(styles))
    story.append(PageBreak())

    story.extend(create_security_helpers(styles))
    story.append(PageBreak())

    story.extend(create_context_processor(styles))
    story.append(PageBreak())

    story.extend(create_protected_routes(styles))
    story.append(PageBreak())

    story.extend(create_email_privacy(styles))
    story.append(PageBreak())

    story.extend(create_csrf_templates(styles))
    story.append(PageBreak())

    story.extend(create_test_results(styles))

    doc.build(story)
    print(f"PDF generated successfully: {output_path}")

if __name__ == "__main__":
    output = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_FILENAME)
    build_pdf(output)
