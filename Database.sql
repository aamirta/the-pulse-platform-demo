USE THEPULSEDB6;
CREATE TABLE Institutes (
    [Institute Id] VARCHAR(50) PRIMARY KEY,
    [Institute Name] VARCHAR(255) NULL
);

CREATE TABLE Incubators (
    [Incubator Id] INT PRIMARY KEY,
    Incubator VARCHAR(50) NULL,
    type_organisme VARCHAR(50) NULL,
    statut VARCHAR(50) NULL,
    telephone VARCHAR(50) NULL,
    phases_investissement VARCHAR(50) NULL,
    ville_organisme VARCHAR(50) NULL,
    date_creation VARCHAR(50) NULL,
    description TEXT NULL,
    email VARCHAR(50) NULL,
    secteurs TEXT NULL,
    image_url VARCHAR(255) NULL,
    ville VARCHAR(50) NULL,
    linkedin VARCHAR(255) NULL,
    partners_or_sponsors VARCHAR(255) NULL
);

-- Create Startups table first without foreign key references
CREATE TABLE Startups (
    [Startup Id] INT PRIMARY KEY,
    [Startup name] VARCHAR(255) NULL,
    stage VARCHAR(50) NULL,
    lastModifiedDate VARCHAR(50) NULL,
    numeroICE VARCHAR(50) NULL,
    numeroRC VARCHAR(50) NULL,
    tribunal_x VARCHAR(50) NULL,
    activite TEXT NULL,
    formeJuridique VARCHAR(50) NULL,
    typeFille VARCHAR(50) NULL,
    dateImmatriculation DATETIME NULL,
    capital DECIMAL(18,2) NULL,
    ompic DECIMAL(18,2) NULL,
    location VARCHAR(50) NULL,
    region VARCHAR(50) NULL,
    contactEmail VARCHAR(50) NULL,
    phone VARCHAR(50) NULL,
    EntrepriseContactSiteWeb VARCHAR(255) NULL,
    EntrepriseContactName VARCHAR(50) NULL,
    linkedin VARCHAR(255) NULL,
    youtubeLink VARCHAR(255) NULL,
    instagramLink VARCHAR(255) NULL,
    logo_url VARCHAR(255) NULL,
    presentationVideo VARCHAR(255) NULL,
    sector VARCHAR(255) NULL,
    markets VARCHAR(50) NULL,
    employees VARCHAR(50) NULL,
    revenue VARCHAR(50) NULL,
    raisedFunds DECIMAL(18,2) NULL,
    valuation VARCHAR(50) NULL,
    incubatedBy VARCHAR(50) NULL,
    isIncubatorValid BIT NULL,
    financedBy VARCHAR(50) NULL,
    isFinancerValid BIT NULL,
    isJEIValidated BIT NULL,
    description TEXT NULL,
    uuid VARCHAR(50) NULL,
    type VARCHAR(50) NULL,
    homepage_url VARCHAR(255) NULL,
    country_code VARCHAR(50) NULL,
    address VARCHAR(255) NULL,
    postal_code DECIMAL(18,2) NULL,
    num_funding_rounds VARCHAR(50) NULL,
    total_funding_usd DECIMAL(18,2) NULL,
    total_funding DECIMAL(18,2) NULL,
    total_funding_currency_code VARCHAR(50) NULL,
    last_funding_on VARCHAR(50) NULL,
    facebook_url VARCHAR(255) NULL,
    twitter_url VARCHAR(255) NULL,
    alias1 VARCHAR(255) NULL,
    CompanyID VARCHAR(50) NULL,
    CompanyAlsoKnownAs VARCHAR(50) NULL,
    CompanyFormerName VARCHAR(50) NULL,
    CompanyLegalName VARCHAR(50) NULL,
    CompanyFinancingStatus VARCHAR(50) NULL,
    CompanyFinancingStatusDate VARCHAR(50) NULL,
    TotalRaised DECIMAL(18,2) NULL,
    TotalRaisedNativeAmount DECIMAL(18,2) NULL,
    TotalRaisedNativeCurrency VARCHAR(50) NULL,
    BusinessStatus VARCHAR(50) NULL,
    BusinessStatusDate VARCHAR(50) NULL,
    OwnershipStatus VARCHAR(50) NULL,
    OwnershipStatusDate VARCHAR(50) NULL,
    Universe VARCHAR(50) NULL,
    EmployeeAsOfDate VARCHAR(50) NULL,
    YearFounded VARCHAR(50) NULL,
    ParentCompany VARCHAR(50) NULL,
    ParentCompanyID VARCHAR(50) NULL,
    FinancingStatusNote TEXT NULL,
    FinancingStatusNoteAsOfDate VARCHAR(50) NULL,
    PrimaryIndustrySector VARCHAR(50) NULL,
    PrimaryIndustryGroup VARCHAR(50) NULL,
    PrimaryIndustryCode VARCHAR(50) NULL,
    AllIndustries VARCHAR(255) NULL,
    Verticals VARCHAR(255) NULL,
    HQPostCode DECIMAL(18,2) NULL,
    HQCountry VARCHAR(50) NULL,
    HQFax VARCHAR(50) NULL,
    HQGlobalRegion VARCHAR(50) NULL,
    HQGlobalSubRegion VARCHAR(50) NULL,
    AlternateOfficeCount DECIMAL(18,2) NULL,
    ActiveInvestors DECIMAL(18,2) NULL,
    FormerInvestors DECIMAL(18,2) NULL,
    Revenue1 DECIMAL(18,2) NULL,
    GrossProfit DECIMAL(18,2) NULL,
    NetIncome DECIMAL(18,2) NULL,
    EnterpriseValue DECIMAL(18,2) NULL,
    EBITDA DECIMAL(18,2) NULL,
    EBIT DECIMAL(18,2) NULL,
    NetDebt DECIMAL(18,2) NULL,
    FiscalPeriod VARCHAR(50) NULL,
    PeriodEndDate VARCHAR(50) NULL,
    FirstFinancingDealID VARCHAR(50) NULL,
    FirstFinancingDate VARCHAR(50) NULL,
    FirstFinancingSize DECIMAL(18,2) NULL,
    FirstFinancingSizeStatus VARCHAR(50) NULL,
    FirstFinancingValuation DECIMAL(18,2) NULL,
    FirstFinancingValuationStatus VARCHAR(50) NULL,
    FirstFinancingDealType VARCHAR(50) NULL,
    FirstFinancingDealType2 VARCHAR(50) NULL,
    FirstFinancingDealClass VARCHAR(50) NULL,
    FirstFinancingDebtDate VARCHAR(50) NULL,
    FirstFinancingStatus VARCHAR(50) NULL,
    LastKnownValuation DECIMAL(18,2) NULL,
    LastKnownValuationDate VARCHAR(50) NULL,
    LastKnownValuationDealType VARCHAR(50) NULL,
    LastFinancingDealID VARCHAR(50) NULL,
    LastFinancingDate VARCHAR(50) NULL,
    LastFinancingSize DECIMAL(18,2) NULL,
    LastFinancingSizeStatus VARCHAR(50) NULL,
    LastFinancingDealType VARCHAR(50) NULL,
    LastFinancingDealType2 VARCHAR(50) NULL,
    LastFinancingDealClass VARCHAR(50) NULL,
    LastFinancingDebtDate VARCHAR(50) NULL,
    LastFinancingStatus VARCHAR(50) NULL,
    [Business Models] VARCHAR(50) NULL,
    [Team Background] VARCHAR(50) NULL,
    Waves DECIMAL(18,2) NULL,
    [Trending Themes] DECIMAL(18,2) NULL,
    [Special Flags: TRUE] VARCHAR(255) NULL,
    [Company Stage] VARCHAR(50) NULL,
    [Is Funded] BIT NULL,
    [Total Funding (USD)] DECIMAL(18,2) NULL,
    [Latest Funded Amount (USD)] DECIMAL(18,2) NULL,
    [Latest Funded Date] VARCHAR(50) NULL,
    [Latest Valuation (USD)] VARCHAR(50) NULL,
    [Institutional Investors] TEXT NULL,
    [Angel Investors] VARCHAR(50) NULL,
    [Annual Revenue (USD)] DECIMAL(18,2) NULL,
    [Annual Net Profit (USD)] DECIMAL(18,2) NULL,
    [Annual EBITDA (USD)] DECIMAL(18,2) NULL,
    [Key People Info] TEXT NULL,
    [Links to Key People Profiles] VARCHAR(255) NULL,
    [Acquisition List] VARCHAR(50) NULL,
    [Is Acquired] BIT NULL,
    [Acquired By] VARCHAR(50) NULL,
    [Acquired Date] DATETIME NULL,
    [Acquired Amount (USD)] DECIMAL(18,2) NULL,
    [Acquisition Type] VARCHAR(50) NULL,
    [Soonicorn Club Status] VARCHAR(50) NULL,
    [Soonicorn Club Event Date] VARCHAR(50) NULL,
    [Company Emails] VARCHAR(50) NULL,
    [Blog Url] VARCHAR(50) NULL,
    [Is Deadpooled] BIT NULL,
    [Deadpooled Date] DECIMAL(18,2) NULL,
    [Status Startup] VARCHAR(50) NULL
);

-- Create Founders table without foreign key references
CREATE TABLE Founders (
    [Founder Id] VARCHAR(50) PRIMARY KEY,
    name VARCHAR(50) NULL,
    first_name VARCHAR(50) NULL,
    last_name VARCHAR(50) NULL,
    current_title VARCHAR(255) NULL,
    current_employer VARCHAR(50) NULL,
    location VARCHAR(50) NULL,
    linkedin_url VARCHAR(255) NULL,
    profile_pic VARCHAR(255) NULL,
    link_twitter VARCHAR(50) NULL,
    link_facebook VARCHAR(50) NULL,
    link_instagram VARCHAR(50) NULL,
    link_quora VARCHAR(50) NULL,
    link_github VARCHAR(50) NULL,
    link_aboutme VARCHAR(50) NULL,
    link_angellist VARCHAR(50) NULL,
    link_stackoverflow VARCHAR(50) NULL,
    company_details_name VARCHAR(50) NULL,
    company_details_logo_url VARCHAR(255) NULL,
    most_recent_ended_exp_title VARCHAR(255) NULL,
    most_recent_ended_exp_company_info_url VARCHAR(255) NULL,
    most_recent_ended_exp_employer VARCHAR(255) NULL,
    most_recent_ended_exp_end_date VARCHAR(50) NULL,
    prev_company_name VARCHAR(255) NULL,
    last_job_change VARCHAR(50) NULL,
    prev_company_logo_url VARCHAR(255) NULL,
    prev_company_info_url VARCHAR(255) NULL,
    skills TEXT NULL,
    teaser_emails VARCHAR(255) NULL,
    teaser_personal_emails VARCHAR(50) NULL,
    teaser_professional_emails VARCHAR(255) NULL,
    teaser_phones VARCHAR(255) NULL,
    url VARCHAR(50) NULL
);

CREATE TABLE Education (
    [Education Id] VARCHAR(50) PRIMARY KEY,
    start_date INT NULL,
    end_date INT NULL,
    degree VARCHAR(255) NULL,
    [Founder Id] VARCHAR(50) NULL,
    [Institute Id] VARCHAR(50) NULL,
    FOREIGN KEY ([Founder Id]) REFERENCES Founders([Founder Id]),
    FOREIGN KEY ([Institute Id]) REFERENCES Institutes([Institute Id])
);

CREATE TABLE Experiences (
    [Experience Id] VARCHAR(50) PRIMARY KEY,
    [Founder Id] VARCHAR(50) NULL,
    Role VARCHAR(255) NULL,
    Company VARCHAR(255) NULL,
    FOREIGN KEY ([Founder Id]) REFERENCES Founders([Founder Id])
);

CREATE TABLE Funds (
    [Fund Id] INT PRIMARY KEY,
    FundName VARCHAR(50) NULL,
    FundNo DECIMAL(18,2) NULL,
    FirstFund VARCHAR(50) NULL,
    Investor VARCHAR(50) NULL,
    InvestorWebsite VARCHAR(50) NULL,
    Vintage DECIMAL(18,2) NULL,
    FundStatus VARCHAR(50) NULL,
    FundSize DECIMAL(18,2) NULL,
    NativeFundSize DECIMAL(18,2) NULL,
    NativeFundCurrency VARCHAR(50) NULL,
    FundSizeGroup VARCHAR(50) NULL,
    FundCategory VARCHAR(50) NULL,
    FundType VARCHAR(50) NULL,
    FundAccessPoint VARCHAR(50) NULL,
    SBICFund VARCHAR(50) NULL,
    CloseDate DATETIME NULL,
    OpenDate DATETIME NULL,
    FundTargetSizeLow DECIMAL(18,2) NULL,
    FundTargetSize VARCHAR(50) NULL,
    Domiciles VARCHAR(50) NULL,
    FundLocation VARCHAR(50) NULL,
    FundCity VARCHAR(50) NULL,
    FundState_Province VARCHAR(50) NULL,
    FundCountry VARCHAR(50) NULL,
    TimeTakenToCloseFund VARCHAR(50) NULL,
    TotalFundInvestments DECIMAL(18,2) NULL,
    TotalActiveFundInvestments DECIMAL(18,2) NULL,
    PreferredIndustry TEXT NULL,
    PreferredVerticals VARCHAR(50) NULL,
    PreferredGeography VARCHAR(50) NULL,
    PreferredInvestmentTypes VARCHAR(50) NULL,
    OtherInvestmentPreferences VARCHAR(255) NULL,
    entity_name VARCHAR(50) NULL,
    entity_type VARCHAR(50) NULL,
    raised_amount_usd DECIMAL(18,2) NULL,
    raised_amount DECIMAL(18,2) NULL,
    raised_amount_currency_code VARCHAR(50) NULL,
    FundID VARCHAR(50) NULL,
    RowID VARCHAR(255) NULL,
    LastUpdated VARCHAR(50) NULL,
    uuid VARCHAR(50) NULL,
    entity_uuid VARCHAR(50) NULL
);

CREATE TABLE Investors (
    [Investor Id] INT PRIMARY KEY,
    [Investor Name] VARCHAR(50) NULL,
    InvestorStatus VARCHAR(50) NULL,
    HQPhone VARCHAR(50) NULL,
    HQEmail VARCHAR(50) NULL,
    [Founding Date] DATETIME NULL,
    domain VARCHAR(50) NULL,
    [Country Code] VARCHAR(50) NULL,
    [Investment Count] DECIMAL(18,2) NULL,
    LastInvestmentDate DATETIME NULL,
    LastInvestmentType VARCHAR(50) NULL,
    LastInvestmentClass VARCHAR(50) NULL,
    TotalInvestmentsInTheLast5Years DECIMAL(18,2) NULL,
    LastFinancingDebtDate DATETIME NULL,
    LastInvestmentStatus VARCHAR(50) NULL,
    LastInvestmentCompany VARCHAR(50) NULL,
    MostLikelyFundraisIng VARCHAR(50) NULL,
    PrimaryInvestorType VARCHAR(50) NULL,
    InvestorNativeCurrency VARCHAR(50) NULL,
    HQLocation VARCHAR(50) NULL,
    HQAddressLine1 VARCHAR(50) NULL,
    HQGlobalSubRegion VARCHAR(50) NULL,
    TotalInvestments DECIMAL(18,2) NULL,
    [Investor Types] VARCHAR(50) NULL,
    LastUpdated VARCHAR(50) NULL,
    type VARCHAR(50) NULL,
    permalink VARCHAR(50) NULL,
    roles VARCHAR(50) NULL,
    region VARCHAR(50) NULL,
    city VARCHAR(50) NULL,
    linkedin_url VARCHAR(255) NULL,
    [Logo Url] VARCHAR(255) NULL,
    [Facebook Url] VARCHAR(255) NULL,
    [Twitter Url] VARCHAR(50) NULL,
    PreferredIndustry VARCHAR(255) NULL,
    Description TEXT NULL,
    PreferredGeography VARCHAR(50) NULL,
    TotalInvestmentsInTheLast12Months DECIMAL(18,2) NULL,
    PreferredInvestmentTypes VARCHAR(50) NULL,
    PreferredVerticals VARCHAR(255) NULL,
    TotalActivePortfolio DECIMAL(18,2) NULL,
    OtherInvestmentPreferences VARCHAR(50) NULL,
    TotalExits DECIMAL(18,2) NULL,
    HQPostCode DECIMAL(18,2) NULL,
    MedianValuation DECIMAL(18,2) NULL,
    MedianRoundAmount DECIMAL(18,2) NULL,
    TotalInvestmentsInTheLast2Years DECIMAL(18,2) NULL,
    LastInvestmentSize DECIMAL(18,2) NULL,
    LastInvestmentSizeStatus VARCHAR(50) NULL,
    LastInvestmentType2 VARCHAR(50) NULL,
    [Total Funding] DECIMAL(18,2) NULL,
    [Total Funding Usd] DECIMAL(18,2) NULL,
    [Total Funding Currency Code] VARCHAR(50) NULL,
    InvestorAlsoKnownAs VARCHAR(50) NULL,
    InvestorLegalName VARCHAR(50) NULL,
    InvestorFormerName VARCHAR(50) NULL,
    ParentCompanyID VARCHAR(50) NULL,
    ParentCompany VARCHAR(50) NULL,
    AUM DECIMAL(18,2) NULL,
    AUMNativeAmount DECIMAL(18,2) NULL,
    DryPowder DECIMAL(18,2) NULL,
    OtherInvestorTypes VARCHAR(50) NULL,
    MinFundSize DECIMAL(18,2) NULL,
    MaxFundSize DECIMAL(18,2) NULL,
    MedianFundSize DECIMAL(18,2) NULL,
    PreferredInvestmentAmount VARCHAR(50) NULL,
    PreferredInvestmentAmountMin DECIMAL(18,2) NULL,
    PreferredInvestmentAmountMinNativeAmount DECIMAL(18,2) NULL,
    PreferredInvestmentAmountMax DECIMAL(18,2) NULL,
    PreferredInvestmentAmountMaxNativeAmount DECIMAL(18,2) NULL,
    HQAddressLine2 VARCHAR(50) NULL,
    HQFax VARCHAR(50) NULL,
    InvestorID VARCHAR(50) NULL,
    uuid VARCHAR(50) NULL
);

CREATE TABLE FundingRounds (
    Funding_Round_Id INT PRIMARY KEY,
    Uuid VARCHAR(50) NULL,
    Dealid VARCHAR(50) NULL,
    Dealno DECIMAL(18,2) NULL,
    [Round Name] VARCHAR(50) NULL,
    [Startup Name] VARCHAR(50) NULL,
    [Domain name] VARCHAR(50) NULL,
    [Founded year] VARCHAR(50) NULL,
    Country VARCHAR(50) NULL,
    Region VARCHAR(50) NULL,
    City VARCHAR(50) NULL,
    Date VARCHAR(50) NULL,
    Dealsynopsis TEXT NULL,
    Dealtype VARCHAR(50) NULL,
    Dealtype2 VARCHAR(50) NULL,
    Dealclass VARCHAR(50) NULL,
    Dealstatus VARCHAR(50) NULL,
    Dealsizestatus VARCHAR(50) NULL,
    [Raised Amount] DECIMAL(18,2) NULL,
    [Raised Amount Usd] DECIMAL(18,2) NULL,
    Nativecurrencyofdeal VARCHAR(50) NULL,
    Addon VARCHAR(50) NULL,
    Raisedtodate DECIMAL(18,2) NULL,
    [Total funding (usd)] DECIMAL(18,2) NULL,
    Overview VARCHAR(255) NULL,
    Businessstatus VARCHAR(50) NULL,
    Financingstatus VARCHAR(50) NULL,
    Typeofstock VARCHAR(50) NULL,
    Vcround VARCHAR(50) NULL,
    [Business models] VARCHAR(50) NULL,
    [Institutional investors] VARCHAR(255) NULL,
    [Angel investors] VARCHAR(50) NULL,
    [Lead investor] VARCHAR(255) NULL,
    Lead_investor_uuids VARCHAR(255) NULL,
    Facilitators VARCHAR(50) NULL,
    [Investor Count] DECIMAL(18,2) NULL,
    Ceo VARCHAR(50) NULL,
    Ceopbid VARCHAR(50) NULL,
    Ceophone VARCHAR(50) NULL,
    Ceoemail VARCHAR(50) NULL,
    Ceobiography TEXT NULL,
    Ceoeducation VARCHAR(255) NULL,
    [Startup Id] INT NULL,
    Companyid VARCHAR(50) NULL,
    Org_uuid VARCHAR(50) NULL
);

CREATE TABLE Investements (
    [Investement Id] INT IDENTITY(1,1) PRIMARY KEY,
    uuid VARCHAR(50) NULL,
    name VARCHAR(255) NULL,
    type VARCHAR(50) NULL,
    permalink VARCHAR(255) NULL,
    cb_url VARCHAR(255) NULL,
    rank DECIMAL(18,2) NULL,
    created_at VARCHAR(50) NULL,
    updated_at VARCHAR(50) NULL,
    funding_round_uuid VARCHAR(50) NULL,
    funding_round_name VARCHAR(50) NULL,
    investor_uuid VARCHAR(50) NULL,
    investor_name VARCHAR(50) NULL,
    investor_type VARCHAR(50) NULL,
    is_lead_investor VARCHAR(50) NULL,
    partner_uuid VARCHAR(50) NULL,
    partner_name VARCHAR(50) NULL,
    [Funding_Round_Id] INT NULL,
    [Investor Id] INT NULL
);

CREATE TABLE LimitedPartner (
    [LimitedPartner Id] INT PRIMARY KEY,
    LimitedPartnerID VARCHAR(50) NULL,
    LimitedPartnerName VARCHAR(50) NULL,
    LimitedPartnerFormerName VARCHAR(255) NULL,
    LimitedPartnerAlsoKnownAs VARCHAR(50) NULL,
    Description TEXT NULL,
    LimitedPartnerType VARCHAR(50) NULL,
    AUM DECIMAL(18,2) NULL,
    YearFounded VARCHAR(50) NULL,
    Website VARCHAR(50) NULL,
    HQLocation VARCHAR(50) NULL,
    HQAddressLine1 VARCHAR(50) NULL,
    HQAddressLine2 VARCHAR(50) NULL,
    HQCity VARCHAR(50) NULL,
    HQPostCode DECIMAL(18,2) NULL,
    HQCountry VARCHAR(50) NULL,
    HQPhone VARCHAR(50) NULL,
    HQFax VARCHAR(50) NULL,
    HQEmail VARCHAR(50) NULL,
    HQGlobalRegion VARCHAR(50) NULL,
    HQGlobalSubRegion VARCHAR(50) NULL,
    SoldSecondaryCommitments VARCHAR(50) NULL,
    BoughtSecondaryCommitments VARCHAR(50) NULL,
    TotalCommitments BIGINT NULL,
    TotalActiveCommitments BIGINT NULL,
    TotalCommitmentsInPEFunds DECIMAL(18,2) NULL,
    TotalCommitmentsInVCFunds BIGINT NULL,
    OpenToFirstTimeFunds VARCHAR(50) NULL,
    RealEstate DECIMAL(18,2) NULL,
    RealEstatePercent DECIMAL(18,2) NULL,
    Equities DECIMAL(18,2) NULL,
    EquitiesPercent DECIMAL(18,2) NULL,
    FixedIncomePercent DECIMAL(18,2) NULL,
    Cash DECIMAL(18,2) NULL,
    CashPercent DECIMAL(18,2) NULL,
    PolicyDescription TEXT NULL,
    PreferredGeography VARCHAR(255) NULL,
    PreferredFundType VARCHAR(255) NULL
);

CREATE TABLE ServiceProvider (
    [ServiceProvider Id] INT PRIMARY KEY,
    ServiceProviderID VARCHAR(50) NULL,
    ServiceProviderName VARCHAR(50) NULL,
    ServiceProviderAlsoKnownAs VARCHAR(50) NULL,
    Employees DECIMAL(18,2) NULL,
    Description VARCHAR(255) NULL,
    Website VARCHAR(50) NULL,
    PrimaryServiceProviderType VARCHAR(50) NULL,
    OtherServiceProviderTypes VARCHAR(50) NULL,
    ServicedCompanies INT NULL,
    ServicedDeals INT NULL,
    ServicedInvestors INT NULL,
    ServicedFunds DECIMAL(18,2) NULL,
    HQLocation VARCHAR(50) NULL,
    HQAddressLine1 VARCHAR(50) NULL,
    HQAddressLine2 VARCHAR(50) NULL,
    HQCity VARCHAR(50) NULL,
    HQPostCode DECIMAL(18,2) NULL,
    HQCountry VARCHAR(50) NULL,
    HQPhone VARCHAR(50) NULL,
    HQFax VARCHAR(50) NULL,
    HQEmail VARCHAR(50) NULL,
    HQGlobalRegion VARCHAR(50) NULL,
    HQGlobalSubRegion VARCHAR(50) NULL,
    RowID VARCHAR(255) NULL,
    LastUpdated VARCHAR(50) NULL
);

CREATE TABLE LPFunds (
    FundName VARCHAR(50) NULL,
    CommitmentDate DATETIME NULL,
    [Fund Id] INT ,
    [LimitedPartner Id] INT ,
    PRIMARY KEY ([Fund Id], [LimitedPartner Id])
);

CREATE TABLE SPFunds (
    FundName VARCHAR(50) NULL,
    InvestorID VARCHAR(50) ,
    InvestorName VARCHAR(50) ,
    ServiceProvided VARCHAR(50) ,
    [Fund Id] INT ,
    [ServiceProvider Id] INT ,
    PRIMARY KEY ([Fund Id], [ServiceProvider Id])
);

CREATE TABLE SPInvestor (
    InvestorName VARCHAR(50) ,
    ServiceType VARCHAR(50) ,
    DealID VARCHAR(50) ,
    ServiceProvided VARCHAR(50) ,
    [Investor Id] INT ,
    [ServiceProvider Id] INT ,
    PRIMARY KEY ([Investor Id], [ServiceProvider Id])
);

CREATE TABLE StartupFounders (
    [Startup Id] INT,
    [Founder Id] VARCHAR(50),
    PRIMARY KEY ([Startup Id], [Founder Id]),
    FOREIGN KEY ([Startup Id]) REFERENCES Startups([Startup Id]),
    FOREIGN KEY ([Founder Id]) REFERENCES Founders([Founder Id])
);

CREATE TABLE StartupIncubators (
    [Startup Id] INT,
    [Incubator Id] INT,
    PRIMARY KEY ([Startup Id], [Incubator Id]),
    FOREIGN KEY ([Startup Id]) REFERENCES Startups([Startup Id]),
    FOREIGN KEY ([Incubator Id]) REFERENCES Incubators([Incubator Id])
);

CREATE TABLE IncubatorFounders (
    [Incubator Id] INT,
    [Founder Id] VARCHAR(50),
    PRIMARY KEY ([Incubator Id], [Founder Id]),
    FOREIGN KEY ([Incubator Id]) REFERENCES Incubators([Incubator Id]),
    FOREIGN KEY ([Founder Id]) REFERENCES Founders([Founder Id])
);

CREATE TABLE FundInvestors (
    [Fund Id] INT,
    [Investor Id] INT,
    PRIMARY KEY ([Fund Id], [Investor Id]),
    FOREIGN KEY ([Fund Id]) REFERENCES Funds([Fund Id]),
    FOREIGN KEY ([Investor Id]) REFERENCES Investors([Investor Id])
);


ALTER TABLE FundingRounds ADD FOREIGN KEY ([Startup Id]) REFERENCES Startups([Startup Id]);

ALTER TABLE Investements ADD FOREIGN KEY ([Funding_Round_Id]) REFERENCES FundingRounds(Funding_Round_Id);
ALTER TABLE Investements ADD FOREIGN KEY ([Investor Id]) REFERENCES Investors([Investor Id]);

ALTER TABLE LPFunds ADD FOREIGN KEY ([Fund Id]) REFERENCES Funds([Fund Id]);
ALTER TABLE LPFunds ADD FOREIGN KEY ([LimitedPartner Id]) REFERENCES LimitedPartner([LimitedPartner Id]);

ALTER TABLE SPFunds ADD FOREIGN KEY ([Fund Id]) REFERENCES Funds([Fund Id]);
ALTER TABLE SPFunds ADD FOREIGN KEY ([ServiceProvider Id]) REFERENCES ServiceProvider([ServiceProvider Id]);

ALTER TABLE SPInvestor ADD FOREIGN KEY ([Investor Id]) REFERENCES Investors([Investor Id]);
ALTER TABLE SPInvestor ADD FOREIGN KEY ([ServiceProvider Id]) REFERENCES ServiceProvider([ServiceProvider Id]);
ALTER TABLE Founders
ALTER COLUMN current_employer VARCHAR(255) NULL;
ALTER TABLE Founders
ALTER COLUMN linkedin_url VARCHAR(255) NULL;

ALTER TABLE Founders
ALTER COLUMN profile_pic VARCHAR(255) NULL;

ALTER TABLE Founders
ALTER COLUMN link_twitter VARCHAR(255) NULL;

ALTER TABLE Founders
ALTER COLUMN link_facebook VARCHAR(255) NULL;

ALTER TABLE Founders
ALTER COLUMN link_instagram VARCHAR(255) NULL;

ALTER TABLE Founders
ALTER COLUMN link_quora VARCHAR(255) NULL;

ALTER TABLE Founders
ALTER COLUMN link_github VARCHAR(255) NULL;

ALTER TABLE Founders
ALTER COLUMN link_aboutme VARCHAR(255) NULL;

ALTER TABLE Founders
ALTER COLUMN link_angellist VARCHAR(255) NULL;

ALTER TABLE Founders
ALTER COLUMN link_stackoverflow VARCHAR(255) NULL;

