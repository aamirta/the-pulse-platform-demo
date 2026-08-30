"""
Create the badge_generations audit table on the prod DB.
Idempotent — uses CREATE TABLE IF NOT EXISTS.

Run once after deploying the app code that adds the BadgeGeneration model.

Usage:
    python scripts/create_badge_generations_table.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL environment variable is required")
from sqlalchemy import create_engine, text

engine = create_engine(os.environ['DATABASE_URL'])

DDL = '''
CREATE TABLE IF NOT EXISTS badge_generations (
    id          SERIAL PRIMARY KEY,
    member_id   INTEGER REFERENCES pulse_members(id) ON DELETE SET NULL,
    full_name   VARCHAR(150),
    category    VARCHAR(50),
    role_label  VARCHAR(255),
    ref_url     VARCHAR(255),
    ip          VARCHAR(45),
    user_agent  VARCHAR(255),
    created_at  TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_badge_generations_created_at
    ON badge_generations (created_at DESC);
'''

with engine.begin() as tx:
    for stmt in [s.strip() for s in DDL.split(';') if s.strip()]:
        tx.execute(text(stmt))
print("✓ badge_generations table ready")
