"""
Import startups from ADD (Agence de Développement du Digital) XLSX files.
Sources: data.gov.ma
- bdd-startups-add_2024.xlsx (1028 startups)
- donnees-sur-les-startups.xlsx (230 startups)
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import openpyxl
from app import app, db
from models import Startup


def normalize_name(name):
    """Normalize startup name for dedup comparison."""
    if not name:
        return ''
    return name.strip().lower().replace('-', ' ').replace('_', ' ')


def load_xlsx(filepath, name_col, city_col, sector_col, extra_cols=None):
    """Load startups from an XLSX file."""
    wb = openpyxl.load_workbook(filepath, read_only=True)
    ws = wb.active

    # Read all rows at once before closing
    all_rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if not all_rows:
        return []

    header_row = all_rows[0]
    data_rows = all_rows[1:]

    # Find column indices
    col_map = {}
    for i, h in enumerate(header_row):
        if h:
            col_map[h.strip()] = i

    startups = []
    for row in data_rows:
        name = row[col_map[name_col]] if name_col in col_map and col_map[name_col] < len(row) else None
        city = row[col_map[city_col]] if city_col in col_map and col_map[city_col] < len(row) else None
        sector = row[col_map[sector_col]] if sector_col in col_map and col_map[sector_col] < len(row) else None

        if not name or not str(name).strip():
            continue

        entry = {
            'name': str(name).strip(),
            'city': str(city).strip() if city else None,
            'sector': str(sector).strip() if sector else None,
        }

        if extra_cols:
            for col_name, key in extra_cols.items():
                idx = col_map.get(col_name)
                entry[key] = str(row[idx]).strip() if idx is not None and idx < len(row) and row[idx] else None

        startups.append(entry)

    return startups


def import_to_db(startups_data):
    """Import startups into the database, skipping duplicates."""
    with app.app_context():
        # Get existing startup names for dedup
        existing = db.session.query(Startup.startup_name).all()
        existing_names = {normalize_name(s[0]) for s in existing if s[0]}

        added = 0
        skipped = 0

        # Get max ID
        max_id = db.session.query(db.func.max(Startup.startup_id)).scalar() or 0

        for s in startups_data:
            norm = normalize_name(s['name'])
            if norm in existing_names:
                skipped += 1
                continue

            max_id += 1
            startup = Startup(
                startup_id=max_id,
                startup_name=s['name'],
                location=s.get('city'),
                sector=s.get('sector'),
                stage=s.get('phase'),
                country_code='MA',
                hq_country='Morocco',
                type='startup',
            )
            db.session.add(startup)
            existing_names.add(norm)
            added += 1

            if added % 100 == 0:
                db.session.commit()
                print(f"  ... committed {added} so far")

        db.session.commit()
        print(f"\nDone! Added: {added}, Skipped (duplicates): {skipped}")
        return added, skipped


def main():
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')

    # Load file 1: BDD Startups ADD 2024 (1028 startups)
    file1 = os.path.join(data_dir, 'bdd-startups-add_2024.xlsx')
    print(f"Loading {file1}...")
    startups1 = load_xlsx(
        file1,
        name_col='Raison social',
        city_col='City',
        sector_col='Main sector',
        extra_cols={'BD source': 'source'}
    )
    print(f"  Found {len(startups1)} startups")

    # Load file 2: Données sur les startups (230 startups)
    file2 = os.path.join(data_dir, 'donnees-sur-les-startups.xlsx')
    print(f"Loading {file2}...")
    startups2 = load_xlsx(
        file2,
        name_col='Nom de la Startup',
        city_col='Ville',
        sector_col='Secteur',
        extra_cols={'Phase': 'phase'}
    )
    print(f"  Found {len(startups2)} startups")

    # Merge: file1 first, then file2 (file2 has phase info)
    seen = set()
    merged = []
    for s in startups1:
        norm = normalize_name(s['name'])
        if norm not in seen:
            seen.add(norm)
            merged.append(s)

    for s in startups2:
        norm = normalize_name(s['name'])
        if norm not in seen:
            seen.add(norm)
            merged.append(s)
        else:
            # Update phase info if available
            if s.get('phase'):
                for m in merged:
                    if normalize_name(m['name']) == norm:
                        m['phase'] = s['phase']
                        break

    print(f"\nMerged: {len(merged)} unique startups")
    print("Importing to database...")
    import_to_db(merged)


if __name__ == '__main__':
    main()
