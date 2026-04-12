"""
Multi-source Moroccan startup founder scraper.
Sources:
  1. start-up.ma /liste-des-dirigeants-et-fondateurs-des-startups/ (66 pages)
  2. start-up.ma individual founder detail pages
  3. Curated data from web articles (Arageek, MAWebzine, African Business, etc.)
"""
import os
import sys
import time
import json
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
from bs4 import BeautifulSoup

BASE_URL = 'https://www.start-up.ma'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
}
DELAY = 1.5
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def get_page(url, retries=3):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                return resp.text
            print(f"    HTTP {resp.status_code}")
        except requests.RequestException as e:
            print(f"    Error: {e}")
        if attempt < retries - 1:
            time.sleep(DELAY * 2)
    return None


# ─────────────────────────────────────────────────────────────
# Source 1: start-up.ma founder listing pages (66 pages)
# ─────────────────────────────────────────────────────────────
def scrape_startup_ma_founder_listing():
    """Scrape all 66 pages of the founder listing on start-up.ma."""
    print("\n" + "=" * 60)
    print("Source 1: start-up.ma founder listing (66 pages)")
    print("=" * 60)

    all_founders = []
    base = f'{BASE_URL}/liste-des-dirigeants-et-fondateurs-des-startups/'

    for page in range(1, 67):
        url = base if page == 1 else f'{base}?pages={page}'
        print(f"  Page {page}/66...", end=' ')
        html = get_page(url)
        if not html:
            print("FAILED")
            continue

        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.select('.card_ecole, .card_founder, .card_formation')

        if not cards:
            # Try broader selectors
            cards = soup.select('[class*="card"]')

        page_founders = []
        for card in cards:
            # Try to extract name
            name_el = card.select_one('.title_card_ecole, h5, h4, h3, .founder-name, strong')
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if not name or len(name) < 3:
                continue

            # Try to find link to detail page
            link = card.find('a', href=re.compile(r'/fondateurs-des-startup/|/liste-des-dirigeants'))
            slug = None
            profile_url = None
            if link and link.get('href'):
                profile_url = link['href']
                slug = profile_url.rstrip('/').split('/')[-1]

            # Try to get role/title
            role_el = card.select_one('.desc_card_ecole, span, .role, .title')
            role = role_el.get_text(strip=True) if role_el else 'Fondateur'

            # Try to get startup name
            startup_el = card.select_one('.startup-name, .company')
            startup_name = startup_el.get_text(strip=True) if startup_el else ''

            founder = {
                'name': name,
                'role': role if role and len(role) > 1 else 'Fondateur',
                'slug': slug,
                'profile_url': profile_url,
                'startup_name': startup_name,
                'source': 'start-up.ma/fondateurs',
            }
            page_founders.append(founder)

        print(f"{len(page_founders)} founders")
        all_founders.extend(page_founders)
        time.sleep(DELAY)

    print(f"  Total from listing: {len(all_founders)}")
    return all_founders


def scrape_founder_detail(slug):
    """Scrape individual founder detail page for more info."""
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

    # Info cards
    for card in soup.select('.card_infromation, .info-card'):
        label_el = card.select_one('.color_p_formation, p, .label')
        value_el = card.find('strong') or card.select_one('.value')
        if not label_el or not value_el:
            continue
        label = label_el.get_text(strip=True).lower()
        value = value_el.get_text(strip=True)

        if 'ville' in label or 'city' in label or 'localisation' in label:
            data['city'] = value
        elif 'titre' in label or 'poste' in label or 'title' in label or 'fonction' in label:
            data['title'] = value
        elif 'startup' in label or 'entreprise' in label or 'société' in label:
            data['startup_name'] = value
        elif 'email' in label:
            data['email'] = value
        elif 'diplôme' in label or 'formation' in label:
            data['education'] = value

    # LinkedIn
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'linkedin.com' in href:
            data['linkedin'] = href
        elif 'twitter.com' in href or 'x.com' in href:
            data['twitter'] = href

    # Profile image
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if 'fondateur' in src or 'avatar' in src or 'profile' in src:
            if src.startswith('http'):
                data['profile_pic'] = src
            break

    return data


# ─────────────────────────────────────────────────────────────
# Source 2: Curated data from web articles
# ─────────────────────────────────────────────────────────────
CURATED_FOUNDERS = [
    # From Arageek article
    {"name": "Malik Belkeziz", "role": "CEO", "startup_name": "Agenz", "city": "Casablanca", "sector": "PropTech", "source": "arageek.com"},
    {"name": "Badr B.", "role": "Co-Founder", "startup_name": "Agenz", "city": "Casablanca", "sector": "PropTech", "source": "arageek.com"},
    {"name": "Noureddine Tabete", "role": "CEO", "startup_name": "Atlantis Digit", "city": "Casablanca", "sector": "Digital Consulting", "source": "arageek.com"},
    {"name": "Kaoutar Elhaloui", "role": "CTO", "startup_name": "Atlantis Digit", "city": "Casablanca", "sector": "Digital Consulting", "source": "arageek.com"},
    {"name": "Ismael Belkhayat", "role": "Co-Founder & CEO", "startup_name": "Chari", "city": "Casablanca", "sector": "FinTech/E-commerce", "source": "arageek.com"},
    {"name": "Sophia Alj", "role": "Co-Founder", "startup_name": "Chari", "city": "Casablanca", "sector": "FinTech/E-commerce", "source": "arageek.com"},
    {"name": "Mouhsin Bour Qaiba", "role": "Co-Founder", "startup_name": "Clean City", "city": "Casablanca", "sector": "Environmental Tech", "source": "arageek.com"},
    {"name": "Mustapha Amraoui", "role": "Co-Founder", "startup_name": "Clean City", "city": "Casablanca", "sector": "Environmental Tech", "source": "arageek.com"},
    {"name": "Mostapha El Alaoui", "role": "Co-Founder", "startup_name": "Clean City", "city": "Casablanca", "sector": "Environmental Tech", "source": "arageek.com"},
    {"name": "Moncef Chlouchi", "role": "Founder", "startup_name": "Inyad", "city": "Casablanca", "sector": "FinTech", "source": "arageek.com"},
    {"name": "Nizar Abdallaoui Maane", "role": "CEO", "startup_name": "KIFAL AUTO", "city": "Casablanca", "sector": "Automotive Tech", "source": "arageek.com"},
    {"name": "Karim Beqqali", "role": "CEO", "startup_name": "Yakeey", "city": "Casablanca", "sector": "PropTech", "source": "arageek.com"},
    # From MAWebzine / African Business / other articles
    {"name": "Omar Alami", "role": "Founder & CEO", "startup_name": "ORA", "city": "Casablanca", "sector": "FinTech/Super-app", "source": "african.business"},
    {"name": "Ismail Bargach", "role": "CEO", "startup_name": "WafR", "city": "Casablanca", "sector": "FinTech", "source": "african.business"},
    {"name": "Reda Sellak", "role": "CTO", "startup_name": "WafR", "city": "Casablanca", "sector": "FinTech", "source": "african.business"},
    {"name": "Brahim Zaid", "role": "Founder", "startup_name": "Alya", "city": "Casablanca", "sector": "FinTech/BNPL", "source": "african.business"},
    {"name": "Hicham Amadi", "role": "Co-Founder", "startup_name": "Tookeez", "city": "Casablanca", "sector": "FinTech", "source": "african.business"},
    {"name": "Wiam Elmejjad", "role": "Co-Founder", "startup_name": "Tookeez", "city": "Casablanca", "sector": "FinTech", "source": "african.business"},
    {"name": "Siham Elmejjad", "role": "Co-Founder", "startup_name": "Tookeez", "city": "Casablanca", "sector": "FinTech", "source": "african.business"},
    {"name": "Ghita Mezzour", "role": "Founder", "startup_name": "AI Company", "city": "Rabat", "sector": "AI", "source": "mawebzine.ma"},
    {"name": "Youssef Benkirane", "role": "Founder", "startup_name": "Payment Solutions", "city": "Casablanca", "sector": "FinTech", "source": "mawebzine.ma"},
    {"name": "Samir Tamri", "role": "CEO", "startup_name": "POSITEAMS", "city": "Casablanca", "sector": "HR Tech", "source": "start-up.ma"},
    {"name": "Simohamed Zizi", "role": "CEO", "startup_name": "Jobzyn", "city": "Casablanca", "sector": "HR Tech", "source": "start-up.ma"},
    {"name": "Moncef Wagas", "role": "CEO", "startup_name": "SpaceUP", "city": "Casablanca", "sector": "SpaceTech", "source": "start-up.ma"},
    {"name": "Zineb Drissi Kaitouni", "role": "CEO", "startup_name": "DabaDoc", "city": "Casablanca", "sector": "HealthTech", "source": "start-up.ma"},
    {"name": "Zineb Kamal", "role": "Founder & CEO", "startup_name": "smarktic", "city": "Casablanca", "sector": "Marketing Tech", "source": "start-up.ma"},
    {"name": "Mehdi Alaoui", "role": "Founder", "startup_name": "LaStartupStation", "city": "Casablanca", "sector": "Tech", "source": "linkedin.com"},
    # MFOUNDERS investors/mentors (Moroccan diaspora)
    {"name": "Ilan Benhaim", "role": "Founder", "startup_name": "MFOUNDERS", "city": "Paris", "sector": "Investment", "source": "mfounders.com"},
    {"name": "Ahmed Abdelmounem", "role": "Member", "startup_name": "MFOUNDERS", "city": "", "sector": "Investment", "source": "mfounders.com"},
    {"name": "Dounia Boumehdi", "role": "Member", "startup_name": "MFOUNDERS", "city": "", "sector": "Investment", "source": "mfounders.com"},
    {"name": "Youssef Agoumi", "role": "Member", "startup_name": "MFOUNDERS", "city": "", "sector": "Investment", "source": "mfounders.com"},
    {"name": "Karim Amor", "role": "Member", "startup_name": "MFOUNDERS", "city": "", "sector": "Investment", "source": "mfounders.com"},
]


# ─────────────────────────────────────────────────────────────
# Main: combine, deduplicate, enrich, save
# ─────────────────────────────────────────────────────────────
def normalize_name(name):
    return re.sub(r'\s+', ' ', name.strip()).lower()


def main():
    output_path = os.path.join(DATA_DIR, 'founders_multi_source.json')

    # Load existing scraped founders to avoid re-scraping
    existing_path = os.path.join(DATA_DIR, 'founders_scraped.json')
    existing_names = set()
    if os.path.exists(existing_path):
        with open(existing_path) as f:
            for item in json.load(f):
                existing_names.add(normalize_name(item.get('name', '')))
        print(f"Existing founders from previous scrape: {len(existing_names)}")

    all_founders = []

    # ── Source 1: start-up.ma founder listing ──
    listing_founders = scrape_startup_ma_founder_listing()
    all_founders.extend(listing_founders)

    # ── Source 2: Curated data from articles ──
    print("\n" + "=" * 60)
    print("Source 2: Curated data from web articles")
    print("=" * 60)
    print(f"  {len(CURATED_FOUNDERS)} curated founders")
    all_founders.extend(CURATED_FOUNDERS)

    # ── Deduplicate ──
    print("\n" + "=" * 60)
    print("Deduplication")
    print("=" * 60)
    seen = set()
    unique = []
    for f in all_founders:
        key = normalize_name(f.get('name', ''))
        if not key or len(key) < 3:
            continue
        if key in seen or key in existing_names:
            continue
        seen.add(key)
        unique.append(f)
    print(f"  Total raw: {len(all_founders)}")
    print(f"  After dedup (excl. existing): {len(unique)}")

    # ── Enrich: scrape detail pages for founders with slugs ──
    print("\n" + "=" * 60)
    print("Enrichment: scraping detail pages")
    print("=" * 60)
    enriched = 0
    for i, f in enumerate(unique):
        slug = f.get('slug')
        if not slug:
            continue
        print(f"  [{i+1}/{len(unique)}] {slug}...", end=' ')
        details = scrape_founder_detail(slug)
        if details:
            if details.get('city'):
                f['city'] = details['city']
            if details.get('title'):
                f['role'] = details['title']
            if details.get('startup_name'):
                f['startup_name'] = details['startup_name']
            if details.get('linkedin'):
                f['linkedin'] = details['linkedin']
            if details.get('twitter'):
                f['twitter'] = details['twitter']
            if details.get('profile_pic'):
                f['profile_pic'] = details['profile_pic']
            if details.get('full_name'):
                f['name'] = details['full_name']
            enriched += 1
            print("OK")
        else:
            print("no details")
        time.sleep(DELAY)
    print(f"  Enriched: {enriched}/{len([f for f in unique if f.get('slug')])}")

    # ── Save ──
    with open(output_path, 'w', encoding='utf-8') as fp:
        json.dump(unique, fp, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(unique)} new founders to {output_path}")

    # ── Import to database ──
    print("\n" + "=" * 60)
    print("Importing to database")
    print("=" * 60)
    try:
        from app import app, db
        from models import Founder, Startup, StartupFounder
    except ImportError:
        print("  Cannot import app — run from project root")
        return

    with app.app_context():
        # Get existing names
        db_names = {normalize_name(n[0]) for n in db.session.query(Founder.name).all() if n[0]}

        # Get max ID
        all_ids = db.session.query(Founder.founder_id).all()
        numeric_ids = []
        for fid in all_ids:
            try:
                numeric_ids.append(int(fid[0]))
            except (ValueError, TypeError):
                pass
        max_id = max(numeric_ids) if numeric_ids else 200000

        added = 0
        for f in unique:
            name = f.get('name', '').strip()
            if not name or normalize_name(name) in db_names:
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
                current_title=(f.get('role') or 'Fondateur')[:255],
                current_employer=(f.get('startup_name') or '')[:255],
                location=(f.get('city') or '')[:50],
                linkedin_url=(f.get('linkedin') or '')[:255],
                profile_pic=(f.get('profile_pic') or '')[:255],
                link_twitter=(f.get('twitter') or '')[:255],
                company_details_name=(f.get('startup_name') or '')[:50],
            )
            db.session.add(founder)
            db_names.add(normalize_name(name))
            added += 1

            # Link to startup if it exists
            startup_name = f.get('startup_name', '')
            if startup_name:
                startup = db.session.query(Startup).filter(
                    Startup.startup_name.ilike(startup_name)
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

            if added % 50 == 0 and added > 0:
                db.session.commit()
                print(f"  ... committed {added}")

        db.session.commit()
        total = db.session.query(Founder).count()
        print(f"\nDone! Added: {added}")
        print(f"Total founders in DB: {total}")


if __name__ == '__main__':
    main()
