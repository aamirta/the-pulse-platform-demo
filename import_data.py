"""Import CSV data into SQLite database."""
import csv
import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db
from models import *

DATA_DIR = "/tmp/Pulse_Data_Insertion/data"

def read_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        return list(reader)

def safe_int(val):
    if not val or val == '' or val == 'nan':
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None

def safe_float(val):
    if not val or val == '' or val == 'nan':
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def safe_str(val):
    if not val or val == '' or val == 'nan':
        return None
    return str(val).strip()

def safe_bool(val):
    if not val or val == '' or val == 'nan':
        return None
    if isinstance(val, str):
        return val.lower() in ('true', '1', 'yes')
    return bool(val)

def import_institutes():
    rows = read_csv("CompleteInstitutes.csv")
    count = 0
    for row in rows:
        inst = Institute(
            institute_id=safe_str(row.get('Institute Id', row.get('institute_id', ''))),
            institute_name=safe_str(row.get('Institute Name', row.get('institute_name', '')))
        )
        if inst.institute_id:
            db.session.merge(inst)
            count += 1
    db.session.commit()
    print(f"  Institutes: {count}")

def import_incubators():
    rows = read_csv("CompleteIncubators.csv")
    count = 0
    for row in rows:
        inc_id = safe_int(row.get('Incubator Id', row.get('incubator_id', '')))
        if not inc_id:
            continue
        inc = Incubator(
            incubator_id=inc_id,
            incubator=safe_str(row.get('Incubator', row.get('incubator', ''))),
            type_organisme=safe_str(row.get('type_organisme', '')),
            statut=safe_str(row.get('statut', '')),
            telephone=safe_str(row.get('telephone', '')),
            phases_investissement=safe_str(row.get('phases_investissement', '')),
            ville_organisme=safe_str(row.get('ville_organisme', '')),
            date_creation=safe_str(row.get('date_creation', '')),
            description=safe_str(row.get('description', '')),
            email=safe_str(row.get('email', '')),
            secteurs=safe_str(row.get('secteurs', '')),
            image_url=safe_str(row.get('image_url', '')),
            ville=safe_str(row.get('ville', '')),
            linkedin=safe_str(row.get('linkedin', '')),
            partners_or_sponsors=safe_str(row.get('partners_or_sponsors', ''))
        )
        db.session.merge(inc)
        count += 1
    db.session.commit()
    print(f"  Incubators: {count}")

def import_startups():
    rows = read_csv("Startups__Cleaned.csv")
    count = 0
    for row in rows:
        sid = safe_int(row.get('Startup Id', ''))
        if not sid:
            continue
        s = Startup(
            startup_id=sid,
            startup_name=safe_str(row.get('Startup name', '')),
            stage=safe_str(row.get('stage', '')),
            last_modified_date=safe_str(row.get('lastModifiedDate', '')),
            numero_ice=safe_str(row.get('numeroICE', '')),
            numero_rc=safe_str(row.get('numeroRC', '')),
            tribunal_x=safe_str(row.get('tribunal_x', '')),
            activite=safe_str(row.get('activite', '')),
            forme_juridique=safe_str(row.get('formeJuridique', '')),
            type_fille=safe_str(row.get('typeFille', '')),
            capital=safe_float(row.get('capital', '')),
            ompic=safe_float(row.get('ompic', '')),
            location=safe_str(row.get('location', '')),
            region=safe_str(row.get('region', '')),
            contact_email=safe_str(row.get('contactEmail', '')),
            phone=safe_str(row.get('phone', '')),
            entreprise_contact_site_web=safe_str(row.get('EntrepriseContactSiteWeb', '')),
            entreprise_contact_name=safe_str(row.get('EntrepriseContactName', '')),
            linkedin=safe_str(row.get('linkedin', '')),
            youtube_link=safe_str(row.get('youtubeLink', '')),
            instagram_link=safe_str(row.get('instagramLink', '')),
            logo_url=safe_str(row.get('logo_url', '')),
            presentation_video=safe_str(row.get('presentationVideo', '')),
            sector=safe_str(row.get('sector', '')),
            markets=safe_str(row.get('markets', '')),
            employees=safe_str(row.get('employees', '')),
            revenue=safe_str(row.get('revenue', '')),
            raised_funds=safe_float(row.get('raisedFunds', '')),
            valuation=safe_str(row.get('valuation', '')),
            incubated_by=safe_str(row.get('incubatedBy', '')),
            is_incubator_valid=safe_bool(row.get('isIncubatorValid', '')),
            financed_by=safe_str(row.get('financedBy', '')),
            is_financer_valid=safe_bool(row.get('isFinancerValid', '')),
            is_jei_validated=safe_bool(row.get('isJEIValidated', '')),
            description=safe_str(row.get('description', '')),
            uuid=safe_str(row.get('uuid', '')),
            type=safe_str(row.get('type', '')),
            homepage_url=safe_str(row.get('homepage_url', '')),
            country_code=safe_str(row.get('country_code', '')),
            address=safe_str(row.get('address', '')),
            postal_code=safe_float(row.get('postal_code', '')),
            num_funding_rounds=safe_str(row.get('num_funding_rounds', '')),
            total_funding_usd=safe_float(row.get('total_funding_usd', '')),
            total_funding=safe_float(row.get('total_funding', '')),
            total_funding_currency_code=safe_str(row.get('total_funding_currency_code', '')),
            last_funding_on=safe_str(row.get('last_funding_on', '')),
            facebook_url=safe_str(row.get('facebook_url', '')),
            twitter_url=safe_str(row.get('twitter_url', '')),
            alias1=safe_str(row.get('alias1', '')),
            company_id=safe_str(row.get('CompanyID', '')),
            company_also_known_as=safe_str(row.get('CompanyAlsoKnownAs', '')),
            company_former_name=safe_str(row.get('CompanyFormerName', '')),
            company_legal_name=safe_str(row.get('CompanyLegalName', '')),
            company_financing_status=safe_str(row.get('CompanyFinancingStatus', '')),
            company_financing_status_date=safe_str(row.get('CompanyFinancingStatusDate', '')),
            total_raised=safe_float(row.get('TotalRaised', '')),
            total_raised_native_amount=safe_float(row.get('TotalRaisedNativeAmount', '')),
            total_raised_native_currency=safe_str(row.get('TotalRaisedNativeCurrency', '')),
            business_status=safe_str(row.get('BusinessStatus', '')),
            business_status_date=safe_str(row.get('BusinessStatusDate', '')),
            ownership_status=safe_str(row.get('OwnershipStatus', '')),
            ownership_status_date=safe_str(row.get('OwnershipStatusDate', '')),
            universe=safe_str(row.get('Universe', '')),
            employee_as_of_date=safe_str(row.get('EmployeeAsOfDate', '')),
            year_founded=safe_str(row.get('YearFounded', '')),
            parent_company=safe_str(row.get('ParentCompany', '')),
            parent_company_id=safe_str(row.get('ParentCompanyID', '')),
            financing_status_note=safe_str(row.get('FinancingStatusNote', '')),
            financing_status_note_as_of_date=safe_str(row.get('FinancingStatusNoteAsOfDate', '')),
            primary_industry_sector=safe_str(row.get('PrimaryIndustrySector', '')),
            primary_industry_group=safe_str(row.get('PrimaryIndustryGroup', '')),
            primary_industry_code=safe_str(row.get('PrimaryIndustryCode', '')),
            all_industries=safe_str(row.get('AllIndustries', '')),
            verticals=safe_str(row.get('Verticals', '')),
            hq_post_code=safe_float(row.get('HQPostCode', '')),
            hq_country=safe_str(row.get('HQCountry', '')),
            hq_fax=safe_str(row.get('HQFax', '')),
            hq_global_region=safe_str(row.get('HQGlobalRegion', '')),
            hq_global_sub_region=safe_str(row.get('HQGlobalSubRegion', '')),
            alternate_office_count=safe_float(row.get('AlternateOfficeCount', '')),
            active_investors=safe_float(row.get('ActiveInvestors', '')),
            former_investors=safe_float(row.get('FormerInvestors', '')),
            revenue1=safe_float(row.get('Revenue', row.get('Revenue1', ''))),
            gross_profit=safe_float(row.get('GrossProfit', '')),
            net_income=safe_float(row.get('NetIncome', '')),
            enterprise_value=safe_float(row.get('EnterpriseValue', '')),
            ebitda=safe_float(row.get('EBITDA', '')),
            ebit=safe_float(row.get('EBIT', '')),
            net_debt=safe_float(row.get('NetDebt', '')),
            fiscal_period=safe_str(row.get('FiscalPeriod', '')),
            period_end_date=safe_str(row.get('PeriodEndDate', '')),
            first_financing_deal_id=safe_str(row.get('FirstFinancingDealID', '')),
            first_financing_date=safe_str(row.get('FirstFinancingDate', '')),
            first_financing_size=safe_float(row.get('FirstFinancingSize', '')),
            first_financing_size_status=safe_str(row.get('FirstFinancingSizeStatus', '')),
            first_financing_valuation=safe_float(row.get('FirstFinancingValuation', '')),
            first_financing_valuation_status=safe_str(row.get('FirstFinancingValuationStatus', '')),
            first_financing_deal_type=safe_str(row.get('FirstFinancingDealType', '')),
            first_financing_deal_type2=safe_str(row.get('FirstFinancingDealType2', '')),
            first_financing_deal_class=safe_str(row.get('FirstFinancingDealClass', '')),
            first_financing_debt_date=safe_str(row.get('FirstFinancingDebtDate', '')),
            first_financing_status=safe_str(row.get('FirstFinancingStatus', '')),
            last_known_valuation=safe_float(row.get('LastKnownValuation', '')),
            last_known_valuation_date=safe_str(row.get('LastKnownValuationDate', '')),
            last_known_valuation_deal_type=safe_str(row.get('LastKnownValuationDealType', '')),
            last_financing_deal_id=safe_str(row.get('LastFinancingDealID', '')),
            last_financing_date=safe_str(row.get('LastFinancingDate', '')),
            last_financing_size=safe_float(row.get('LastFinancingSize', '')),
            last_financing_size_status=safe_str(row.get('LastFinancingSizeStatus', '')),
            last_financing_deal_type=safe_str(row.get('LastFinancingDealType', '')),
            last_financing_deal_type2=safe_str(row.get('LastFinancingDealType2', '')),
            last_financing_deal_class=safe_str(row.get('LastFinancingDealClass', '')),
            last_financing_debt_date=safe_str(row.get('LastFinancingDebtDate', '')),
            last_financing_status=safe_str(row.get('LastFinancingStatus', '')),
            business_models=safe_str(row.get('Business Models', '')),
            team_background=safe_str(row.get('Team Background', '')),
            waves=safe_float(row.get('Waves', '')),
            trending_themes=safe_float(row.get('Trending Themes', '')),
            special_flags_true=safe_str(row.get('Special Flags: TRUE', '')),
            company_stage=safe_str(row.get('Company Stage', '')),
            is_funded=safe_bool(row.get('Is Funded', '')),
            total_funding_usd_alt=safe_float(row.get('Total Funding (USD)', '')),
            latest_funded_amount_usd=safe_float(row.get('Latest Funded Amount (USD)', '')),
            latest_funded_date=safe_str(row.get('Latest Funded Date', '')),
            latest_valuation_usd=safe_str(row.get('Latest Valuation (USD)', '')),
            institutional_investors=safe_str(row.get('Institutional Investors', '')),
            angel_investors=safe_str(row.get('Angel Investors', '')),
            annual_revenue_usd=safe_float(row.get('Annual Revenue (USD)', '')),
            annual_net_profit_usd=safe_float(row.get('Annual Net Profit (USD)', '')),
            annual_ebitda_usd=safe_float(row.get('Annual EBITDA (USD)', '')),
            key_people_info=safe_str(row.get('Key People Info', '')),
            links_to_key_people_profiles=safe_str(row.get('Links to Key People Profiles', '')),
            acquisition_list=safe_str(row.get('Acquisition List', '')),
            is_acquired=safe_bool(row.get('Is Acquired', '')),
            acquired_by=safe_str(row.get('Acquired By', '')),
            acquired_amount_usd=safe_float(row.get('Acquired Amount (USD)', '')),
            acquisition_type=safe_str(row.get('Acquisition Type', '')),
            soonicorn_club_status=safe_str(row.get('Soonicorn Club Status', '')),
            soonicorn_club_event_date=safe_str(row.get('Soonicorn Club Event Date', '')),
            company_emails=safe_str(row.get('Company Emails', '')),
            blog_url=safe_str(row.get('Blog Url', '')),
            is_deadpooled=safe_bool(row.get('Is Deadpooled', '')),
            deadpooled_date=safe_float(row.get('Deadpooled Date', '')),
            status_startup=safe_str(row.get('Status Startup', ''))
        )
        db.session.merge(s)
        count += 1
    db.session.commit()
    print(f"  Startups: {count}")

def import_founders():
    rows = read_csv("CompleteFounders.csv")
    count = 0
    for row in rows:
        fid = safe_str(row.get('Founder Id', row.get('founder_id', '')))
        if not fid:
            continue
        f = Founder(
            founder_id=fid,
            name=safe_str(row.get('name', '')),
            first_name=safe_str(row.get('first_name', '')),
            last_name=safe_str(row.get('last_name', '')),
            current_title=safe_str(row.get('current_title', '')),
            current_employer=safe_str(row.get('current_employer', '')),
            location=safe_str(row.get('location', '')),
            linkedin_url=safe_str(row.get('linkedin_url', '')),
            profile_pic=safe_str(row.get('profile_pic', '')),
            link_twitter=safe_str(row.get('link_twitter', '')),
            link_facebook=safe_str(row.get('link_facebook', '')),
            link_instagram=safe_str(row.get('link_instagram', '')),
            link_quora=safe_str(row.get('link_quora', '')),
            link_github=safe_str(row.get('link_github', '')),
            link_aboutme=safe_str(row.get('link_aboutme', '')),
            link_angellist=safe_str(row.get('link_angellist', '')),
            link_stackoverflow=safe_str(row.get('link_stackoverflow', '')),
            company_details_name=safe_str(row.get('company_details_name', '')),
            company_details_logo_url=safe_str(row.get('company_details_logo_url', '')),
            most_recent_ended_exp_title=safe_str(row.get('most_recent_ended_exp_title', '')),
            most_recent_ended_exp_company_info_url=safe_str(row.get('most_recent_ended_exp_company_info_url', '')),
            most_recent_ended_exp_employer=safe_str(row.get('most_recent_ended_exp_employer', '')),
            most_recent_ended_exp_end_date=safe_str(row.get('most_recent_ended_exp_end_date', '')),
            prev_company_name=safe_str(row.get('prev_company_name', '')),
            last_job_change=safe_str(row.get('last_job_change', '')),
            prev_company_logo_url=safe_str(row.get('prev_company_logo_url', '')),
            prev_company_info_url=safe_str(row.get('prev_company_info_url', '')),
            skills=safe_str(row.get('skills', '')),
            teaser_emails=safe_str(row.get('teaser_emails', '')),
            teaser_personal_emails=safe_str(row.get('teaser_personal_emails', '')),
            teaser_professional_emails=safe_str(row.get('teaser_professional_emails', '')),
            teaser_phones=safe_str(row.get('teaser_phones', '')),
            url=safe_str(row.get('url', ''))
        )
        db.session.merge(f)
        count += 1
    db.session.commit()
    print(f"  Founders: {count}")

def import_investors():
    rows = read_csv("InvestorsCleaned.csv")
    count = 0
    for row in rows:
        iid = safe_int(row.get('Investor Id', ''))
        if not iid:
            continue
        inv = Investor(
            investor_id=iid,
            investor_name=safe_str(row.get('Investor Name', '')),
            investor_status=safe_str(row.get('InvestorStatus', '')),
            hq_phone=safe_str(row.get('HQPhone', '')),
            hq_email=safe_str(row.get('HQEmail', '')),
            domain=safe_str(row.get('domain', '')),
            country_code=safe_str(row.get('Country Code', '')),
            investment_count=safe_float(row.get('Investment Count', '')),
            primary_investor_type=safe_str(row.get('PrimaryInvestorType', '')),
            investor_native_currency=safe_str(row.get('InvestorNativeCurrency', '')),
            hq_location=safe_str(row.get('HQLocation', '')),
            hq_address_line1=safe_str(row.get('HQAddressLine1', '')),
            hq_global_sub_region=safe_str(row.get('HQGlobalSubRegion', '')),
            total_investments=safe_float(row.get('TotalInvestments', '')),
            investor_types=safe_str(row.get('Investor Types', '')),
            last_updated=safe_str(row.get('LastUpdated', '')),
            type=safe_str(row.get('type', '')),
            permalink=safe_str(row.get('permalink', '')),
            roles=safe_str(row.get('roles', '')),
            region=safe_str(row.get('region', '')),
            city=safe_str(row.get('city', '')),
            linkedin_url=safe_str(row.get('linkedin_url', '')),
            logo_url=safe_str(row.get('Logo Url', '')),
            facebook_url=safe_str(row.get('Facebook Url', '')),
            twitter_url=safe_str(row.get('Twitter Url', '')),
            preferred_industry=safe_str(row.get('PreferredIndustry', '')),
            description=safe_str(row.get('Description', '')),
            preferred_geography=safe_str(row.get('PreferredGeography', '')),
            preferred_investment_types=safe_str(row.get('PreferredInvestmentTypes', '')),
            preferred_verticals=safe_str(row.get('PreferredVerticals', '')),
            total_active_portfolio=safe_float(row.get('TotalActivePortfolio', '')),
            total_exits=safe_float(row.get('TotalExits', '')),
            total_funding=safe_float(row.get('Total Funding', '')),
            total_funding_usd=safe_float(row.get('Total Funding Usd', '')),
            total_funding_currency_code=safe_str(row.get('Total Funding Currency Code', '')),
            aum=safe_float(row.get('AUM', '')),
            uuid=safe_str(row.get('uuid', ''))
        )
        db.session.merge(inv)
        count += 1
    db.session.commit()
    print(f"  Investors: {count}")

def import_funds():
    rows = read_csv("FundsCleaned.csv")
    count = 0
    for row in rows:
        fid = safe_int(row.get('Fund Id', ''))
        if not fid:
            continue
        fund = Fund(
            fund_id=fid,
            fund_name=safe_str(row.get('FundName', '')),
            fund_no=safe_float(row.get('FundNo', '')),
            first_fund=safe_str(row.get('FirstFund', '')),
            investor=safe_str(row.get('Investor', '')),
            investor_website=safe_str(row.get('InvestorWebsite', '')),
            vintage=safe_float(row.get('Vintage', '')),
            fund_status=safe_str(row.get('FundStatus', '')),
            fund_size=safe_float(row.get('FundSize', '')),
            fund_category=safe_str(row.get('FundCategory', '')),
            fund_type=safe_str(row.get('FundType', '')),
            fund_location=safe_str(row.get('FundLocation', '')),
            fund_city=safe_str(row.get('FundCity', '')),
            fund_country=safe_str(row.get('FundCountry', '')),
            preferred_industry=safe_str(row.get('PreferredIndustry', '')),
            preferred_geography=safe_str(row.get('PreferredGeography', '')),
            entity_name=safe_str(row.get('entity_name', '')),
            entity_type=safe_str(row.get('entity_type', '')),
            raised_amount_usd=safe_float(row.get('raised_amount_usd', '')),
            raised_amount=safe_float(row.get('raised_amount', '')),
            raised_amount_currency_code=safe_str(row.get('raised_amount_currency_code', '')),
            uuid=safe_str(row.get('uuid', '')),
            entity_uuid=safe_str(row.get('entity_uuid', ''))
        )
        db.session.merge(fund)
        count += 1
    db.session.commit()
    print(f"  Funds: {count}")

def import_funding_rounds():
    rows = read_csv("FundingRoundsCleaned.csv")
    count = 0
    for row in rows:
        frid = safe_int(row.get('Funding_Round_Id', ''))
        if not frid:
            continue
        fr = FundingRound(
            funding_round_id=frid,
            uuid=safe_str(row.get('Uuid', '')),
            deal_id=safe_str(row.get('Dealid', '')),
            deal_no=safe_float(row.get('Dealno', '')),
            round_name=safe_str(row.get('Round Name', '')),
            startup_name=safe_str(row.get('Startup Name', '')),
            domain_name=safe_str(row.get('Domain name', '')),
            founded_year=safe_str(row.get('Founded year', '')),
            country=safe_str(row.get('Country', '')),
            region=safe_str(row.get('Region', '')),
            city=safe_str(row.get('City', '')),
            date=safe_str(row.get('Date', '')),
            deal_synopsis=safe_str(row.get('Dealsynopsis', '')),
            deal_type=safe_str(row.get('Dealtype', '')),
            deal_type2=safe_str(row.get('Dealtype2', '')),
            deal_class=safe_str(row.get('Dealclass', '')),
            deal_status=safe_str(row.get('Dealstatus', '')),
            deal_size_status=safe_str(row.get('Dealsizestatus', '')),
            raised_amount=safe_float(row.get('Raised Amount', '')),
            raised_amount_usd=safe_float(row.get('Raised Amount Usd', '')),
            native_currency_of_deal=safe_str(row.get('Nativecurrencyofdeal', '')),
            addon=safe_str(row.get('Addon', '')),
            raised_to_date=safe_float(row.get('Raisedtodate', '')),
            total_funding_usd=safe_float(row.get('Total funding (usd)', '')),
            overview=safe_str(row.get('Overview', '')),
            business_status=safe_str(row.get('Businessstatus', '')),
            financing_status=safe_str(row.get('Financingstatus', '')),
            institutional_investors=safe_str(row.get('Institutional investors', '')),
            angel_investors=safe_str(row.get('Angel investors', '')),
            lead_investor=safe_str(row.get('Lead investor', '')),
            lead_investor_uuids=safe_str(row.get('Lead_investor_uuids', '')),
            investor_count=safe_float(row.get('Investor Count', '')),
            ceo=safe_str(row.get('Ceo', '')),
            ceo_biography=safe_str(row.get('Ceobiography', '')),
            startup_id=safe_int(row.get('Startup Id', '')),
            company_id=safe_str(row.get('Companyid', '')),
            org_uuid=safe_str(row.get('Org_uuid', ''))
        )
        db.session.merge(fr)
        count += 1
    db.session.commit()
    print(f"  FundingRounds: {count}")

def import_education():
    rows = read_csv("CompleteEducation.csv")
    count = 0
    for row in rows:
        eid = safe_str(row.get('Education Id', row.get('education_id', '')))
        if not eid:
            continue
        e = Education(
            education_id=eid,
            start_date=safe_int(row.get('start_date', '')),
            end_date=safe_int(row.get('end_date', '')),
            degree=safe_str(row.get('degree', '')),
            founder_id=safe_str(row.get('Founder Id', row.get('founder_id', ''))),
            institute_id=safe_str(row.get('Institute Id', row.get('institute_id', '')))
        )
        db.session.merge(e)
        count += 1
    db.session.commit()
    print(f"  Education: {count}")

def import_experiences():
    rows = read_csv("CompleteExperiences.csv")
    count = 0
    for row in rows:
        eid = safe_str(row.get('Experience Id', row.get('experience_id', '')))
        if not eid:
            continue
        e = Experience(
            experience_id=eid,
            founder_id=safe_str(row.get('Founder Id', row.get('founder_id', ''))),
            role=safe_str(row.get('Role', row.get('role', ''))),
            company=safe_str(row.get('Company', row.get('company', '')))
        )
        db.session.merge(e)
        count += 1
    db.session.commit()
    print(f"  Experiences: {count}")

def import_investments():
    rows = read_csv("investementsRaw.csv")
    count = 0
    for row in rows:
        iid = safe_int(row.get('Investement Id', ''))
        if not iid:
            continue
        inv = Investment(
            investment_id=iid,
            uuid=safe_str(row.get('uuid', '')),
            name=safe_str(row.get('name', '')),
            type=safe_str(row.get('type', '')),
            permalink=safe_str(row.get('permalink', '')),
            cb_url=safe_str(row.get('cb_url', '')),
            rank=safe_float(row.get('rank', '')),
            created_at=safe_str(row.get('created_at', '')),
            updated_at=safe_str(row.get('updated_at', '')),
            funding_round_uuid=safe_str(row.get('funding_round_uuid', '')),
            funding_round_name=safe_str(row.get('funding_round_name', '')),
            investor_uuid=safe_str(row.get('investor_uuid', '')),
            investor_name=safe_str(row.get('investor_name', '')),
            investor_type=safe_str(row.get('investor_type', '')),
            is_lead_investor=safe_str(row.get('is_lead_investor', '')),
            partner_uuid=safe_str(row.get('partner_uuid', '')),
            partner_name=safe_str(row.get('partner_name', '')),
            funding_round_id=safe_int(row.get('Funding_Round_Id', '')),
            investor_id=safe_int(row.get('Investor Id', ''))
        )
        db.session.merge(inv)
        count += 1
    db.session.commit()
    print(f"  Investments: {count}")

def import_association(filename, model_class, field_map):
    rows = read_csv(filename)
    count = 0
    for row in rows:
        kwargs = {}
        skip = False
        for csv_col, (attr, converter) in field_map.items():
            val = converter(row.get(csv_col, ''))
            if val is None:
                skip = True
                break
            kwargs[attr] = val
        if skip:
            continue
        obj = model_class(**kwargs)
        db.session.merge(obj)
        count += 1
    db.session.commit()
    print(f"  {model_class.__tablename__}: {count}")

def main():
    with app.app_context():
        # Delete existing db and recreate
        db.drop_all()
        db.create_all()

        # Add default user
        user = User(username='admin', password='admin')
        db.session.add(user)
        db.session.commit()

        print("Importing data...")
        import_institutes()
        import_incubators()
        import_startups()
        import_founders()
        import_investors()
        import_funds()
        import_funding_rounds()
        import_education()
        import_experiences()
        import_investments()

        # Association tables
        print("Importing associations...")
        import_association("CompleteStartupFounder.csv", StartupFounder, {
            'Startup Id': ('startup_id', safe_int),
            'Founder Id': ('founder_id', safe_str)
        })
        import_association("CompleteStartupIncubator.csv", StartupIncubator, {
            'Startup Id': ('startup_id', safe_int),
            'Incubator Id': ('incubator_id', safe_int)
        })
        import_association("IncubatorFounders.csv", IncubatorFounder, {
            'Incubator Id': ('incubator_id', safe_int),
            'Founder Id': ('founder_id', safe_str)
        })
        import_association("FundInvestors.csv", FundInvestor, {
            'Fund Id': ('fund_id', safe_int),
            'Investor Id': ('investor_id', safe_int)
        })

        print("\nDone! All data imported.")

if __name__ == "__main__":
    main()
