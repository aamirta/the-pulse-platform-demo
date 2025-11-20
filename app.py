from flask import Flask, request, redirect, render_template_string, session, url_for,render_template
from models import * 
from Functions import *
import urllib.parse
from collections import Counter
from sqlalchemy import func, or_, event
import urllib.parse
import uuid
import time
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "pulse_secret"
#app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=2)
app.config['SESSION_REFRESH_EACH_REQUEST'] = False
# Azure SQL connection details
driver = "ODBC Driver 17 for SQL Server"
server = "thepulseserver.database.windows.net"
database = "THEPULSEDB"
username = "thepulseadmin"
password = "thepulse@008"

driver_encoded = urllib.parse.quote_plus(driver)
username_encoded = urllib.parse.quote_plus(username)
password_encoded = urllib.parse.quote_plus(password)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mssql+pyodbc://{username_encoded}:{password_encoded}@{server}/{database}"
    f"?driver={driver_encoded}&Encrypt=yes&TrustServerCertificate=no"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 3600,
    'connect_args': {
        'timeout': 100,
        'login_timeout': 100
    }
}
# Initialize database with app
db.init_app(app)
SERVER_TOKEN = str(uuid.uuid4())
@app.before_request
def require_password():
    allowed_routes = ['login']
    if (
        'logged_in' not in session
        or session.get("server_token") != SERVER_TOKEN
    ) and request.endpoint not in allowed_routes:
        return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session.permanent = False  # Session expires when browser closes
            session["logged_in"] = True
            session["server_token"] = SERVER_TOKEN
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Invalid credentials. Please try again.")
    
    return render_template("login.html")

@app.route("/")
def home():
    startups = Startup.query.all()
    founders = Founder.query.all()
    investors = Investor.query.all()
    deals = FundingRound.query.all()
    
    total_funding = sum(deal.raised_amount_usd if deal.raised_amount_usd is not None else 0 for deal in deals)
    total_funding_millions = total_funding / 1_000_000
    
    # Get cities and their counts properly
    cities_list = [startup.location for startup in startups if startup.location and startup.location != "Morocco"]
    city_counter = Counter(cities_list)
    
    # Extract cities and counts in the same order
    cities = get_unique_cities(startups)
    topcities, NbStartupsByCity = get_top_cities(startups, cities, n=10)

    #Numbr of startups by sector 
    Sectors=get_unique_sectors(startups)
    topsectors, nbstartupsbysector=get_top_sectors(startups,Sectors,n=10)
    #print(topsectors, nbstartupsbysector)

    #total funding by year
    years, total_by_year = get_totalFunding_groupby_year(deals)
    print(years, total_by_year)

    #total funding by sector
    topsectors_funding, total_funding_by_sector = get_total_funding_by_sector(deals, Sectors, n=10)
    #top startups by total funding
    top_startups_funding, total_funding_by_startup = toptotalfundingByStartup(startups)
    
    return render_template("home.html", 
                         startups=startups, 
                         founders=founders, 
                         investors=investors, 
                         deals=deals,
                         total_funding=total_funding_millions,
                         topcities=topcities,
                         NbStartupsByCity=NbStartupsByCity,
                         topsectors=topsectors,
                         nbstartupsbysector=nbstartupsbysector,
                         years=years,
                         total_by_year=total_by_year,
                         topsectors_funding=topsectors_funding,
                         total_funding_by_sector=total_funding_by_sector,
                         top_startups_funding=top_startups_funding,
                         total_funding_by_startup=total_funding_by_startup)


@app.route("/startups", methods=["GET"])
def startups():
    # Base query
    query = Startup.query
    
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
    
    # Fetch filtered results
    all_startups = query.all()
    
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
        sector_counts=sector_counts
    )

@app.route("/incubators")
def incubators():
    query = Incubator.query
    
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

    all_incubators = query.all()
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
    
    return render_template(
        "incubators.html",
        incubators=all_incubators,
        distinct_cities=distinct_cities,
        distinct_investementphase=distinct_investementphase,
        distinct_startups=distinct_startups,
        selected=request.args,
        phase_counts=phase_counts
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

    return render_template("startup_detail.html", startup=startup, founders=founders, fundingRounds=fundingRounds, incubators=incubators, investors=investors)


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
    query = Investor.query
    selected_locations = request.args.getlist("location")
    selected_investor_types = request.args.getlist("investor_type")
    selected_startups = request.args.getlist("startup")
    
    if selected_startups:
        startupsSelected = Startup.query.filter(Startup.startup_id.in_(selected_startups)).all()
        investorsFiltered = FilterInvestorsByStartups(startupsSelected)
        investor_ids = [investor.investor_id for investor in investorsFiltered]
        query = query.filter(Investor.investor_id.in_(investor_ids))
    if selected_locations:
        query = query.filter(Investor.city.in_(selected_locations))
    if selected_investor_types:
        query = query.filter(Investor.primary_investor_type.in_(selected_investor_types))
    all_investors = query.all()
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
    
    return render_template(
        "investors.html",
        investors=all_investors,
        distinct_locations=distinct_locations,
        distinct_investor_types=distinct_investor_types,
        distinct_startups=distinct_startups,
        selected=request.args
    )

@app.route("/investor/<int:investor_id>")
def investor_details(investor_id):
    from sqlalchemy.orm import joinedload
    
    investor = Investor.query.get_or_404(investor_id)
    
    # Explicitly load investments with their funding rounds using eager loading
    investements = Investment.query.options(joinedload(Investment.funding_round).joinedload(FundingRound.startup)).filter(
        Investment.investor_id == investor_id
    ).all()
    
    startups = StartupsInvestedByInvestor(investor)
    
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
                              funds=funds)


@app.route("/founders")
def founders():
    query = Founder.query
    selected_cities = request.args.getlist("city")
    selected_startups = request.args.getlist("startup")

    if selected_cities:
        query = query.filter(Founder.location.in_(selected_cities))
    if selected_startups:
        query = query.filter(Founder.startups.any(Startup.startup_id.in_(selected_startups)))
    all_founders = query.all()
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
        selected=request.args
    )


@app.route("/funds")
def funds():
    all_funds = Fund.query.all()
    return render_template(
        "funds.html",
        funds=all_funds
    )

@app.route("/funding-rounds", methods=["GET"])
def funding_rounds():
    query = FundingRound.query

    # Filters from request
    round_name = request.args.get("round_name")
    startup_name = request.args.get("startup_name")
    year = request.args.get("year")
    country = request.args.get("country")
    deal_type = request.args.get("deal_type")
    lead_investor = request.args.get("lead_investor")
    deal_class = request.args.get("deal_class")
    region = request.args.get("region")
    city = request.args.get("city")
    institutional_investors = request.args.get("institutional_investors")
    angel_investors = request.args.get("angel_investors")

    # Apply filters
    if round_name:
        query = query.filter(FundingRound.round_name.ilike(f"%{round_name}%"))
    if startup_name:
        query = query.filter(FundingRound.startup_name.ilike(f"%{startup_name}%"))
    if year:
        query = query.filter(FundingRound.founded_year == year)
    if country:
        query = query.filter(FundingRound.country.ilike(f"%{country}%"))
    if deal_type:
        query = query.filter(FundingRound.deal_type.ilike(f"%{deal_type}%"))
    if lead_investor:
        query = query.filter(FundingRound.lead_investor.ilike(f"%{lead_investor}%"))
    if deal_class:
        query = query.filter(FundingRound.deal_class.ilike(f"%{deal_class}%"))
    if region:
        query = query.filter(FundingRound.region.ilike(f"%{region}%"))
    if city:
        query = query.filter(FundingRound.city.ilike(f"%{city}%"))
    if institutional_investors:
        query = query.filter(FundingRound.institutional_investors.ilike(f"%{institutional_investors}%"))
    if angel_investors:
        query = query.filter(FundingRound.angel_investors.ilike(f"%{angel_investors}%"))

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

    rounds = query.all()
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
        selected=request.args
    )

@app.route("/join")
def join():
    return render_template("join.html")

@app.route("/entrepreneur-form")
def entrepreneur_form():
    incubators = Incubator.query.all()
    investors = Investor.query.all()
    return render_template("entrepreneur-form.html", incubators=incubators, investors=investors)

@app.route("/investor-form")
def investor_form():
    return render_template("investor-form.html")

@app.route("/program-form")
def program_form():
    return render_template("program-form.html")

@app.route("/talent-form")
def talent_form():
    return render_template("talent-form.html")

if __name__ == "__main__":
    app.run(debug=True)
