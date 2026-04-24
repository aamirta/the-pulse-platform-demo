"""
CLI wrapper that uses the repo-level `badge_generator` module so
the CLI and the Flask route always stay in sync.

Usage:
    python generate_badge.py <photo> <out> "<full name>" "<role>"
    python generate_badge.py   # defaults to Simohammed Damiri
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from badge_generator import generate


if __name__ == '__main__':
    if len(sys.argv) >= 5:
        photo, out, name, role = sys.argv[1:5]
    else:
        photo = ('/Users/damirimohamed/Desktop/Github/ThePulsePlateform/'
                 'static/images/founders/SimoDamiri.jpeg')
        out   = os.path.join(os.path.dirname(__file__), 'badge_simo.png')
        name  = 'Simohammed Damiri'
        role  = 'Founder & CEO, Nessiam'

    # Optional category arg to force accent colour
    category = sys.argv[5] if len(sys.argv) >= 6 else None

    generate(photo, name, role,
             out=out,
             category=category,
             ref_url='https://www.thepulse.ma/badge')
    print(f"Wrote {out}")
