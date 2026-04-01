from collections import Counter
from collections import defaultdict
from datetime import datetime

def get_top_sectors(startups, sectors, n=10):
    sector_counter = Counter()
    for startup in startups:
        if startup.sector:
            startup_sectors = [s.strip() for s in startup.sector.split(",") if s.strip()]
            for s in startup_sectors:
                if s in sectors: 
                    sector_counter[s] += 1
    
    topsectors , nbstartupsbysector= zip(*sector_counter.most_common(n))
    return list(topsectors), list(nbstartupsbysector)

def get_unique_sectors(startups):
    unique_sectors = set()

    for startup in startups:
        if startup.sector:
            for s in startup.sector.split(","):
                cleaned = s.strip()
                if cleaned:
                    unique_sectors.add(cleaned)

    return sorted(unique_sectors)

def get_unique_investementphase(incubators):
    unique_investementsphase = set()

    for incubator in incubators:
        if incubator.phases_investissement:
            for s in incubator.phases_investissement.split(","):
                cleaned = s.strip()
                if cleaned:
                    unique_investementsphase.add(cleaned)

    return sorted(unique_investementsphase)


def get_unique_cities(startups):
    unique_cities = set()

    for startup in startups:
        if startup.location and startup.location != "Morocco(City Not Defined)":
            unique_cities.add(startup.location.strip())

    return sorted(unique_cities)


def get_top_cities(startups, cities, n=10):
    city_counter = Counter()

    for startup in startups:
        if startup.location and startup.location != "Morocco":
            location = startup.location.strip()
            if location in cities:  # Only count if it's in canonical list
                city_counter[location] += 1

    # Return top n as list of (city, count)
    topcities, nbstartupsbycity = zip(*city_counter.most_common(n))
    return list(topcities), list(nbstartupsbycity)

def get_totalFunding_groupby_year(funding_rounds):
    yearly_totals = defaultdict(float)
    for fr in funding_rounds:
        if not fr.date or not fr.raised_amount_usd:
            continue  

        try:
            year = datetime.strptime(fr.date.strip(), "%Y-%m-%d").year
        except ValueError:
            try:
                year = int(fr.date.strip())  
            except ValueError:
                continue 

        yearly_totals[year] += float(fr.raised_amount_usd / 1_000_000)

    years = sorted(yearly_totals.keys())
    totals = [yearly_totals[y] for y in years]

    return years, totals


def get_total_funding_by_sector(funding_rounds, sectors, n=10):
    sector_totals = defaultdict(float)

    for fr in funding_rounds:
        if fr.startup and fr.startup.sector and fr.raised_amount_usd:
            # Si un startup a plusieurs secteurs
            startup_sectors = [s.strip() for s in fr.startup.sector.split(",") if s.strip()]
            for s in startup_sectors:
                if s in sectors:
                    sector_totals[s] += float(fr.raised_amount_usd/1_000_000)

    if not sector_totals:
        return [], []

    # Trier par montant décroissant
    sorted_totals = sorted(sector_totals.items(), key=lambda x: x[1], reverse=True)[:n]
    topsectors, totals = zip(*sorted_totals)
    return list(topsectors), list(totals)
def compute_sector_counts(startups, distinct_sectors):
    counts = {}
    for sec in distinct_sectors:
        counts[sec] = sum(
            1 for s in startups if s.sector and sec in [x.strip() for x in s.sector.split(",")]
        )
    return counts

def compute_phaseinvestissement_counts(incubators, distinct_investementphase):
    counts = {}
    for phase in distinct_investementphase:
        counts[phase] = sum(
            1
            for inc in incubators
            if inc.phases_investissement
            and phase in [x.strip() for x in inc.phases_investissement.split(",")]
        )
    return counts

def toptotalfundingByStartup(startups, n=7):
    funding_dict = {}
    for startup in startups:
        total_from_rounds = sum(
            fr.raised_amount_usd for fr in startup.funding_rounds if fr.raised_amount_usd
        )
        # Use total_funding_usd field as fallback if no funding rounds
        total_from_field = float(startup.total_funding_usd or 0)
        total_funding = max(total_from_rounds, total_from_field)
        funding_dict[startup] = total_funding / 1_000_000  # in millions

    # Sort by total funding and get top n
    sorted_funding = sorted(funding_dict.items(), key=lambda x: x[1], reverse=True)[:n]

    top_startups, top_fundings = zip(*sorted_funding) if sorted_funding else ([], [])
    # if starup name is Argan Infrastructure Fund skiip it
    filtered_startups = []
    filtered_fundings = []
    for startup, funding in zip(top_startups, top_fundings):
        if startup.startup_name != "Argan Infrastructure Fund" and startup.startup_name != "chari":
            filtered_startups.append(startup)
            filtered_fundings.append(funding)
    return list(filtered_startups), list(filtered_fundings)

def StartupsInvestedByInvestor(investor):
    StartupsInvested=set()
    if investor.investments:
        for investment in investor.investments:
            if investment.funding_round and investment.funding_round.startup:
                StartupsInvested.add(investment.funding_round.startup)

    return list(StartupsInvested)
def StartupsInvestedByListOfInvestors(Investors):
    StartupsInvested=set()
    for investor in Investors:
        for investment in investor.investments:
            if investment.funding_round and investment.funding_round.startup:
                StartupsInvested.add(investment.funding_round.startup)

    return list(StartupsInvested)

def StartupsIncubatedByListOfIncubators(Incubators):
    StartupsIncubated=set()
    for incubator in Incubators:
        if incubator.startups:
            StartupsIncubated.update(incubator.startups)
    return list(StartupsIncubated)

def FilterIncubatorsByStartups(Startups):
    FilteredIncubators=[]
    StartupsSet=set(Startups)
    for startup in StartupsSet:
        if startup.incubators:
            FilteredIncubators.extend(startup.incubators)
    return list(set(FilteredIncubators))


def FilterFoundersByStartups(Startups):
    FoundersSet=[]
    for startup in Startups:
        if startup.founders:
            FoundersSet.extend(startup.founders)
    return list(set(FoundersSet))

def InvestorsOfStartup(startup):
    InvestorsSet=set()
    for fr in startup.funding_rounds:
        for investment in fr.investments:
            if investment.investor:
                InvestorsSet.add(investment.investor)
    return list(InvestorsSet)

def FilterInvestorsByStartups(Startups):
    InvestorsSet=[]
    for startup in Startups:
        for fr in startup.funding_rounds:
            for investment in fr.investments:
                if investment.investor:
                    InvestorsSet.append(investment.investor)
    return list(set(InvestorsSet))