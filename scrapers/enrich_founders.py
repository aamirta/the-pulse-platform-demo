"""
Enrich startups that have no founders by searching the internet for founder/CEO info.
Uses Startpage search to find LinkedIn profiles and news articles about founders,
then parses results to extract founder names and LinkedIn profiles.

Usage:
    python scrapers/enrich_founders.py [--dry-run] [--limit N]
"""
import os
import sys
import re
import time
import random
import argparse
from urllib.parse import urlparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ['DATABASE_URL'] = (
    'postgresql://postgres.lianafeunaxlzqfvslob:'
    'Habiba456!!!!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'
)

import requests
from bs4 import BeautifulSoup
from app import app, db
from models import Startup, Founder, StartupFounder

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/125.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}
MIN_DELAY = 4
MAX_DELAY = 8

# Domains to exclude from search results (our own platform, generic listings)
EXCLUDED_DOMAINS = {
    'thepulse.ma', 'www.thepulse.ma',
}

TITLE_RE = re.compile(
    r'(?:founder|co-founder|ceo|fondateur|co-fondateur|pdg|directeur g[eé]n[eé]ral)',
    re.IGNORECASE
)

# Words that should not appear in person names
BLACKLIST_WORDS = {
    'linkedin', 'facebook', 'twitter', 'instagram', 'youtube', 'google',
    'morocco', 'maroc', 'startup', 'founder', 'ceo', 'about', 'team',
    'contact', 'home', 'page', 'company', 'entreprise', 'societe',
    'agence', 'digital', 'corporation', 'solutions', 'services', 'group',
    'tech', 'technologies', 'consulting', 'marketing', 'media', 'web',
    'labs', 'studio', 'ventures', 'capital', 'fund', 'holding',
    'association', 'foundation', 'institut', 'academy', 'leader',
    'network', 'platform', 'hub', 'club', 'center', 'centre',
    'africa', 'african', 'global', 'international', 'world',
    'observatory', 'organization', 'organisation', 'committee', 'council',
    'corporate', 'europe', 'european', 'national', 'regional',
    'sarl', 'sas', 'sa', 'inc', 'ltd', 'llc', 'gmbh',
    # French job titles / common words that are not person names
    'créateur', 'createur', 'créatrice', 'directeur', 'directrice',
    'fondateur', 'fondatrice', 'président', 'presidente', 'présidente',
    'gérant', 'gerante', 'gérante', 'responsable', 'manager', 'chef',
    'coordinateur', 'coordinatrice', 'analyste', 'ingénieur', 'ingenieur',
    'développeur', 'developpeur', 'designer', 'architecte', 'consultant',
    'conseiller', 'conseillère', 'expert', 'spécialiste', 'specialiste',
    'évènement', 'evenement', 'événement', 'projet', 'produit',
    'commercial', 'technique', 'financier', 'général', 'general',
    'adjoint', 'adjointe', 'principal', 'senior', 'junior',
}

# Generic words too common to reliably identify a specific startup
GENERIC_STARTUP_NAMES = {
    'advertiser', 'digital', 'tech', 'media', 'solutions', 'services',
    'consulting', 'agency', 'studio', 'labs', 'group', 'hub', 'app',
    'connect', 'smart', 'data', 'cloud', 'mobile', 'pro', 'net',
    'web', 'soft', 'sys', 'info', 'one', 'first', 'next', 'new',
}


def delay():
    """Sleep a random amount between MIN_DELAY and MAX_DELAY seconds."""
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


def search_web(query):
    """
    Search using DuckDuckGo and return structured results.
    Returns: [{'title': ..., 'url': ..., 'snippet': ...}, ...]
    """
    from ddgs import DDGS
    try:
        raw = list(DDGS().text(query, max_results=10))
    except Exception as e:
        print(f"    [ERR] Search failed: {e}")
        return []

    results = []
    for r in raw:
        url = r.get('href', '')
        if not url.startswith('http'):
            continue

        # Skip excluded domains
        try:
            domain = urlparse(url).netloc.lower()
            if domain in EXCLUDED_DOMAINS:
                continue
        except Exception:
            pass

        results.append({
            'title': r.get('title', ''),
            'url': url,
            'snippet': r.get('body', ''),
        })

    return results


def extract_linkedin_name(url):
    """Extract a person's name from a LinkedIn profile URL slug."""
    match = re.search(r'linkedin\.com/in/([^/?]+)', url)
    if not match:
        return None
    slug = match.group(1).rstrip('/')
    parts = slug.split('-')
    name_parts = []
    for p in parts:
        if len(p) > 8 and re.match(r'^[a-f0-9]+$', p):
            continue
        if p.isdigit():
            continue
        if len(p) <= 1:
            continue
        name_parts.append(p)
    if len(name_parts) < 2 or len(name_parts) > 4:
        return None
    name = ' '.join(name_parts).title()
    return name if len(name) > 4 else None


def is_valid_person_name(name):
    """Check that a string looks like a real person's name, not a company."""
    if not name or len(name) < 4:
        return False

    # Remove trailing dots and commas
    name = name.strip().rstrip('.,;:')

    # Strip honorifics / prefixes
    name = re.sub(r'^(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Prof\.?|Mme\.?|M\.)\s+', '', name, flags=re.IGNORECASE)

    parts = name.strip().split()
    if len(parts) < 2 or len(parts) > 4:
        return False

    # Reject if name contains dots (likely fragmented text like "Ismail Belkhayat. Co")
    if '.' in name:
        return False

    # Reject all-uppercase names (likely company names like "ALYA PAY")
    if name == name.upper():
        return False

    # Reject if any word >3 chars is fully uppercase (e.g. "Ouassim BERNOSSI")
    for p in parts:
        if len(p) > 3 and p == p.upper():
            return False

    # Reject if any word looks like concatenated garbage (e.g. "KONTAKTYCEOEurope")
    for part in parts:
        # More than 2 uppercase letters in a row inside a word = garbage
        if re.search(r'[A-Z]{3,}', part) and part != part.upper():
            return False

    # Reject common English phrases that slip through
    name_lower = name.lower()
    PHRASE_BLACKLIST = [
        'who we are', 'what we do', 'about us', 'our team', 'meet the',
        'the california', 'the company', 'la mise en', 'mise en place',
        'reid hoffman',  # LinkedIn founder, not a Moroccan startup founder
    ]
    if any(phrase in name_lower for phrase in PHRASE_BLACKLIST):
        return False

    for part in parts:
        lower_part = part.lower()
        if lower_part in BLACKLIST_WORDS:
            return False
        # Check apostrophe-joined subwords (e.g. "d'évènement")
        if "'" in lower_part or '\u2019' in lower_part:
            subparts = re.split(r"['\u2019]", lower_part)
            if any(sp in BLACKLIST_WORDS for sp in subparts if len(sp) > 1):
                return False

    # Must contain only letters, spaces, hyphens, apostrophes (no dots)
    if not re.match(r"^[A-Za-zÀ-ÿ\s\-']+$", name):
        return False
    if any(len(p) < 2 or len(p) > 20 for p in parts):
        return False
    if len(name) > 40:
        return False

    # Each part of the name should start with an uppercase letter (proper noun check)
    for part in parts:
        # Skip short connectors like "el", "de", "ben", "al"
        if len(part) <= 3 and part[0].islower():
            continue
        if not part[0].isupper() and not part[0] in 'ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞß':
            return False

    return True


def extract_title_from_text(text):
    """Extract a title (CEO, Founder, etc.) from text."""
    text_lower = text.lower()
    if 'co-founder' in text_lower or 'co-fondateur' in text_lower or 'cofound' in text_lower:
        return 'Co-Founder'
    if 'ceo' in text_lower or 'chief executive' in text_lower:
        return 'CEO'
    if 'founder' in text_lower or 'fondateur' in text_lower:
        return 'Founder'
    if 'pdg' in text_lower or 'directeur' in text_lower:
        return 'CEO'
    if 'cto' in text_lower:
        return 'CTO'
    if 'coo' in text_lower:
        return 'COO'
    return 'Founder'


def extract_names_from_text(text, startup_name):
    """Extract person names from text using founder/CEO title patterns."""
    candidates = []

    # Pattern: "Name - Title" or "Name, Title"
    for pattern in [
        r'([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\-\']+(?:\s+[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\-\']+){1,3})\s*[-–|,]\s*(?:founder|co-founder|ceo|cto|coo|fondateur|co-fondateur|pdg|directeur)',
        r'(?:founded by|fondée? par|créée? par|co-?founded by)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\-\']+(?:\s+[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\-\']+){1,3})',
        r'(?:CEO|founder|co-founder|fondateur|pdg)\s*(?:[:,]|de|at|chez|of)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\-\']+(?:\s+[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\-\']+){1,3})',
    ]:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            name = match.group(1).strip()
            name = re.sub(
                r'\s+(and|et|de|at|chez|is|was|has|the|a|an|le|la|les|un|une|des)$',
                '', name, flags=re.IGNORECASE
            )
            if is_valid_person_name(name):
                candidates.append(name)

    return candidates


def startup_name_in_result(startup_name, url, title, snippet):
    """Check if a search result is actually related to this startup."""
    sn = startup_name.lower().strip()
    combined = f"{url} {title} {snippet}".lower()

    # If the startup name is a single generic word, require it with Morocco context
    words = sn.split()
    if len(words) == 1 and sn in GENERIC_STARTUP_NAMES:
        if sn in combined and ('maroc' in combined or 'morocco' in combined):
            return True
        return False

    # Direct match in any field
    if sn in combined:
        return True

    # Simplified name (remove suffixes)
    simplified = re.sub(r'\s+(sarl|sas|sa|inc|ltd|llc|app|\.com|\.ma)$', '', sn, flags=re.IGNORECASE)
    if simplified != sn and len(simplified) > 3 and simplified in combined:
        return True

    # URL slug match
    slug = re.sub(r'[^a-z0-9]', '', sn)
    url_cleaned = url.lower().replace('-', '').replace('_', '')
    if len(slug) >= 5 and slug in url_cleaned:
        return True

    return False


def scrape_website_for_founder(website_url):
    """Try to find founder/team info from the startup's website."""
    if not website_url:
        return []

    if not website_url.startswith('http'):
        website_url = 'https://' + website_url
    website_url = website_url.rstrip('/')

    candidates = []
    paths_to_try = ['', '/about', '/about-us', '/team', '/equipe', '/a-propos']

    for path in paths_to_try:
        url = website_url + path
        try:
            resp = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True)
            if resp.status_code != 200:
                continue
        except requests.RequestException:
            continue

        soup = BeautifulSoup(resp.text, 'html.parser')
        text = soup.get_text(' ', strip=True)

        names = extract_names_from_text(text, '')
        if names:
            for name in names[:2]:
                title = extract_title_from_text(text)
                candidates.append({
                    'name': name,
                    'title': title,
                    'linkedin_url': None,
                    'source': f'website:{path or "/"}',
                })

        # Look for LinkedIn profile links
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'linkedin.com/in/' in href:
                ln_name = extract_linkedin_name(href)
                if ln_name and is_valid_person_name(ln_name):
                    if not any(c['name'].lower() == ln_name.lower() for c in candidates):
                        candidates.append({
                            'name': ln_name,
                            'title': 'Founder',
                            'linkedin_url': href,
                            'source': f'website:{path or "/"}',
                        })

        if candidates:
            break
        time.sleep(1)

    return candidates[:2]


def search_founder_for_startup(startup_name, website=None, linkedin_url=None, sector=None):
    """
    Search for founder/CEO of a startup using multiple strategies.
    Returns a list of dicts with max 2 founders per startup.
    """
    found_founders = []
    seen_names = set()

    def add_founder(name, title, linkedin_url_val=None, source='search'):
        if len(found_founders) >= 2:
            return
        norm = name.strip().lower()
        if norm in seen_names:
            return
        seen_names.add(norm)
        found_founders.append({
            'name': name.strip(),
            'title': title,
            'linkedin_url': linkedin_url_val,
            'source': source,
        })

    # ---- Strategy 1: Single combined search ----
    query = f'"{startup_name}" founder OR fondateur OR CEO Morocco'
    print(f"    Search: {query[:80]}...")
    results = search_web(query)
    print(f"    -> {len(results)} results")

    for r in results:
        if len(found_founders) >= 2:
            break
        url = r['url']
        title = r['title']
        snippet = r['snippet']
        combined = f"{title} {snippet}"

        if not startup_name_in_result(startup_name, url, title, snippet):
            continue

        # Check if result mentions founder/CEO terms
        if not TITLE_RE.search(combined):
            continue

        # Extract from title (e.g. "Ismael Belkhayat - CEO at Chari - LinkedIn")
        title_match = re.match(
            r'^([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\-\']+(?:\s+[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\-\']+){1,3})\s*[-–|]',
            title
        )
        if title_match:
            name = title_match.group(1).strip()
            if is_valid_person_name(name):
                role = extract_title_from_text(combined)
                li_url = url if 'linkedin.com/in/' in url else None
                add_founder(name, role, li_url, 'google')

        # Also try extracting from snippet text
        names = extract_names_from_text(combined, startup_name)
        for name in names:
            role = extract_title_from_text(combined)
            li_url = url if 'linkedin.com/in/' in url else None
            add_founder(name, role, li_url, 'google')

        # LinkedIn URL name extraction as fallback
        if 'linkedin.com/in/' in url and len(found_founders) == 0:
            ln_name = extract_linkedin_name(url)
            if ln_name and is_valid_person_name(ln_name):
                role = extract_title_from_text(combined)
                add_founder(ln_name, role, url, 'google_linkedin')

    # ---- Strategy 2: French search (only if needed) ----
    if len(found_founders) < 1:
        delay()
        query2 = f'"{startup_name}" fondateur CEO Maroc'
        print(f"    Search FR: {query2[:80]}...")
        results2 = search_web(query2)
        print(f"    -> {len(results2)} results")

        for r in results2:
            if len(found_founders) >= 2:
                break
            url = r['url']
            title = r['title']
            snippet = r['snippet']
            combined = f"{title} {snippet}"

            if not startup_name_in_result(startup_name, url, title, snippet):
                continue
            if not TITLE_RE.search(combined):
                continue

            title_match = re.match(
                r'^([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\-\']+(?:\s+[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\-\']+){1,3})\s*[-–|]',
                title
            )
            if title_match:
                name = title_match.group(1).strip()
                if is_valid_person_name(name):
                    role = extract_title_from_text(combined)
                    li_url = url if 'linkedin.com/in/' in url else None
                    add_founder(name, role, li_url, 'google_fr')

            names = extract_names_from_text(combined, startup_name)
            for name in names:
                role = extract_title_from_text(combined)
                li_url = url if 'linkedin.com/in/' in url else None
                add_founder(name, role, li_url, 'google_fr')

    # ---- Strategy 3: Try the startup website ----
    if len(found_founders) < 2 and website:
        print(f"    Trying website: {website}...")
        try:
            web_founders = scrape_website_for_founder(website)
            for wf in web_founders:
                add_founder(wf['name'], wf['title'], wf.get('linkedin_url'), 'website')
        except Exception as e:
            print(f"    [WARN] Website scraping failed: {e}")

    return found_founders


def get_startups_without_founders():
    """Query startups that have no linked founders and have a website or LinkedIn."""
    from sqlalchemy import text
    sql = """
        SELECT s."Startup Id", s."Startup name", s."EntrepriseContactSiteWeb",
               s.linkedin, s.sector
        FROM "Startups" s
        WHERE NOT EXISTS (
            SELECT 1 FROM "StartupFounders" sf WHERE sf."Startup Id" = s."Startup Id"
        )
        AND (s."EntrepriseContactSiteWeb" IS NOT NULL OR s.linkedin IS NOT NULL)
        ORDER BY
            CASE WHEN s."EntrepriseContactSiteWeb" IS NOT NULL AND s.linkedin IS NOT NULL THEN 0
                 WHEN s."EntrepriseContactSiteWeb" IS NOT NULL THEN 1
                 ELSE 2 END,
            s."Startup name"
    """
    result = db.session.execute(text(sql))
    rows = result.fetchall()
    return [
        {
            'startup_id': row[0],
            'startup_name': row[1],
            'website': row[2],
            'linkedin': row[3],
            'sector': row[4],
        }
        for row in rows
    ]


def get_next_founder_id():
    """Get the next available numeric founder ID."""
    from sqlalchemy import text
    result = db.session.execute(
        text('SELECT MAX(CAST("Founder Id" AS INTEGER)) FROM "Founders" WHERE "Founder Id" ~ \'^[0-9]+$\'')
    )
    row = result.fetchone()
    max_id = row[0] if row and row[0] else 100000
    return max_id + 1


def main():
    parser = argparse.ArgumentParser(description='Enrich startups without founders')
    parser.add_argument('--dry-run', action='store_true',
                        help='Search but do not insert into database')
    parser.add_argument('--limit', type=int, default=50,
                        help='Max number of startups to process (default: 50)')
    args = parser.parse_args()

    with app.app_context():
        print("=" * 70)
        print("FOUNDER ENRICHMENT SCRIPT")
        print("=" * 70)

        all_startups = get_startups_without_founders()
        print(f"\nTotal startups without founders (with website/LinkedIn): {len(all_startups)}")

        if not all_startups:
            print("No startups to enrich. Exiting.")
            return

        batch = all_startups[:args.limit]
        print(f"Processing batch of {len(batch)} startups (limit={args.limit})")
        if args.dry_run:
            print("[DRY RUN MODE - no database changes will be made]")

        print()

        next_id = get_next_founder_id()
        print(f"Next founder ID will start at: {next_id}")
        print()

        total_found = 0
        total_inserted = 0
        results_log = []

        for i, startup in enumerate(batch):
            sid = startup['startup_id']
            name = startup['startup_name'] or f"Startup #{sid}"
            website = startup['website']
            linkedin = startup['linkedin']
            sector = startup['sector']

            print(f"[{i+1}/{len(batch)}] {name}")
            print(f"  Website: {website or 'N/A'}")
            print(f"  LinkedIn: {linkedin or 'N/A'}")
            print(f"  Sector: {sector or 'N/A'}")

            try:
                founders = search_founder_for_startup(
                    name, website=website, linkedin_url=linkedin, sector=sector
                )
            except Exception as e:
                print(f"  [ERR] Search failed: {e}")
                founders = []

            if not founders:
                print(f"  => No founders found")
                results_log.append({'startup': name, 'founders': []})
            else:
                print(f"  => Found {len(founders)} founder(s):")
                for f in founders:
                    li_info = f" [LinkedIn: {f['linkedin_url']}]" if f.get('linkedin_url') else ''
                    print(f"     - {f['name']} ({f['title']}){li_info} via {f.get('source', '?')}")

                total_found += len(founders)
                results_log.append({'startup': name, 'founders': founders})

                if not args.dry_run:
                    for f in founders:
                        fid = str(next_id)
                        next_id += 1

                        parts = f['name'].split()
                        first_name = parts[0] if parts else ''
                        last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''

                        # Check if founder with same name already exists
                        existing = db.session.query(Founder).filter(
                            Founder.name == f['name']
                        ).first()

                        if existing:
                            existing_link = db.session.query(StartupFounder).filter_by(
                                startup_id=sid,
                                founder_id=existing.founder_id
                            ).first()
                            if not existing_link:
                                link = StartupFounder(
                                    startup_id=sid,
                                    founder_id=existing.founder_id
                                )
                                db.session.add(link)
                                total_inserted += 1
                                print(f"     -> Linked existing founder {existing.founder_id}")
                        else:
                            founder = Founder(
                                founder_id=fid,
                                name=f['name'][:50],
                                first_name=first_name[:50],
                                last_name=last_name[:50],
                                current_title=f.get('title', 'Founder')[:255],
                                current_employer=name[:255],
                                company_details_name=name[:50],
                                linkedin_url=(f['linkedin_url'][:255]
                                              if f.get('linkedin_url') else None),
                            )
                            db.session.add(founder)

                            link = StartupFounder(
                                startup_id=sid,
                                founder_id=fid
                            )
                            db.session.add(link)
                            total_inserted += 1
                            print(f"     -> Inserted founder {fid}")

                    try:
                        db.session.commit()
                    except Exception as e:
                        print(f"     [ERR] DB commit failed: {e}")
                        db.session.rollback()

            print()
            delay()

        # Summary
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Startups processed: {len(batch)}")
        print(f"Founders found: {total_found}")
        if not args.dry_run:
            print(f"Founders inserted/linked: {total_inserted}")
        else:
            print("[DRY RUN - nothing was inserted]")

        startups_with_results = [r for r in results_log if r['founders']]
        startups_without_results = [r for r in results_log if not r['founders']]

        print(f"\nStartups where founders were found: {len(startups_with_results)}")
        for r in startups_with_results:
            names = ', '.join(f['name'] for f in r['founders'])
            print(f"  {r['startup']}: {names}")

        print(f"\nStartups where NO founders were found: {len(startups_without_results)}")
        for r in startups_without_results:
            print(f"  {r['startup']}")


if __name__ == '__main__':
    main()
