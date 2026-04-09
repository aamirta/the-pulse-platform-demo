"""
Scraper for start-up.ma — Moroccan startup directory.
Scrapes listing pages (58 pages) + individual startup detail pages.
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
from models import Startup

BASE_URL = 'https://www.start-up.ma'
LISTING_URL = f'{BASE_URL}/liste-startups-au-maroc/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
}
DELAY = 2  # seconds between requests


def normalize_name(name):
    if not name:
        return ''
    return name.strip().lower().replace('-', ' ').replace('_', ' ')


def get_page(url, retries=3):
    """Fetch a page with retries."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                return resp.text
            print(f"  HTTP {resp.status_code} for {url}")
        except requests.RequestException as e:
            print(f"  Error fetching {url}: {e}")
        if attempt < retries - 1:
            time.sleep(DELAY * 2)
    return None


def scrape_listing_page(page_num):
    """Scrape a single listing page, return list of startup slugs/names."""
    url = f'{LISTING_URL}?pages={page_num}'
    html = get_page(url)
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    startups = []

    # Find startup cards using .card_ecole class
    cards = soup.select('.card_ecole')

    for card in cards:
        link = card.find('a', href=re.compile(r'/liste-startups-au-maroc/[^?]'))
        title_el = card.select_one('.title_card_ecole')
        desc_el = card.select_one('.description_card_ecole')

        name = title_el.get_text(strip=True) if title_el else None
        slug = None
        description = desc_el.get_text(strip=True) if desc_el else None

        if link and '/liste-startups-au-maroc/' in link['href']:
            href = link['href'].rstrip('/')
            slug = href.split('/')[-1]

        if name or slug:
            startups.append({
                'name': name,
                'slug': slug,
                'description': description,
            })

    return startups


def scrape_startup_detail(slug):
    """Scrape an individual startup page for details."""
    url = f'{LISTING_URL}{slug}/'
    html = get_page(url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')
    data = {}

    # Name from h1
    h1 = soup.find('h1')
    if h1:
        data['name'] = h1.get_text(strip=True)

    # Logo — look for img in the startup header area
    logo_img = soup.select_one('.logo_startup img, .startup-logo img, .single-startup img')
    if not logo_img:
        # Try finding an img with wp-content/uploads in src near the top
        for img in soup.find_all('img', src=True):
            if 'wp-content/uploads' in img['src'] and 'logo' not in img.get('class', []):
                data['logo_url'] = img['src']
                break
    else:
        data['logo_url'] = logo_img['src']

    # Information panel — .card_infromation (note: typo in original site)
    info_cards = soup.select('.card_infromation')
    for card in info_cards:
        label_el = card.select_one('.color_p_formation, p')
        value_el = card.find('strong')
        if not label_el or not value_el:
            continue

        label = label_el.get_text(strip=True).lower()
        value = value_el.get_text(strip=True)

        if "chiffre" in label or "affaire" in label:
            data['revenue'] = value
        elif "effectif" in label or "employé" in label:
            data['employees'] = value
        elif "création" in label or "fondée" in label:
            data['year_founded'] = value
        elif "état" in label or "statut" in label:
            data['status'] = value
        elif "ville" in label:
            data['city'] = value
        elif "valorisation" in label:
            data['valuation'] = value

    # Sector from sector cards
    sector_links = soup.select('.title_card_secteur a, a[href*="secteur"]')
    sectors = []
    for s in sector_links:
        txt = s.get_text(strip=True)
        if txt and 'secteur' not in txt.lower() and len(txt) > 2:
            sectors.append(txt)
    if sectors:
        data['sector'] = ', '.join(sectors[:3])

    # Founders — look for fondateur section
    founder_cards = soup.select('.card_fondateur, .fondateur_card, .founder-card')
    founders = []
    for f in founder_cards:
        fname = f.find('h3') or f.find('h4') or f.find('strong')
        frole = f.find('span') or f.find('p')
        if fname:
            founders.append({
                'name': fname.get_text(strip=True),
                'role': frole.get_text(strip=True) if frole else None,
            })
    if founders:
        data['founders'] = founders

    # Social links — only from specific sections, not navbar
    info_section = soup.select_one('.space_card_information, .content-area')
    search_area = info_section if info_section else soup
    for a in search_area.find_all('a', href=True):
        href = a['href']
        if 'linkedin.com/company' in href or 'linkedin.com/in/' in href:
            data['linkedin'] = href
        elif 'facebook.com/' in href and 'start-up.ma' not in href:
            data['facebook'] = href
        elif ('twitter.com/' in href or 'x.com/' in href) and 'start-up.ma' not in href:
            data['twitter'] = href

    return data


def save_to_json(data, filepath):
    """Save scraped data to JSON for inspection."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(data)} entries to {filepath}")


def import_to_db(startups_data):
    """Import scraped startups into the database."""
    with app.app_context():
        existing = db.session.query(Startup.startup_name).all()
        existing_names = {normalize_name(s[0]) for s in existing if s[0]}

        max_id = db.session.query(db.func.max(Startup.startup_id)).scalar() or 0
        added = 0
        skipped = 0

        for s in startups_data:
            name = s.get('name')
            if not name:
                continue

            norm = normalize_name(name)
            if norm in existing_names:
                skipped += 1
                continue

            max_id += 1
            startup = Startup(
                startup_id=max_id,
                startup_name=name,
                location=s.get('city'),
                sector=s.get('sector'),
                description=s.get('description'),
                logo_url=s.get('logo_url'),
                linkedin=s.get('linkedin'),
                facebook_url=s.get('facebook'),
                twitter_url=s.get('twitter'),
                homepage_url=s.get('website'),
                employees=s.get('employees'),
                revenue=s.get('revenue'),
                valuation=s.get('valuation'),
                year_founded=s.get('year_founded'),
                business_status=s.get('status'),
                country_code='MA',
                hq_country='Morocco',
                type='startup',
            )
            db.session.add(startup)
            existing_names.add(norm)
            added += 1

            if added % 50 == 0:
                db.session.commit()
                print(f"  ... committed {added} so far")

        db.session.commit()
        print(f"\nDone! Added: {added}, Skipped (duplicates): {skipped}")
        return added, skipped


def main():
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)

    all_startups = []
    seen_slugs = set()

    # Phase 1: Scrape all listing pages
    print("=" * 60)
    print("Phase 1: Scraping listing pages from start-up.ma")
    print("=" * 60)

    for page in range(1, 59):
        print(f"Page {page}/58...", end=' ')
        entries = scrape_listing_page(page)
        new_count = 0
        for e in entries:
            slug = e.get('slug')
            if slug and slug not in seen_slugs:
                seen_slugs.add(slug)
                all_startups.append(e)
                new_count += 1
        print(f"{new_count} new startups (total: {len(all_startups)})")
        time.sleep(DELAY)

    print(f"\nTotal unique startups from listings: {len(all_startups)}")

    # Phase 2: Scrape individual detail pages
    print("\n" + "=" * 60)
    print("Phase 2: Scraping detail pages")
    print("=" * 60)

    for i, startup in enumerate(all_startups):
        slug = startup.get('slug')
        if not slug:
            continue

        print(f"  [{i+1}/{len(all_startups)}] {slug}...", end=' ')
        details = scrape_startup_detail(slug)
        if details:
            startup.update(details)
            print("OK")
        else:
            print("FAILED")
        time.sleep(DELAY)

    # Save raw data to JSON
    json_path = os.path.join(data_dir, 'startup_ma_scraped.json')
    save_to_json(all_startups, json_path)

    # Phase 3: Import to database
    print("\n" + "=" * 60)
    print("Phase 3: Importing to database")
    print("=" * 60)
    import_to_db(all_startups)


if __name__ == '__main__':
    main()
