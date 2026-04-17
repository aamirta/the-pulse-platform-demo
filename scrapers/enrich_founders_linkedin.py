"""
Enrich existing founders in the database who have no linkedin_url.
For each founder lacking a LinkedIn URL, searches Startpage (privacy-friendly,
no rate-limit) for "<Name> <Employer> site:linkedin.com/in" and picks the
best linkedin.com/in/ result.

Usage:
    python scrapers/enrich_founders_linkedin.py [--dry-run] [--limit N] [--skip-confirmed]

Runs slowly (4-8s between requests) to stay under Startpage's limits.
348 founders ≈ 30-45 min to complete.
"""
import os
import sys
import re
import time
import random
import argparse
from urllib.parse import quote

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ['DATABASE_URL'] = (
    'postgresql://postgres.lianafeunaxlzqfvslob:'
    'Habiba456!!!!@aws-0-eu-west-1.pooler.supabase.com:5432/postgres'
)

import requests
from bs4 import BeautifulSoup
from app import app, db
from models import Founder

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/125.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}
MIN_DELAY = 4
MAX_DELAY = 8

LINKEDIN_RE = re.compile(r'linkedin\.com/in/([a-zA-Z0-9\-\_%]+)/?', re.IGNORECASE)


def search_linkedin(name, employer=None):
    """Search Startpage for a founder's LinkedIn /in/ URL. Returns URL or None."""
    query_parts = [f'"{name}"']
    if employer and employer.strip():
        query_parts.append(f'"{employer.strip()}"')
    query_parts.append('site:linkedin.com/in')
    query = ' '.join(query_parts)
    url = f'https://www.startpage.com/sp/search?query={quote(query)}'

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"    [net-error] {e}")
        return None

    # Find all linkedin.com/in/<slug> references
    matches = LINKEDIN_RE.findall(r.text)
    if not matches:
        return None

    # Prefer the slug that contains the name (case-insensitive)
    name_tokens = [t.lower() for t in re.findall(r'\w+', name) if len(t) > 2]
    best = None
    for slug in matches:
        slug_lower = slug.lower()
        if any(t in slug_lower for t in name_tokens):
            best = slug
            break
    if not best:
        best = matches[0]
    return f'https://www.linkedin.com/in/{best}'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--verbose', '-v', action='store_true')
    args = parser.parse_args()

    with app.app_context():
        q = Founder.query.filter(
            db.or_(Founder.linkedin_url.is_(None), Founder.linkedin_url == ''),
            Founder.name.isnot(None),
            Founder.name != '',
        )
        if args.limit:
            q = q.limit(args.limit)
        founders = q.all()

        print(f"Found {len(founders)} founders without LinkedIn URL")
        if args.dry_run:
            print("DRY-RUN mode: no DB writes")

        stats = {'updated': 0, 'not_found': 0, 'skipped': 0, 'errors': 0}
        for i, f in enumerate(founders, 1):
            name = (f.name or '').strip()
            employer = (f.current_employer or '').strip()
            if not name:
                stats['skipped'] += 1
                continue

            print(f"[{i}/{len(founders)}] {name!r} @ {employer!r}")
            try:
                linkedin = search_linkedin(name, employer)
            except Exception as e:
                print(f"    [error] {e}")
                stats['errors'] += 1
                time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
                continue

            if linkedin:
                print(f"    → {linkedin}")
                if not args.dry_run:
                    f.linkedin_url = linkedin
                    db.session.commit()
                stats['updated'] += 1
            else:
                print(f"    → NOT FOUND")
                stats['not_found'] += 1

            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

        print(f"\n=== DONE ===")
        print(f"  Updated:   {stats['updated']}")
        print(f"  Not found: {stats['not_found']}")
        print(f"  Skipped:   {stats['skipped']}")
        print(f"  Errors:    {stats['errors']}")


if __name__ == '__main__':
    main()
