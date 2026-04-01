"""
Scrape and download investor logos using domain-based APIs.
Uses Clearbit Logo API (free) with Google Favicon as fallback.
"""
import os
import re
import requests
import time
from app import app, db
from models import Investor

LOGO_DIR = os.path.join(os.path.dirname(__file__), 'static', 'images', 'investors')
os.makedirs(LOGO_DIR, exist_ok=True)

def clean_domain(domain):
    """Extract clean domain from a URL or domain string."""
    if not domain:
        return None
    domain = domain.strip()
    domain = re.sub(r'^https?://', '', domain)
    domain = re.sub(r'^www\.', '', domain)
    domain = domain.split('/')[0]
    return domain if domain else None

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

def fetch_logo_for_investor(investor):
    """Try to fetch a logo for an investor using various APIs."""
    domain = clean_domain(investor.domain)
    if not domain:
        print(f"  No domain for {investor.investor_name}, skipping")
        return None

    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', investor.investor_name.lower().strip())
    filename = f"{safe_name}.png"
    filepath = os.path.join(LOGO_DIR, filename)

    if os.path.exists(filepath):
        print(f"  Logo already exists: {filename}")
        return f"/static/images/investors/{filename}"

    # Try Clearbit Logo API
    clearbit_url = f"https://logo.clearbit.com/{domain}"
    print(f"  Trying Clearbit for {domain}...")
    if download_image(clearbit_url, filepath):
        print(f"  Success: {filename}")
        return f"/static/images/investors/{filename}"

    # Try Google Favicon API (high-res)
    google_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
    print(f"  Trying Google Favicon for {domain}...")
    if download_image(google_url, filepath):
        print(f"  Success (favicon): {filename}")
        return f"/static/images/investors/{filename}"

    print(f"  No logo found for {investor.investor_name}")
    return None

def main():
    with app.app_context():
        investors = Investor.query.filter(
            (Investor.logo_url == None) | (Investor.logo_url == '')
        ).all()

        print(f"Found {len(investors)} investors without logos\n")

        updated = 0
        for investor in investors:
            print(f"Processing: {investor.investor_name}")
            logo_path = fetch_logo_for_investor(investor)
            if logo_path:
                investor.logo_url = logo_path
                db.session.commit()
                updated += 1
                print(f"  Updated DB with {logo_path}")
            time.sleep(0.5)

        print(f"\nDone! Updated {updated}/{len(investors)} investor logos.")

if __name__ == '__main__':
    main()
