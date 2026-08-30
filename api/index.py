import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import shutil
tmp_db_path = "/tmp/thepulse.db"
source_db_path = os.path.join(ROOT_DIR, "backend", "thepulse.db")
if os.path.exists(source_db_path):
    # Unconditionally copy the database to ensure a pristine mock on every cold start
    # and bypass any DATABASE_URL set by Vercel environment variables
    shutil.copyfile(source_db_path, tmp_db_path)

os.environ["DATABASE_URL"] = f"sqlite:///{tmp_db_path}"
os.environ["PULSE_ALLOW_SQLITE_TESTING"] = "1"

from backend.main import app  # noqa: E402

__all__ = ["app"]
