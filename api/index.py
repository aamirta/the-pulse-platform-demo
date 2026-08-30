"""Vercel serverless entrypoint for the FastAPI backend.

Vercel discovers this file as a Python function and serves the module-level
``app`` as an ASGI application. ``vercel.json`` rewrites every API, health and
docs path onto it; everything else is served from the static build in ``public``.
"""

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    # Prepend, not append: backend/api/routes/members.py imports the top-level
    # badge_generator module, which only resolves once the repo root is on the path.
    sys.path.insert(0, ROOT_DIR)

if not os.environ.get("DATABASE_URL"):
    import shutil
    tmp_db_path = "/tmp/thepulse.db"
    source_db_path = os.path.join(ROOT_DIR, "backend", "thepulse.db")
    if os.path.exists(source_db_path) and not os.path.exists(tmp_db_path):
        shutil.copyfile(source_db_path, tmp_db_path)
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_db_path}"
    os.environ["PULSE_ALLOW_SQLITE_TESTING"] = "1"
from backend.main import app  # noqa: E402

__all__ = ["app"]
