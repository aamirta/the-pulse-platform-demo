from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "User"

    user_id: Mapped[int] = mapped_column("UserId", Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column("Username", String(100), nullable=False, unique=True)
    password: Mapped[str] = mapped_column("Password", String(255), nullable=False)
    email: Mapped[str | None] = mapped_column("Email", String(255), nullable=True, unique=True)
    # Bumped to end every session this account has open. Tokens carry the value
    # they were minted with, so a stale one stops validating immediately.
    token_version: Mapped[int] = mapped_column(
        "token_version", Integer, nullable=False, default=0, server_default="0"
    )


class Institute(Base):
    __tablename__ = "Institutes"

    institute_id: Mapped[str] = mapped_column("Institute Id", String(50), primary_key=True)
    institute_name: Mapped[str | None] = mapped_column("Institute Name", String(255))

    educations: Mapped[list["Education"]] = relationship(back_populates="institute")


class Incubator(Base):
    __tablename__ = "Incubators"

    incubator_id: Mapped[int] = mapped_column("Incubator Id", Integer, primary_key=True)
    incubator: Mapped[str | None] = mapped_column("Incubator", String(50))
    type_organisme: Mapped[str | None] = mapped_column(String(50))
    statut: Mapped[str | None] = mapped_column(String(50))
    telephone: Mapped[str | None] = mapped_column(String(50))
    phases_investissement: Mapped[str | None] = mapped_column(String(50))
    ville_organisme: Mapped[str | None] = mapped_column(String(50))
    date_creation: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(String(50))
    secteurs: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(255))
    ville: Mapped[str | None] = mapped_column(String(50))
    linkedin: Mapped[str | None] = mapped_column(String(255))
    partners_or_sponsors: Mapped[str | None] = mapped_column(String(255))

    startups: Mapped[list["Startup"]] = relationship(
        secondary="StartupIncubators", back_populates="incubators"
    )
    founders: Mapped[list["Founder"]] = relationship(
        secondary="IncubatorFounders",
        back_populates="founder_incubators",
    )


class Startup(Base):
    __tablename__ = "Startups"

    startup_id: Mapped[int] = mapped_column("Startup Id", Integer, primary_key=True)
    startup_name: Mapped[str | None] = mapped_column("Startup name", String(255))
    stage: Mapped[str | None] = mapped_column(String(50))
    last_modified_date: Mapped[str | None] = mapped_column("lastModifiedDate", String(50))
    numero_ice: Mapped[str | None] = mapped_column("numeroICE", String(50))
    numero_rc: Mapped[str | None] = mapped_column("numeroRC", String(50))
    tribunal_x: Mapped[str | None] = mapped_column("tribunal_x", String(50))
    activite: Mapped[str | None] = mapped_column(Text)
    forme_juridique: Mapped[str | None] = mapped_column("formeJuridique", String(50))
    type_fille: Mapped[str | None] = mapped_column("typeFille", String(50))
    date_immatriculation: Mapped[DateTime | None] = mapped_column("dateImmatriculation", DateTime)
    capital: Mapped[Numeric[Any] | None] = mapped_column("capital", Numeric(18, 2))
    ompic: Mapped[Numeric[Any] | None] = mapped_column("ompic", Numeric(18, 2))
    location: Mapped[str | None] = mapped_column(String(50))
    region: Mapped[str | None] = mapped_column(String(50))
    contact_email: Mapped[str | None] = mapped_column("contactEmail", String(50))
    phone: Mapped[str | None] = mapped_column(String(50))
    entreprise_contact_site_web: Mapped[str | None] = mapped_column(
        "EntrepriseContactSiteWeb", String(255)
    )
    entreprise_contact_name: Mapped[str | None] = mapped_column("EntrepriseContactName", String(50))
    linkedin: Mapped[str | None] = mapped_column(String(255))
    youtube_link: Mapped[str | None] = mapped_column("youtubeLink", String(255))
    instagram_link: Mapped[str | None] = mapped_column("instagramLink", String(255))
    logo_url: Mapped[str | None] = mapped_column("logo_url", String(255))
    presentation_video: Mapped[str | None] = mapped_column("presentationVideo", String(255))
    sector: Mapped[str | None] = mapped_column(String(255))
    markets: Mapped[str | None] = mapped_column(String(50))
    employees: Mapped[str | None] = mapped_column(String(50))
    revenue: Mapped[str | None] = mapped_column(String(50))
    raised_funds: Mapped[Numeric[Any] | None] = mapped_column("raisedFunds", Numeric(18, 2))
    valuation: Mapped[str | None] = mapped_column(String(50))
    incubated_by: Mapped[str | None] = mapped_column("incubatedBy", String(50))
    is_incubator_valid: Mapped[bool | None] = mapped_column("isIncubatorValid", Boolean)
    financed_by: Mapped[str | None] = mapped_column("financedBy", String(50))
    is_financer_valid: Mapped[bool | None] = mapped_column("isFinancerValid", Boolean)
    is_jei_validated: Mapped[bool | None] = mapped_column("isJEIValidated", Boolean)
    description: Mapped[str | None] = mapped_column(Text)
    description_en: Mapped[str | None] = mapped_column("description_en", Text)
    uuid: Mapped[str | None] = mapped_column(String(50))
    type: Mapped[str | None] = mapped_column(String(50))
    homepage_url: Mapped[str | None] = mapped_column("homepage_url", String(255))
    country_code: Mapped[str | None] = mapped_column("country_code", String(50))
    address: Mapped[str | None] = mapped_column(String(255))
    postal_code: Mapped[Numeric[Any] | None] = mapped_column("postal_code", Numeric(18, 2))
    num_funding_rounds: Mapped[str | None] = mapped_column("num_funding_rounds", String(50))
    total_funding_usd: Mapped[Numeric[Any] | None] = mapped_column("total_funding_usd", Numeric(18, 2))
    total_funding: Mapped[Numeric[Any] | None] = mapped_column("total_funding", Numeric(18, 2))
    total_funding_currency_code: Mapped[str | None] = mapped_column(
        "total_funding_currency_code", String(50)
    )
    last_funding_on: Mapped[str | None] = mapped_column("last_funding_on", String(50))
    facebook_url: Mapped[str | None] = mapped_column("facebook_url", String(255))
    twitter_url: Mapped[str | None] = mapped_column("twitter_url", String(255))
    alias1: Mapped[str | None] = mapped_column("alias1", String(255))
    company_id: Mapped[str | None] = mapped_column("CompanyID", String(50))
    company_also_known_as: Mapped[str | None] = mapped_column("CompanyAlsoKnownAs", String(50))
    company_former_name: Mapped[str | None] = mapped_column("CompanyFormerName", String(50))
    company_legal_name: Mapped[str | None] = mapped_column("CompanyLegalName", String(50))
    company_financing_status: Mapped[str | None] = mapped_column(
        "CompanyFinancingStatus", String(50)
    )
    company_financing_status_date: Mapped[str | None] = mapped_column(
        "CompanyFinancingStatusDate", String(50)
    )
    total_raised: Mapped[Numeric[Any] | None] = mapped_column("TotalRaised", Numeric(18, 2))
    total_raised_native_amount: Mapped[Numeric[Any] | None] = mapped_column(
        "TotalRaisedNativeAmount", Numeric(18, 2)
    )
    total_raised_native_currency: Mapped[str | None] = mapped_column(
        "TotalRaisedNativeCurrency", String(50)
    )
    business_status: Mapped[str | None] = mapped_column("BusinessStatus", String(50))
    business_status_date: Mapped[str | None] = mapped_column("BusinessStatusDate", String(50))
    ownership_status: Mapped[str | None] = mapped_column("OwnershipStatus", String(50))
    ownership_status_date: Mapped[str | None] = mapped_column("OwnershipStatusDate", String(50))
    universe: Mapped[str | None] = mapped_column("Universe", String(50))
    employee_as_of_date: Mapped[str | None] = mapped_column("EmployeeAsOfDate", String(50))
    year_founded: Mapped[str | None] = mapped_column("YearFounded", String(50))
    parent_company: Mapped[str | None] = mapped_column("ParentCompany", String(50))
    parent_company_id: Mapped[str | None] = mapped_column("ParentCompanyID", String(50))
    financing_status_note: Mapped[str | None] = mapped_column("FinancingStatusNote", Text)
    financing_status_note_as_of_date: Mapped[str | None] = mapped_column(
        "FinancingStatusNoteAsOfDate", String(50)
    )
    primary_industry_sector: Mapped[str | None] = mapped_column("PrimaryIndustrySector", String(50))
    primary_industry_group: Mapped[str | None] = mapped_column("PrimaryIndustryGroup", String(50))
    primary_industry_code: Mapped[str | None] = mapped_column("PrimaryIndustryCode", String(50))
    all_industries: Mapped[str | None] = mapped_column("AllIndustries", String(255))
    verticals: Mapped[str | None] = mapped_column("Verticals", String(255))
    hq_post_code: Mapped[Numeric[Any] | None] = mapped_column("HQPostCode", Numeric(18, 2))
    hq_country: Mapped[str | None] = mapped_column("HQCountry", String(50))
    hq_fax: Mapped[str | None] = mapped_column("HQFax", String(50))
    hq_global_region: Mapped[str | None] = mapped_column("HQGlobalRegion", String(50))
    hq_global_sub_region: Mapped[str | None] = mapped_column("HQGlobalSubRegion", String(50))
    alternate_office_count: Mapped[Numeric[Any] | None] = mapped_column(
        "AlternateOfficeCount", Numeric(18, 2)
    )
    active_investors: Mapped[Numeric[Any] | None] = mapped_column("ActiveInvestors", Numeric(18, 2))
    former_investors: Mapped[Numeric[Any] | None] = mapped_column("FormerInvestors", Numeric(18, 2))
    revenue1: Mapped[Numeric[Any] | None] = mapped_column("Revenue1", Numeric(18, 2))
    gross_profit: Mapped[Numeric[Any] | None] = mapped_column("GrossProfit", Numeric(18, 2))
    net_income: Mapped[Numeric[Any] | None] = mapped_column("NetIncome", Numeric(18, 2))
    enterprise_value: Mapped[Numeric[Any] | None] = mapped_column("EnterpriseValue", Numeric(18, 2))
    ebitda: Mapped[Numeric[Any] | None] = mapped_column("EBITDA", Numeric(18, 2))
    ebit: Mapped[Numeric[Any] | None] = mapped_column("EBIT", Numeric(18, 2))
    net_debt: Mapped[Numeric[Any] | None] = mapped_column("NetDebt", Numeric(18, 2))
    fiscal_period: Mapped[str | None] = mapped_column("FiscalPeriod", String(50))
    period_end_date: Mapped[str | None] = mapped_column("PeriodEndDate", String(50))
    first_financing_deal_id: Mapped[str | None] = mapped_column("FirstFinancingDealID", String(50))
    first_financing_date: Mapped[str | None] = mapped_column("FirstFinancingDate", String(50))
    first_financing_size: Mapped[Numeric[Any] | None] = mapped_column(
        "FirstFinancingSize", Numeric(18, 2)
    )
    first_financing_size_status: Mapped[str | None] = mapped_column(
        "FirstFinancingSizeStatus", String(50)
    )
    first_financing_valuation: Mapped[Numeric[Any] | None] = mapped_column(
        "FirstFinancingValuation", Numeric(18, 2)
    )
    first_financing_valuation_status: Mapped[str | None] = mapped_column(
        "FirstFinancingValuationStatus", String(50)
    )
    first_financing_deal_type: Mapped[str | None] = mapped_column(
        "FirstFinancingDealType", String(50)
    )
    first_financing_deal_type2: Mapped[str | None] = mapped_column(
        "FirstFinancingDealType2", String(50)
    )
    first_financing_deal_class: Mapped[str | None] = mapped_column(
        "FirstFinancingDealClass", String(50)
    )
    first_financing_debt_date: Mapped[str | None] = mapped_column(
        "FirstFinancingDebtDate", String(50)
    )
    first_financing_status: Mapped[str | None] = mapped_column("FirstFinancingStatus", String(50))
    last_known_valuation: Mapped[Numeric[Any] | None] = mapped_column(
        "LastKnownValuation", Numeric(18, 2)
    )
    last_known_valuation_date: Mapped[str | None] = mapped_column(
        "LastKnownValuationDate", String(50)
    )
    last_known_valuation_deal_type: Mapped[str | None] = mapped_column(
        "LastKnownValuationDealType", String(50)
    )
    last_financing_deal_id: Mapped[str | None] = mapped_column("LastFinancingDealID", String(50))
    last_financing_date: Mapped[str | None] = mapped_column("LastFinancingDate", String(50))
    last_financing_size: Mapped[Numeric[Any] | None] = mapped_column("LastFinancingSize", Numeric(18, 2))
    last_financing_size_status: Mapped[str | None] = mapped_column(
        "LastFinancingSizeStatus", String(50)
    )
    last_financing_deal_type: Mapped[str | None] = mapped_column(
        "LastFinancingDealType", String(50)
    )
    last_financing_deal_type2: Mapped[str | None] = mapped_column(
        "LastFinancingDealType2", String(50)
    )
    last_financing_deal_class: Mapped[str | None] = mapped_column(
        "LastFinancingDealClass", String(50)
    )
    last_financing_debt_date: Mapped[str | None] = mapped_column(
        "LastFinancingDebtDate", String(50)
    )
    last_financing_status: Mapped[str | None] = mapped_column("LastFinancingStatus", String(50))
    business_models: Mapped[str | None] = mapped_column("Business Models", String(50))
    team_background: Mapped[str | None] = mapped_column("Team Background", String(50))
    waves: Mapped[Numeric[Any] | None] = mapped_column("Waves", Numeric(18, 2))
    trending_themes: Mapped[Numeric[Any] | None] = mapped_column("Trending Themes", Numeric(18, 2))
    special_flags_true: Mapped[str | None] = mapped_column("Special Flags: TRUE", String(255))
    company_stage: Mapped[str | None] = mapped_column("Company Stage", String(50))
    is_funded: Mapped[bool | None] = mapped_column("Is Funded", Boolean)
    total_funding_usd_alt: Mapped[Numeric[Any] | None] = mapped_column(
        "Total Funding (USD)", Numeric(18, 2)
    )
    latest_funded_amount_usd: Mapped[Numeric[Any] | None] = mapped_column(
        "Latest Funded Amount (USD)", Numeric(18, 2)
    )
    latest_funded_date: Mapped[str | None] = mapped_column("Latest Funded Date", String(50))
    latest_valuation_usd: Mapped[str | None] = mapped_column("Latest Valuation (USD)", String(50))
    institutional_investors: Mapped[str | None] = mapped_column("Institutional Investors", Text)
    angel_investors: Mapped[str | None] = mapped_column("Angel Investors", String(50))
    annual_revenue_usd: Mapped[Numeric[Any] | None] = mapped_column(
        "Annual Revenue (USD)", Numeric(18, 2)
    )
    annual_net_profit_usd: Mapped[Numeric[Any] | None] = mapped_column(
        "Annual Net Profit (USD)", Numeric(18, 2)
    )
    annual_ebitda_usd: Mapped[Numeric[Any] | None] = mapped_column("Annual EBITDA (USD)", Numeric(18, 2))
    key_people_info: Mapped[str | None] = mapped_column("Key People Info", Text)
    links_to_key_people_profiles: Mapped[str | None] = mapped_column(
        "Links to Key People Profiles", String(255)
    )
    acquisition_list: Mapped[str | None] = mapped_column("Acquisition List", String(50))
    is_acquired: Mapped[bool | None] = mapped_column("Is Acquired", Boolean)
    acquired_by: Mapped[str | None] = mapped_column("Acquired By", String(50))
    acquired_date: Mapped[DateTime | None] = mapped_column("Acquired Date", DateTime)
    acquired_amount_usd: Mapped[Numeric[Any] | None] = mapped_column(
        "Acquired Amount (USD)", Numeric(18, 2)
    )
    acquisition_type: Mapped[str | None] = mapped_column("Acquisition Type", String(50))
    soonicorn_club_status: Mapped[str | None] = mapped_column("Soonicorn Club Status", String(50))
    soonicorn_club_event_date: Mapped[str | None] = mapped_column(
        "Soonicorn Club Event Date", String(50)
    )
    company_emails: Mapped[str | None] = mapped_column("Company Emails", String(50))
    blog_url: Mapped[str | None] = mapped_column("Blog Url", String(50))
    is_deadpooled: Mapped[bool | None] = mapped_column("Is Deadpooled", Boolean)
    deadpooled_date: Mapped[Numeric[Any] | None] = mapped_column("Deadpooled Date", Numeric(18, 2))
    status_startup: Mapped[str | None] = mapped_column("Status Startup", String(50))

    funding_rounds: Mapped[list["FundingRound"]] = relationship(back_populates="startup")
    founders: Mapped[list["Founder"]] = relationship(
        secondary="StartupFounders", back_populates="startups"
    )
    incubators: Mapped[list["Incubator"]] = relationship(
        secondary="StartupIncubators", back_populates="startups"
    )


class FundingRound(Base):
    __tablename__ = "FundingRounds"

    funding_round_id: Mapped[int] = mapped_column("Funding_Round_Id", Integer, primary_key=True)
    uuid: Mapped[str | None] = mapped_column("Uuid", String(50))
    deal_id: Mapped[str | None] = mapped_column("Dealid", String(50))
    deal_no: Mapped[Numeric[Any] | None] = mapped_column("Dealno", Numeric(18, 2))
    round_name: Mapped[str | None] = mapped_column("Round Name", String(50))
    startup_name: Mapped[str | None] = mapped_column("Startup Name", String(50))
    domain_name: Mapped[str | None] = mapped_column("Domain name", String(50))
    founded_year: Mapped[str | None] = mapped_column("Founded year", String(50))
    country: Mapped[str | None] = mapped_column("Country", String(50))
    region: Mapped[str | None] = mapped_column("Region", String(50))
    city: Mapped[str | None] = mapped_column("City", String(50))
    date: Mapped[str | None] = mapped_column("Date", String(50))
    deal_synopsis: Mapped[str | None] = mapped_column("Dealsynopsis", Text)
    deal_type: Mapped[str | None] = mapped_column("Dealtype", String(50))
    deal_type2: Mapped[str | None] = mapped_column("Dealtype2", String(50))
    deal_class: Mapped[str | None] = mapped_column("Dealclass", String(50))
    deal_status: Mapped[str | None] = mapped_column("Dealstatus", String(50))
    deal_size_status: Mapped[str | None] = mapped_column("Dealsizestatus", String(50))
    raised_amount: Mapped[Numeric[Any] | None] = mapped_column("Raised Amount", Numeric(18, 2))
    raised_amount_usd: Mapped[Numeric[Any] | None] = mapped_column("Raised Amount Usd", Numeric(18, 2))
    native_currency_of_deal: Mapped[str | None] = mapped_column("Nativecurrencyofdeal", String(50))
    addon: Mapped[str | None] = mapped_column("Addon", String(50))
    raised_to_date: Mapped[Numeric[Any] | None] = mapped_column("Raisedtodate", Numeric(18, 2))
    total_funding_usd: Mapped[Numeric[Any] | None] = mapped_column("Total funding (usd)", Numeric(18, 2))
    overview: Mapped[str | None] = mapped_column("Overview", String(255))
    business_status: Mapped[str | None] = mapped_column("Businessstatus", String(50))
    financing_status: Mapped[str | None] = mapped_column("Financingstatus", String(50))
    type_of_stock: Mapped[str | None] = mapped_column("Typeofstock", String(50))
    vc_round: Mapped[str | None] = mapped_column("Vcround", String(50))
    business_models: Mapped[str | None] = mapped_column("Business models", String(50))
    institutional_investors: Mapped[str | None] = mapped_column(
        "Institutional investors", String(255)
    )
    angel_investors: Mapped[str | None] = mapped_column("Angel investors", String(50))
    lead_investor: Mapped[str | None] = mapped_column("Lead investor", String(255))
    lead_investor_uuids: Mapped[str | None] = mapped_column("Lead_investor_uuids", String(255))
    facilitators: Mapped[str | None] = mapped_column("Facilitators", String(50))
    investor_count: Mapped[Numeric[Any] | None] = mapped_column("Investor Count", Numeric(18, 2))
    ceo: Mapped[str | None] = mapped_column("Ceo", String(50))
    ceo_pbid: Mapped[str | None] = mapped_column("Ceopbid", String(50))
    ceo_phone: Mapped[str | None] = mapped_column("Ceophone", String(50))
    ceo_email: Mapped[str | None] = mapped_column("Ceoemail", String(50))
    ceo_biography: Mapped[str | None] = mapped_column("Ceobiography", Text)
    ceo_education: Mapped[str | None] = mapped_column("Ceoeducation", String(255))
    startup_id: Mapped[int | None] = mapped_column(
        "Startup Id", Integer, ForeignKey("Startups.Startup Id")
    )
    company_id: Mapped[str | None] = mapped_column("Companyid", String(50))
    org_uuid: Mapped[str | None] = mapped_column("Org_uuid", String(50))

    startup: Mapped[Optional["Startup"]] = relationship(back_populates="funding_rounds")
    investments: Mapped[list["Investment"]] = relationship(back_populates="funding_round")


class Investment(Base):
    __tablename__ = "Investements"

    investment_id: Mapped[int] = mapped_column("Investement Id", Integer, primary_key=True)
    uuid: Mapped[str | None] = mapped_column("uuid", String(50))
    name: Mapped[str | None] = mapped_column("name", String(255))
    type: Mapped[str | None] = mapped_column("type", String(50))
    permalink: Mapped[str | None] = mapped_column("permalink", String(255))
    cb_url: Mapped[str | None] = mapped_column("cb_url", String(255))
    rank: Mapped[Numeric[Any] | None] = mapped_column("rank", Numeric(18, 2))
    created_at: Mapped[str | None] = mapped_column("created_at", String(50))
    updated_at: Mapped[str | None] = mapped_column("updated_at", String(50))
    funding_round_uuid: Mapped[str | None] = mapped_column("funding_round_uuid", String(50))
    funding_round_name: Mapped[str | None] = mapped_column("funding_round_name", String(50))
    investor_uuid: Mapped[str | None] = mapped_column("investor_uuid", String(50))
    investor_name: Mapped[str | None] = mapped_column("investor_name", String(50))
    investor_type: Mapped[str | None] = mapped_column("investor_type", String(50))
    is_lead_investor: Mapped[str | None] = mapped_column("is_lead_investor", String(50))
    partner_uuid: Mapped[str | None] = mapped_column("partner_uuid", String(50))
    partner_name: Mapped[str | None] = mapped_column("partner_name", String(50))
    funding_round_id: Mapped[int | None] = mapped_column(
        "Funding_Round_Id", Integer, ForeignKey("FundingRounds.Funding_Round_Id")
    )
    investor_id: Mapped[int | None] = mapped_column(
        "Investor Id", Integer, ForeignKey("Investors.Investor Id")
    )

    funding_round: Mapped[Optional["FundingRound"]] = relationship(back_populates="investments")
    investor: Mapped[Optional["Investor"]] = relationship(back_populates="investments")


class LimitedPartner(Base):
    __tablename__ = "LimitedPartner"

    limited_partner_id: Mapped[int] = mapped_column("LimitedPartner Id", Integer, primary_key=True)
    limited_partner_id_alt: Mapped[str | None] = mapped_column("LimitedPartnerID", String(50))
    limited_partner_name: Mapped[str | None] = mapped_column("LimitedPartnerName", String(50))
    limited_partner_former_name: Mapped[str | None] = mapped_column(
        "LimitedPartnerFormerName", String(255)
    )
    limited_partner_also_known_as: Mapped[str | None] = mapped_column(
        "LimitedPartnerAlsoKnownAs", String(50)
    )
    description: Mapped[str | None] = mapped_column("Description", Text)
    limited_partner_type: Mapped[str | None] = mapped_column("LimitedPartnerType", String(50))
    aum: Mapped[Numeric[Any] | None] = mapped_column("AUM", Numeric(18, 2))
    year_founded: Mapped[str | None] = mapped_column("YearFounded", String(50))
    website: Mapped[str | None] = mapped_column("Website", String(50))
    hq_location: Mapped[str | None] = mapped_column("HQLocation", String(50))
    hq_address_line1: Mapped[str | None] = mapped_column("HQAddressLine1", String(50))
    hq_address_line2: Mapped[str | None] = mapped_column("HQAddressLine2", String(50))
    hq_city: Mapped[str | None] = mapped_column("HQCity", String(50))
    hq_post_code: Mapped[Numeric[Any] | None] = mapped_column("HQPostCode", Numeric(18, 2))
    hq_country: Mapped[str | None] = mapped_column("HQCountry", String(50))
    hq_phone: Mapped[str | None] = mapped_column("HQPhone", String(50))
    hq_fax: Mapped[str | None] = mapped_column("HQFax", String(50))
    hq_email: Mapped[str | None] = mapped_column("HQEmail", String(50))
    hq_global_region: Mapped[str | None] = mapped_column("HQGlobalRegion", String(50))
    hq_global_sub_region: Mapped[str | None] = mapped_column("HQGlobalSubRegion", String(50))
    sold_secondary_commitments: Mapped[str | None] = mapped_column(
        "SoldSecondaryCommitments", String(50)
    )
    bought_secondary_commitments: Mapped[str | None] = mapped_column(
        "BoughtSecondaryCommitments", String(50)
    )
    total_commitments: Mapped[int | None] = mapped_column("TotalCommitments", BigInteger)
    total_active_commitments: Mapped[int | None] = mapped_column(
        "TotalActiveCommitments", BigInteger
    )
    total_commitments_in_pe_funds: Mapped[Numeric[Any] | None] = mapped_column(
        "TotalCommitmentsInPEFunds", Numeric(18, 2)
    )
    total_commitments_in_vc_funds: Mapped[int | None] = mapped_column(
        "TotalCommitmentsInVCFunds", BigInteger
    )
    open_to_first_time_funds: Mapped[str | None] = mapped_column("OpenToFirstTimeFunds", String(50))
    real_estate: Mapped[Numeric[Any] | None] = mapped_column("RealEstate", Numeric(18, 2))
    real_estate_percent: Mapped[Numeric[Any] | None] = mapped_column("RealEstatePercent", Numeric(18, 2))
    equities: Mapped[Numeric[Any] | None] = mapped_column("Equities", Numeric(18, 2))
    equities_percent: Mapped[Numeric[Any] | None] = mapped_column("EquitiesPercent", Numeric(18, 2))
    fixed_income_percent: Mapped[Numeric[Any] | None] = mapped_column(
        "FixedIncomePercent", Numeric(18, 2)
    )
    cash: Mapped[Numeric[Any] | None] = mapped_column("Cash", Numeric(18, 2))
    cash_percent: Mapped[Numeric[Any] | None] = mapped_column("CashPercent", Numeric(18, 2))
    policy_description: Mapped[str | None] = mapped_column("PolicyDescription", Text)
    preferred_geography: Mapped[str | None] = mapped_column("PreferredGeography", String(255))
    preferred_fund_type: Mapped[str | None] = mapped_column("PreferredFundType", String(255))

    lp_funds: Mapped[list["LPFund"]] = relationship(back_populates="limited_partner")


class ServiceProvider(Base):
    __tablename__ = "ServiceProvider"

    service_provider_id: Mapped[int] = mapped_column(
        "ServiceProvider Id", Integer, primary_key=True
    )
    service_provider_id_alt: Mapped[str | None] = mapped_column("ServiceProviderID", String(50))
    service_provider_name: Mapped[str | None] = mapped_column("ServiceProviderName", String(50))
    service_provider_also_known_as: Mapped[str | None] = mapped_column(
        "ServiceProviderAlsoKnownAs", String(50)
    )
    employees: Mapped[Numeric[Any] | None] = mapped_column("Employees", Numeric(18, 2))
    description: Mapped[str | None] = mapped_column("Description", String(255))
    website: Mapped[str | None] = mapped_column("Website", String(50))
    primary_service_provider_type: Mapped[str | None] = mapped_column(
        "PrimaryServiceProviderType", String(50)
    )
    other_service_provider_types: Mapped[str | None] = mapped_column(
        "OtherServiceProviderTypes", String(50)
    )
    serviced_companies: Mapped[int | None] = mapped_column("ServicedCompanies", Integer)
    serviced_deals: Mapped[int | None] = mapped_column("ServicedDeals", Integer)
    serviced_investors: Mapped[int | None] = mapped_column("ServicedInvestors", Integer)
    serviced_funds: Mapped[Numeric[Any] | None] = mapped_column("ServicedFunds", Numeric(18, 2))
    hq_location: Mapped[str | None] = mapped_column("HQLocation", String(50))
    hq_address_line1: Mapped[str | None] = mapped_column("HQAddressLine1", String(50))
    hq_address_line2: Mapped[str | None] = mapped_column("HQAddressLine2", String(50))
    hq_city: Mapped[str | None] = mapped_column("HQCity", String(50))
    hq_post_code: Mapped[Numeric[Any] | None] = mapped_column("HQPostCode", Numeric(18, 2))
    hq_country: Mapped[str | None] = mapped_column("HQCountry", String(50))
    hq_phone: Mapped[str | None] = mapped_column("HQPhone", String(50))
    hq_fax: Mapped[str | None] = mapped_column("HQFax", String(50))
    hq_email: Mapped[str | None] = mapped_column("HQEmail", String(50))
    hq_global_region: Mapped[str | None] = mapped_column("HQGlobalRegion", String(50))
    hq_global_sub_region: Mapped[str | None] = mapped_column("HQGlobalSubRegion", String(50))
    row_id: Mapped[str | None] = mapped_column("RowID", String(255))
    last_updated: Mapped[str | None] = mapped_column("LastUpdated", String(50))

    sp_funds: Mapped[list["SPFund"]] = relationship(back_populates="service_provider")
    sp_investors: Mapped[list["SPInvestor"]] = relationship(back_populates="service_provider")


class LPFund(Base):
    __tablename__ = "LPFunds"

    fund_name: Mapped[str | None] = mapped_column("FundName", String(50))
    commitment_date: Mapped[DateTime | None] = mapped_column("CommitmentDate", DateTime)
    fund_id: Mapped[int] = mapped_column(
        "Fund Id", Integer, ForeignKey("Funds.Fund Id"), primary_key=True, nullable=False
    )
    limited_partner_id: Mapped[int] = mapped_column(
        "LimitedPartner Id",
        Integer,
        ForeignKey("LimitedPartner.LimitedPartner Id"),
        primary_key=True,
        nullable=False,
    )

    fund: Mapped["Fund"] = relationship(back_populates="lp_funds")
    limited_partner: Mapped["LimitedPartner"] = relationship(back_populates="lp_funds")


class SPFund(Base):
    __tablename__ = "SPFunds"

    fund_name: Mapped[str | None] = mapped_column("FundName", String(50))
    investor_id_alt: Mapped[str | None] = mapped_column("InvestorID", String(50))
    investor_name: Mapped[str | None] = mapped_column("InvestorName", String(50))
    service_provided: Mapped[str | None] = mapped_column("ServiceProvided", String(50))
    fund_id: Mapped[int] = mapped_column(
        "Fund Id", Integer, ForeignKey("Funds.Fund Id"), primary_key=True, nullable=False
    )
    service_provider_id: Mapped[int] = mapped_column(
        "ServiceProvider Id",
        Integer,
        ForeignKey("ServiceProvider.ServiceProvider Id"),
        primary_key=True,
        nullable=False,
    )

    fund: Mapped["Fund"] = relationship(back_populates="sp_funds")
    service_provider: Mapped["ServiceProvider"] = relationship(back_populates="sp_funds")


class SPInvestor(Base):
    __tablename__ = "SPInvestor"

    investor_name: Mapped[str | None] = mapped_column("InvestorName", String(50))
    service_type: Mapped[str | None] = mapped_column("ServiceType", String(50))
    deal_id: Mapped[str | None] = mapped_column("DealID", String(50))
    service_provided: Mapped[str | None] = mapped_column("ServiceProvided", String(50))
    investor_id: Mapped[int] = mapped_column(
        "Investor Id",
        Integer,
        ForeignKey("Investors.Investor Id"),
        primary_key=True,
        nullable=False,
    )
    service_provider_id: Mapped[int] = mapped_column(
        "ServiceProvider Id",
        Integer,
        ForeignKey("ServiceProvider.ServiceProvider Id"),
        primary_key=True,
        nullable=False,
    )

    investor: Mapped["Investor"] = relationship(back_populates="sp_investors")
    service_provider: Mapped["ServiceProvider"] = relationship(back_populates="sp_investors")


class StartupFounder(Base):
    __tablename__ = "StartupFounders"

    startup_id: Mapped[int] = mapped_column(
        "Startup Id", Integer, ForeignKey("Startups.Startup Id"), primary_key=True
    )
    founder_id: Mapped[str] = mapped_column(
        "Founder Id", String(50), ForeignKey("Founders.Founder Id"), primary_key=True
    )


class StartupIncubator(Base):
    __tablename__ = "StartupIncubators"

    startup_id: Mapped[int] = mapped_column(
        "Startup Id", Integer, ForeignKey("Startups.Startup Id"), primary_key=True
    )
    incubator_id: Mapped[int] = mapped_column(
        "Incubator Id", Integer, ForeignKey("Incubators.Incubator Id"), primary_key=True
    )


class IncubatorFounder(Base):
    __tablename__ = "IncubatorFounders"

    incubator_id: Mapped[int] = mapped_column(
        "Incubator Id", Integer, ForeignKey("Incubators.Incubator Id"), primary_key=True
    )
    founder_id: Mapped[str] = mapped_column(
        "Founder Id", String(50), ForeignKey("Founders.Founder Id"), primary_key=True
    )


class FundInvestor(Base):
    __tablename__ = "FundInvestors"

    fund_id: Mapped[int] = mapped_column(
        "Fund Id", Integer, ForeignKey("Funds.Fund Id"), primary_key=True
    )
    investor_id: Mapped[int] = mapped_column(
        "Investor Id", Integer, ForeignKey("Investors.Investor Id"), primary_key=True
    )


class Founder(Base):
    __tablename__ = "Founders"

    founder_id: Mapped[str] = mapped_column("Founder Id", String(50), primary_key=True)
    # The community account behind this profile, when there is one.
    #
    # Founder ids are strings — scraped rows carry a numeric id, and a row
    # created at onboarding carries a random token — so a founder cannot be
    # addressed through ``member_entity_links``, whose ``entity_id`` is an
    # integer. Onboarding creates this row *from* a member, so the identity is
    # known at that moment; recording it here is what lets a profile page offer
    # a Message button. NULL means a scraped profile nobody has claimed.
    member_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("pulse_members.id", ondelete="SET NULL"), index=True
    )
    name: Mapped[str | None] = mapped_column("name", String(50))
    first_name: Mapped[str | None] = mapped_column("first_name", String(50))
    last_name: Mapped[str | None] = mapped_column("last_name", String(50))
    current_title: Mapped[str | None] = mapped_column("current_title", String(255))
    current_employer: Mapped[str | None] = mapped_column("current_employer", String(255))
    location: Mapped[str | None] = mapped_column("location", String(50))
    linkedin_url: Mapped[str | None] = mapped_column("linkedin_url", String(255))
    profile_pic: Mapped[str | None] = mapped_column("profile_pic", String(255))
    link_twitter: Mapped[str | None] = mapped_column("link_twitter", String(255))
    link_facebook: Mapped[str | None] = mapped_column("link_facebook", String(255))
    link_instagram: Mapped[str | None] = mapped_column("link_instagram", String(255))
    link_quora: Mapped[str | None] = mapped_column("link_quora", String(255))
    link_github: Mapped[str | None] = mapped_column("link_github", String(255))
    link_aboutme: Mapped[str | None] = mapped_column("link_aboutme", String(255))
    link_angellist: Mapped[str | None] = mapped_column("link_angellist", String(255))
    link_stackoverflow: Mapped[str | None] = mapped_column("link_stackoverflow", String(255))
    company_details_name: Mapped[str | None] = mapped_column("company_details_name", String(50))
    company_details_logo_url: Mapped[str | None] = mapped_column(
        "company_details_logo_url", String(255)
    )
    most_recent_ended_exp_title: Mapped[str | None] = mapped_column(
        "most_recent_ended_exp_title", String(255)
    )
    most_recent_ended_exp_company_info_url: Mapped[str | None] = mapped_column(
        "most_recent_ended_exp_company_info_url", String(255)
    )
    most_recent_ended_exp_employer: Mapped[str | None] = mapped_column(
        "most_recent_ended_exp_employer", String(255)
    )
    most_recent_ended_exp_end_date: Mapped[str | None] = mapped_column(
        "most_recent_ended_exp_end_date", String(50)
    )
    prev_company_name: Mapped[str | None] = mapped_column("prev_company_name", String(255))
    last_job_change: Mapped[str | None] = mapped_column("last_job_change", String(50))
    prev_company_logo_url: Mapped[str | None] = mapped_column("prev_company_logo_url", String(255))
    prev_company_info_url: Mapped[str | None] = mapped_column("prev_company_info_url", String(255))
    skills: Mapped[str | None] = mapped_column("skills", Text)
    teaser_emails: Mapped[str | None] = mapped_column("teaser_emails", String(255))
    teaser_personal_emails: Mapped[str | None] = mapped_column("teaser_personal_emails", String(50))
    teaser_professional_emails: Mapped[str | None] = mapped_column(
        "teaser_professional_emails", String(255)
    )
    teaser_phones: Mapped[str | None] = mapped_column("teaser_phones", String(255))
    url: Mapped[str | None] = mapped_column("url", String(50))

    educations: Mapped[list["Education"]] = relationship(back_populates="founder")
    experiences: Mapped[list["Experience"]] = relationship(back_populates="founder")
    startups: Mapped[list["Startup"]] = relationship(
        secondary="StartupFounders", back_populates="founders"
    )
    founder_incubators: Mapped[list["Incubator"]] = relationship(
        secondary="IncubatorFounders", back_populates="founders"
    )


class Education(Base):
    __tablename__ = "Education"

    education_id: Mapped[str] = mapped_column("Education Id", String(50), primary_key=True)
    start_date: Mapped[int | None] = mapped_column("start_date", Integer)
    end_date: Mapped[int | None] = mapped_column("end_date", Integer)
    degree: Mapped[str | None] = mapped_column("degree", String(255))
    founder_id: Mapped[str | None] = mapped_column(
        "Founder Id", String(50), ForeignKey("Founders.Founder Id")
    )
    institute_id: Mapped[str | None] = mapped_column(
        "Institute Id", String(50), ForeignKey("Institutes.Institute Id")
    )

    founder: Mapped[Optional["Founder"]] = relationship(back_populates="educations")
    institute: Mapped[Optional["Institute"]] = relationship(back_populates="educations")


class Experience(Base):
    __tablename__ = "Experiences"

    experience_id: Mapped[str] = mapped_column("Experience Id", String(50), primary_key=True)
    founder_id: Mapped[str | None] = mapped_column(
        "Founder Id", String(50), ForeignKey("Founders.Founder Id")
    )
    role: Mapped[str | None] = mapped_column("Role", String(255))
    company: Mapped[str | None] = mapped_column("Company", String(255))

    founder: Mapped[Optional["Founder"]] = relationship(back_populates="experiences")


class Fund(Base):
    __tablename__ = "Funds"

    fund_id: Mapped[int] = mapped_column("Fund Id", Integer, primary_key=True)
    fund_name: Mapped[str | None] = mapped_column("FundName", String(50))
    fund_no: Mapped[Numeric[Any] | None] = mapped_column("FundNo", Numeric(18, 2))
    first_fund: Mapped[str | None] = mapped_column("FirstFund", String(50))
    investor: Mapped[str | None] = mapped_column("Investor", String(50))
    investor_website: Mapped[str | None] = mapped_column("InvestorWebsite", String(50))
    vintage: Mapped[Numeric[Any] | None] = mapped_column("Vintage", Numeric(18, 2))
    fund_status: Mapped[str | None] = mapped_column("FundStatus", String(50))
    fund_size: Mapped[Numeric[Any] | None] = mapped_column("FundSize", Numeric(18, 2))
    native_fund_size: Mapped[Numeric[Any] | None] = mapped_column("NativeFundSize", Numeric(18, 2))
    native_fund_currency: Mapped[str | None] = mapped_column("NativeFundCurrency", String(50))
    fund_size_group: Mapped[str | None] = mapped_column("FundSizeGroup", String(50))
    fund_category: Mapped[str | None] = mapped_column("FundCategory", String(50))
    fund_type: Mapped[str | None] = mapped_column("FundType", String(50))
    fund_access_point: Mapped[str | None] = mapped_column("FundAccessPoint", String(50))
    sbic_fund: Mapped[str | None] = mapped_column("SBICFund", String(50))
    close_date: Mapped[DateTime | None] = mapped_column("CloseDate", DateTime)
    open_date: Mapped[DateTime | None] = mapped_column("OpenDate", DateTime)
    fund_target_size_low: Mapped[Numeric[Any] | None] = mapped_column(
        "FundTargetSizeLow", Numeric(18, 2)
    )
    fund_target_size: Mapped[str | None] = mapped_column("FundTargetSize", String(50))
    domiciles: Mapped[str | None] = mapped_column("Domiciles", String(50))
    fund_location: Mapped[str | None] = mapped_column("FundLocation", String(50))
    fund_city: Mapped[str | None] = mapped_column("FundCity", String(50))
    fund_state_province: Mapped[str | None] = mapped_column("FundState_Province", String(50))
    fund_country: Mapped[str | None] = mapped_column("FundCountry", String(50))
    time_taken_to_close_fund: Mapped[str | None] = mapped_column("TimeTakenToCloseFund", String(50))
    total_fund_investments: Mapped[Numeric[Any] | None] = mapped_column(
        "TotalFundInvestments", Numeric(18, 2)
    )
    total_active_fund_investments: Mapped[Numeric[Any] | None] = mapped_column(
        "TotalActiveFundInvestments", Numeric(18, 2)
    )
    preferred_industry: Mapped[str | None] = mapped_column("PreferredIndustry", Text)
    preferred_verticals: Mapped[str | None] = mapped_column("PreferredVerticals", String(50))
    preferred_geography: Mapped[str | None] = mapped_column("PreferredGeography", String(50))
    preferred_investment_types: Mapped[str | None] = mapped_column(
        "PreferredInvestmentTypes", String(50)
    )
    other_investment_preferences: Mapped[str | None] = mapped_column(
        "OtherInvestmentPreferences", String(255)
    )
    entity_name: Mapped[str | None] = mapped_column("entity_name", String(50))
    entity_type: Mapped[str | None] = mapped_column("entity_type", String(50))
    raised_amount_usd: Mapped[Numeric[Any] | None] = mapped_column("raised_amount_usd", Numeric(18, 2))
    raised_amount: Mapped[Numeric[Any] | None] = mapped_column("raised_amount", Numeric(18, 2))
    raised_amount_currency_code: Mapped[str | None] = mapped_column(
        "raised_amount_currency_code", String(50)
    )
    fund_id_alt: Mapped[str | None] = mapped_column("FundID", String(50))
    row_id: Mapped[str | None] = mapped_column("RowID", String(255))
    last_updated: Mapped[str | None] = mapped_column("LastUpdated", String(50))
    uuid: Mapped[str | None] = mapped_column("uuid", String(50))
    entity_uuid: Mapped[str | None] = mapped_column("entity_uuid", String(50))

    investors: Mapped[list["Investor"]] = relationship(
        secondary="FundInvestors", back_populates="funds"
    )
    lp_funds: Mapped[list["LPFund"]] = relationship(back_populates="fund")
    sp_funds: Mapped[list["SPFund"]] = relationship(back_populates="fund")


class Investor(Base):
    __tablename__ = "Investors"

    investor_id: Mapped[int] = mapped_column("Investor Id", Integer, primary_key=True)
    investor_name: Mapped[str | None] = mapped_column("Investor Name", String(50))
    investor_status: Mapped[str | None] = mapped_column("InvestorStatus", String(50))
    hq_phone: Mapped[str | None] = mapped_column("HQPhone", String(50))
    hq_email: Mapped[str | None] = mapped_column("HQEmail", String(50))
    founding_date: Mapped[DateTime | None] = mapped_column("Founding Date", DateTime)
    domain: Mapped[str | None] = mapped_column("domain", String(50))
    country_code: Mapped[str | None] = mapped_column("Country Code", String(50))
    investment_count: Mapped[Numeric[Any] | None] = mapped_column("Investment Count", Numeric(18, 2))
    last_investment_date: Mapped[DateTime | None] = mapped_column("LastInvestmentDate", DateTime)
    last_investment_type: Mapped[str | None] = mapped_column("LastInvestmentType", String(50))
    last_investment_class: Mapped[str | None] = mapped_column("LastInvestmentClass", String(50))
    total_investments_in_the_last_5_years: Mapped[Numeric[Any] | None] = mapped_column(
        "TotalInvestmentsInTheLast5Years", Numeric(18, 2)
    )
    last_financing_debt_date: Mapped[DateTime | None] = mapped_column(
        "LastFinancingDebtDate", DateTime
    )
    last_investment_status: Mapped[str | None] = mapped_column("LastInvestmentStatus", String(50))
    last_investment_company: Mapped[str | None] = mapped_column("LastInvestmentCompany", String(50))
    most_likely_fundraising: Mapped[str | None] = mapped_column("MostLikelyFundraisIng", String(50))
    primary_investor_type: Mapped[str | None] = mapped_column("PrimaryInvestorType", String(50))
    investor_native_currency: Mapped[str | None] = mapped_column(
        "InvestorNativeCurrency", String(50)
    )
    hq_location: Mapped[str | None] = mapped_column("HQLocation", String(50))
    hq_address_line1: Mapped[str | None] = mapped_column("HQAddressLine1", String(50))
    hq_global_sub_region: Mapped[str | None] = mapped_column("HQGlobalSubRegion", String(50))
    total_investments: Mapped[Numeric[Any] | None] = mapped_column("TotalInvestments", Numeric(18, 2))
    investor_types: Mapped[str | None] = mapped_column("Investor Types", String(50))
    last_updated: Mapped[str | None] = mapped_column("LastUpdated", String(50))
    type: Mapped[str | None] = mapped_column("type", String(50))
    permalink: Mapped[str | None] = mapped_column("permalink", String(50))
    roles: Mapped[str | None] = mapped_column("roles", String(50))
    region: Mapped[str | None] = mapped_column("region", String(50))
    city: Mapped[str | None] = mapped_column("city", String(50))
    linkedin_url: Mapped[str | None] = mapped_column("linkedin_url", String(255))
    logo_url: Mapped[str | None] = mapped_column("Logo Url", String(255))
    facebook_url: Mapped[str | None] = mapped_column("Facebook Url", String(255))
    twitter_url: Mapped[str | None] = mapped_column("Twitter Url", String(50))
    preferred_industry: Mapped[str | None] = mapped_column("PreferredIndustry", String(255))
    description: Mapped[str | None] = mapped_column("Description", Text)
    preferred_geography: Mapped[str | None] = mapped_column("PreferredGeography", String(50))
    total_investments_in_the_last_12_months: Mapped[Numeric[Any] | None] = mapped_column(
        "TotalInvestmentsInTheLast12Months", Numeric(18, 2)
    )
    preferred_investment_types: Mapped[str | None] = mapped_column(
        "PreferredInvestmentTypes", String(50)
    )
    preferred_verticals: Mapped[str | None] = mapped_column("PreferredVerticals", String(255))
    total_active_portfolio: Mapped[Numeric[Any] | None] = mapped_column(
        "TotalActivePortfolio", Numeric(18, 2)
    )
    other_investment_preferences: Mapped[str | None] = mapped_column(
        "OtherInvestmentPreferences", String(50)
    )
    total_exits: Mapped[Numeric[Any] | None] = mapped_column("TotalExits", Numeric(18, 2))
    hq_post_code: Mapped[Numeric[Any] | None] = mapped_column("HQPostCode", Numeric(18, 2))
    median_valuation: Mapped[Numeric[Any] | None] = mapped_column("MedianValuation", Numeric(18, 2))
    median_round_amount: Mapped[Numeric[Any] | None] = mapped_column("MedianRoundAmount", Numeric(18, 2))
    total_investments_in_the_last_2_years: Mapped[Numeric[Any] | None] = mapped_column(
        "TotalInvestmentsInTheLast2Years", Numeric(18, 2)
    )
    last_investment_size: Mapped[Numeric[Any] | None] = mapped_column(
        "LastInvestmentSize", Numeric(18, 2)
    )
    last_investment_size_status: Mapped[str | None] = mapped_column(
        "LastInvestmentSizeStatus", String(50)
    )
    last_investment_type2: Mapped[str | None] = mapped_column("LastInvestmentType2", String(50))
    total_funding: Mapped[Numeric[Any] | None] = mapped_column("Total Funding", Numeric(18, 2))
    total_funding_usd: Mapped[Numeric[Any] | None] = mapped_column("Total Funding Usd", Numeric(18, 2))
    total_funding_currency_code: Mapped[str | None] = mapped_column(
        "Total Funding Currency Code", String(50)
    )
    investor_also_known_as: Mapped[str | None] = mapped_column("InvestorAlsoKnownAs", String(50))
    investor_legal_name: Mapped[str | None] = mapped_column("InvestorLegalName", String(50))
    investor_former_name: Mapped[str | None] = mapped_column("InvestorFormerName", String(50))
    parent_company_id: Mapped[str | None] = mapped_column("ParentCompanyID", String(50))
    parent_company: Mapped[str | None] = mapped_column("ParentCompany", String(50))
    aum: Mapped[Numeric[Any] | None] = mapped_column("AUM", Numeric(18, 2))
    aum_native_amount: Mapped[Numeric[Any] | None] = mapped_column("AUMNativeAmount", Numeric(18, 2))
    dry_powder: Mapped[Numeric[Any] | None] = mapped_column("DryPowder", Numeric(18, 2))
    other_investor_types: Mapped[str | None] = mapped_column("OtherInvestorTypes", String(50))
    min_fund_size: Mapped[Numeric[Any] | None] = mapped_column("MinFundSize", Numeric(18, 2))
    max_fund_size: Mapped[Numeric[Any] | None] = mapped_column("MaxFundSize", Numeric(18, 2))
    median_fund_size: Mapped[Numeric[Any] | None] = mapped_column("MedianFundSize", Numeric(18, 2))
    preferred_investment_amount: Mapped[str | None] = mapped_column(
        "PreferredInvestmentAmount", String(50)
    )
    preferred_investment_amount_min: Mapped[Numeric[Any] | None] = mapped_column(
        "PreferredInvestmentAmountMin", Numeric(18, 2)
    )
    preferred_investment_amount_min_native_amount: Mapped[Numeric[Any] | None] = mapped_column(
        "PreferredInvestmentAmountMinNativeAmount", Numeric(18, 2)
    )
    preferred_investment_amount_max: Mapped[Numeric[Any] | None] = mapped_column(
        "PreferredInvestmentAmountMax", Numeric(18, 2)
    )
    preferred_investment_amount_max_native_amount: Mapped[Numeric[Any] | None] = mapped_column(
        "PreferredInvestmentAmountMaxNativeAmount", Numeric(18, 2)
    )
    hq_address_line2: Mapped[str | None] = mapped_column("HQAddressLine2", String(50))
    hq_fax: Mapped[str | None] = mapped_column("HQFax", String(50))
    investor_id_alt: Mapped[str | None] = mapped_column("InvestorID", String(50))
    uuid: Mapped[str | None] = mapped_column("uuid", String(50))

    investments: Mapped[list["Investment"]] = relationship(back_populates="investor")
    sp_investors: Mapped[list["SPInvestor"]] = relationship(back_populates="investor")
    funds: Mapped[list["Fund"]] = relationship(
        secondary="FundInvestors", back_populates="investors"
    )


class Talent(Base):
    __tablename__ = "talents"

    talent_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    location: Mapped[str | None] = mapped_column(String(100))
    current_title: Mapped[str | None] = mapped_column(String(255))
    years_experience: Mapped[str | None] = mapped_column(String(50))
    professional_bio: Mapped[str | None] = mapped_column(Text)
    skills: Mapped[str | None] = mapped_column(Text)
    industries_of_interest: Mapped[str | None] = mapped_column(Text)
    role_type: Mapped[str | None] = mapped_column(String(50))
    work_format: Mapped[str | None] = mapped_column(String(50))
    salary_range: Mapped[str | None] = mapped_column(String(100))
    availability: Mapped[str | None] = mapped_column(String(50))
    looking_for: Mapped[str | None] = mapped_column(Text)
    linkedin_url: Mapped[str | None] = mapped_column(String(255))
    portfolio_website: Mapped[str | None] = mapped_column(String(255))
    github_profile: Mapped[str | None] = mapped_column(String(255))
    other_profile: Mapped[str | None] = mapped_column(String(255))
    education: Mapped[str | None] = mapped_column(Text)
    achievements: Mapped[str | None] = mapped_column(Text)
    languages: Mapped[str | None] = mapped_column(String(255))
    profile_pic: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())


class Expert(Base):
    __tablename__ = "experts"

    expert_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    location: Mapped[str | None] = mapped_column(String(100))
    current_title: Mapped[str | None] = mapped_column(String(255))
    organization: Mapped[str | None] = mapped_column(String(255))
    expertise_domain: Mapped[str | None] = mapped_column(String(100))
    years_experience: Mapped[str | None] = mapped_column(String(50))
    professional_bio: Mapped[str | None] = mapped_column(Text)
    skills: Mapped[str | None] = mapped_column(Text)
    industries_of_interest: Mapped[str | None] = mapped_column(Text)
    services_offered: Mapped[str | None] = mapped_column(Text)
    target_audience: Mapped[str | None] = mapped_column(String(255))
    availability: Mapped[str | None] = mapped_column(String(50))
    linkedin_url: Mapped[str | None] = mapped_column(String(255))
    portfolio_website: Mapped[str | None] = mapped_column(String(255))
    other_profile: Mapped[str | None] = mapped_column(String(255))
    achievements: Mapped[str | None] = mapped_column(Text)
    languages: Mapped[str | None] = mapped_column(String(255))
    profile_pic: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())


class CofounderProject(Base):
    __tablename__ = "cofounder_projects"

    project_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    domain: Mapped[str | None] = mapped_column(String(100))
    skills_needed: Mapped[str | None] = mapped_column(Text)
    project_stage: Mapped[str | None] = mapped_column(String(50))
    author_name: Mapped[str | None] = mapped_column(String(100))
    author_email: Mapped[str | None] = mapped_column(String(255))
    author_affiliation: Mapped[str | None] = mapped_column(String(255))
    author_linkedin: Mapped[str | None] = mapped_column(String(255))
    roles_needed: Mapped[str | None] = mapped_column(Text)
    commitment_type: Mapped[str | None] = mapped_column(String(50))
    location_preference: Mapped[str | None] = mapped_column(String(50))
    equity_offered: Mapped[str | None] = mapped_column(String(100))
    contact_info: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())


class Article(Base):
    __tablename__ = "articles"

    article_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(50))
    source: Mapped[str | None] = mapped_column(String(255))
    source_url: Mapped[str | None] = mapped_column(String(500))
    author: Mapped[str | None] = mapped_column(String(100))
    image_url: Mapped[str | None] = mapped_column(String(500))
    tags: Mapped[str | None] = mapped_column(Text)
    is_featured: Mapped[bool | None] = mapped_column(Boolean, default=False)
    published_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())


class Resource(Base):
    __tablename__ = "resources"

    resource_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100))
    resource_type: Mapped[str | None] = mapped_column(String(50))
    url: Mapped[str | None] = mapped_column(String(500))
    organization: Mapped[str | None] = mapped_column(String(255))
    tags: Mapped[str | None] = mapped_column(Text)
    is_featured: Mapped[bool | None] = mapped_column(Boolean, default=False)
    published_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())


class ResourceApplication(Base):
    """A member's registration for an event or application to an opportunity.

    Both events and opportunities are rows in ``resources``, so a single table
    backs them, distinguished by ``kind``. Without this, the Events and
    Opportunities pages showed a success message and discarded the submission.
    """

    __tablename__ = "resource_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resource_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("resources.resource_id", ondelete="CASCADE"), nullable=False, index=True
    )
    member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pulse_members.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # "registration" for events, "application" for opportunities.
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())

    __table_args__ = (
        # One submission per member per resource; re-submitting updates it.
        UniqueConstraint("resource_id", "member_id", name="uq_resource_application_member"),
    )


class Post(Base):
    __tablename__ = "posts"

    post_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_name: Mapped[str | None] = mapped_column(String(100))
    author_role: Mapped[str | None] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    post_type: Mapped[str | None] = mapped_column(String(50), default="post")
    image_url: Mapped[str | None] = mapped_column(String(500))
    link_url: Mapped[str | None] = mapped_column(String(500))
    link_title: Mapped[str | None] = mapped_column(String(255))
    tags: Mapped[str | None] = mapped_column(Text)
    likes_count: Mapped[int | None] = mapped_column(Integer, default=0)
    comments_count: Mapped[int | None] = mapped_column(Integer, default=0)
    is_published: Mapped[bool | None] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())
    author_pic: Mapped[str | None] = mapped_column(String(500))
    author_founder_id: Mapped[str | None] = mapped_column(String(50))


class PulseMember(Base):
    __tablename__ = "pulse_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    confirmation_token: Mapped[str | None] = mapped_column(String(100), unique=True)
    is_confirmed: Mapped[bool | None] = mapped_column(Boolean, default=False)
    profile_pic: Mapped[str | None] = mapped_column(Text)
    linkedin: Mapped[str | None] = mapped_column(String(255))
    form_data: Mapped[str | None] = mapped_column(Text)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reset_token: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    reset_token_expires_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    referred_by_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("pulse_members.id", ondelete="SET NULL"), nullable=True
    )
    # Bumped to end every session this member has open; see ``User.token_version``.
    token_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())


class BadgeGeneration(Base):
    """Audit trail for every /badge/generate hit — used for analytics
    and to track viral spread."""

    __tablename__ = "badge_generations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    member_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("pulse_members.id", ondelete="SET NULL")
    )
    full_name: Mapped[str | None] = mapped_column(String(150))
    category: Mapped[str | None] = mapped_column(String(50))
    role_label: Mapped[str | None] = mapped_column(String(255))
    ref_url: Mapped[str | None] = mapped_column(String(255))
    ip: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now(), index=True)


class DirectMessage(Base):
    """One message between two accounts, addressed by email on both ends.

    There is no conversation row: a thread is every message whose ``from_email``
    and ``to_email`` are the pair, which is why both columns are indexed with the
    timestamp the inbox sorts on.
    """

    __tablename__ = "direct_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int | None] = mapped_column(Integer)
    to_name: Mapped[str | None] = mapped_column(String(100))
    to_email: Mapped[str | None] = mapped_column(String(255))
    from_name: Mapped[str | None] = mapped_column(String(100))
    from_email: Mapped[str | None] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool | None] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())

    __table_args__ = (
        Index("ix_direct_messages_to_created", "to_email", "created_at"),
        Index("ix_direct_messages_from_created", "from_email", "created_at"),
        Index("ix_direct_messages_to_unread", "to_email", "is_read"),
    )


class PostLike(Base):
    __tablename__ = "post_likes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.post_id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_type: Mapped[str] = mapped_column(String(10), nullable=False)
    actor_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("post_id", "actor_type", "actor_id", name="uq_post_like_actor"),
    )


class PostComment(Base):
    __tablename__ = "post_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.post_id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_type: Mapped[str] = mapped_column(String(10), nullable=False)
    actor_id: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())



# ---------------------------------------------------------------------------
# Identity bridge: PulseMember -> directory entity
# ---------------------------------------------------------------------------
class MemberEntityLink(Base):
    """Claim linking a community member to a directory entity they represent.

    ``PulseMember.role`` is free text captured at onboarding, so it cannot decide
    *which* startup or investor a member speaks for. Every startup-scoped
    authorization decision resolves through an approved row in this table
    instead, which is the only server-side source of truth for entity ownership.
    """

    __tablename__ = "member_entity_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pulse_members.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # "startup" | "investor" | "incubator"
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # "owner" | "admin" | "member"
    entity_role: Mapped[str] = mapped_column(String(20), nullable=False, default="owner")
    # "pending" | "approved" | "rejected" | "revoked"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    approved_by_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("User.UserId", ondelete="SET NULL")
    )
    approved_at: Mapped[DateTime | None] = mapped_column(DateTime)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("member_id", "entity_type", "entity_id", name="uq_member_entity_link"),
        Index("ix_member_entity_links_entity", "entity_type", "entity_id", "status"),
    )


# ---------------------------------------------------------------------------
# Deal Room
# ---------------------------------------------------------------------------
class DealRoom(Base):
    """A startup's private investor data room. Exactly one per startup."""

    __tablename__ = "deal_rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    startup_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Startups.Startup Id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    name: Mapped[str | None] = mapped_column(String(200))
    summary: Mapped[str | None] = mapped_column(Text)
    # "draft" | "active" | "paused" | "closed"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)

    # Gating and protection defaults applied to every participant.
    nda_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    nda_version: Mapped[str | None] = mapped_column(String(40))
    nda_body: Mapped[str | None] = mapped_column(Text)
    # When true the room forces watermarking regardless of per-grant settings.
    watermark_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Permission new participants receive when no explicit grant applies.
    default_permission: Mapped[str] = mapped_column(
        String(30), nullable=False, default="view_watermark"
    )
    allow_downloads: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_by_member_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("pulse_members.id", ondelete="SET NULL")
    )
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class DealRoomFolder(Base):
    """A category folder inside a deal room. Folders may nest one level or more."""

    __tablename__ = "deal_room_folders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deal_room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deal_rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("deal_room_folders.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    # One of DEAL_ROOM_CATEGORIES.
    category: Mapped[str] = mapped_column(String(40), nullable=False, default="other")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by_member_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("pulse_members.id", ondelete="SET NULL")
    )
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())

    __table_args__ = (Index("ix_deal_room_folders_room_parent", "deal_room_id", "parent_id"),)


class DealRoomDocument(Base):
    """A logical document. File bytes live on its versions, never here."""

    __tablename__ = "deal_room_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deal_room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deal_rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    folder_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("deal_room_folders.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(40), nullable=False, default="other")
    # "draft" | "published" | "archived"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    current_version_id: Mapped[int | None] = mapped_column(Integer)
    created_by_member_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("pulse_members.id", ondelete="SET NULL")
    )
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    # Soft delete: audit rows must keep pointing at a resolvable document.
    deleted_at: Mapped[DateTime | None] = mapped_column(DateTime, index=True)

    __table_args__ = (
        Index("ix_deal_room_documents_room_status", "deal_room_id", "status", "deleted_at"),
    )


class DealRoomDocumentVersion(Base):
    """An immutable uploaded revision of a document."""

    __tablename__ = "deal_room_document_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deal_room_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # Opaque key into private storage. Never a URL, never client-supplied.
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    page_count: Mapped[int | None] = mapped_column(Integer)
    uploaded_by_member_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("pulse_members.id", ondelete="SET NULL")
    )
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("document_id", "version_no", name="uq_deal_room_document_version"),
    )


class DealRoomParticipant(Base):
    """An investor's membership of one deal room, with its own permission scope."""

    __tablename__ = "deal_room_participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deal_room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deal_rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pulse_members.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Optional link to the directory Investor record this participant represents.
    investor_id: Mapped[int | None] = mapped_column(Integer)
    # "invited" | "requested" | "active" | "suspended" | "revoked" | "rejected"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="invited", index=True)
    # Room-wide default for this participant; folder/document grants override it.
    permission: Mapped[str] = mapped_column(String(30), nullable=False, default="view_watermark")
    expires_at: Mapped[DateTime | None] = mapped_column(DateTime, index=True)
    nda_accepted_at: Mapped[DateTime | None] = mapped_column(DateTime)
    nda_version: Mapped[str | None] = mapped_column(String(40))
    invited_by_member_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("pulse_members.id", ondelete="SET NULL")
    )
    # Only a hash of the invitation token is stored, as for a password.
    invite_token_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    invite_expires_at: Mapped[DateTime | None] = mapped_column(DateTime)
    last_activity_at: Mapped[DateTime | None] = mapped_column(DateTime)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("deal_room_id", "member_id", name="uq_deal_room_participant"),
        Index("ix_deal_room_participants_room_status", "deal_room_id", "status"),
    )


class DealRoomAccessGrant(Base):
    """A per-folder or per-document permission override for one participant."""

    __tablename__ = "deal_room_access_grants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    participant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("deal_room_participants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # "folder" | "document"
    resource_type: Mapped[str] = mapped_column(String(20), nullable=False)
    resource_id: Mapped[int] = mapped_column(Integer, nullable=False)
    permission: Mapped[str] = mapped_column(String(30), nullable=False, default="view_watermark")
    created_by_member_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("pulse_members.id", ondelete="SET NULL")
    )
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "participant_id", "resource_type", "resource_id", name="uq_deal_room_access_grant"
        ),
    )


class DealRoomAccessRequest(Base):
    """An investor's request to be admitted to a deal room."""

    __tablename__ = "deal_room_access_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deal_room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deal_rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pulse_members.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message: Mapped[str | None] = mapped_column(Text)
    # "pending" | "approved" | "rejected" | "info_requested"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    decision_note: Mapped[str | None] = mapped_column(Text)
    decided_by_member_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("pulse_members.id", ondelete="SET NULL")
    )
    decided_at: Mapped[DateTime | None] = mapped_column(DateTime)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())

    __table_args__ = (
        Index("ix_deal_room_access_requests_room_status", "deal_room_id", "status"),
    )


class DealRoomNdaAcceptance(Base):
    """Immutable record that a member accepted a room's NDA at a point in time."""

    __tablename__ = "deal_room_nda_acceptances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deal_room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deal_rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pulse_members.id", ondelete="CASCADE"), nullable=False, index=True
    )
    participant_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("deal_room_participants.id", ondelete="SET NULL")
    )
    nda_version: Mapped[str] = mapped_column(String(40), nullable=False)
    # Hash of the exact NDA text accepted, so a later edit cannot rewrite history.
    nda_body_sha256: Mapped[str | None] = mapped_column(String(64))
    signature_name: Mapped[str | None] = mapped_column(String(160))
    accepted_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())
    ip: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(255))

    __table_args__ = (
        Index("ix_deal_room_nda_room_member", "deal_room_id", "member_id"),
    )


class DealRoomQuestion(Base):
    """A question asked by an investor, optionally about a specific document."""

    __tablename__ = "deal_room_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deal_room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deal_rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("deal_room_documents.id", ondelete="SET NULL"), index=True
    )
    asked_by_member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pulse_members.id", ondelete="CASCADE"), nullable=False, index=True
    )
    participant_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("deal_room_participants.id", ondelete="SET NULL")
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    # "open" | "answered" | "closed"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", index=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    __table_args__ = (Index("ix_deal_room_questions_room_status", "deal_room_id", "status"),)


class DealRoomAnswer(Base):
    """A startup or admin reply to a deal room question."""

    __tablename__ = "deal_room_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deal_room_questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    answered_by_member_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("pulse_members.id", ondelete="SET NULL")
    )
    answered_by_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("User.UserId", ondelete="SET NULL")
    )
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())


class DealRoomAuditEvent(Base):
    """Append-only audit trail. Never updated or deleted by application code."""

    __tablename__ = "deal_room_audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deal_room_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("deal_rooms.id", ondelete="CASCADE"), index=True
    )
    startup_id: Mapped[int | None] = mapped_column(Integer, index=True)
    actor_member_id: Mapped[int | None] = mapped_column(Integer, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(Integer)
    actor_email: Mapped[str | None] = mapped_column(String(255))
    # "startup" | "investor" | "admin" | "anonymous"
    actor_role: Mapped[str | None] = mapped_column(String(20))
    action: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(30))
    resource_id: Mapped[int | None] = mapped_column(Integer)
    # JSON-encoded detail. Must never contain document contents or credentials.
    meta: Mapped[str | None] = mapped_column(Text)
    ip: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now(), index=True)

    __table_args__ = (
        Index("ix_deal_room_audit_room_created", "deal_room_id", "created_at"),
        Index("ix_deal_room_audit_room_action", "deal_room_id", "action"),
    )


class DealRoomDocumentView(Base):
    """Per-view engagement record backing investor analytics."""

    __tablename__ = "deal_room_document_views"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deal_room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deal_rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deal_room_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_version_id: Mapped[int | None] = mapped_column(Integer)
    participant_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("deal_room_participants.id", ondelete="CASCADE"), index=True
    )
    member_id: Mapped[int | None] = mapped_column(Integer, index=True)
    # "preview" | "view" | "download"
    event: Mapped[str] = mapped_column(String(20), nullable=False, default="view")
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    pages_viewed: Mapped[int | None] = mapped_column(Integer)
    ip: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now(), index=True)

    __table_args__ = (
        Index("ix_deal_room_views_room_doc", "deal_room_id", "document_id"),
        Index("ix_deal_room_views_participant", "participant_id", "created_at"),
    )


# ---------------------------------------------------------------------------
# Deal Room marketplace: opportunity posts
# ---------------------------------------------------------------------------
class DealRoomPost(Base):
    """One opportunity posted to the Deal Room marketplace.

    The private data rooms above answer "here are my documents, who may see
    them?". This answers the question that comes *before* it: "who am I looking
    for, and why?". A post is public to signed-in members once published, which
    is why authorship is pinned to a member id and why entity attribution is
    checked against ``member_entity_links`` rather than taken from the body.

    Filterable facets are stored as indexed scalar columns because the board
    filters on them in SQL; ``tags`` is display-only free text and deliberately
    is not a filter.
    """

    __tablename__ = "deal_room_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pulse_members.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # What kind of ask this is. See backend.core.post_taxonomy.POST_TYPES.
    post_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    summary: Mapped[str] = mapped_column(String(400), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)

    # Who the author wants to hear from.
    looking_for: Mapped[str | None] = mapped_column(Text)
    counterparty_type: Mapped[str] = mapped_column(String(40), nullable=False, default="any")

    # Facets the board filters on.
    sector: Mapped[str | None] = mapped_column(String(120), index=True)
    stage: Mapped[str | None] = mapped_column(String(60), index=True)
    location: Mapped[str | None] = mapped_column(String(120), index=True)

    # The commercial shape of the ask. Nullable throughout: a co-founder search
    # has no ticket size and a capital raise has no commitment level.
    amount_min: Mapped[float | None] = mapped_column(Numeric(18, 2))
    amount_max: Mapped[float | None] = mapped_column(Numeric(18, 2))
    currency: Mapped[str | None] = mapped_column(String(8), default="MAD")
    equity_offered: Mapped[str | None] = mapped_column(String(60))
    commitment: Mapped[str | None] = mapped_column(String(40))
    deadline: Mapped[DateTime | None] = mapped_column(DateTime)

    # Free-text labels, comma separated. Display only.
    tags: Mapped[str | None] = mapped_column(String(400))

    # Attribution: the directory entity the author speaks for on this post.
    # Written only after an approved claim is verified server-side.
    entity_type: Mapped[str | None] = mapped_column(String(20))
    entity_id: Mapped[int | None] = mapped_column(Integer)
    entity_name: Mapped[str | None] = mapped_column(String(200))

    # Optional bridge into the private side: "documents are in my data room".
    deal_room_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("deal_rooms.id", ondelete="SET NULL"), index=True
    )

    # "draft" | "published" | "closed" | "archived"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    # "visible" | "flagged" | "removed"
    moderation_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="visible", index=True
    )
    moderation_note: Mapped[str | None] = mapped_column(Text)

    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    response_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    published_at: Mapped[DateTime | None] = mapped_column(DateTime)
    closed_at: Mapped[DateTime | None] = mapped_column(DateTime)

    __table_args__ = (
        # The board's default read: visible published posts, newest first.
        Index("ix_deal_room_posts_board", "status", "moderation_status", "published_at"),
        Index("ix_deal_room_posts_author_status", "author_member_id", "status"),
        Index("ix_deal_room_posts_type_status", "post_type", "status"),
    )


class DealRoomPostResponse(Base):
    """One member's expression of interest in a post.

    Responding also opens a direct message thread with the author, so this row
    is the audit record of that contact rather than the message itself: the
    conversation lives in ``direct_messages`` like every other thread, and the
    unique constraint is what stops a post being answered ten times by the same
    account.
    """

    __tablename__ = "deal_room_post_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deal_room_posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    responder_member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pulse_members.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # "pending" | "accepted" | "declined"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())
    decided_at: Mapped[DateTime | None] = mapped_column(DateTime)

    __table_args__ = (
        UniqueConstraint("post_id", "responder_member_id", name="uq_post_response_once"),
        Index("ix_post_responses_post_created", "post_id", "created_at"),
    )


class DealRoomPostReport(Base):
    """A member's report that a post breaches the rules."""

    __tablename__ = "deal_room_post_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("deal_room_posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reporter_member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pulse_members.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # "spam" | "misleading" | "offensive" | "scam" | "off_topic" | "other"
    reason: Mapped[str] = mapped_column(String(40), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text)
    # "open" | "actioned" | "dismissed"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", index=True)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime, default=func.now())
    reviewed_at: Mapped[DateTime | None] = mapped_column(DateTime)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("User.UserId", ondelete="SET NULL")
    )

    __table_args__ = (
        UniqueConstraint("post_id", "reporter_member_id", name="uq_post_report_once"),
    )


__all__ = [
    "Article",
    "BadgeGeneration",
    "Base",
    "CofounderProject",
    "DealRoom",
    "DealRoomAccessGrant",
    "DealRoomAccessRequest",
    "DealRoomAnswer",
    "DealRoomAuditEvent",
    "DealRoomDocument",
    "DealRoomDocumentVersion",
    "DealRoomDocumentView",
    "DealRoomFolder",
    "DealRoomNdaAcceptance",
    "DealRoomParticipant",
    "DealRoomPost",
    "DealRoomPostReport",
    "DealRoomPostResponse",
    "DealRoomQuestion",
    "DirectMessage",
    "Education",
    "Experience",
    "Expert",
    "Founder",
    "Fund",
    "FundInvestor",
    "FundingRound",
    "Incubator",
    "IncubatorFounder",
    "Institute",
    "Investment",
    "Investor",
    "LPFund",
    "LimitedPartner",
    "MemberEntityLink",
    "Post",
    "PostComment",
    "PostLike",
    "PulseMember",
    "Resource",
    "ResourceApplication",
    "SPFund",
    "SPInvestor",
    "ServiceProvider",
    "Startup",
    "StartupFounder",
    "StartupIncubator",
    "Talent",
    "User",
]
