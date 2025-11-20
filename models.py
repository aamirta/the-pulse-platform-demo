from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'User'
    
    user_id = db.Column('UserId', db.Integer, primary_key=True, autoincrement=True)
    username = db.Column('Username', db.String(100), nullable=False, unique=True)
    password = db.Column('Password', db.String(255), nullable=False)



class Institute(db.Model):
    __tablename__ = 'Institutes'
    
    institute_id = db.Column('Institute Id', db.String(50), primary_key=True)
    institute_name = db.Column('Institute Name', db.String(255), nullable=True)
    
    # Relationships
    educations = db.relationship('Education', backref='institute', lazy=True)


class Incubator(db.Model):
    __tablename__ = 'Incubators'
    
    incubator_id = db.Column('Incubator Id', db.Integer, primary_key=True)
    incubator = db.Column('Incubator', db.String(50), nullable=True)
    type_organisme = db.Column('type_organisme', db.String(50), nullable=True)
    statut = db.Column('statut', db.String(50), nullable=True)
    telephone = db.Column('telephone', db.String(50), nullable=True)
    phases_investissement = db.Column('phases_investissement', db.String(50), nullable=True)
    ville_organisme = db.Column('ville_organisme', db.String(50), nullable=True)
    date_creation = db.Column('date_creation', db.String(50), nullable=True)
    description = db.Column('description', db.Text, nullable=True)
    email = db.Column('email', db.String(50), nullable=True)
    secteurs = db.Column('secteurs', db.Text, nullable=True)
    image_url = db.Column('image_url', db.String(255), nullable=True)
    ville = db.Column('ville', db.String(50), nullable=True)
    linkedin = db.Column('linkedin', db.String(255), nullable=True)
    partners_or_sponsors = db.Column('partners_or_sponsors', db.String(255), nullable=True)
    
    # Relationships
    startups = db.relationship('Startup', secondary='StartupIncubators', backref='incubators', lazy=True)
    founders = db.relationship('Founder', secondary='IncubatorFounders', backref='founder_incubators', lazy=True)


class Startup(db.Model):
    __tablename__ = 'Startups'
    
    startup_id = db.Column('Startup Id', db.Integer, primary_key=True)
    startup_name = db.Column('Startup name', db.String(255), nullable=True)
    stage = db.Column('stage', db.String(50), nullable=True)
    last_modified_date = db.Column('lastModifiedDate', db.String(50), nullable=True)
    numero_ice = db.Column('numeroICE', db.String(50), nullable=True)
    numero_rc = db.Column('numeroRC', db.String(50), nullable=True)
    tribunal_x = db.Column('tribunal_x', db.String(50), nullable=True)
    activite = db.Column('activite', db.Text, nullable=True)
    forme_juridique = db.Column('formeJuridique', db.String(50), nullable=True)
    type_fille = db.Column('typeFille', db.String(50), nullable=True)
    date_immatriculation = db.Column('dateImmatriculation', db.DateTime, nullable=True)
    capital = db.Column('capital', db.Numeric(18, 2), nullable=True)
    ompic = db.Column('ompic', db.Numeric(18, 2), nullable=True)
    location = db.Column('location', db.String(50), nullable=True)
    region = db.Column('region', db.String(50), nullable=True)
    contact_email = db.Column('contactEmail', db.String(50), nullable=True)
    phone = db.Column('phone', db.String(50), nullable=True)
    entreprise_contact_site_web = db.Column('EntrepriseContactSiteWeb', db.String(255), nullable=True)
    entreprise_contact_name = db.Column('EntrepriseContactName', db.String(50), nullable=True)
    linkedin = db.Column('linkedin', db.String(255), nullable=True)
    youtube_link = db.Column('youtubeLink', db.String(255), nullable=True)
    instagram_link = db.Column('instagramLink', db.String(255), nullable=True)
    logo_url = db.Column('logo_url', db.String(255), nullable=True)
    presentation_video = db.Column('presentationVideo', db.String(255), nullable=True)
    sector = db.Column('sector', db.String(255), nullable=True)
    markets = db.Column('markets', db.String(50), nullable=True)
    employees = db.Column('employees', db.String(50), nullable=True)
    revenue = db.Column('revenue', db.String(50), nullable=True)
    raised_funds = db.Column('raisedFunds', db.Numeric(18, 2), nullable=True)
    valuation = db.Column('valuation', db.String(50), nullable=True)
    incubated_by = db.Column('incubatedBy', db.String(50), nullable=True)
    is_incubator_valid = db.Column('isIncubatorValid', db.Boolean, nullable=True)
    financed_by = db.Column('financedBy', db.String(50), nullable=True)
    is_financer_valid = db.Column('isFinancerValid', db.Boolean, nullable=True)
    is_jei_validated = db.Column('isJEIValidated', db.Boolean, nullable=True)
    description = db.Column('description', db.Text, nullable=True)
    uuid = db.Column('uuid', db.String(50), nullable=True)
    type = db.Column('type', db.String(50), nullable=True)
    homepage_url = db.Column('homepage_url', db.String(255), nullable=True)
    country_code = db.Column('country_code', db.String(50), nullable=True)
    address = db.Column('address', db.String(255), nullable=True)
    postal_code = db.Column('postal_code', db.Numeric(18, 2), nullable=True)
    num_funding_rounds = db.Column('num_funding_rounds', db.String(50), nullable=True)
    total_funding_usd = db.Column('total_funding_usd', db.Numeric(18, 2), nullable=True)
    total_funding = db.Column('total_funding', db.Numeric(18, 2), nullable=True)
    total_funding_currency_code = db.Column('total_funding_currency_code', db.String(50), nullable=True)
    last_funding_on = db.Column('last_funding_on', db.String(50), nullable=True)
    facebook_url = db.Column('facebook_url', db.String(255), nullable=True)
    twitter_url = db.Column('twitter_url', db.String(255), nullable=True)
    alias1 = db.Column('alias1', db.String(255), nullable=True)
    company_id = db.Column('CompanyID', db.String(50), nullable=True)
    company_also_known_as = db.Column('CompanyAlsoKnownAs', db.String(50), nullable=True)
    company_former_name = db.Column('CompanyFormerName', db.String(50), nullable=True)
    company_legal_name = db.Column('CompanyLegalName', db.String(50), nullable=True)
    company_financing_status = db.Column('CompanyFinancingStatus', db.String(50), nullable=True)
    company_financing_status_date = db.Column('CompanyFinancingStatusDate', db.String(50), nullable=True)
    total_raised = db.Column('TotalRaised', db.Numeric(18, 2), nullable=True)
    total_raised_native_amount = db.Column('TotalRaisedNativeAmount', db.Numeric(18, 2), nullable=True)
    total_raised_native_currency = db.Column('TotalRaisedNativeCurrency', db.String(50), nullable=True)
    business_status = db.Column('BusinessStatus', db.String(50), nullable=True)
    business_status_date = db.Column('BusinessStatusDate', db.String(50), nullable=True)
    ownership_status = db.Column('OwnershipStatus', db.String(50), nullable=True)
    ownership_status_date = db.Column('OwnershipStatusDate', db.String(50), nullable=True)
    universe = db.Column('Universe', db.String(50), nullable=True)
    employee_as_of_date = db.Column('EmployeeAsOfDate', db.String(50), nullable=True)
    year_founded = db.Column('YearFounded', db.String(50), nullable=True)
    parent_company = db.Column('ParentCompany', db.String(50), nullable=True)
    parent_company_id = db.Column('ParentCompanyID', db.String(50), nullable=True)
    financing_status_note = db.Column('FinancingStatusNote', db.Text, nullable=True)
    financing_status_note_as_of_date = db.Column('FinancingStatusNoteAsOfDate', db.String(50), nullable=True)
    primary_industry_sector = db.Column('PrimaryIndustrySector', db.String(50), nullable=True)
    primary_industry_group = db.Column('PrimaryIndustryGroup', db.String(50), nullable=True)
    primary_industry_code = db.Column('PrimaryIndustryCode', db.String(50), nullable=True)
    all_industries = db.Column('AllIndustries', db.String(255), nullable=True)
    verticals = db.Column('Verticals', db.String(255), nullable=True)
    hq_post_code = db.Column('HQPostCode', db.Numeric(18, 2), nullable=True)
    hq_country = db.Column('HQCountry', db.String(50), nullable=True)
    hq_fax = db.Column('HQFax', db.String(50), nullable=True)
    hq_global_region = db.Column('HQGlobalRegion', db.String(50), nullable=True)
    hq_global_sub_region = db.Column('HQGlobalSubRegion', db.String(50), nullable=True)
    alternate_office_count = db.Column('AlternateOfficeCount', db.Numeric(18, 2), nullable=True)
    active_investors = db.Column('ActiveInvestors', db.Numeric(18, 2), nullable=True)
    former_investors = db.Column('FormerInvestors', db.Numeric(18, 2), nullable=True)
    revenue1 = db.Column('Revenue1', db.Numeric(18, 2), nullable=True)
    gross_profit = db.Column('GrossProfit', db.Numeric(18, 2), nullable=True)
    net_income = db.Column('NetIncome', db.Numeric(18, 2), nullable=True)
    enterprise_value = db.Column('EnterpriseValue', db.Numeric(18, 2), nullable=True)
    ebitda = db.Column('EBITDA', db.Numeric(18, 2), nullable=True)
    ebit = db.Column('EBIT', db.Numeric(18, 2), nullable=True)
    net_debt = db.Column('NetDebt', db.Numeric(18, 2), nullable=True)
    fiscal_period = db.Column('FiscalPeriod', db.String(50), nullable=True)
    period_end_date = db.Column('PeriodEndDate', db.String(50), nullable=True)
    first_financing_deal_id = db.Column('FirstFinancingDealID', db.String(50), nullable=True)
    first_financing_date = db.Column('FirstFinancingDate', db.String(50), nullable=True)
    first_financing_size = db.Column('FirstFinancingSize', db.Numeric(18, 2), nullable=True)
    first_financing_size_status = db.Column('FirstFinancingSizeStatus', db.String(50), nullable=True)
    first_financing_valuation = db.Column('FirstFinancingValuation', db.Numeric(18, 2), nullable=True)
    first_financing_valuation_status = db.Column('FirstFinancingValuationStatus', db.String(50), nullable=True)
    first_financing_deal_type = db.Column('FirstFinancingDealType', db.String(50), nullable=True)
    first_financing_deal_type2 = db.Column('FirstFinancingDealType2', db.String(50), nullable=True)
    first_financing_deal_class = db.Column('FirstFinancingDealClass', db.String(50), nullable=True)
    first_financing_debt_date = db.Column('FirstFinancingDebtDate', db.String(50), nullable=True)
    first_financing_status = db.Column('FirstFinancingStatus', db.String(50), nullable=True)
    last_known_valuation = db.Column('LastKnownValuation', db.Numeric(18, 2), nullable=True)
    last_known_valuation_date = db.Column('LastKnownValuationDate', db.String(50), nullable=True)
    last_known_valuation_deal_type = db.Column('LastKnownValuationDealType', db.String(50), nullable=True)
    last_financing_deal_id = db.Column('LastFinancingDealID', db.String(50), nullable=True)
    last_financing_date = db.Column('LastFinancingDate', db.String(50), nullable=True)
    last_financing_size = db.Column('LastFinancingSize', db.Numeric(18, 2), nullable=True)
    last_financing_size_status = db.Column('LastFinancingSizeStatus', db.String(50), nullable=True)
    last_financing_deal_type = db.Column('LastFinancingDealType', db.String(50), nullable=True)
    last_financing_deal_type2 = db.Column('LastFinancingDealType2', db.String(50), nullable=True)
    last_financing_deal_class = db.Column('LastFinancingDealClass', db.String(50), nullable=True)
    last_financing_debt_date = db.Column('LastFinancingDebtDate', db.String(50), nullable=True)
    last_financing_status = db.Column('LastFinancingStatus', db.String(50), nullable=True)
    business_models = db.Column('Business Models', db.String(50), nullable=True)
    team_background = db.Column('Team Background', db.String(50), nullable=True)
    waves = db.Column('Waves', db.Numeric(18, 2), nullable=True)
    trending_themes = db.Column('Trending Themes', db.Numeric(18, 2), nullable=True)
    special_flags_true = db.Column('Special Flags: TRUE', db.String(255), nullable=True)
    company_stage = db.Column('Company Stage', db.String(50), nullable=True)
    is_funded = db.Column('Is Funded', db.Boolean, nullable=True)
    total_funding_usd_alt = db.Column('Total Funding (USD)', db.Numeric(18, 2), nullable=True)
    latest_funded_amount_usd = db.Column('Latest Funded Amount (USD)', db.Numeric(18, 2), nullable=True)
    latest_funded_date = db.Column('Latest Funded Date', db.String(50), nullable=True)
    latest_valuation_usd = db.Column('Latest Valuation (USD)', db.String(50), nullable=True)
    institutional_investors = db.Column('Institutional Investors', db.Text, nullable=True)
    angel_investors = db.Column('Angel Investors', db.String(50), nullable=True)
    annual_revenue_usd = db.Column('Annual Revenue (USD)', db.Numeric(18, 2), nullable=True)
    annual_net_profit_usd = db.Column('Annual Net Profit (USD)', db.Numeric(18, 2), nullable=True)
    annual_ebitda_usd = db.Column('Annual EBITDA (USD)', db.Numeric(18, 2), nullable=True)
    key_people_info = db.Column('Key People Info', db.Text, nullable=True)
    links_to_key_people_profiles = db.Column('Links to Key People Profiles', db.String(255), nullable=True)
    acquisition_list = db.Column('Acquisition List', db.String(50), nullable=True)
    is_acquired = db.Column('Is Acquired', db.Boolean, nullable=True)
    acquired_by = db.Column('Acquired By', db.String(50), nullable=True)
    acquired_date = db.Column('Acquired Date', db.DateTime, nullable=True)
    acquired_amount_usd = db.Column('Acquired Amount (USD)', db.Numeric(18, 2), nullable=True)
    acquisition_type = db.Column('Acquisition Type', db.String(50), nullable=True)
    soonicorn_club_status = db.Column('Soonicorn Club Status', db.String(50), nullable=True)
    soonicorn_club_event_date = db.Column('Soonicorn Club Event Date', db.String(50), nullable=True)
    company_emails = db.Column('Company Emails', db.String(50), nullable=True)
    blog_url = db.Column('Blog Url', db.String(50), nullable=True)
    is_deadpooled = db.Column('Is Deadpooled', db.Boolean, nullable=True)
    deadpooled_date = db.Column('Deadpooled Date', db.Numeric(18, 2), nullable=True)
    status_startup = db.Column('Status Startup', db.String(50), nullable=True)
    
    # Relationships
    funding_rounds = db.relationship('FundingRound', backref='startup', lazy=True)
    founders = db.relationship('Founder', secondary='StartupFounders', backref='startups', lazy=True)
    




class FundingRound(db.Model):
    __tablename__ = 'FundingRounds'
    
    funding_round_id = db.Column('Funding_Round_Id', db.Integer, primary_key=True)
    uuid = db.Column('Uuid', db.String(50), nullable=True)
    deal_id = db.Column('Dealid', db.String(50), nullable=True)
    deal_no = db.Column('Dealno', db.Numeric(18, 2), nullable=True)
    round_name = db.Column('Round Name', db.String(50), nullable=True)
    startup_name = db.Column('Startup Name', db.String(50), nullable=True)
    domain_name = db.Column('Domain name', db.String(50), nullable=True)
    founded_year = db.Column('Founded year', db.String(50), nullable=True)
    country = db.Column('Country', db.String(50), nullable=True)
    region = db.Column('Region', db.String(50), nullable=True)
    city = db.Column('City', db.String(50), nullable=True)
    date = db.Column('Date', db.String(50), nullable=True)
    deal_synopsis = db.Column('Dealsynopsis', db.Text, nullable=True)
    deal_type = db.Column('Dealtype', db.String(50), nullable=True)
    deal_type2 = db.Column('Dealtype2', db.String(50), nullable=True)
    deal_class = db.Column('Dealclass', db.String(50), nullable=True)
    deal_status = db.Column('Dealstatus', db.String(50), nullable=True)
    deal_size_status = db.Column('Dealsizestatus', db.String(50), nullable=True)
    raised_amount = db.Column('Raised Amount', db.Numeric(18, 2), nullable=True)
    raised_amount_usd = db.Column('Raised Amount Usd', db.Numeric(18, 2), nullable=True)
    native_currency_of_deal = db.Column('Nativecurrencyofdeal', db.String(50), nullable=True)
    addon = db.Column('Addon', db.String(50), nullable=True)
    raised_to_date = db.Column('Raisedtodate', db.Numeric(18, 2), nullable=True)
    total_funding_usd = db.Column('Total funding (usd)', db.Numeric(18, 2), nullable=True)
    overview = db.Column('Overview', db.String(255), nullable=True)
    business_status = db.Column('Businessstatus', db.String(50), nullable=True)
    financing_status = db.Column('Financingstatus', db.String(50), nullable=True)
    type_of_stock = db.Column('Typeofstock', db.String(50), nullable=True)
    vc_round = db.Column('Vcround', db.String(50), nullable=True)
    business_models = db.Column('Business models', db.String(50), nullable=True)
    institutional_investors = db.Column('Institutional investors', db.String(255), nullable=True)
    angel_investors = db.Column('Angel investors', db.String(50), nullable=True)
    lead_investor = db.Column('Lead investor', db.String(255), nullable=True)
    lead_investor_uuids = db.Column('Lead_investor_uuids', db.String(255), nullable=True)
    facilitators = db.Column('Facilitators', db.String(50), nullable=True)
    investor_count = db.Column('Investor Count', db.Numeric(18, 2), nullable=True)
    ceo = db.Column('Ceo', db.String(50), nullable=True)
    ceo_pbid = db.Column('Ceopbid', db.String(50), nullable=True)
    ceo_phone = db.Column('Ceophone', db.String(50), nullable=True)
    ceo_email = db.Column('Ceoemail', db.String(50), nullable=True)
    ceo_biography = db.Column('Ceobiography', db.Text, nullable=True)
    ceo_education = db.Column('Ceoeducation', db.String(255), nullable=True)
    startup_id = db.Column('Startup Id', db.Integer, db.ForeignKey('Startups.Startup Id'), nullable=True)
    company_id = db.Column('Companyid', db.String(50), nullable=True)
    org_uuid = db.Column('Org_uuid', db.String(50), nullable=True)
    
    # Relationships
    investments = db.relationship('Investment', backref='funding_round', lazy=True)


class Investment(db.Model):
    __tablename__ = 'Investements'
    
    investment_id = db.Column('Investement Id', db.Integer, primary_key=True)
    uuid = db.Column('uuid', db.String(50), nullable=True)
    name = db.Column('name', db.String(255), nullable=True)
    type = db.Column('type', db.String(50), nullable=True)
    permalink = db.Column('permalink', db.String(255), nullable=True)
    cb_url = db.Column('cb_url', db.String(255), nullable=True)
    rank = db.Column('rank', db.Numeric(18, 2), nullable=True)
    created_at = db.Column('created_at', db.String(50), nullable=True)
    updated_at = db.Column('updated_at', db.String(50), nullable=True)
    funding_round_uuid = db.Column('funding_round_uuid', db.String(50), nullable=True)
    funding_round_name = db.Column('funding_round_name', db.String(50), nullable=True)
    investor_uuid = db.Column('investor_uuid', db.String(50), nullable=True)
    investor_name = db.Column('investor_name', db.String(50), nullable=True)
    investor_type = db.Column('investor_type', db.String(50), nullable=True)
    is_lead_investor = db.Column('is_lead_investor', db.String(50), nullable=True)
    partner_uuid = db.Column('partner_uuid', db.String(50), nullable=True)
    partner_name = db.Column('partner_name', db.String(50), nullable=True)
    funding_round_id = db.Column('Funding_Round_Id', db.Integer, db.ForeignKey('FundingRounds.Funding_Round_Id'), nullable=True)
    investor_id = db.Column('Investor Id', db.Integer, db.ForeignKey('Investors.Investor Id'), nullable=True)


class LimitedPartner(db.Model):
    __tablename__ = 'LimitedPartner'
    
    limited_partner_id = db.Column('LimitedPartner Id', db.Integer, primary_key=True)
    limited_partner_id_alt = db.Column('LimitedPartnerID', db.String(50), nullable=True)
    limited_partner_name = db.Column('LimitedPartnerName', db.String(50), nullable=True)
    limited_partner_former_name = db.Column('LimitedPartnerFormerName', db.String(255), nullable=True)
    limited_partner_also_known_as = db.Column('LimitedPartnerAlsoKnownAs', db.String(50), nullable=True)
    description = db.Column('Description', db.Text, nullable=True)
    limited_partner_type = db.Column('LimitedPartnerType', db.String(50), nullable=True)
    aum = db.Column('AUM', db.Numeric(18, 2), nullable=True)
    year_founded = db.Column('YearFounded', db.String(50), nullable=True)
    website = db.Column('Website', db.String(50), nullable=True)
    hq_location = db.Column('HQLocation', db.String(50), nullable=True)
    hq_address_line1 = db.Column('HQAddressLine1', db.String(50), nullable=True)
    hq_address_line2 = db.Column('HQAddressLine2', db.String(50), nullable=True)
    hq_city = db.Column('HQCity', db.String(50), nullable=True)
    hq_post_code = db.Column('HQPostCode', db.Numeric(18, 2), nullable=True)
    hq_country = db.Column('HQCountry', db.String(50), nullable=True)
    hq_phone = db.Column('HQPhone', db.String(50), nullable=True)
    hq_fax = db.Column('HQFax', db.String(50), nullable=True)
    hq_email = db.Column('HQEmail', db.String(50), nullable=True)
    hq_global_region = db.Column('HQGlobalRegion', db.String(50), nullable=True)
    hq_global_sub_region = db.Column('HQGlobalSubRegion', db.String(50), nullable=True)
    sold_secondary_commitments = db.Column('SoldSecondaryCommitments', db.String(50), nullable=True)
    bought_secondary_commitments = db.Column('BoughtSecondaryCommitments', db.String(50), nullable=True)
    total_commitments = db.Column('TotalCommitments', db.BigInteger, nullable=True)
    total_active_commitments = db.Column('TotalActiveCommitments', db.BigInteger, nullable=True)
    total_commitments_in_pe_funds = db.Column('TotalCommitmentsInPEFunds', db.Numeric(18, 2), nullable=True)
    total_commitments_in_vc_funds = db.Column('TotalCommitmentsInVCFunds', db.BigInteger, nullable=True)
    open_to_first_time_funds = db.Column('OpenToFirstTimeFunds', db.String(50), nullable=True)
    real_estate = db.Column('RealEstate', db.Numeric(18, 2), nullable=True)
    real_estate_percent = db.Column('RealEstatePercent', db.Numeric(18, 2), nullable=True)
    equities = db.Column('Equities', db.Numeric(18, 2), nullable=True)
    equities_percent = db.Column('EquitiesPercent', db.Numeric(18, 2), nullable=True)
    fixed_income_percent = db.Column('FixedIncomePercent', db.Numeric(18, 2), nullable=True)
    cash = db.Column('Cash', db.Numeric(18, 2), nullable=True)
    cash_percent = db.Column('CashPercent', db.Numeric(18, 2), nullable=True)
    policy_description = db.Column('PolicyDescription', db.Text, nullable=True)
    preferred_geography = db.Column('PreferredGeography', db.String(255), nullable=True)
    preferred_fund_type = db.Column('PreferredFundType', db.String(255), nullable=True)
    
    # Relationships
    lp_funds = db.relationship('LPFund', backref='limited_partner', lazy=True)


class ServiceProvider(db.Model):
    __tablename__ = 'ServiceProvider'
    
    service_provider_id = db.Column('ServiceProvider Id', db.Integer, primary_key=True)
    service_provider_id_alt = db.Column('ServiceProviderID', db.String(50), nullable=True)
    service_provider_name = db.Column('ServiceProviderName', db.String(50), nullable=True)
    service_provider_also_known_as = db.Column('ServiceProviderAlsoKnownAs', db.String(50), nullable=True)
    employees = db.Column('Employees', db.Numeric(18, 2), nullable=True)
    description = db.Column('Description', db.String(255), nullable=True)
    website = db.Column('Website', db.String(50), nullable=True)
    primary_service_provider_type = db.Column('PrimaryServiceProviderType', db.String(50), nullable=True)
    other_service_provider_types = db.Column('OtherServiceProviderTypes', db.String(50), nullable=True)
    serviced_companies = db.Column('ServicedCompanies', db.Integer, nullable=True)
    serviced_deals = db.Column('ServicedDeals', db.Integer, nullable=True)
    serviced_investors = db.Column('ServicedInvestors', db.Integer, nullable=True)
    serviced_funds = db.Column('ServicedFunds', db.Numeric(18, 2), nullable=True)
    hq_location = db.Column('HQLocation', db.String(50), nullable=True)
    hq_address_line1 = db.Column('HQAddressLine1', db.String(50), nullable=True)
    hq_address_line2 = db.Column('HQAddressLine2', db.String(50), nullable=True)
    hq_city = db.Column('HQCity', db.String(50), nullable=True)
    hq_post_code = db.Column('HQPostCode', db.Numeric(18, 2), nullable=True)
    hq_country = db.Column('HQCountry', db.String(50), nullable=True)
    hq_phone = db.Column('HQPhone', db.String(50), nullable=True)
    hq_fax = db.Column('HQFax', db.String(50), nullable=True)
    hq_email = db.Column('HQEmail', db.String(50), nullable=True)
    hq_global_region = db.Column('HQGlobalRegion', db.String(50), nullable=True)
    hq_global_sub_region = db.Column('HQGlobalSubRegion', db.String(50), nullable=True)
    row_id = db.Column('RowID', db.String(255), nullable=True)
    last_updated = db.Column('LastUpdated', db.String(50), nullable=True)
    
    # Relationships
    sp_funds = db.relationship('SPFund', backref='service_provider', lazy=True)
    sp_investors = db.relationship('SPInvestor', backref='service_provider', lazy=True)


class LPFund(db.Model):
    __tablename__ = 'LPFunds'
    
    fund_name = db.Column('FundName', db.String(50), nullable=True)
    commitment_date = db.Column('CommitmentDate', db.DateTime, nullable=True)
    fund_id = db.Column('Fund Id', db.Integer, db.ForeignKey('Funds.Fund Id'), nullable=False, primary_key=True)
    limited_partner_id = db.Column('LimitedPartner Id', db.Integer, db.ForeignKey('LimitedPartner.LimitedPartner Id'), nullable=False, primary_key=True)


class SPFund(db.Model):
    __tablename__ = 'SPFunds'
    
    fund_name = db.Column('FundName', db.String(50), nullable=True)
    investor_id_alt = db.Column('InvestorID', db.String(50), nullable=True)
    investor_name = db.Column('InvestorName', db.String(50), nullable=True)
    service_provided = db.Column('ServiceProvided', db.String(50), nullable=True)
    fund_id = db.Column('Fund Id', db.Integer, db.ForeignKey('Funds.Fund Id'), nullable=False, primary_key=True)
    service_provider_id = db.Column('ServiceProvider Id', db.Integer, db.ForeignKey('ServiceProvider.ServiceProvider Id'), nullable=False, primary_key=True)


class SPInvestor(db.Model):
    __tablename__ = 'SPInvestor'
    
    investor_name = db.Column('InvestorName', db.String(50), nullable=True)
    service_type = db.Column('ServiceType', db.String(50), nullable=True)
    deal_id = db.Column('DealID', db.String(50), nullable=True)
    service_provided = db.Column('ServiceProvided', db.String(50), nullable=True)
    investor_id = db.Column('Investor Id', db.Integer, db.ForeignKey('Investors.Investor Id'), nullable=False, primary_key=True)
    service_provider_id = db.Column('ServiceProvider Id', db.Integer, db.ForeignKey('ServiceProvider.ServiceProvider Id'), nullable=False, primary_key=True)


# Association tables for many-to-many relationships
class StartupFounder(db.Model):
    __tablename__ = 'StartupFounders'
    
    startup_id = db.Column('Startup Id', db.Integer, db.ForeignKey('Startups.Startup Id'), primary_key=True)
    founder_id = db.Column('Founder Id', db.String(50), db.ForeignKey('Founders.Founder Id'), primary_key=True)


class StartupIncubator(db.Model):
    __tablename__ = 'StartupIncubators'
    
    startup_id = db.Column('Startup Id', db.Integer, db.ForeignKey('Startups.Startup Id'), primary_key=True)
    incubator_id = db.Column('Incubator Id', db.Integer, db.ForeignKey('Incubators.Incubator Id'), primary_key=True)


class IncubatorFounder(db.Model):
    __tablename__ = 'IncubatorFounders'
    
    incubator_id = db.Column('Incubator Id', db.Integer, db.ForeignKey('Incubators.Incubator Id'), primary_key=True)
    founder_id = db.Column('Founder Id', db.String(50), db.ForeignKey('Founders.Founder Id'), primary_key=True)


class FundInvestor(db.Model):
    __tablename__ = 'FundInvestors'
    
    fund_id = db.Column('Fund Id', db.Integer, db.ForeignKey('Funds.Fund Id'), primary_key=True)
    investor_id = db.Column('Investor Id', db.Integer, db.ForeignKey('Investors.Investor Id'), primary_key=True)


class Founder(db.Model):
    __tablename__ = 'Founders'
    
    founder_id = db.Column('Founder Id', db.String(50), primary_key=True)
    name = db.Column('name', db.String(50), nullable=True)
    first_name = db.Column('first_name', db.String(50), nullable=True)
    last_name = db.Column('last_name', db.String(50), nullable=True)
    current_title = db.Column('current_title', db.String(255), nullable=True)
    current_employer = db.Column('current_employer', db.String(255), nullable=True)
    location = db.Column('location', db.String(50), nullable=True)
    linkedin_url = db.Column('linkedin_url', db.String(255), nullable=True)
    profile_pic = db.Column('profile_pic', db.String(255), nullable=True)
    link_twitter = db.Column('link_twitter', db.String(255), nullable=True)
    link_facebook = db.Column('link_facebook', db.String(255), nullable=True)
    link_instagram = db.Column('link_instagram', db.String(255), nullable=True)
    link_quora = db.Column('link_quora', db.String(255), nullable=True)
    link_github = db.Column('link_github', db.String(255), nullable=True)
    link_aboutme = db.Column('link_aboutme', db.String(255), nullable=True)
    link_angellist = db.Column('link_angellist', db.String(255), nullable=True)
    link_stackoverflow = db.Column('link_stackoverflow', db.String(255), nullable=True)
    company_details_name = db.Column('company_details_name', db.String(50), nullable=True)
    company_details_logo_url = db.Column('company_details_logo_url', db.String(255), nullable=True)
    most_recent_ended_exp_title = db.Column('most_recent_ended_exp_title', db.String(255), nullable=True)
    most_recent_ended_exp_company_info_url = db.Column('most_recent_ended_exp_company_info_url', db.String(255), nullable=True)
    most_recent_ended_exp_employer = db.Column('most_recent_ended_exp_employer', db.String(255), nullable=True)
    most_recent_ended_exp_end_date = db.Column('most_recent_ended_exp_end_date', db.String(50), nullable=True)
    prev_company_name = db.Column('prev_company_name', db.String(255), nullable=True)
    last_job_change = db.Column('last_job_change', db.String(50), nullable=True)
    prev_company_logo_url = db.Column('prev_company_logo_url', db.String(255), nullable=True)
    prev_company_info_url = db.Column('prev_company_info_url', db.String(255), nullable=True)
    skills = db.Column('skills', db.Text, nullable=True)
    teaser_emails = db.Column('teaser_emails', db.String(255), nullable=True)
    teaser_personal_emails = db.Column('teaser_personal_emails', db.String(50), nullable=True)
    teaser_professional_emails = db.Column('teaser_professional_emails', db.String(255), nullable=True)
    teaser_phones = db.Column('teaser_phones', db.String(255), nullable=True)
    url = db.Column('url', db.String(50), nullable=True)
    
    # Relationships
    educations = db.relationship('Education', backref='founder', lazy=True)
    experiences = db.relationship('Experience', backref='founder', lazy=True)


class Education(db.Model):
    __tablename__ = 'Education'
    
    education_id = db.Column('Education Id', db.String(50), primary_key=True)
    start_date = db.Column('start_date', db.Integer, nullable=True)
    end_date = db.Column('end_date', db.Integer, nullable=True)
    degree = db.Column('degree', db.String(255), nullable=True)
    founder_id = db.Column('Founder Id', db.String(50), db.ForeignKey('Founders.Founder Id'), nullable=True)
    institute_id = db.Column('Institute Id', db.String(50), db.ForeignKey('Institutes.Institute Id'), nullable=True)


class Experience(db.Model):
    __tablename__ = 'Experiences'
    
    experience_id = db.Column('Experience Id', db.String(50), primary_key=True)
    founder_id = db.Column('Founder Id', db.String(50), db.ForeignKey('Founders.Founder Id'), nullable=True)
    role = db.Column('Role', db.String(255), nullable=True)
    company = db.Column('Company', db.String(255), nullable=True)


class Fund(db.Model):
    __tablename__ = 'Funds'
    
    fund_id = db.Column('Fund Id', db.Integer, primary_key=True)
    fund_name = db.Column('FundName', db.String(50), nullable=True)
    fund_no = db.Column('FundNo', db.Numeric(18, 2), nullable=True)
    first_fund = db.Column('FirstFund', db.String(50), nullable=True)
    investor = db.Column('Investor', db.String(50), nullable=True)
    investor_website = db.Column('InvestorWebsite', db.String(50), nullable=True)
    vintage = db.Column('Vintage', db.Numeric(18, 2), nullable=True)
    fund_status = db.Column('FundStatus', db.String(50), nullable=True)
    fund_size = db.Column('FundSize', db.Numeric(18, 2), nullable=True)
    native_fund_size = db.Column('NativeFundSize', db.Numeric(18, 2), nullable=True)
    native_fund_currency = db.Column('NativeFundCurrency', db.String(50), nullable=True)
    fund_size_group = db.Column('FundSizeGroup', db.String(50), nullable=True)
    fund_category = db.Column('FundCategory', db.String(50), nullable=True)
    fund_type = db.Column('FundType', db.String(50), nullable=True)
    fund_access_point = db.Column('FundAccessPoint', db.String(50), nullable=True)
    sbic_fund = db.Column('SBICFund', db.String(50), nullable=True)
    close_date = db.Column('CloseDate', db.DateTime, nullable=True)
    open_date = db.Column('OpenDate', db.DateTime, nullable=True)
    fund_target_size_low = db.Column('FundTargetSizeLow', db.Numeric(18, 2), nullable=True)
    fund_target_size = db.Column('FundTargetSize', db.String(50), nullable=True)
    domiciles = db.Column('Domiciles', db.String(50), nullable=True)
    fund_location = db.Column('FundLocation', db.String(50), nullable=True)
    fund_city = db.Column('FundCity', db.String(50), nullable=True)
    fund_state_province = db.Column('FundState_Province', db.String(50), nullable=True)
    fund_country = db.Column('FundCountry', db.String(50), nullable=True)
    time_taken_to_close_fund = db.Column('TimeTakenToCloseFund', db.String(50), nullable=True)
    total_fund_investments = db.Column('TotalFundInvestments', db.Numeric(18, 2), nullable=True)
    total_active_fund_investments = db.Column('TotalActiveFundInvestments', db.Numeric(18, 2), nullable=True)
    preferred_industry = db.Column('PreferredIndustry', db.Text, nullable=True)
    preferred_verticals = db.Column('PreferredVerticals', db.String(50), nullable=True)
    preferred_geography = db.Column('PreferredGeography', db.String(50), nullable=True)
    preferred_investment_types = db.Column('PreferredInvestmentTypes', db.String(50), nullable=True)
    other_investment_preferences = db.Column('OtherInvestmentPreferences', db.String(255), nullable=True)
    entity_name = db.Column('entity_name', db.String(50), nullable=True)
    entity_type = db.Column('entity_type', db.String(50), nullable=True)
    raised_amount_usd = db.Column('raised_amount_usd', db.Numeric(18, 2), nullable=True)
    raised_amount = db.Column('raised_amount', db.Numeric(18, 2), nullable=True)
    raised_amount_currency_code = db.Column('raised_amount_currency_code', db.String(50), nullable=True)
    fund_id_alt = db.Column('FundID', db.String(50), nullable=True)
    row_id = db.Column('RowID', db.String(255), nullable=True)
    last_updated = db.Column('LastUpdated', db.String(50), nullable=True)
    uuid = db.Column('uuid', db.String(50), nullable=True)
    entity_uuid = db.Column('entity_uuid', db.String(50), nullable=True)
    
    # Relationships
    investors = db.relationship('Investor', secondary='FundInvestors', backref='funds', lazy=True)
    lp_funds = db.relationship('LPFund', backref='fund', lazy=True)
    sp_funds = db.relationship('SPFund', backref='fund', lazy=True)


class Investor(db.Model):
    __tablename__ = 'Investors'
    
    investor_id = db.Column('Investor Id', db.Integer, primary_key=True)
    investor_name = db.Column('Investor Name', db.String(50), nullable=True)
    investor_status = db.Column('InvestorStatus', db.String(50), nullable=True)
    hq_phone = db.Column('HQPhone', db.String(50), nullable=True)
    hq_email = db.Column('HQEmail', db.String(50), nullable=True)
    founding_date = db.Column('Founding Date', db.DateTime, nullable=True)
    domain = db.Column('domain', db.String(50), nullable=True)
    country_code = db.Column('Country Code', db.String(50), nullable=True)
    investment_count = db.Column('Investment Count', db.Numeric(18, 2), nullable=True)
    last_investment_date = db.Column('LastInvestmentDate', db.DateTime, nullable=True)
    last_investment_type = db.Column('LastInvestmentType', db.String(50), nullable=True)
    last_investment_class = db.Column('LastInvestmentClass', db.String(50), nullable=True)
    total_investments_in_the_last_5_years = db.Column('TotalInvestmentsInTheLast5Years', db.Numeric(18, 2), nullable=True)
    last_financing_debt_date = db.Column('LastFinancingDebtDate', db.DateTime, nullable=True)
    last_investment_status = db.Column('LastInvestmentStatus', db.String(50), nullable=True)
    last_investment_company = db.Column('LastInvestmentCompany', db.String(50), nullable=True)
    most_likely_fundraising = db.Column('MostLikelyFundraisIng', db.String(50), nullable=True)
    primary_investor_type = db.Column('PrimaryInvestorType', db.String(50), nullable=True)
    investor_native_currency = db.Column('InvestorNativeCurrency', db.String(50), nullable=True)
    hq_location = db.Column('HQLocation', db.String(50), nullable=True)
    hq_address_line1 = db.Column('HQAddressLine1', db.String(50), nullable=True)
    hq_global_sub_region = db.Column('HQGlobalSubRegion', db.String(50), nullable=True)
    total_investments = db.Column('TotalInvestments', db.Numeric(18, 2), nullable=True)
    investor_types = db.Column('Investor Types', db.String(50), nullable=True)
    last_updated = db.Column('LastUpdated', db.String(50), nullable=True)
    type = db.Column('type', db.String(50), nullable=True)
    permalink = db.Column('permalink', db.String(50), nullable=True)
    roles = db.Column('roles', db.String(50), nullable=True)
    region = db.Column('region', db.String(50), nullable=True)
    city = db.Column('city', db.String(50), nullable=True)
    linkedin_url = db.Column('linkedin_url', db.String(255), nullable=True)
    logo_url = db.Column('Logo Url', db.String(255), nullable=True)
    facebook_url = db.Column('Facebook Url', db.String(255), nullable=True)
    twitter_url = db.Column('Twitter Url', db.String(50), nullable=True)
    preferred_industry = db.Column('PreferredIndustry', db.String(255), nullable=True)
    description = db.Column('Description', db.Text, nullable=True)
    preferred_geography = db.Column('PreferredGeography', db.String(50), nullable=True)
    total_investments_in_the_last_12_months = db.Column('TotalInvestmentsInTheLast12Months', db.Numeric(18, 2), nullable=True)
    preferred_investment_types = db.Column('PreferredInvestmentTypes', db.String(50), nullable=True)
    preferred_verticals = db.Column('PreferredVerticals', db.String(255), nullable=True)
    total_active_portfolio = db.Column('TotalActivePortfolio', db.Numeric(18, 2), nullable=True)
    other_investment_preferences = db.Column('OtherInvestmentPreferences', db.String(50), nullable=True)
    total_exits = db.Column('TotalExits', db.Numeric(18, 2), nullable=True)
    hq_post_code = db.Column('HQPostCode', db.Numeric(18, 2), nullable=True)
    median_valuation = db.Column('MedianValuation', db.Numeric(18, 2), nullable=True)
    median_round_amount = db.Column('MedianRoundAmount', db.Numeric(18, 2), nullable=True)
    total_investments_in_the_last_2_years = db.Column('TotalInvestmentsInTheLast2Years', db.Numeric(18, 2), nullable=True)
    last_investment_size = db.Column('LastInvestmentSize', db.Numeric(18, 2), nullable=True)
    last_investment_size_status = db.Column('LastInvestmentSizeStatus', db.String(50), nullable=True)
    last_investment_type2 = db.Column('LastInvestmentType2', db.String(50), nullable=True)
    total_funding = db.Column('Total Funding', db.Numeric(18, 2), nullable=True)
    total_funding_usd = db.Column('Total Funding Usd', db.Numeric(18, 2), nullable=True)
    total_funding_currency_code = db.Column('Total Funding Currency Code', db.String(50), nullable=True)
    investor_also_known_as = db.Column('InvestorAlsoKnownAs', db.String(50), nullable=True)
    investor_legal_name = db.Column('InvestorLegalName', db.String(50), nullable=True)
    investor_former_name = db.Column('InvestorFormerName', db.String(50), nullable=True)
    parent_company_id = db.Column('ParentCompanyID', db.String(50), nullable=True)
    parent_company = db.Column('ParentCompany', db.String(50), nullable=True)
    aum = db.Column('AUM', db.Numeric(18, 2), nullable=True)
    aum_native_amount = db.Column('AUMNativeAmount', db.Numeric(18, 2), nullable=True)
    dry_powder = db.Column('DryPowder', db.Numeric(18, 2), nullable=True)
    other_investor_types = db.Column('OtherInvestorTypes', db.String(50), nullable=True)
    min_fund_size = db.Column('MinFundSize', db.Numeric(18, 2), nullable=True)
    max_fund_size = db.Column('MaxFundSize', db.Numeric(18, 2), nullable=True)
    median_fund_size = db.Column('MedianFundSize', db.Numeric(18, 2), nullable=True)
    preferred_investment_amount = db.Column('PreferredInvestmentAmount', db.String(50), nullable=True)
    preferred_investment_amount_min = db.Column('PreferredInvestmentAmountMin', db.Numeric(18, 2), nullable=True)
    preferred_investment_amount_min_native_amount = db.Column('PreferredInvestmentAmountMinNativeAmount', db.Numeric(18, 2), nullable=True)
    preferred_investment_amount_max = db.Column('PreferredInvestmentAmountMax', db.Numeric(18, 2), nullable=True)
    preferred_investment_amount_max_native_amount = db.Column('PreferredInvestmentAmountMaxNativeAmount', db.Numeric(18, 2), nullable=True)
    hq_address_line2 = db.Column('HQAddressLine2', db.String(50), nullable=True)
    hq_fax = db.Column('HQFax', db.String(50), nullable=True)
    investor_id_alt = db.Column('InvestorID', db.String(50), nullable=True)
    uuid = db.Column('uuid', db.String(50), nullable=True)
    
    # Relationships
    investments = db.relationship('Investment', backref='investor', lazy=True)
    sp_investors = db.relationship('SPInvestor', backref='investor', lazy=True)