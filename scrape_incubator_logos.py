"""
Scrape and download incubator logos using domain-based APIs.
Uses Clearbit Logo API with Google Favicon as fallback.
Then updates the database image_url field.
"""
import os
import re
import requests
import time
from app import app, db
from models import Incubator

LOGO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images', 'incubators')
os.makedirs(LOGO_DIR, exist_ok=True)

# Known websites for Moroccan incubators without logos
INCUBATOR_DOMAINS = {
    57: '212founders.co',
    12: 'lastartupfactory.co',
    8: 'hseven.co',
    4: 'startupmaroc.org',
    11: 'cfcim.org',
    13: 'impactlab.africa',
    18: 'mfoundersprogram.com',
    30: 'alxafrica.com',
    32: 'ceed-global.org',
    33: 'climatelaunchpad.org',
    43: 'orangefab.com',
    44: 'plugandplaytechcenter.com',
    48: 'um6p.ma',
    56: 'enactus.org',
    10: 'um5.ac.ma',
    28: 'akwagroup.com',
    29: 'um6p.ma',
    39: 'happyventures.co',
    40: 'incubooster.com',
    42: 'snrt.ma',
    45: 'rdmaroc.com',
    47: 'skytrend.ma',
    49: 'mrtb.ma',
    51: 'um6p.ma',
    52: 'um6p.ma',
    53: 'um6p.ma',
    54: 'um6p.ma',
    55: 'um6p.ma',
    14: 'reseau-entreprendre.org',
    31: 'um5.ac.ma',
    34: 'um6p.ma',
    35: 'clustermenara.ma',
    38: 'generation-entrepreneurs.ma',
    46: 'sbs-education.com',
}

# External URLs (from start-up.ma S3 bucket) for specific incubators
KNOWN_URLS = {
    # StartGate logo from start-up.ma
}

def download_image(url, filepath, timeout=10):
    """Download an image from a URL to a local filepath."""
    try:
        resp = requests.get(url, timeout=timeout, stream=True)
        if resp.status_code == 200 and len(resp.content) > 500:
            content_type = resp.headers.get('content-type', '')
            if 'image' in content_type or 'octet-stream' in content_type:
                with open(filepath, 'wb') as f:
                    f.write(resp.content)
                return True
    except Exception as e:
        print(f"  Error downloading {url}: {e}")
    return False


def main():
    with app.app_context():
        incubators = Incubator.query.filter(
            (Incubator.image_url == None) | (Incubator.image_url == '')
        ).all()

        print(f"Found {len(incubators)} incubators without logos\n")

        updated = 0
        for inc in incubators:
            domain = INCUBATOR_DOMAINS.get(inc.incubator_id)
            if not domain:
                print(f"No domain for {inc.incubator} (id={inc.incubator_id}), skipping")
                continue

            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', inc.incubator.lower().strip())
            filename = f"{safe_name}.png"
            filepath = os.path.join(LOGO_DIR, filename)

            if os.path.exists(filepath):
                print(f"Already exists: {inc.incubator}")
                logo_path = f"/static/images/incubators/{filename}"
                inc.image_url = logo_path
                db.session.commit()
                updated += 1
                continue

            # Try Clearbit
            clearbit_url = f"https://logo.clearbit.com/{domain}"
            print(f"Trying Clearbit for {inc.incubator} ({domain})...")
            if download_image(clearbit_url, filepath):
                print(f"  OK: {filename}")
                logo_path = f"/static/images/incubators/{filename}"
                inc.image_url = logo_path
                db.session.commit()
                updated += 1
                continue

            # Try Google Favicon
            google_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
            print(f"  Trying Google Favicon...")
            if download_image(google_url, filepath):
                print(f"  OK (favicon): {filename}")
                logo_path = f"/static/images/incubators/{filename}"
                inc.image_url = logo_path
                db.session.commit()
                updated += 1
                continue

            print(f"  FAILED: {inc.incubator}")
            time.sleep(0.3)

        print(f"\nDone! Updated {updated}/{len(incubators)} incubator logos.")


if __name__ == '__main__':
    main()
