"""
Import GITEX Africa 2026 Morocco exhibitors into the database.
Source: exhibitors.gitexafrica.com (476+ Moroccan exhibitors including the Morocco 300 startups)
"""
import os
import sys
import csv
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app, db
from models import Startup


def normalize_name(name):
    if not name:
        return ''
    return name.strip().lower().replace('-', ' ').replace('_', ' ')


def clean_description(desc):
    """Clean HTML tags from description."""
    if not desc:
        return None
    import re
    desc = re.sub(r'<[^>]+>', ' ', desc)
    desc = re.sub(r'\s+', ' ', desc).strip()
    # Fix encoding issues
    desc = desc.replace('â\x80\x99', "'").replace('â\x80\x93', '–').replace('Ã©', 'é')
    desc = desc.replace('Ã¨', 'è').replace('Ã ', 'à').replace('Ã®', 'î')
    desc = desc.replace('Ã´', 'ô').replace('Ã¹', 'ù').replace('Ã¢', 'â')
    desc = desc.replace('Ã§', 'ç').replace('Ã«', 'ë').replace('Ã¯', 'ï')
    return desc


EXCLUDED_NAMES = {
    '2M TV', 'AMCI (Morocco Agency for International Cooperation',
    'Agence de Developpement du Digital - #ADD', 'Al Akhawayn University',
    'Al Barid bank', 'Attijariwafa bank', 'CDG', 'CDG BEP', 'CDG INVEST',
    'CDG Incept', 'CIH BANK', 'Enterprise Services CDG',
    'FEDERATION APEBI', 'GROUPE BARID AL-MAGHRIB', 'Groupe BCP',
    'Groupe Maroc Telecom', 'INWI', 'Mastercard Foundation',
    'OCP Group', 'Orange', 'SAHAM BANK', 'TANGER MED SPECIAL AGENCY',
    'MINISTRY MOU STAGE',
}


def is_startup(entry):
    """Filter out non-startup entities (banks, government, large corps, media)."""
    name = entry.get('name', '')
    if name in EXCLUDED_NAMES:
        return False
    name_lower = name.lower()
    # Exclude obvious large institutions
    exclude_keywords = [
        'bank', 'banque', 'ministry', 'ministère', 'université', 'university',
        'ONCF', 'ONEE', 'ONDA', 'SNRT', 'RAM ',
    ]
    for kw in exclude_keywords:
        if kw.lower() in name_lower:
            return False
    return True


def main():
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'gitex_africa_2026_morocco_exhibitors.csv')

    print(f"Loading {csv_path}...")
    all_entries = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            all_entries.append(row)

    # Filter startups only
    entries = [e for e in all_entries if is_startup(e)]
    print(f"Total exhibitors: {len(all_entries)}, Startups after filtering: {len(entries)}")

    with app.app_context():
        existing = db.session.query(Startup.startup_name).all()
        existing_names = {normalize_name(s[0]) for s in existing if s[0]}
        max_id = db.session.query(db.func.max(Startup.startup_id)).scalar() or 0

        added = 0
        skipped = 0

        for entry in entries:
            name = entry.get('name', '').strip()
            if not name:
                continue

            norm = normalize_name(name)
            if norm in existing_names:
                skipped += 1
                continue

            max_id += 1
            description = clean_description(entry.get('description'))
            sectors = entry.get('sectors', '').strip()

            startup = Startup(
                startup_id=max_id,
                startup_name=name,
                description=description,
                sector=sectors[:255] if sectors else None,
                all_industries=sectors if sectors else None,
                country_code='MA',
                hq_country='Morocco',
                type='startup',
                universe='GITEX Africa 2026',
            )
            db.session.add(startup)
            existing_names.add(norm)
            added += 1

            if added % 100 == 0:
                db.session.commit()
                print(f"  ... committed {added} so far")

        db.session.commit()
        print(f"\nDone! Added: {added}, Skipped (duplicates): {skipped}")


if __name__ == '__main__':
    main()
