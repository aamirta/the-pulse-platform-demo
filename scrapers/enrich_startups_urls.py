"""
Enrich startups that have no website or LinkedIn URL by searching DuckDuckGo.
Finds their official website and LinkedIn company page, then updates the DB.

Usage:
    python scrapers/enrich_startups_urls.py [--dry-run] [--limit N]
"""
import os
import sys
import re
import time
import random
import argparse
from urllib.parse import urlparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ddgs import DDGS
import psycopg2
from sqlalchemy import create_engine, text

# Resolve Supabase hostname via DoH since local DNS may be broken
def _resolve_supabase_host():
    """Resolve Supabase pooler hostname via Google DNS-over-HTTPS."""
    import json
    try:
        resp = __import__('requests').get(
            'https://dns.google/resolve',
            params={'name': 'aws-0-eu-west-1.pooler.supabase.com', 'type': 'A'},
            timeout=5
        )
        data = resp.json()
        for answer in data.get('Answer', []):
            if answer.get('type') == 1:  # A record
                return answer['data']
    except Exception:
        pass
    return 'aws-0-eu-west-1.pooler.supabase.com'  # fallback

_SUPABASE_IP = _resolve_supabase_host()
DATABASE_URL = (
    f'postgresql://postgres.lianafeunaxlzqfvslob:'
    f'Habiba456!!!!@{_SUPABASE_IP}:5432/postgres'
)
engine = create_engine(DATABASE_URL)

# ---------------------------------------------------------------------------
MIN_DELAY = 3
MAX_DELAY = 6

# Domains that are NOT the startup's own website
EXCLUDED_DOMAINS = {
    'facebook.com', 'twitter.com', 'x.com', 'instagram.com', 'youtube.com',
    'tiktok.com', 'pinterest.com', 'reddit.com', 'wikipedia.org',
    'linkedin.com', 'www.linkedin.com',
    'thepulse.ma', 'www.thepulse.ma',
    'start-up.ma', 'www.start-up.ma',
    'crunchbase.com', 'pitchbook.com', 'tracxn.com', 'dealroom.co',
    'angel.co', 'wellfound.com', 'f6s.com', 'startupranking.com',
    'google.com', 'google.co.ma', 'bing.com', 'duckduckgo.com',
    'apple.com', 'play.google.com', 'apps.apple.com',
    'bloomberg.com', 'reuters.com', 'forbes.com',
    'kerix.net', 'charika.ma', 'societe.com',
}

# Domains likely to be listing/directory sites, not the startup itself
DIRECTORY_PATTERNS = [
    'annuaire', 'directory', 'listing', 'pages-jaunes', 'yellowpages',
    'kompass', 'europages', 'manta.com', 'zoominfo.com', 'dnb.com',
]


def delay():
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


def score_website(url, startup_name):
    """
    Score how likely a URL is the startup's own website.
    Returns: int score (0 = not a match, higher = better match)
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace('www.', '')
    except Exception:
        return 0

    # Absolute exclusions
    if domain in EXCLUDED_DOMAINS or any(d in domain for d in EXCLUDED_DOMAINS):
        return 0
    if any(pat in domain for pat in DIRECTORY_PATTERNS):
        return 0

    # Exclude known news/press/blog/listing sites
    NOISE_DOMAINS = {
        'failory.com', 'startupresearcher.com', 'mystartupworld.com',
        'menastartupdigest.com', 'bt-africa.com', 'siliconvalley.ma',
        'gitexafrica.com', 'forbesindia.com', 'techcrunch.com',
        'wamda.com', 'thebigdeal.com', 'disrupt-africa.com',
        'maghrebintelligence.com', 'medias24.com', 'leseco.ma',
        'leconomiste.com', 'lavieeco.com', 'challenge.ma',
        'telquel.ma', 'hespress.com', 'le360.ma', 'h24info.ma',
        'huffpostmaghreb.com', 'welovebuzz.com', 'thecondia.com',
        'innovation-village.com', 'regtechafrica.com', 'tipsloves.com',
        'map.ma', 'mapnews.ma', 'lematin.ma',
    }
    if domain in NOISE_DOMAINS:
        return 0

    # Startup name slug
    name_slug = re.sub(r'[^a-z0-9]', '', startup_name.lower())
    # Take first word if multi-word (e.g. "3C10 Distribution" -> "3c10")
    first_word_slug = re.sub(r'[^a-z0-9]', '', startup_name.split()[0].lower()) if startup_name.split() else name_slug

    domain_base = domain.split('.')[0]  # e.g. "2p" from "2p.ma"
    domain_slug = re.sub(r'[^a-z0-9]', '', domain_base)

    score = 0

    # Strong: startup name IS the domain (e.g. "2p.ma" for "2P particulier à particulier")
    if len(name_slug) >= 3 and name_slug == domain_slug:
        score = 100
    elif len(first_word_slug) >= 3 and first_word_slug == domain_slug:
        score = 90
    elif len(name_slug) >= 4 and name_slug in domain_slug:
        score = 80
    elif len(first_word_slug) >= 4 and first_word_slug in domain_slug:
        score = 70
    elif domain.endswith('.ma') and len(domain_slug) >= 3:
        # .ma domain but name doesn't match — could still be them (rebranded etc.)
        score = 20
    else:
        # Random .com — probably not the startup
        score = 0

    return score


def extract_linkedin_company(url):
    """Extract LinkedIn company URL if it matches the pattern."""
    match = re.search(r'(https?://(?:www\.)?linkedin\.com/company/[^/?&#]+)', url)
    return match.group(1) if match else None


def search_startup_urls(startup_name, sector=None):
    """
    Search for a startup's website and LinkedIn page.
    Returns: {'website': url_or_None, 'linkedin': url_or_None}
    """
    result = {'website': None, 'linkedin': None}

    # Search query
    query = f'{startup_name} startup Morocco site officiel'
    if sector:
        # Add first sector keyword for specificity
        first_sector = sector.split(',')[0].strip()
        query = f'{startup_name} {first_sector} startup Morocco'

    try:
        raw = list(DDGS().text(query, max_results=10))
    except Exception as e:
        print(f"    [ERR] Search failed: {e}")
        return result

    print(f"    -> {len(raw)} results")

    best_website = None
    best_score = 0

    for r in raw:
        url = r.get('href', '')
        if not url.startswith('http'):
            continue

        # Check for LinkedIn company page
        if 'linkedin.com/company/' in url and not result['linkedin']:
            li_url = extract_linkedin_company(url)
            if li_url:
                result['linkedin'] = li_url
                print(f"    [LinkedIn] {li_url}")

        # Score this URL as a potential website
        s = score_website(url, startup_name)
        if s > best_score:
            best_score = s
            best_website = url

    # Only accept website if score is high enough (name matches domain)
    if best_website and best_score >= 50:
        result['website'] = best_website
        print(f"    [Website] {best_website} (score={best_score})")

    # If no website found, try a more targeted search
    if not result['website']:
        delay()
        try:
            raw2 = list(DDGS().text(f'"{startup_name}" site:.ma', max_results=5))
            for r in raw2:
                url = r.get('href', '')
                if url.startswith('http'):
                    s = score_website(url, startup_name)
                    if s >= 50:
                        result['website'] = url
                        print(f"    [Website v2] {url} (score={s})")
                        break
        except Exception:
            pass

    return result


def get_startups_without_urls():
    """Get startups that have no website AND no LinkedIn, and no founders linked."""
    sql = """
        SELECT s."Startup Id", s."Startup name", s.sector
        FROM "Startups" s
        WHERE s."EntrepriseContactSiteWeb" IS NULL
        AND s.linkedin IS NULL
        AND NOT EXISTS (
            SELECT 1 FROM "StartupFounders" sf WHERE sf."Startup Id" = s."Startup Id"
        )
        ORDER BY s."Startup name"
    """
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        return [
            {'startup_id': row[0], 'startup_name': row[1], 'sector': row[2]}
            for row in result.fetchall()
        ]


def main():
    parser = argparse.ArgumentParser(description='Enrich startups with website/LinkedIn URLs')
    parser.add_argument('--dry-run', action='store_true',
                        help='Search but do not update database')
    parser.add_argument('--limit', type=int, default=100,
                        help='Max startups to process (default: 100)')
    args = parser.parse_args()

    print("=" * 70)
    print("STARTUP URL ENRICHMENT")
    print("=" * 70)

    all_startups = get_startups_without_urls()
    print(f"\nTotal startups without website/LinkedIn (and no founders): {len(all_startups)}")

    if not all_startups:
        print("Nothing to enrich.")
        return

    batch = all_startups[:args.limit]
    print(f"Processing batch of {len(batch)} (limit={args.limit})")
    if args.dry_run:
        print("[DRY RUN]")
    print()

    stats = {'website_found': 0, 'linkedin_found': 0, 'updated': 0}

    for i, startup in enumerate(batch):
        sid = startup['startup_id']
        name = startup['startup_name'] or f"Startup #{sid}"
        sector = startup['sector']

        print(f"[{i+1}/{len(batch)}] {name} ({sector or 'N/A'})")

        try:
            urls = search_startup_urls(name, sector=sector)
        except Exception as e:
            print(f"  [ERR] {e}")
            urls = {'website': None, 'linkedin': None}

        if urls['website']:
            stats['website_found'] += 1
        if urls['linkedin']:
            stats['linkedin_found'] += 1

        if not urls['website'] and not urls['linkedin']:
            print(f"    => Nothing found")
        elif not args.dry_run:
            updates = []
            params = {'sid': sid}
            if urls['website']:
                updates.append('"EntrepriseContactSiteWeb" = :website')
                params['website'] = urls['website'][:255]
            if urls['linkedin']:
                updates.append('linkedin = :linkedin')
                params['linkedin'] = urls['linkedin'][:255]

            if updates:
                sql = f'UPDATE "Startups" SET {", ".join(updates)} WHERE "Startup Id" = :sid'
                with engine.begin() as conn:
                    conn.execute(text(sql), params)
                stats['updated'] += 1
                print(f"    => Updated in DB")

        print()
        delay()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Startups processed: {len(batch)}")
    print(f"Websites found: {stats['website_found']}")
    print(f"LinkedIn found: {stats['linkedin_found']}")
    if not args.dry_run:
        print(f"Startups updated in DB: {stats['updated']}")
    else:
        print("[DRY RUN - nothing updated]")


if __name__ == '__main__':
    main()
