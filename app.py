from flask import Flask, request, redirect, render_template_string, session, url_for, render_template, jsonify, Response
import csv
import io
import json
from models import *
from Functions import *
import urllib.parse
from collections import Counter
from sqlalchemy import func, or_, event, case, literal
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
try:
    import resend
except ImportError:
    resend = None
import uuid
import time
import threading
from datetime import timedelta, datetime as _dt

import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "pulse_secret")
#app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=2)
app.config['SESSION_REFRESH_EACH_REQUEST'] = False

# Use Supabase PostgreSQL if DATABASE_URL is set, otherwise fall back to SQLite
database_url = os.environ.get("DATABASE_URL")
if database_url:
    print(f"[PULSE] Using PostgreSQL: {database_url[:30]}...", flush=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=60000 -c client_encoding=UTF8'
        }
    }
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'thepulse.db')
    print("[PULSE] WARNING: Using SQLite (no DATABASE_URL set)", flush=True)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration — Resend (prod) with Gmail SMTP fallback (local)
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
GMAIL_USER = os.environ.get('GMAIL_USER', 'contact@thepulse.ma')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
if RESEND_API_KEY and resend:
    resend.api_key = RESEND_API_KEY

# Upload config
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Simple in-memory cache for home page data
_home_cache = {'data': None, 'expires': 0, 'lock': threading.Lock()}

# Initialize database with app
db.init_app(app)

# Create tables and default user if DB doesn't exist
with app.app_context():
    db.create_all()
    if not User.query.first():
        default_user = User(username='admin', password='admin')
        db.session.add(default_user)
        db.session.commit()
# Auth disabled for demo
# @app.before_request
# def require_password():
#     allowed_routes = ['login', 'static', 'confirm_email', 'complete_profile', 'my_profile',
#                       'join', 'entrepreneur_form', 'investor_form', 'program_form',
#                       'talent_form', 'cofounder_form']
#     if 'logged_in' not in session and request.endpoint not in allowed_routes:
#         return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session.permanent = False
            session["logged_in"] = True
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Invalid credentials. Please try again.")
    
    return render_template("login.html")

def _build_home_data():
    """Build all home page data from DB. Called once, cached for 5 min."""
    class CountObj:
        def __init__(self, n):
            self._n = n
        def __len__(self):
            return self._n
        def __iter__(self):
            return iter([])

    try:
        startup_count = db.session.query(db.func.count(Startup.startup_id)).scalar() or 0
        founder_count = db.session.query(db.func.count(Founder.founder_id)).scalar() or 0
        investor_count = db.session.query(db.func.count(Investor.investor_id)).scalar() or 0
        incubator_count = db.session.query(db.func.count(Incubator.incubator_id)).scalar() or 0
    except Exception:
        startup_count = founder_count = investor_count = incubator_count = 0

    try:
        from sqlalchemy.orm import joinedload as jl
        deals = FundingRound.query.options(jl(FundingRound.startup)).all()
        total_funding_millions = sum(d.raised_amount_usd or 0 for d in deals) / 1_000_000
    except Exception:
        deals = []
        total_funding_millions = 0

    topcities = NbStartupsByCity = topsectors = nbstartupsbysector = []
    sector_counter = Counter()
    try:
        startups_for_charts = db.session.query(Startup.location, Startup.sector).filter(
            db.or_(Startup.location.isnot(None), Startup.sector.isnot(None))
        ).all()
        cities_list = [s.location for s in startups_for_charts if s.location and s.location != "Morocco"]
        city_counter = Counter(cities_list)
        topcities = [c for c, _ in city_counter.most_common(10)]
        NbStartupsByCity = [n for _, n in city_counter.most_common(10)]
        for s in startups_for_charts:
            if s.sector:
                for sec in s.sector.split(','):
                    sec = sec.strip()
                    if sec:
                        sector_counter[sec] += 1
        topsectors = [s for s, _ in sector_counter.most_common(10)]
        nbstartupsbysector = [n for _, n in sector_counter.most_common(10)]
    except Exception:
        pass

    try:
        years, total_by_year = get_totalFunding_groupby_year(deals)
    except Exception:
        years, total_by_year = [], []

    try:
        topsectors_funding, total_funding_by_sector = get_total_funding_by_sector(deals, list(sector_counter.keys()), n=10)
    except Exception:
        topsectors_funding, total_funding_by_sector = [], []

    try:
        top_funded = db.session.query(Startup).filter(
            Startup.total_funding_usd.isnot(None)
        ).order_by(Startup.total_funding_usd.desc()).limit(10).all()
        top_startups_funding = top_funded[:3]
        total_funding_by_startup = [float(s.total_funding_usd or 0) for s in top_funded[:3]]
    except Exception:
        top_startups_funding, total_funding_by_startup = [], []

    try:
        appels_a_projets = Resource.query.filter(
            Resource.category.in_(['Appels à projets', 'Appel à projet']),
            Resource.is_featured == True
        ).order_by(Resource.published_at.desc()).limit(3).all()
    except Exception:
        appels_a_projets = []

    try:
        cofound_projects = CofounderProject.query.order_by(CofounderProject.created_at.desc()).limit(3).all()
    except Exception:
        cofound_projects = []

    try:
        recent_articles = Article.query.order_by(Article.article_id.desc()).limit(4).all()
    except Exception:
        recent_articles = []

    home_feed_items = []
    home_trending_tags = []
    try:
        _nf_posts = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).limit(20).all()
        _nf_articles = Article.query.order_by(Article.published_at.desc()).limit(10).all()
        _feed = []
        for p in _nf_posts:
            _feed.append({'type': 'post', 'obj': p, 'date': p.created_at})
        for a in _nf_articles:
            _feed.append({'type': 'article', 'obj': a, 'date': a.published_at})
        _feed.sort(key=lambda x: x['date'] if x['date'] else _dt.min, reverse=True)
        _articles = [x for x in _feed if x['type'] == 'article'][:2]
        _posts = [x for x in _feed if x['type'] == 'post' and x['obj'].post_type in ('post', 'question', 'announcement')][:1]
        _opps = [x for x in _feed if x['type'] == 'post' and x['obj'].post_type == 'opportunity'][:2]
        home_feed_items = _articles + _posts + _opps
        home_feed_items.sort(key=lambda x: x['date'] if x['date'] else _dt.min, reverse=True)
        _all_tags = []
        for p in _nf_posts:
            if p.tags:
                _all_tags.extend([t.strip() for t in p.tags.split(',') if t.strip()])
        home_trending_tags = Counter(_all_tags).most_common(8)
    except Exception:
        pass

    try:
        home_recent_rounds = FundingRound.query.filter(
            FundingRound.raised_amount_usd.isnot(None)
        ).order_by(FundingRound.date.desc()).limit(4).all()
    except Exception:
        home_recent_rounds = []

    try:
        home_appels_sidebar = Resource.query.filter(
            Resource.category.in_(['Appels à projets', 'Appel à projet']),
            Resource.is_featured == True
        ).order_by(Resource.published_at.desc()).limit(3).all()
    except Exception:
        home_appels_sidebar = []

    return dict(
        startups=CountObj(startup_count), founders=CountObj(founder_count),
        investors=CountObj(investor_count), incubators=CountObj(incubator_count),
        deals=deals, total_funding=total_funding_millions,
        topcities=topcities, NbStartupsByCity=NbStartupsByCity,
        topsectors=topsectors, nbstartupsbysector=nbstartupsbysector,
        years=years, total_by_year=total_by_year,
        topsectors_funding=topsectors_funding, total_funding_by_sector=total_funding_by_sector,
        top_startups_funding=top_startups_funding, total_funding_by_startup=total_funding_by_startup,
        appels_a_projets=appels_a_projets, cofound_projects=cofound_projects,
        recent_articles=recent_articles, home_feed_items=home_feed_items,
        home_trending_tags=home_trending_tags, home_recent_rounds=home_recent_rounds,
        home_appels_sidebar=home_appels_sidebar,
    )

@app.route("/")
def home():
    now = time.time()
    if _home_cache['data'] is not None and now < _home_cache['expires']:
        return render_template("home.html", **_home_cache['data'])

    with _home_cache['lock']:
        if _home_cache['data'] is not None and time.time() < _home_cache['expires']:
            return render_template("home.html", **_home_cache['data'])
        try:
            data = _build_home_data()
            _home_cache['data'] = data
            _home_cache['expires'] = time.time() + 600  # 10 min cache
        except Exception:
            if _home_cache['data'] is not None:
                return render_template("home.html", **_home_cache['data'])
            raise

    return render_template("home.html", **_home_cache['data'])


@app.route("/startups", methods=["GET"])
def startups():
    # Base query
    query = Startup.query

    # Search
    search_query = request.args.get("q", "").strip()
    if search_query:
        query = query.filter(or_(
            Startup.startup_name.ilike(f"%{search_query}%"),
            Startup.sector.ilike(f"%{search_query}%"),
            Startup.location.ilike(f"%{search_query}%")
        ))

    # Multi-select filters
    selected_cities = request.args.getlist("city")
    selected_sectors = request.args.getlist("sector")
    selected_status = request.args.getlist("status")
    selected_stages = request.args.getlist("stage")
    selected_forms = request.args.getlist("forme")
    selected_investors = request.args.getlist("investor")
    selected_incubators = request.args.getlist("incubator")

    
    # Apply filters
    if selected_investors:
        investorsSelected = Investor.query.filter(Investor.investor_id.in_(selected_investors)).all()
        startups_invested = StartupsInvestedByListOfInvestors(investorsSelected)
        startup_ids = [startup.startup_id for startup in startups_invested]
        query = query.filter(Startup.startup_id.in_(startup_ids))
    if selected_incubators:
        incubatorsSelected = Incubator.query.filter(Incubator.incubator_id.in_(selected_incubators)).all()
        startups_incubated = StartupsIncubatedByListOfIncubators(incubatorsSelected)
        startup_ids = [startup.startup_id for startup in startups_incubated]
        query = query.filter(Startup.startup_id.in_(startup_ids))
    if selected_cities:
        query = query.filter(Startup.location.in_(selected_cities))
    if selected_sectors:
            conditions = []
            for sector in selected_sectors:
                conditions.append(Startup.sector.ilike(f"%{sector}%"))
            query = query.filter(or_(*conditions))
    if selected_status:
        query = query.filter(Startup.status_startup.in_(selected_status))
    if selected_stages:
        query = query.filter(Startup.stage.in_(selected_stages))
    if selected_forms:
        query = query.filter(Startup.forme_juridique.in_(selected_forms))
    
    # Sort
    sort_by = request.args.get('sort', 'funding')
    if sort_by == 'name':
        order = Startup.startup_name.asc()
    elif sort_by == 'funding_asc':
        order = Startup.total_funding_usd.asc()
    else:  # default: funding desc
        order = Startup.total_funding_usd.desc()

    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(
        db.case((Startup.total_funding_usd.isnot(None), 0), else_=1),
        order
    ).paginate(page=page, per_page=20, error_out=False)
    all_startups = pagination.items

    # Get distinct values for filters (from all data, not filtered)
    distinct_cities = db.session.query(Startup.location)\
        .filter(Startup.location.isnot(None))\
        .filter(Startup.location != '')\
        .distinct()\
        .order_by(Startup.location)\
        .all()
    distinct_cities = [city[0] for city in distinct_cities]

    distinct_sectors = get_unique_sectors(Startup.query.all())

    distinct_status = db.session.query(Startup.status_startup)\
        .filter(Startup.status_startup.isnot(None))\
        .filter(Startup.status_startup != '')\
        .distinct()\
        .order_by(Startup.status_startup)\
        .all()
    distinct_status = [status[0] for status in distinct_status]
    
    distinct_stages = db.session.query(Startup.stage)\
        .filter(Startup.stage.isnot(None))\
        .filter(Startup.stage != '')\
        .distinct()\
        .order_by(Startup.stage)\
        .all()
    distinct_stages = [stage[0] for stage in distinct_stages]
    
    distinct_forms = db.session.query(Startup.forme_juridique)\
        .filter(Startup.forme_juridique.isnot(None))\
        .filter(Startup.forme_juridique != '')\
        .distinct()\
        .order_by(Startup.forme_juridique)\
        .all()
    distinct_forms = [form[0] for form in distinct_forms]

    distinct_investors = db.session.query(Investor.investor_id, Investor.investor_name)\
        .filter(Investor.investor_name.isnot(None))\
        .filter(Investor.investor_name != '')\
        .distinct()\
        .order_by(Investor.investor_name)\
        .all()

    distinct_incubators = db.session.query(Incubator.incubator_id, Incubator.incubator)\
        .distinct()\
        .order_by(Incubator.incubator)\
        .all()

    sector_counts = compute_sector_counts(all_startups, distinct_sectors)

    # Total funding raised (from deals, same as home page)
    deals = FundingRound.query.all()
    total_funding = sum(deal.raised_amount_usd if deal.raised_amount_usd is not None else 0 for deal in deals)
    total_funding_millions = total_funding / 1_000_000

    # Chart data: top 5 sectors and cities
    all_startups_full = query.all()
    chart_sector_counts = Counter()
    chart_city_counts = Counter()
    for s in all_startups_full:
        if s.sector:
            for sec in s.sector.split(','):
                chart_sector_counts[sec.strip()] += 1
        if s.location:
            chart_city_counts[s.location] += 1
    top_sectors = dict(chart_sector_counts.most_common(5))
    top_cities = dict(chart_city_counts.most_common(5))

    return render_template(
        "startups.html",
        startups=all_startups,
        distinct_cities=distinct_cities,
        distinct_sectors=distinct_sectors,
        distinct_status=distinct_status,
        distinct_stages=distinct_stages,
        distinct_forms=distinct_forms,
        distinct_investors=distinct_investors,
        distinct_incubators=distinct_incubators,
        selected=request.args,
        sector_counts=sector_counts,
        pagination=pagination,
        top_sectors=top_sectors,
        top_cities=top_cities,
        total_funding_millions=total_funding_millions
    )

@app.route("/incubators")
def incubators():
    query = Incubator.query

    search_query = request.args.get("q", "").strip()
    if search_query:
        query = query.filter(or_(
            Incubator.incubator.ilike(f"%{search_query}%"),
            Incubator.ville_organisme.ilike(f"%{search_query}%")
        ))

    # Multi-select filters
    selected_cities = request.args.getlist("city")
    selected_investementphase = request.args.getlist("phases_investissement")
    selected_startups = request.args.getlist("startup")
    if selected_startups:
        startupsSelected = Startup.query.filter(Startup.startup_id.in_(selected_startups)).all()
        incubatorsFiltered = FilterIncubatorsByStartups(startupsSelected)
        incubator_ids = [incubator.incubator_id for incubator in incubatorsFiltered]
        query = query.filter(Incubator.incubator_id.in_(incubator_ids))
    if selected_cities:
        query = query.filter(Incubator.ville_organisme.in_(selected_cities))
    if selected_investementphase:
            conditions = []
            for invphase in selected_investementphase:
                conditions.append(Incubator.phases_investissement.ilike(f"%{invphase}%"))
            query = query.filter(or_(*conditions))

    # Priority sorting: well-known incubators first, then those with images, then alphabetical
    priority_score = case(
        (Incubator.incubator.ilike('%212 Founders%'), 1),
        (Incubator.incubator.ilike('%Flat6Labs%'), 2),
        (Incubator.incubator.ilike('%Technopark%'), 3),
        (Incubator.incubator.ilike('%Endeavor%'), 4),
        (Incubator.incubator.ilike('%StartGate%'), 5),
        (Incubator.incubator.ilike('%LaStartupFactory%'), 6),
        (Incubator.incubator.ilike('%La Startup Factory%'), 6),
        (Incubator.incubator.ilike('%Plug%Play%'), 7),
        (Incubator.incubator.ilike('%Orange Corners%'), 8),
        (Incubator.incubator.ilike('%Hseven%'), 9),
        (Incubator.incubator.ilike('%UM6P%'), 10),
        (Incubator.incubator.ilike('%Emerging Business Factory%'), 11),
        (Incubator.incubator.ilike('%Bidaya%'), 12),
        (Incubator.incubator.ilike('%Accelab%'), 13),
        (Incubator.incubator.ilike('%New Work Lab%'), 14),
        (Incubator.incubator.ilike('%Enactus%'), 15),
        (Incubator.incubator.ilike('%Impact Lab%'), 16),
        (Incubator.incubator.ilike('%StartUp Maroc%'), 17),
        (Incubator.incubator.ilike('%Climate Launchpad%'), 18),
        (Incubator.incubator.ilike('%CEED%'), 19),
        (Incubator.incubator.ilike('%Open Startup%'), 20),
        else_=50
    )
    has_image = case(
        (Incubator.image_url.isnot(None), 0),
        else_=1
    )
    query = query.order_by(priority_score, has_image, Incubator.incubator)

    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    all_incubators = pagination.items
    distinct_cities = db.session.query(Incubator.ville_organisme)\
    .filter(Incubator.ville_organisme.isnot(None))\
    .filter(Incubator.ville_organisme != '')\
    .distinct()\
    .order_by(Incubator.ville_organisme)\
    .all()
    distinct_cities = [city[0] for city in distinct_cities]
    distinct_investementphase = get_unique_investementphase(Incubator.query.all())
    phase_counts = compute_phaseinvestissement_counts(all_incubators, distinct_investementphase)
    
    # Get all startups for the filter
    distinct_startups = db.session.query(Startup.startup_id, Startup.startup_name, Startup.sector)\
        .filter(Startup.startup_name.isnot(None))\
        .filter(Startup.startup_name != '')\
        .order_by(Startup.startup_name)\
        .all()
    
    try:
        pulse_member_emails = [r[0].lower() for r in db.session.execute(db.text('SELECT email FROM pulse_members')).fetchall()]
    except Exception:
        pulse_member_emails = []

    return render_template(
        "incubators.html",
        incubators=all_incubators,
        distinct_cities=distinct_cities,
        distinct_investementphase=distinct_investementphase,
        distinct_startups=distinct_startups,
        selected=request.args,
        phase_counts=phase_counts,
        pagination=pagination,
        pulse_member_emails=pulse_member_emails
    )

@app.route("/about-us")
def about():
    return render_template("aboutus.html")

@app.route("/startup/<int:startup_id>")
def startup_detail(startup_id):
    startup = Startup.query.get_or_404(startup_id)
    founders = startup.founders
    fundingRounds = startup.funding_rounds
    incubators = startup.incubators
    investors = InvestorsOfStartup(startup)

    # Calculate total funding raised
    total_raised = sum(float(fr.raised_amount_usd) for fr in fundingRounds if fr.raised_amount_usd) if fundingRounds else 0

    # Get investor names from funding rounds (lead_investor + institutional)
    fr_investor_names = set()
    for fr in fundingRounds:
        if fr.lead_investor:
            for name in fr.lead_investor.split(','):
                name = name.strip().rstrip('.')
                if name and name.lower() not in ('undisclosed', 'private investors', 'n/a', ''):
                    fr_investor_names.add(name)
        if fr.institutional_investors:
            for name in fr.institutional_investors.split(','):
                name = name.strip().rstrip('.')
                if name and name.lower() not in ('undisclosed', 'private investors', 'n/a', ''):
                    fr_investor_names.add(name)

    # Match fr_investor_names to real Investor objects (for logos)
    existing_investor_names = {inv.investor_name for inv in investors}
    fr_matched_investors = []
    fr_unmatched_names = set()
    for name in fr_investor_names:
        if name not in existing_investor_names:
            matched = Investor.query.filter(Investor.investor_name.ilike(f"%{name}%")).first()
            if matched and matched.investor_name not in existing_investor_names:
                fr_matched_investors.append(matched)
                existing_investor_names.add(matched.investor_name)
            else:
                fr_unmatched_names.add(name)

    fr_unmatched_names = {name for name in fr_unmatched_names if "verod-kepple" not in name.lower()}

    return render_template("startup_detail.html", startup=startup, founders=founders, fundingRounds=fundingRounds, incubators=incubators, investors=investors, total_raised=total_raised, fr_investor_names=fr_unmatched_names, fr_matched_investors=fr_matched_investors)


@app.route("/founder/<string:founder_id>")
def founder_detail(founder_id):
    founder = Founder.query.get_or_404(founder_id)
    startups = founder.startups
    educations = founder.educations
    experiences = founder.experiences

    return render_template("founder_detail.html", founder=founder, startups=startups,
                           educations=educations, experiences=experiences)

#incubatordetails
@app.route("/incubator/<int:incubator_id>")
def incubator_detail(incubator_id):
    incubator = Incubator.query.get_or_404(incubator_id)
    startups = incubator.startups
    founders = incubator.founders
    return render_template("incubator_detail.html", incubator=incubator, startups=startups, founders=founders)

@app.route("/investors")
def investors():
    from sqlalchemy.orm import subqueryload
    try:
        pulse_member_emails = [r[0].lower() for r in db.session.execute(db.text('SELECT email FROM pulse_members')).fetchall()]
    except Exception:
        pulse_member_emails = []
    query = Investor.query.options(
        subqueryload(Investor.investments)
        .subqueryload(Investment.funding_round)
        .subqueryload(FundingRound.startup)
    ).filter(
        db.or_(
            Investor.investment_count > 0,
            Investor.investments.any(),
            Investor.hq_email.in_(pulse_member_emails) if pulse_member_emails else db.literal(False)
        )
    ).filter(
        Investor.investor_id != 55
    )
    search_query = request.args.get("q", "").strip()
    if search_query:
        query = query.filter(or_(
            Investor.investor_name.ilike(f"%{search_query}%"),
            Investor.primary_investor_type.ilike(f"%{search_query}%"),
            Investor.city.ilike(f"%{search_query}%")
        ))

    selected_locations = request.args.getlist("locations")
    selected_investor_types = request.args.getlist("investor_types")
    selected_startups = request.args.getlist("startups")

    if selected_startups:
        startupsSelected = Startup.query.filter(Startup.startup_id.in_(selected_startups)).all()
        investorsFiltered = FilterInvestorsByStartups(startupsSelected)
        investor_ids = [investor.investor_id for investor in investorsFiltered]
        query = query.filter(Investor.investor_id.in_(investor_ids))
    if selected_locations:
        query = query.filter(Investor.city.in_(selected_locations))
    if selected_investor_types:
        query = query.filter(Investor.primary_investor_type.in_(selected_investor_types))

    # Compute completeness score: count of key non-null fields, with UM6P Ventures (id=25) featured first
    completeness_score = (
        case((Investor.investor_name.isnot(None), 1), else_=0) +
        case((Investor.logo_url.isnot(None), 1), else_=0) +
        case((Investor.description.isnot(None), 1), else_=0) +
        case((Investor.primary_investor_type.isnot(None), 1), else_=0) +
        case((Investor.city.isnot(None), 1), else_=0) +
        case((Investor.hq_location.isnot(None), 1), else_=0) +
        case((Investor.founding_date.isnot(None), 1), else_=0) +
        case((Investor.preferred_industry.isnot(None), 1), else_=0) +
        case((Investor.last_investment_company.isnot(None), 1), else_=0) +
        case((Investor.linkedin_url.isnot(None), 1), else_=0) +
        case((Investor.domain.isnot(None), 1), else_=0) +
        case((Investor.investment_count.isnot(None), 1), else_=0) +
        case((Investor.preferred_investment_types.isnot(None), 1), else_=0) +
        case((Investor.preferred_verticals.isnot(None), 1), else_=0) +
        case((Investor.preferred_geography.isnot(None), 1), else_=0) +
        case((Investor.investor_status.isnot(None), 1), else_=0) +
        case((Investor.facebook_url.isnot(None), 1), else_=0) +
        case((Investor.twitter_url.isnot(None), 1), else_=0)
    )
    # Featured flag: UM6P Ventures always first
    featured = case((Investor.investor_id == 25, 1), else_=0)
    # New Member flag: pulse members get priority when sorted by new joiners
    is_new_member = case(
        (Investor.hq_email.in_(pulse_member_emails) if pulse_member_emails else db.literal(False), 1),
        else_=0
    )

    sort_by = request.args.get("sort", "default")
    if sort_by == "new_joiners":
        query = query.order_by(is_new_member.desc(), featured.desc(), completeness_score.desc(), Investor.investor_name)
    else:
        query = query.order_by(featured.desc(), completeness_score.desc(), Investor.investor_name)

    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page=page, per_page=9, error_out=False)
    all_investors = pagination.items
    distinct_locations = db.session.query(Investor.city)\
        .filter(Investor.city.isnot(None))\
        .filter(Investor.city != '')\
        .distinct()\
        .order_by(Investor.city)\
        .all()
    distinct_locations = [location[0] for location in distinct_locations]

    distinct_investor_types = db.session.query(Investor.primary_investor_type)\
        .filter(Investor.primary_investor_type.isnot(None))\
        .filter(Investor.primary_investor_type != '')\
        .distinct()\
        .order_by(Investor.primary_investor_type)\
        .all()
    distinct_investor_types = [investor_type[0] for investor_type in distinct_investor_types]
    
    # Get all startups for the filter
    distinct_startups = db.session.query(Startup.startup_id, Startup.startup_name, Startup.sector)\
        .filter(Startup.startup_name.isnot(None))\
        .filter(Startup.startup_name != '')\
        .distinct()\
        .order_by(Startup.startup_name)\
        .all()
    
    # View filter: all (default), institutional, non-institutional
    view_filter = request.args.get("view", "all")

    all_funds = Fund.query.order_by(Fund.fund_name).all()

    return render_template(
        "investors.html",
        investors=all_investors,
        view_filter=view_filter,
        distinct_locations=distinct_locations,
        distinct_investor_types=distinct_investor_types,
        distinct_startups=distinct_startups,
        selected=request.args,
        pagination=pagination,
        funds=all_funds,
        pulse_member_emails=pulse_member_emails
    )

@app.route("/investor/<int:investor_id>")
def investor_details(investor_id):
    from sqlalchemy.orm import joinedload
    try:
        pulse_member_emails = [r[0].lower() for r in db.session.execute(db.text('SELECT email FROM pulse_members')).fetchall()]
    except Exception:
        pulse_member_emails = []

    investor = Investor.query.get_or_404(investor_id)
    
    # Explicitly load investments with their funding rounds using eager loading
    investements = Investment.query.options(joinedload(Investment.funding_round).joinedload(FundingRound.startup)).filter(
        Investment.investor_id == investor_id
    ).all()
    
    startups = StartupsInvestedByInvestor(investor)
    # Sort by funding (most funded first)
    startups.sort(key=lambda s: float(s.total_funding_usd or 0), reverse=True)

    # Get all unique funding rounds that are actually loaded
    fundingRounds = []
    seen_round_ids = set()
    for inv in investements:
        if inv.funding_round and inv.funding_round.funding_round_id not in seen_round_ids:
            fundingRounds.append(inv.funding_round)
            seen_round_ids.add(inv.funding_round.funding_round_id)
    
    funds = investor.funds
    return render_template("investor_detail.html", investor=investor, startups=startups,
                            fundingRounds=fundingRounds, investements=investements,
                              funds=funds, pulse_member_emails=pulse_member_emails)


@app.route("/founders")
def founders():
    try:
        pulse_member_emails = [r[0].lower() for r in db.session.execute(db.text('SELECT email FROM pulse_members')).fetchall()]
    except Exception:
        pulse_member_emails = []
    query = Founder.query.filter(
        Founder.name.isnot(None), Founder.name != '',
        db.or_(
            Founder.current_title.isnot(None),
            Founder.profile_pic.isnot(None),
            Founder.location.isnot(None),
            Founder.company_details_name.isnot(None),
            Founder.linkedin_url.isnot(None)
        )
    )
    search_query = request.args.get("q", "").strip()
    selected_cities = request.args.getlist("city")
    selected_startups = request.args.getlist("startup")

    if search_query:
        query = query.filter(
            db.or_(
                Founder.name.ilike(f"%{search_query}%"),
                Founder.first_name.ilike(f"%{search_query}%"),
                Founder.last_name.ilike(f"%{search_query}%"),
                Founder.current_title.ilike(f"%{search_query}%"),
                Founder.current_employer.ilike(f"%{search_query}%"),
                Founder.company_details_name.ilike(f"%{search_query}%"),
                Founder.location.ilike(f"%{search_query}%")
            )
        )
    if selected_cities:
        query = query.filter(Founder.location.in_(selected_cities))
    if selected_startups:
        query = query.filter(Founder.startups.any(Startup.startup_id.in_(selected_startups)))
    # Sort founders by their startup's funding amount (highest first)
    max_funding = db.session.query(
        StartupFounder.founder_id,
        db.func.max(Startup.total_funding_usd).label('max_funding')
    ).join(Startup, StartupFounder.startup_id == Startup.startup_id)\
     .group_by(StartupFounder.founder_id).subquery()

    query = query.outerjoin(max_funding, Founder.founder_id == max_funding.c.founder_id)

    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(
        db.case((max_funding.c.max_funding.isnot(None), 0), else_=1),
        max_funding.c.max_funding.desc(),
        Founder.name.asc()
    ).paginate(page=page, per_page=20, error_out=False)
    all_founders = pagination.items
    distinct_cities = db.session.query(Founder.location)\
        .filter(Founder.location.isnot(None))\
        .filter(Founder.location != '')\
        .distinct()\
        .order_by(Founder.location)\
        .all()
    distinct_cities = [city[0] for city in distinct_cities]
    distinct_startups = db.session.query(Startup.startup_id, Startup.startup_name, Startup.sector)\
        .filter(Startup.startup_name.isnot(None))\
        .filter(Startup.startup_name != '')\
        .distinct()\
        .order_by(Startup.startup_name)\
        .all()

    return render_template(
        "founders.html",
        founders=all_founders,
        distinct_cities=distinct_cities,
        distinct_startups=distinct_startups,
        selected=request.args,
        pagination=pagination,
        pulse_member_emails=pulse_member_emails
    )


@app.route("/funds")
def funds():
    return redirect(url_for('investors', view='funds'))

@app.route("/funding-rounds", methods=["GET"])
def funding_rounds():
    query = FundingRound.query

    search_query = request.args.get("q", "").strip()
    if search_query:
        query = query.filter(or_(
            FundingRound.startup_name.ilike(f"%{search_query}%"),
            FundingRound.round_name.ilike(f"%{search_query}%"),
            FundingRound.lead_investor.ilike(f"%{search_query}%")
        ))

    # Filters from request (plural names to match template checkboxes)
    round_names = request.args.getlist("round_names")
    startup_names = request.args.getlist("startup_names")
    years = request.args.getlist("years")
    countries = request.args.getlist("countries")
    deal_types = request.args.getlist("deal_types")
    lead_investors = request.args.getlist("lead_investors")
    deal_classes = request.args.getlist("deal_classes")
    regions = request.args.getlist("regions")
    cities = request.args.getlist("cities")
    institutional_investors = request.args.getlist("institutional_investors")
    angel_investors = request.args.getlist("angel_investors")

    # Apply filters
    if round_names:
        query = query.filter(FundingRound.round_name.in_(round_names))
    if startup_names:
        query = query.filter(FundingRound.startup_name.in_(startup_names))
    if years:
        query = query.filter(FundingRound.founded_year.in_(years))
    if countries:
        query = query.filter(FundingRound.country.in_(countries))
    if deal_types:
        query = query.filter(FundingRound.deal_type.in_(deal_types))
    if lead_investors:
        query = query.filter(FundingRound.lead_investor.in_(lead_investors))
    if deal_classes:
        query = query.filter(FundingRound.deal_class.in_(deal_classes))
    if regions:
        query = query.filter(FundingRound.region.in_(regions))
    if cities:
        query = query.filter(FundingRound.city.in_(cities))
    if institutional_investors:
        query = query.filter(FundingRound.institutional_investors.in_(institutional_investors))
    if angel_investors:
        query = query.filter(FundingRound.angel_investors.in_(angel_investors))

    # Get distinct values for filters
    distinct_round_names = db.session.query(FundingRound.round_name).filter(FundingRound.round_name.isnot(None)).distinct().order_by(FundingRound.round_name).all()
    distinct_round_names = [r[0] for r in distinct_round_names]
    distinct_startup_names = db.session.query(FundingRound.startup_name).filter(FundingRound.startup_name.isnot(None)).distinct().order_by(FundingRound.startup_name).all()
    distinct_startup_names = [s[0] for s in distinct_startup_names]
    distinct_years = db.session.query(FundingRound.founded_year).filter(FundingRound.founded_year.isnot(None)).distinct().order_by(FundingRound.founded_year).all()
    distinct_years = [y[0] for y in distinct_years]
    distinct_countries = db.session.query(FundingRound.country).filter(FundingRound.country.isnot(None)).distinct().order_by(FundingRound.country).all()
    distinct_countries = [c[0] for c in distinct_countries]
    distinct_deal_types = db.session.query(FundingRound.deal_type).filter(FundingRound.deal_type.isnot(None)).distinct().order_by(FundingRound.deal_type).all()
    distinct_deal_types = [d[0] for d in distinct_deal_types]
    distinct_deal_classes = db.session.query(FundingRound.deal_class).filter(FundingRound.deal_class.isnot(None)).distinct().order_by(FundingRound.deal_class).all()
    distinct_deal_classes = [dc[0] for dc in distinct_deal_classes]
    distinct_regions = db.session.query(FundingRound.region).filter(FundingRound.region.isnot(None)).distinct().order_by(FundingRound.region).all()
    distinct_regions = [r[0] for r in distinct_regions]
    distinct_cities = db.session.query(FundingRound.city).filter(FundingRound.city.isnot(None)).distinct().order_by(FundingRound.city).all()
    distinct_cities = [c[0] for c in distinct_cities]
    distinct_institutional_investors = db.session.query(FundingRound.institutional_investors).filter(FundingRound.institutional_investors.isnot(None)).distinct().order_by(FundingRound.institutional_investors).all()
    distinct_institutional_investors = [ii[0] for ii in distinct_institutional_investors]
    distinct_angel_investors = db.session.query(FundingRound.angel_investors).filter(FundingRound.angel_investors.isnot(None)).distinct().order_by(FundingRound.angel_investors).all()
    distinct_angel_investors = [ai[0] for ai in distinct_angel_investors]
    distinct_lead_investors = db.session.query(FundingRound.lead_investor).filter(FundingRound.lead_investor.isnot(None)).distinct().order_by(FundingRound.lead_investor).all()
    distinct_lead_investors = [l[0] for l in distinct_lead_investors]

    # Chart data: amounts raised by year
    all_rounds_full = query.all()
    year_amounts = {}
    for fr in all_rounds_full:
        if fr.founded_year and fr.raised_amount_usd:
            year = str(fr.founded_year).replace('.0', '')
            year_amounts[year] = year_amounts.get(year, 0) + float(fr.raised_amount_usd)
    year_amounts = dict(sorted(year_amounts.items()))

    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    rounds = pagination.items
    return render_template(
        "funding_rounds.html",
        funding_rounds=rounds,
        distinct_round_names=distinct_round_names,
        distinct_startup_names=distinct_startup_names,
        distinct_years=distinct_years,
        distinct_countries=distinct_countries,
        distinct_deal_types=distinct_deal_types,
        distinct_deal_classes=distinct_deal_classes,
        distinct_regions=distinct_regions,
        distinct_cities=distinct_cities,
        distinct_institutional_investors=distinct_institutional_investors,
        distinct_angel_investors=distinct_angel_investors,
        distinct_lead_investors=distinct_lead_investors,
        selected=request.args,
        pagination=pagination,
        year_amounts=year_amounts
    )

## ============================================
## JOIN THE PULSE - Registration Flow
## ============================================

def send_confirmation_email(member):
    """Send confirmation email via Resend (prod) or Gmail SMTP (local fallback)."""
    confirm_url = url_for('confirm_email', token=member.confirmation_token, _external=True)
    html_content = render_template("emails/confirmation.html",
                                   name=member.full_name,
                                   confirm_url=confirm_url,
                                   role=member.role)
    # Try Resend first (production)
    if RESEND_API_KEY and resend:
        try:
            resend.Emails.send({
                "from": "The Pulse <contact@thepulse.ma>",
                "to": [member.email],
                "subject": "Confirmez votre inscription - The Pulse",
                "html": html_content,
            })
            print(f"[EMAIL OK via Resend] Confirmation sent to {member.email}", flush=True)
            return
        except Exception as e:
            print(f"[RESEND ERROR] {e} — falling back to Gmail SMTP", flush=True)

    # Gmail SMTP fallback (local dev)
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Confirmez votre inscription - The Pulse"
        msg["From"] = f"The Pulse <{GMAIL_USER}>"
        msg["To"] = member.email
        msg.attach(MIMEText(html_content, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            smtp.sendmail(GMAIL_USER, member.email, msg.as_string())
        print(f"[EMAIL OK via Gmail] Confirmation sent to {member.email}", flush=True)
    except Exception as e:
        print(f"[EMAIL ERROR] {e} — member {member.email} can confirm at {confirm_url}", flush=True)

def register_pulse_member(email, full_name, role, form_data_dict):
    """Create a PulseMember, auto-confirm, and try to send email. Returns (member, error)."""
    existing = PulseMember.query.filter_by(email=email).first()
    if existing and existing.is_confirmed:
        return existing, "Cette adresse email est déjà utilisée. <a href='/member-login'>Connectez-vous</a> pour accéder à votre profil."
    if existing and not existing.is_confirmed:
        existing.confirmation_token = str(uuid.uuid4())
        existing.full_name = full_name
        existing.role = role
        existing.is_confirmed = True
        existing.form_data = json.dumps(form_data_dict, ensure_ascii=False)
        db.session.commit()
        send_confirmation_email(existing)
        session["member_id"] = existing.id
        return existing, None

    member = PulseMember(
        email=email,
        full_name=full_name,
        role=role,
        confirmation_token=str(uuid.uuid4()),
        is_confirmed=True,
        form_data=json.dumps(form_data_dict, ensure_ascii=False)
    )
    db.session.add(member)
    db.session.commit()
    send_confirmation_email(member)
    session["member_id"] = member.id
    return member, None

## ============================================
## SEARCH API + JOIN FLOW
## ============================================

ROLE_CONFIG = {
    'entrepreneur': {'model': 'Startup', 'name_field': 'startup_name', 'id_field': 'startup_id', 'form_route': '/entrepreneur-form', 'edit_param': 'startup_id', 'label': 'Startup'},
    'investor': {'model': 'Investor', 'name_field': 'investor_name', 'id_field': 'investor_id', 'form_route': '/investor-form', 'edit_param': 'investor_id', 'label': 'Investisseur'},
    'program': {'model': 'Incubator', 'name_field': 'incubator', 'id_field': 'incubator_id', 'form_route': '/program-form', 'edit_param': 'incubator_id', 'label': 'Programme'},
    'incubator': {'model': 'Incubator', 'name_field': 'incubator', 'id_field': 'incubator_id', 'form_route': '/program-form?type=incubator', 'edit_param': 'incubator_id', 'label': 'Incubateur'},
    'talent': {'model': 'Founder', 'name_field': 'name', 'id_field': 'founder_id', 'form_route': '/talent-form', 'edit_param': 'founder_id', 'label': 'Talent / Fondateur'},
}

@app.route("/api/search/<role>")
def api_search(role):
    q = request.args.get("q", "").strip()
    config = ROLE_CONFIG.get(role)
    if not config or len(q) < 2:
        return jsonify([])
    model_class = globals().get(config['model'])
    name_field = getattr(model_class, config['name_field'])
    results = model_class.query.filter(name_field.ilike(f"%{q}%")).limit(8).all()
    items = []
    for r in results:
        name = getattr(r, config['name_field']) or "Sans nom"
        rid = getattr(r, config['id_field'])
        desc = getattr(r, 'description', None) or getattr(r, 'type_organisme', None) or ""
        if desc and len(desc) > 80:
            desc = desc[:80] + "..."
        form_url = config['form_route']
        sep = '&' if '?' in form_url else '?'
        edit_url = f"{form_url}{sep}{config['edit_param']}={rid}"
        items.append({"id": rid, "name": name, "description": desc, "url": edit_url})
    return jsonify(items)

@app.route("/join/<role>")
def join_search(role):
    config = ROLE_CONFIG.get(role)
    if not config:
        return redirect(url_for("join"))
    return render_template("join-search.html", role=role, config=config)

@app.context_processor
def inject_current_member():
    """Make current_member and unread_count available in all templates."""
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
    return {"current_member": None, "unread_count": 0}

@app.route("/join")
def join():
    return render_template("join.html")

@app.route("/entrepreneur-form", methods=["GET", "POST"])
def entrepreneur_form():
    startup_id = request.args.get("startup_id")
    existing = Startup.query.get(startup_id) if startup_id else None
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        full_name = request.form.get("full_name", "").strip()
        form_data = {k: v for k, v in request.form.items() if k not in ('email', 'full_name')}
        # Update existing startup if editing
        if existing:
            for key, val in form_data.items():
                if val and hasattr(existing, key):
                    setattr(existing, key, val)
            db.session.commit()
        member, error = register_pulse_member(email, full_name, "entrepreneur", form_data)
        if error:
            incubators = Incubator.query.all()
            investors = Investor.query.all()
            return render_template("entrepreneur-form.html", incubators=incubators, investors=investors, error=error, startup=existing)
        return render_template("email-sent.html", email=email)
    incubators = Incubator.query.all()
    investors = Investor.query.all()
    return render_template("entrepreneur-form.html", incubators=incubators, investors=investors, startup=existing)

@app.route("/investor-form", methods=["GET", "POST"])
def investor_form():
    inv_id = request.args.get("investor_id")
    existing = Investor.query.get(inv_id) if inv_id else None
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        full_name = request.form.get("full_name", "").strip()
        form_data = {k: v for k, v in request.form.items() if k not in ('email', 'full_name')}
        if existing:
            for key, val in form_data.items():
                if val and hasattr(existing, key):
                    setattr(existing, key, val)
            db.session.commit()
        member, error = register_pulse_member(email, full_name, "investor", form_data)
        if error:
            return render_template("investor-form.html", error=error, investor=existing)
        return render_template("email-sent.html", email=email)
    return render_template("investor-form.html", investor=existing)

@app.route("/program-form", methods=["GET", "POST"])
def program_form():
    inc_id = request.args.get("incubator_id")
    existing = Incubator.query.get(inc_id) if inc_id else None
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        full_name = request.form.get("full_name", "").strip()
        form_data = {k: v for k, v in request.form.items() if k not in ('email', 'full_name')}
        role = "incubator" if request.args.get("type") == "incubator" else "program"
        if existing:
            for key, val in form_data.items():
                if val and hasattr(existing, key):
                    setattr(existing, key, val)
            db.session.commit()
        member, error = register_pulse_member(email, full_name, role, form_data)
        if error:
            return render_template("program-form.html", error=error, program=existing)
        return render_template("email-sent.html", email=email)
    return render_template("program-form.html", program=existing)

@app.route("/talent-form", methods=["GET", "POST"])
def talent_form():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        full_name = request.form.get("full_name", "").strip()
        form_data = {k: v for k, v in request.form.items() if k not in ('email', 'full_name')}

        # Check if talent with this email already exists
        existing_talent = Talent.query.filter(db.func.lower(Talent.email) == email.lower()).first()
        if existing_talent:
            return render_template("talent-form.html",
                error="Cette adresse email est déjà utilisée. <a href='" + url_for('member_login') + "'>Connectez-vous</a> pour accéder à votre profil.")

        # Also save to Talent table for the talent directory
        new_talent = Talent(
            full_name=full_name,
            email=email,
            phone=request.form.get("phone"),
            location=request.form.get("location"),
            current_title=request.form.get("current_title"),
            years_experience=request.form.get("years_experience"),
            professional_bio=request.form.get("professional_bio"),
            skills=request.form.get("skills"),
            industries_of_interest=request.form.get("industries_of_interest"),
            role_type=request.form.get("role_type"),
            work_format=request.form.get("work_format"),
            salary_range=request.form.get("salary_range"),
            availability=request.form.get("availability"),
            looking_for=request.form.get("looking_for"),
            linkedin_url=request.form.get("linkedin_url"),
            portfolio_website=request.form.get("portfolio_website"),
            github_profile=request.form.get("github_profile"),
            other_profile=request.form.get("other_profile"),
            education=request.form.get("education"),
            achievements=request.form.get("achievements"),
            languages=request.form.get("languages")
        )
        db.session.add(new_talent)
        db.session.commit()

        member, error = register_pulse_member(email, full_name, "talent", form_data)
        if error:
            return render_template("talent-form.html", error=error)
        return render_template("email-sent.html", email=email)
    return render_template("talent-form.html")

## ============================================
## EMAIL CONFIRMATION + PROFILE SETUP
## ============================================

@app.route("/confirm/<token>")
def confirm_email(token):
    member = PulseMember.query.filter_by(confirmation_token=token).first()
    if not member:
        return render_template("email-sent.html", error="Lien de confirmation invalide ou expire.")
    member.is_confirmed = True
    db.session.commit()
    return redirect(url_for("complete_profile", member_id=member.id))

@app.route("/complete-profile/<int:member_id>", methods=["GET", "POST"])
def complete_profile(member_id):
    member = PulseMember.query.get_or_404(member_id)
    if not member.is_confirmed:
        return redirect(url_for("join"))
    if request.method == "POST":
        file = request.files.get("profile_pic")
        if file and file.filename and allowed_file(file.filename):
            try:
                file_data = file.read()
                # Limit to 2MB to avoid DB issues
                if len(file_data) > 2 * 1024 * 1024:
                    return render_template("complete-profile.html", member=member,
                        error="La photo est trop lourde. Maximum 2MB.")
                ext = file.filename.rsplit('.', 1)[1].lower()
                b64 = base64.b64encode(file_data).decode('utf-8')
                member.profile_pic = f"data:image/{ext};base64,{b64}"
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"[UPLOAD ERROR] {e}", flush=True)
                return render_template("complete-profile.html", member=member,
                    error="Erreur lors de l'upload. Essayez avec une image plus petite.")
        return redirect(url_for("my_profile", member_id=member.id))
    return render_template("complete-profile.html", member=member)

@app.route("/my-profile/<int:member_id>")
def my_profile(member_id):
    from datetime import datetime
    member = PulseMember.query.get_or_404(member_id)
    form_data = json.loads(member.form_data) if member.form_data else {}
    return render_template("my-profile.html", member=member, form_data=form_data, now=datetime.now())

@app.route("/logout-member")
def logout_member():
    session.pop("member_id", None)
    return redirect(url_for("home"))

@app.route("/member-login", methods=["GET", "POST"])
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
            error = "Vous n'avez pas encore défini de mot de passe. Utilisez le lien reçu par email pour accéder à votre profil, puis créez un mot de passe."
        else:
            error = "Email ou mot de passe incorrect."
    return render_template("member-login.html", error=error)

@app.route("/edit-profile/<int:member_id>", methods=["GET", "POST"])
def edit_profile(member_id):
    member = PulseMember.query.get_or_404(member_id)
    form_data = json.loads(member.form_data) if member.form_data else {}
    if request.method == "POST":
        try:
            member.full_name = request.form.get("full_name", member.full_name).strip()
            member.role = request.form.get("role", member.role)
            file = request.files.get("profile_pic")
            if file and file.filename and allowed_file(file.filename):
                file_data = file.read()
                ext = file.filename.rsplit('.', 1)[1].lower()
                b64 = base64.b64encode(file_data).decode('utf-8')
                member.profile_pic = f"data:image/{ext};base64,{b64}"
            # Update form_data fields
            reserved = {'full_name', 'role', 'profile_pic', 'csrf_token'}
            for key in request.form:
                if key not in reserved:
                    val = request.form.get(key, "").strip()
                    form_data[key] = val
            member.form_data = json.dumps(form_data, ensure_ascii=False)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"[EDIT PROFILE ERROR] {e}", flush=True)
            return render_template("edit-profile.html", member=member, form_data=form_data)
        return redirect(url_for("my_profile", member_id=member_id))
    return render_template("edit-profile.html", member=member, form_data=form_data)

@app.route("/set-password/<int:member_id>", methods=["GET", "POST"])
def set_password(member_id):
    member = PulseMember.query.get_or_404(member_id)
    error = None
    success = None
    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if len(password) < 8:
            error = "Password must be at least 8 characters."
        elif password != confirm:
            error = "Passwords do not match."
        else:
            member.password_hash = generate_password_hash(password)
            db.session.commit()
            success = "Password set successfully!"
    return render_template("set-password.html", member=member, error=error, success=success)

@app.route("/delete-account/<int:member_id>", methods=["POST"])
def delete_account(member_id):
    member = PulseMember.query.get_or_404(member_id)
    db.session.delete(member)
    db.session.commit()
    session.pop("member_id", None)
    return redirect(url_for("home"))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    message = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        member = PulseMember.query.filter_by(email=email).first()
        if member:
            token = str(uuid.uuid4())
            member.confirmation_token = token
            db.session.commit()
            reset_url = url_for("reset_password", token=token, _external=True)
            # Send reset email
            html = render_template("emails/reset_password.html", name=member.full_name.split()[0], reset_url=reset_url)
            print(f"[RESET] Sending reset email to {member.email}, RESEND_API_KEY set: {bool(RESEND_API_KEY)}, resend module: {bool(resend)}", flush=True)
            try:
                if RESEND_API_KEY and resend:
                    result = resend.Emails.send({
                        "from": "The Pulse <contact@thepulse.ma>",
                        "to": [member.email],
                        "subject": "Réinitialisation de votre mot de passe - The Pulse",
                        "html": html,
                    })
                    print(f"[RESET OK via Resend] {result}", flush=True)
                else:
                    print(f"[RESET] Falling back to Gmail SMTP", flush=True)
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = "Réinitialisation de votre mot de passe - The Pulse"
                    msg["From"] = f"The Pulse <{GMAIL_USER}>"
                    msg["To"] = member.email
                    msg.attach(MIMEText(html, "html"))
                    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                        smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
                        smtp.sendmail(GMAIL_USER, member.email, msg.as_string())
                    print(f"[RESET OK via Gmail]", flush=True)
            except Exception as e:
                print(f"[RESET EMAIL ERROR] {e}", flush=True)
        message = "Si cette adresse existe, un lien de réinitialisation a été envoyé."
    return render_template("forgot-password.html", message=message)

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    member = PulseMember.query.filter_by(confirmation_token=token).first_or_404()
    error = None
    success = None
    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if len(password) < 8:
            error = "Le mot de passe doit contenir au moins 8 caractères."
        elif password != confirm:
            error = "Les mots de passe ne correspondent pas."
        else:
            member.password_hash = generate_password_hash(password)
            member.confirmation_token = str(uuid.uuid4())  # invalidate token
            db.session.commit()
            session["member_id"] = member.id
            success = "Mot de passe mis à jour avec succès !"
    return render_template("reset-password.html", member=member, error=error, success=success, token=token)

@app.route("/talents")
def talents():
    query = Talent.query
    search = request.args.get("search", "").strip()
    selected_role = request.args.get("role_type", "")
    selected_availability = request.args.get("availability", "")

    if search:
        query = query.filter(
            db.or_(
                Talent.full_name.ilike(f"%{search}%"),
                Talent.skills.ilike(f"%{search}%"),
                Talent.current_title.ilike(f"%{search}%"),
                Talent.industries_of_interest.ilike(f"%{search}%")
            )
        )
    if selected_role:
        query = query.filter(Talent.role_type == selected_role)
    if selected_availability:
        query = query.filter(Talent.availability == selected_availability)

    all_talents = query.all()
    return render_template("talents.html", talents=all_talents, search=search, selected_role=selected_role, selected_availability=selected_availability)

## ============================================
## TOOLBOX AI
## ============================================

@app.route("/toolbox")
def toolbox():
    return render_template("toolbox.html")


## ============================================
## CO-FOUNDERS
## ============================================

@app.route("/cofounders")
def cofounders():
    query = CofounderProject.query
    search = request.args.get("search", "").strip()
    selected_stage = request.args.get("stage", "")
    selected_domain = request.args.get("domain", "")
    selected_commitment = request.args.get("commitment", "")

    if search:
        query = query.filter(
            db.or_(
                CofounderProject.project_title.ilike(f"%{search}%"),
                CofounderProject.description.ilike(f"%{search}%"),
                CofounderProject.skills_needed.ilike(f"%{search}%"),
                CofounderProject.domain.ilike(f"%{search}%")
            )
        )
    if selected_stage:
        query = query.filter(CofounderProject.project_stage == selected_stage)
    if selected_domain:
        query = query.filter(CofounderProject.domain.ilike(f"%{selected_domain}%"))
    if selected_commitment:
        query = query.filter(CofounderProject.commitment_type == selected_commitment)

    all_projects = query.order_by(CofounderProject.created_at.desc()).all()
    return render_template("cofounders.html", projects=all_projects, search=search,
                         selected_stage=selected_stage, selected_domain=selected_domain,
                         selected_commitment=selected_commitment)

@app.route("/cofounder-form", methods=["GET", "POST"])
def cofounder_form():
    if request.method == "POST":
        new_project = CofounderProject(
            project_title=request.form.get("project_title"),
            description=request.form.get("description"),
            domain=request.form.get("domain"),
            skills_needed=request.form.get("skills_needed"),
            project_stage=request.form.get("project_stage"),
            author_name=request.form.get("author_name"),
            author_email=request.form.get("author_email"),
            author_affiliation=request.form.get("author_affiliation"),
            author_linkedin=request.form.get("author_linkedin"),
            roles_needed=request.form.get("roles_needed"),
            commitment_type=request.form.get("commitment_type"),
            location_preference=request.form.get("location_preference"),
            equity_offered=request.form.get("equity_offered"),
            contact_info=request.form.get("contact_info")
        )
        db.session.add(new_project)
        db.session.commit()
        return redirect(url_for("cofounders"))
    return render_template("cofounder-form.html")


## ============================================
## EXPERTS
## ============================================

@app.route("/expert/<int:expert_id>")
def expert_detail(expert_id):
    from datetime import datetime
    expert = Expert.query.get_or_404(expert_id)
    return render_template("expert-detail.html", expert=expert, now=datetime.now())


@app.route("/experts")
def experts():
    query = Expert.query
    search = request.args.get("search", "").strip()
    selected_domain = request.args.get("domain", "")
    selected_availability = request.args.get("availability", "")

    if search:
        query = query.filter(
            db.or_(
                Expert.full_name.ilike(f"%{search}%"),
                Expert.skills.ilike(f"%{search}%"),
                Expert.current_title.ilike(f"%{search}%"),
                Expert.expertise_domain.ilike(f"%{search}%"),
                Expert.organization.ilike(f"%{search}%")
            )
        )
    if selected_domain:
        query = query.filter(Expert.expertise_domain == selected_domain)
    if selected_availability:
        query = query.filter(Expert.availability == selected_availability)

    all_experts = query.order_by(Expert.created_at.desc()).all()
    # Deduplicate by email — keep only the most recent entry per email
    seen_emails = set()
    unique_experts = []
    for expert in all_experts:
        key = (expert.email or "").strip().lower()
        if key and key in seen_emails:
            continue
        if key:
            seen_emails.add(key)
        unique_experts.append(expert)

    # Also include PulseMembers with role "expert" who are NOT already in experts table
    expert_members = PulseMember.query.filter_by(role="expert", is_confirmed=True).all()
    for m in expert_members:
        key = (m.email or "").strip().lower()
        if key and key in seen_emails:
            continue
        if key:
            seen_emails.add(key)
        # Parse form_data for extra fields
        import json as _json
        fd = {}
        if m.form_data:
            try:
                fd = _json.loads(m.form_data)
            except Exception:
                pass
        # Build a lightweight object that looks like an Expert for the template
        class _ExpertProxy:
            pass
        proxy = _ExpertProxy()
        proxy.expert_id = None  # Not a real Expert row
        proxy.full_name = m.full_name
        proxy.email = m.email
        proxy.profile_pic = m.profile_pic
        proxy.current_title = fd.get("current_title", "")
        proxy.organization = fd.get("organization") or fd.get("company_name", "")
        proxy.location = fd.get("location") or fd.get("city", "")
        proxy.expertise_domain = fd.get("expertise_domain", "")
        proxy.years_experience = fd.get("years_experience", "")
        proxy.skills = fd.get("skills", "")
        proxy.services_offered = fd.get("services_offered", "")
        proxy.target_audience = fd.get("target_audience", "")
        proxy.availability = fd.get("availability", "")
        proxy.linkedin_url = fd.get("linkedin_url") or fd.get("linkedin", "")
        proxy.portfolio_website = fd.get("portfolio_website") or fd.get("website", "")
        proxy.created_at = m.created_at
        # Apply same search/domain/availability filters
        if search:
            s = search.lower()
            haystack = " ".join([
                proxy.full_name or "", proxy.skills or "", proxy.current_title or "",
                proxy.expertise_domain or "", proxy.organization or ""
            ]).lower()
            if s not in haystack:
                continue
        if selected_domain and proxy.expertise_domain != selected_domain:
            continue
        if selected_availability and proxy.availability != selected_availability:
            continue
        unique_experts.append(proxy)

    all_experts = unique_experts
    from datetime import datetime
    return render_template("experts.html", experts=all_experts, search=search,
                         selected_domain=selected_domain, selected_availability=selected_availability,
                         now=datetime.now())

@app.route("/expert-form", methods=["GET", "POST"])
def expert_form():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        full_name = request.form.get("full_name", "").strip()
        form_data = {k: v for k, v in request.form.items() if k not in ('email', 'full_name')}

        # Check if expert with this email already exists
        existing_expert = Expert.query.filter(db.func.lower(Expert.email) == email.lower()).first()
        if existing_expert:
            return render_template("expert-form.html",
                error="Cette adresse email est déjà utilisée. <a href='" + url_for('member_login') + "'>Connectez-vous</a> pour accéder à votre profil.")

        new_expert = Expert(
            full_name=full_name,
            email=email,
            phone=request.form.get("phone"),
            location=request.form.get("location"),
            current_title=request.form.get("current_title"),
            organization=request.form.get("organization"),
            expertise_domain=request.form.get("expertise_domain"),
            years_experience=request.form.get("years_experience"),
            professional_bio=request.form.get("professional_bio"),
            skills=request.form.get("skills"),
            industries_of_interest=request.form.get("industries_of_interest"),
            services_offered=request.form.get("services_offered"),
            target_audience=request.form.get("target_audience"),
            availability=request.form.get("availability"),
            linkedin_url=request.form.get("linkedin_url"),
            portfolio_website=request.form.get("portfolio_website"),
            other_profile=request.form.get("other_profile"),
            achievements=request.form.get("achievements"),
            languages=request.form.get("languages")
        )
        db.session.add(new_expert)
        db.session.commit()

        member, error = register_pulse_member(email, full_name, "expert", form_data)
        if error:
            return render_template("expert-form.html", error=error)
        return render_template("email-sent.html", email=email)
    return render_template("expert-form.html")


## ============================================
## ACTUALITÉS
## ============================================

@app.route("/actualites")
def actualites():
    query = Article.query
    search = request.args.get("search", "").strip()
    selected_category = request.args.get("category", "")

    if search:
        query = query.filter(
            db.or_(
                Article.title.ilike(f"%{search}%"),
                Article.summary.ilike(f"%{search}%"),
                Article.tags.ilike(f"%{search}%")
            )
        )
    if selected_category:
        query = query.filter(Article.category == selected_category)

    all_articles = query.order_by(Article.published_at.desc()).all()
    featured = [a for a in all_articles if a.is_featured]
    return render_template("actualites.html", articles=all_articles, featured=featured,
                         search=search, selected_category=selected_category)

@app.route("/article/<int:article_id>")
def article_detail(article_id):
    article = Article.query.get_or_404(article_id)
    return render_template("article_detail.html", article=article)

@app.route("/article-form", methods=["GET", "POST"])
def article_form():
    if request.method == "POST":
        new_article = Article(
            title=request.form.get("title"),
            content=request.form.get("content"),
            summary=request.form.get("summary"),
            category=request.form.get("category"),
            source=request.form.get("source"),
            source_url=request.form.get("source_url"),
            author=request.form.get("author"),
            image_url=request.form.get("image_url"),
            tags=request.form.get("tags"),
            is_featured=bool(request.form.get("is_featured"))
        )
        db.session.add(new_article)
        db.session.commit()
        return redirect(url_for("actualites"))
    return render_template("article-form.html")


## ============================================
## RESSOURCES
## ============================================

@app.route("/ressources")
def ressources():
    query = Resource.query
    search = request.args.get("search", "").strip()
    selected_category = request.args.get("category", "")
    selected_type = request.args.get("type", "")

    if search:
        query = query.filter(
            db.or_(
                Resource.title.ilike(f"%{search}%"),
                Resource.description.ilike(f"%{search}%"),
                Resource.tags.ilike(f"%{search}%"),
                Resource.organization.ilike(f"%{search}%")
            )
        )
    if selected_category:
        query = query.filter(Resource.category == selected_category)
    if selected_type:
        query = query.filter(Resource.resource_type == selected_type)

    all_resources = query.order_by(Resource.created_at.desc()).all()
    return render_template("ressources.html", resources=all_resources, search=search,
                         selected_category=selected_category, selected_type=selected_type)

@app.route("/resource-form", methods=["GET", "POST"])
def resource_form():
    if request.method == "POST":
        new_resource = Resource(
            title=request.form.get("title"),
            description=request.form.get("description"),
            category=request.form.get("category"),
            resource_type=request.form.get("resource_type"),
            url=request.form.get("url"),
            organization=request.form.get("organization"),
            tags=request.form.get("tags"),
            is_featured=bool(request.form.get("is_featured"))
        )
        db.session.add(new_resource)
        db.session.commit()
        return redirect(url_for("ressources"))
    return render_template("resource-form.html")


@app.route("/api/global-search")
def api_global_search():
    q = request.args.get("q", "").strip()
    if not q or len(q) < 2:
        return jsonify({"startups": [], "founders": [], "investors": [], "incubators": []})

    pattern = f"%{q}%"
    results = {}

    # Startups
    startups = Startup.query.filter(Startup.startup_name.ilike(pattern)).limit(5).all()
    results["startups"] = [
        {
            "name": s.startup_name,
            "type": "Startup",
            "url": f"/startup/{s.startup_id}",
            "subtitle": s.sector
        }
        for s in startups if s.startup_name
    ]

    # Founders
    founders = Founder.query.filter(Founder.name.ilike(pattern)).limit(5).all()
    results["founders"] = [
        {
            "name": f.name,
            "type": "Founder",
            "url": f"/founder/{f.founder_id}",
            "subtitle": f.current_title
        }
        for f in founders if f.name
    ]

    # Investors
    investors = Investor.query.filter(Investor.investor_name.ilike(pattern)).limit(5).all()
    results["investors"] = [
        {
            "name": i.investor_name,
            "type": "Investor",
            "url": f"/investor/{i.investor_id}",
            "subtitle": i.primary_investor_type
        }
        for i in investors if i.investor_name
    ]

    # Incubators
    incubators = Incubator.query.filter(Incubator.incubator.ilike(pattern)).limit(5).all()
    results["incubators"] = [
        {
            "name": inc.incubator,
            "type": "Incubator",
            "url": f"/incubator/{inc.incubator_id}",
            "subtitle": inc.type_organisme
        }
        for inc in incubators if inc.incubator
    ]

    return jsonify(results)


@app.route('/api/map-data')
def map_data():
    from sqlalchemy import func as sqlfunc
    results = db.session.query(
        Startup.location, sqlfunc.count(Startup.startup_id)
    ).filter(Startup.location.isnot(None), Startup.location != '').group_by(Startup.location).all()

    city_coords = {
        'Casablanca': [33.5731, -7.5898],
        'Rabat': [34.0209, -6.8416],
        'Marrakech': [31.6295, -7.9811],
        'Tanger': [35.7595, -5.8340],
        'Fès': [34.0181, -5.0078],
        'Agadir': [30.4278, -9.5981],
        'Oujda': [34.6814, -1.9086],
        'Kénitra': [34.2610, -6.5802],
        'Tétouan': [35.5889, -5.3626],
        'Meknès': [33.8935, -5.5547],
        'Mohammedia': [33.6866, -7.3831],
        'Benguerir': [32.2333, -7.9500],
        'Laâyoune': [27.1536, -13.2033],
        'Dakhla': [23.7148, -15.9370],
        'Guelmim': [28.9833, -10.0500],
        'Tan-Tan': [28.4378, -11.1028],
        'Settat': [33.0011, -7.6166],
        'El Jadida': [33.2316, -8.5007],
        'Safi': [32.2994, -9.2372],
        'Nador': [35.1688, -2.9287],
        'Khouribga': [32.8811, -6.9063],
        'Beni Mellal': [32.3373, -6.3498],
        'Morocco': [31.7917, -7.0926],
    }

    data = []
    for city, count in results:
        city_clean = city.strip()
        coords = city_coords.get(city_clean)
        if not coords:
            for key, val in city_coords.items():
                if key.lower() in city_clean.lower() or city_clean.lower() in key.lower():
                    coords = val
                    break
        if coords:
            data.append({'city': city_clean, 'count': count, 'lat': coords[0], 'lng': coords[1]})

    return jsonify(data)



# ============================================
#   CSV EXPORT ROUTES
# ============================================

@app.route("/startups/export")
def startups_export():
    query = Startup.query

    selected_cities = request.args.getlist("city")
    selected_sectors = request.args.getlist("sector")
    selected_status = request.args.getlist("status")
    selected_stages = request.args.getlist("stage")
    selected_forms = request.args.getlist("forme")
    selected_investors = request.args.getlist("investor")
    selected_incubators = request.args.getlist("incubator")

    if selected_investors:
        investorsSelected = Investor.query.filter(Investor.investor_id.in_(selected_investors)).all()
        startups_invested = StartupsInvestedByListOfInvestors(investorsSelected)
        startup_ids = [s.startup_id for s in startups_invested]
        query = query.filter(Startup.startup_id.in_(startup_ids))
    if selected_incubators:
        incubatorsSelected = Incubator.query.filter(Incubator.incubator_id.in_(selected_incubators)).all()
        startups_incubated = StartupsIncubatedByListOfIncubators(incubatorsSelected)
        startup_ids = [s.startup_id for s in startups_incubated]
        query = query.filter(Startup.startup_id.in_(startup_ids))
    if selected_cities:
        query = query.filter(Startup.location.in_(selected_cities))
    if selected_sectors:
        conditions = []
        for sector in selected_sectors:
            conditions.append(Startup.sector.ilike(f"%{sector}%"))
        query = query.filter(or_(*conditions))
    if selected_status:
        query = query.filter(Startup.status_startup.in_(selected_status))
    if selected_stages:
        query = query.filter(Startup.stage.in_(selected_stages))
    if selected_forms:
        query = query.filter(Startup.forme_juridique.in_(selected_forms))

    all_startups = query.order_by(
        db.case((Startup.total_funding_usd.isnot(None), 0), else_=1),
        Startup.total_funding_usd.desc()
    ).all()

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['Name', 'Sector', 'Location', 'Region', 'Stage', 'Website'])
    for s in all_startups:
        writer.writerow([
            s.startup_name or '',
            s.sector or '',
            s.location or '',
            s.region or '',
            s.stage or '',
            s.homepage_url or ''
        ])

    output = si.getvalue()
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=startups_export.csv'}
    )


@app.route("/investors/export")
def investors_export():
    from sqlalchemy.orm import subqueryload
    query = Investor.query.options(
        subqueryload(Investor.investments)
        .subqueryload(Investment.funding_round)
        .subqueryload(FundingRound.startup)
    )

    selected_locations = request.args.getlist("locations")
    selected_investor_types = request.args.getlist("investor_types")
    selected_startups = request.args.getlist("startups")

    if selected_startups:
        startupsSelected = Startup.query.filter(Startup.startup_id.in_(selected_startups)).all()
        investorsFiltered = FilterInvestorsByStartups(startupsSelected)
        investor_ids = [inv.investor_id for inv in investorsFiltered]
        query = query.filter(Investor.investor_id.in_(investor_ids))
    if selected_locations:
        query = query.filter(Investor.city.in_(selected_locations))
    if selected_investor_types:
        query = query.filter(Investor.primary_investor_type.in_(selected_investor_types))

    all_investors = query.all()

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['Name', 'Type', 'Location', 'Status', 'Investment Count'])
    for inv in all_investors:
        writer.writerow([
            inv.investor_name or '',
            inv.primary_investor_type or '',
            inv.city or '',
            inv.investor_status or '',
            inv.investment_count or ''
        ])

    output = si.getvalue()
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=investors_export.csv'}
    )


@app.route("/founders/export")
def founders_export():
    query = Founder.query
    selected_cities = request.args.getlist("city")
    selected_startups = request.args.getlist("startup")

    if selected_cities:
        query = query.filter(Founder.location.in_(selected_cities))
    if selected_startups:
        query = query.filter(Founder.startups.any(Startup.startup_id.in_(selected_startups)))

    all_founders = query.all()

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['Name', 'Title', 'Company', 'Location'])
    for f in all_founders:
        name = f.name or ''
        if not name and (f.first_name or f.last_name):
            name = ((f.first_name or '') + ' ' + (f.last_name or '')).strip()
        writer.writerow([
            name,
            f.current_title or '',
            f.company_details_name or '',
            f.location or ''
        ])

    output = si.getvalue()
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=founders_export.csv'}
    )


@app.route("/funding-rounds/export")
def funding_rounds_export():
    query = FundingRound.query

    round_names = request.args.getlist("round_names")
    startup_names = request.args.getlist("startup_names")
    years = request.args.getlist("years")
    countries = request.args.getlist("countries")
    deal_types = request.args.getlist("deal_types")
    lead_investors = request.args.getlist("lead_investors")
    deal_classes = request.args.getlist("deal_classes")
    regions = request.args.getlist("regions")
    cities = request.args.getlist("cities")
    institutional_investors = request.args.getlist("institutional_investors")
    angel_investors = request.args.getlist("angel_investors")

    if round_names:
        query = query.filter(FundingRound.round_name.in_(round_names))
    if startup_names:
        query = query.filter(FundingRound.startup_name.in_(startup_names))
    if years:
        query = query.filter(FundingRound.founded_year.in_(years))
    if countries:
        query = query.filter(FundingRound.country.in_(countries))
    if deal_types:
        query = query.filter(FundingRound.deal_type.in_(deal_types))
    if lead_investors:
        query = query.filter(FundingRound.lead_investor.in_(lead_investors))
    if deal_classes:
        query = query.filter(FundingRound.deal_class.in_(deal_classes))
    if regions:
        query = query.filter(FundingRound.region.in_(regions))
    if cities:
        query = query.filter(FundingRound.city.in_(cities))
    if institutional_investors:
        query = query.filter(FundingRound.institutional_investors.in_(institutional_investors))
    if angel_investors:
        query = query.filter(FundingRound.angel_investors.in_(angel_investors))

    all_rounds = query.all()

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['Round', 'Startup', 'Amount USD', 'Deal Type', 'Lead Investor', 'Year', 'City'])
    for fr in all_rounds:
        writer.writerow([
            fr.round_name or '',
            fr.startup_name or '',
            fr.raised_amount_usd or '',
            fr.deal_type or '',
            fr.lead_investor or '',
            fr.founded_year or '',
            fr.city or ''
        ])

    output = si.getvalue()
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=funding_rounds_export.csv'}
    )


@app.route("/favorites")
def favorites():
    return render_template("favorites.html")


# ============================================================
# NEWSFEED ROUTES
# ============================================================

def _cleanup_seed_posts():
    """Remove fake seed posts and add to_email column if missing."""
    fake_authors = [
        "Youssef El Amrani", "Imane Bensaid", "Mehdi Tazi",
        "Salma Ouazzani", "Amine Benali", "Nadia El Fassi",
    ]
    deleted = Post.query.filter(Post.author_name.in_(fake_authors)).delete(synchronize_session=False)
    if deleted:
        db.session.commit()
        print(f"[PULSE] Cleaned up {deleted} fake seed posts", flush=True)
    # Ensure to_email column exists on direct_messages
    try:
        db.session.execute(db.text("ALTER TABLE direct_messages ADD COLUMN to_email VARCHAR(255)"))
        db.session.commit()
        print("[PULSE] Added to_email column to direct_messages", flush=True)
    except Exception:
        db.session.rollback()


with app.app_context():
    db.create_all()
    _cleanup_seed_posts()


@app.route("/newsfeed")
def newsfeed():
    from datetime import datetime

    # Fetch member posts only (no curated articles in the feed)
    posts = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).all()
    articles = []

    # Build feed from member posts only
    feed_items = []
    for p in posts:
        feed_items.append({
            'type': 'post',
            'obj': p,
            'date': p.created_at,
        })

    feed_items.sort(key=lambda x: x['date'] if x['date'] else datetime.min, reverse=True)

    # Sidebar: trending tags from posts
    all_tags = []
    for p in posts:
        if p.tags:
            all_tags.extend([t.strip() for t in p.tags.split(',') if t.strip()])
    tag_counter = Counter(all_tags)
    trending_tags = tag_counter.most_common(8)

    # Sidebar: recent funding rounds
    recent_rounds = FundingRound.query.filter(
        FundingRound.raised_amount_usd.isnot(None)
    ).order_by(FundingRound.date.desc()).limit(3).all()

    # Sidebar: featured resources (appels à projets)
    appels_projets = Resource.query.filter(
        Resource.category == 'Appels à projets',
        Resource.is_featured == True
    ).order_by(Resource.published_at.desc()).limit(2).all()

    return render_template(
        "newsfeed.html",
        feed_items=feed_items,
        posts=posts,
        articles=articles,
        trending_tags=trending_tags,
        recent_rounds=recent_rounds,
        appels_projets=appels_projets,
    )


@app.route("/newsfeed/post", methods=["POST"])
def create_post():
    author_name = request.form.get("author_name", "").strip()
    author_role = request.form.get("author_role", "").strip()
    content = request.form.get("content", "").strip()
    post_type = request.form.get("post_type", "post").strip()
    tags = request.form.get("tags", "").strip()

    if not content:
        return redirect(url_for("newsfeed"))

    post = Post(
        author_name=author_name or "Membre anonyme",
        author_role=author_role or "Membre de l'écosystème",
        content=content,
        post_type=post_type,
        tags=tags,
        likes_count=0,
        comments_count=0,
        is_published=False,
    )
    db.session.add(post)
    db.session.commit()
    return render_template("email-sent.html", email=None, post_message=True)


@app.route("/newsfeed/like/<int:post_id>", methods=["POST"])
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.likes_count = (post.likes_count or 0) + 1
    db.session.commit()
    return jsonify({"likes": post.likes_count})


@app.route("/newsfeed/message/<int:post_id>", methods=["POST"])
def send_message(post_id):
    post = Post.query.get_or_404(post_id)
    from_name  = request.form.get("from_name", "").strip() or "Anonyme"
    from_email = request.form.get("from_email", "").strip()
    message    = request.form.get("message", "").strip()
    if not message:
        return jsonify({"ok": False, "error": "Message vide"}), 400
    dm = DirectMessage(
        post_id    = post_id,
        to_name    = post.author_name,
        from_name  = from_name,
        from_email = from_email,
        message    = message,
    )
    db.session.add(dm)
    db.session.commit()
    return jsonify({"ok": True, "to": post.author_name})


@app.route("/send-pulse", methods=["POST"])
def send_pulse():
    data = request.get_json(silent=True) or {}
    to_name    = data.get("to_name", "").strip()
    to_email   = data.get("to_email", "").strip()
    from_name  = data.get("from_name", "").strip() or "Anonyme"
    from_email = data.get("from_email", "").strip()
    message    = data.get("message", "").strip()
    if not message:
        return jsonify({"ok": False, "error": "Message vide"}), 400
    dm = DirectMessage(
        to_name    = to_name,
        to_email   = to_email,
        from_name  = from_name,
        from_email = from_email,
        message    = message,
    )
    db.session.add(dm)
    db.session.commit()
    return jsonify({"ok": True, "to": to_name})


@app.route("/inbox")
def inbox():
    member_id = session.get("member_id")
    if not member_id:
        return redirect(url_for("member_login"))
    member = PulseMember.query.get(member_id)
    if not member:
        session.pop("member_id", None)
        return redirect(url_for("member_login"))
    my_email = member.email.strip().lower()

    # All messages where I'm sender or receiver
    all_msgs = DirectMessage.query.filter(
        db.or_(
            db.func.lower(DirectMessage.to_email) == my_email,
            db.func.lower(DirectMessage.from_email) == my_email,
        )
    ).order_by(DirectMessage.created_at.asc()).all()

    # Group into conversations by the other person's email
    conversations = {}  # other_email -> {name, email, messages[], unread}
    for m in all_msgs:
        if (m.from_email or "").strip().lower() == my_email:
            other_email = (m.to_email or "").strip().lower()
            other_name = m.to_name or other_email or "Inconnu"
        else:
            other_email = (m.from_email or "").strip().lower()
            other_name = m.from_name or other_email or "Inconnu"
        if not other_email:
            continue
        if other_email not in conversations:
            conversations[other_email] = {
                "name": other_name, "email": other_email,
                "messages": [], "unread": 0, "last_time": m.created_at,
            }
        conversations[other_email]["messages"].append(m)
        conversations[other_email]["last_time"] = m.created_at
        # Update name to most recent known name
        if other_name and other_name != other_email:
            conversations[other_email]["name"] = other_name
        if (m.to_email or "").strip().lower() == my_email and not m.is_read:
            conversations[other_email]["unread"] += 1

    # Sort conversations by last message time (most recent first)
    sorted_convos = sorted(conversations.values(), key=lambda c: c["last_time"], reverse=True)

    # Fetch profile pics for conversation partners
    all_partner_emails = [c["email"] for c in sorted_convos]
    pic_map = {}
    if all_partner_emails:
        members_with_pics = PulseMember.query.filter(
            db.func.lower(PulseMember.email).in_(all_partner_emails)
        ).all()
        for pm in members_with_pics:
            pic_map[pm.email.strip().lower()] = {
                "pic": pm.profile_pic, "id": pm.id, "name": pm.full_name
            }
        experts_with_pics = Expert.query.filter(
            db.func.lower(Expert.email).in_(all_partner_emails)
        ).all()
        for ex in experts_with_pics:
            key = (ex.email or "").strip().lower()
            if key not in pic_map:
                pic_map[key] = {"pic": ex.profile_pic or "", "id": None, "name": ex.full_name, "expert_id": ex.expert_id}
            elif "expert_id" not in pic_map[key]:
                pic_map[key]["expert_id"] = ex.expert_id

    for c in sorted_convos:
        info = pic_map.get(c["email"], {})
        c["pic"] = info.get("pic", "")
        c["member_id"] = info.get("id")
        c["expert_id"] = info.get("expert_id")

    # Pre-select conversation
    selected_email = request.args.get("with", "")
    if not selected_email and sorted_convos:
        selected_email = sorted_convos[0]["email"]

    return render_template("inbox.html", member=member, conversations=sorted_convos,
                           selected_email=selected_email, my_email=my_email)


@app.route("/inbox/messages/<path:other_email>")
def inbox_messages(other_email):
    """API: return messages for a conversation as JSON."""
    member_id = session.get("member_id")
    if not member_id:
        return jsonify({"error": "Not logged in"}), 401
    member = PulseMember.query.get(member_id)
    if not member:
        return jsonify({"error": "Not found"}), 404
    my_email = member.email.strip().lower()
    other = other_email.strip().lower()

    msgs = DirectMessage.query.filter(
        db.or_(
            db.and_(db.func.lower(DirectMessage.from_email) == my_email,
                    db.func.lower(DirectMessage.to_email) == other),
            db.and_(db.func.lower(DirectMessage.from_email) == other,
                    db.func.lower(DirectMessage.to_email) == my_email),
        )
    ).order_by(DirectMessage.created_at.asc()).all()

    # Mark incoming as read
    for m in msgs:
        if (m.to_email or "").strip().lower() == my_email and not m.is_read:
            m.is_read = True
    db.session.commit()

    return jsonify([{
        "id": m.id,
        "from_name": m.from_name,
        "from_email": m.from_email,
        "to_name": m.to_name,
        "to_email": m.to_email,
        "message": m.message,
        "is_mine": (m.from_email or "").strip().lower() == my_email,
        "time": m.created_at.strftime("%d %b %Y à %H:%M") if m.created_at else "",
    } for m in msgs])


@app.route("/inbox/reply", methods=["POST"])
def inbox_reply():
    """Send a reply in a conversation."""
    member_id = session.get("member_id")
    if not member_id:
        return jsonify({"error": "Not logged in"}), 401
    member = PulseMember.query.get(member_id)
    if not member:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json(silent=True) or {}
    to_email = data.get("to_email", "").strip()
    to_name = data.get("to_name", "").strip()
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"ok": False, "error": "Message vide"}), 400
    dm = DirectMessage(
        to_name=to_name,
        to_email=to_email,
        from_name=member.full_name,
        from_email=member.email,
        message=message,
    )
    db.session.add(dm)
    db.session.commit()
    return jsonify({"ok": True})


# ── Admin dashboard ─────────────────────────────────────────────────────
ADMIN_EMAILS = {"mohammed.damiri@um6p.ma", "hamid.bouchikhi@um6p.ma", "simohammed.damiri@gmail.com", "damiri@thepulse.ma"}

def _require_admin():
    """Return the current member if admin, else abort 403."""
    member_id = session.get("member_id")
    if not member_id:
        return None
    m = PulseMember.query.get(member_id)
    if not m or m.email.lower() not in ADMIN_EMAILS:
        return None
    return m

@app.route("/admin/pulsers")
def admin_pulsers():
    admin = _require_admin()
    if not admin:
        flash("Accès réservé aux administrateurs.", "error")
        return redirect(url_for("home"))
    from datetime import datetime
    members = PulseMember.query.order_by(PulseMember.created_at.desc()).all()
    stats = {
        "total": len(members),
        "confirmed": sum(1 for m in members if m.is_confirmed),
        "pending": sum(1 for m in members if not m.is_confirmed),
        "with_photo": sum(1 for m in members if m.profile_pic),
        "with_password": sum(1 for m in members if m.password_hash),
        "roles": {},
    }
    for m in members:
        stats["roles"][m.role] = stats["roles"].get(m.role, 0) + 1
    return render_template("admin-pulsers.html", members=members, stats=stats, now=datetime.now())


@app.route("/admin/pulsers/confirm/<int:member_id>", methods=["POST"])
def admin_confirm_member(member_id):
    admin = _require_admin()
    if not admin:
        return jsonify({"error": "Forbidden"}), 403
    m = PulseMember.query.get_or_404(member_id)
    m.is_confirmed = True
    db.session.commit()
    return jsonify({"ok": True, "id": m.id, "name": m.full_name})


@app.route("/admin/pulsers/delete/<int:member_id>", methods=["POST"])
def admin_delete_member(member_id):
    admin = _require_admin()
    if not admin:
        return jsonify({"error": "Forbidden"}), 403
    m = PulseMember.query.get_or_404(member_id)
    db.session.delete(m)
    db.session.commit()
    return jsonify({"ok": True, "id": m.id, "name": m.full_name})


@app.route("/admin/pulsers/bulk", methods=["POST"])
def admin_bulk_action():
    admin = _require_admin()
    if not admin:
        return jsonify({"error": "Forbidden"}), 403
    data = request.get_json(silent=True) or {}
    action = data.get("action")
    ids = data.get("ids", [])
    if not ids:
        return jsonify({"error": "No IDs"}), 400
    members = PulseMember.query.filter(PulseMember.id.in_(ids)).all()
    if action == "confirm":
        for m in members:
            m.is_confirmed = True
        db.session.commit()
        return jsonify({"ok": True, "count": len(members)})
    elif action == "delete":
        for m in members:
            db.session.delete(m)
        db.session.commit()
        return jsonify({"ok": True, "count": len(members)})
    return jsonify({"error": "Unknown action"}), 400


if __name__ == "__main__":
    app.run(debug=True, port=8080)
