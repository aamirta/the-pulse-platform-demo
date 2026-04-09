"""
Scrape founders from start-up.ma startup detail pages.
Extracts founder names and roles from the "Fondateurs & Investisseurs" section.
"""
import os
import sys
import time
import json
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
from bs4 import BeautifulSoup
from app import app, db
from models import Founder, Startup, StartupFounder

BASE_URL = 'https://www.start-up.ma'
LISTING_URL = f'{BASE_URL}/liste-startups-au-maroc/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
}
DELAY = 1.5


def normalize_name(name):
    if not name:
        return ''
    return name.strip().lower()


def get_page(url, retries=3):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                return resp.text
        except requests.RequestException:
            pass
        if attempt < retries - 1:
            time.sleep(DELAY * 2)
    return None


def extract_founders_from_page(slug):
    """Extract founder names and roles from a startup detail page."""
    url = f'{LISTING_URL}{slug}/'
    html = get_page(url)
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    founders = []

    # Find the Fondateurs section
    for h in soup.find_all(['h2', 'h3']):
        if 'fondateur' in h.get_text(strip=True).lower():
            section = h.parent
            # Find founder links (h5 > a with /fondateurs-des-startup/ pattern)
            for h5 in section.find_all('h5'):
                link = h5.find('a', href=re.compile(r'/fondateurs-des-startup/'))
                name = h5.get_text(strip=True)
                role_el = h5.find_next('span')
                role = role_el.get_text(strip=True) if role_el else 'Fondateur'

                if name and len(name) > 2:
                    founder_slug = None
                    if link:
                        founder_slug = link['href'].rstrip('/').split('/')[-1]

                    founders.append({
                        'name': name,
                        'role': role if role and role not in ['La suite', 'Rejoignez'] else 'Fondateur',
                        'slug': founder_slug,
                        'profile_url': link['href'] if link else None,
                    })
            break

    return founders


def scrape_founder_detail(slug):
    """Scrape a founder's individual page for more details."""
    url = f'{BASE_URL}/fondateurs-des-startup/{slug}/'
    html = get_page(url)
    if not html:
        return {}

    soup = BeautifulSoup(html, 'html.parser')
    data = {}

    # Name
    h1 = soup.find('h1')
    if h1:
        data['full_name'] = h1.get_text(strip=True)

    # Info cards (same structure as startup pages)
    for card in soup.select('.card_infromation'):
        label_el = card.select_one('.color_p_formation, p')
        value_el = card.find('strong')
        if not label_el or not value_el:
            continue
        label = label_el.get_text(strip=True).lower()
        value = value_el.get_text(strip=True)

        if 'ville' in label or 'city' in label:
            data['city'] = value
        elif 'titre' in label or 'poste' in label or 'title' in label:
            data['title'] = value

    # LinkedIn
    for a in soup.find_all('a', href=True):
        if 'linkedin.com' in a['href']:
            data['linkedin'] = a['href']
            break

    return data


def get_all_startup_slugs():
    """Get slugs from all listing pages."""
    all_slugs = []
    for page in range(1, 59):
        url = f'{LISTING_URL}?pages={page}'
        html = get_page(url)
        if not html:
            continue
        soup = BeautifulSoup(html, 'html.parser')
        for card in soup.select('.card_ecole'):
            link = card.find('a', href=re.compile(r'/liste-startups-au-maroc/[^?]'))
            title_el = card.select_one('.title_card_ecole')
            if link:
                slug = link['href'].rstrip('/').split('/')[-1]
                name = title_el.get_text(strip=True) if title_el else slug
                all_slugs.append({'slug': slug, 'name': name})
        time.sleep(DELAY)
        print(f'  Page {page}/58: {len(all_slugs)} slugs total')
    return all_slugs


def main():
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')

    # Use previously scraped data if available
    json_path = os.path.join(data_dir, 'startup_ma_scraped.json')
    if os.path.exists(json_path):
        with open(json_path) as f:
            startups_data = json.load(f)
        slugs = [{'slug': s['slug'], 'name': s.get('name', '')} for s in startups_data if s.get('slug')]
        print(f"Using {len(slugs)} slugs from cached data")
    else:
        print("Fetching slugs from listing pages...")
        slugs = get_all_startup_slugs()

    # Phase 1: Extract founders from each startup page
    print("\n" + "=" * 60)
    print("Phase 1: Extracting founders from startup pages")
    print("=" * 60)

    all_founders = []
    startup_founder_map = []  # (startup_name, founder_name)

    for i, s in enumerate(slugs):
        slug = s['slug']
        startup_name = s.get('name', slug)
        print(f"  [{i+1}/{len(slugs)}] {slug}...", end=' ')

        founders = extract_founders_from_page(slug)
        if founders:
            print(f"{len(founders)} founders")
            for f in founders:
                f['startup_name'] = startup_name
                f['startup_slug'] = slug
                all_founders.append(f)
                startup_founder_map.append((startup_name, f['name']))
        else:
            print("no founders")

        time.sleep(DELAY)

    print(f"\nTotal founders found: {len(all_founders)}")

    # Save raw data
    founders_json = os.path.join(data_dir, 'founders_scraped.json')
    with open(founders_json, 'w', encoding='utf-8') as f:
        json.dump(all_founders, f, ensure_ascii=False, indent=2)
    print(f"Saved to {founders_json}")

    # Phase 2: Import to database
    print("\n" + "=" * 60)
    print("Phase 2: Importing founders to database")
    print("=" * 60)

    with app.app_context():
        existing_founders = db.session.query(Founder.name).all()
        existing_names = {normalize_name(n[0]) for n in existing_founders if n[0]}

        # Get max founder_id (it's a string in this schema)
        all_ids = db.session.query(Founder.founder_id).all()
        numeric_ids = []
        for fid in all_ids:
            try:
                numeric_ids.append(int(fid[0]))
            except (ValueError, TypeError):
                pass
        max_id = max(numeric_ids) if numeric_ids else 100000

        added = 0
        skipped = 0

        for f in all_founders:
            name = f['name']
            norm = normalize_name(name)
            if norm in existing_names:
                skipped += 1
                continue

            max_id += 1
            parts = name.split()
            first_name = parts[0] if parts else ''
            last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''

            founder = Founder(
                founder_id=str(max_id),
                name=name[:50],
                first_name=first_name[:50],
                last_name=last_name[:50],
                current_title=f.get('role', 'Fondateur')[:255],
                current_employer=f.get('startup_name', '')[:255],
                company_details_name=f.get('startup_name', '')[:50],
            )
            db.session.add(founder)
            existing_names.add(norm)
            added += 1

            # Link to startup
            startup = db.session.query(Startup).filter(
                Startup.startup_name.ilike(f['startup_name'])
            ).first()
            if startup:
                existing_link = db.session.query(StartupFounder).filter_by(
                    startup_id=startup.startup_id,
                    founder_id=str(max_id)
                ).first()
                if not existing_link:
                    link = StartupFounder(
                        startup_id=startup.startup_id,
                        founder_id=str(max_id)
                    )
                    db.session.add(link)

            if added % 50 == 0:
                db.session.commit()
                print(f"  ... committed {added}")

        db.session.commit()
        total = db.session.query(Founder).count()
        print(f"\nDone! Added: {added}, Skipped: {skipped}")
        print(f"Total founders in DB: {total}")


if __name__ == '__main__':
    main()
