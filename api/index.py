"""Vercel serverless entrypoint.

The deployment has no Postgres attached, so the app runs against the SQLite
snapshot shipped alongside it (see ``scripts/demo/build_demo_db.py``). SQLite
cannot be written to on the read-only function filesystem, so the file is
copied into /tmp on the first request of a cold start.
"""

import logging
import os
import shutil
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

logger = logging.getLogger("pulse.vercel")

TMP_DB_PATH = "/tmp/thepulse.db"

# Where the bundled database may land. The build includes it at the first path;
# the others cover a runtime that flattens the tree. This used to be an
# os.walk() of the whole deployment on every cold start, which scanned
# node_modules to find a file whose location is known.
_CANDIDATE_DB_PATHS = (
    os.path.join(ROOT_DIR, "backend", "thepulse.db"),
    os.path.join(ROOT_DIR, "thepulse.db"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "thepulse.db"),
)

_real_app = None


def _prepare_database() -> None:
    """Point the app at a writable copy of the bundled SQLite snapshot."""
    source = next((path for path in _CANDIDATE_DB_PATHS if os.path.exists(path)), None)

    if source:
        if not os.path.exists(TMP_DB_PATH):
            shutil.copyfile(source, TMP_DB_PATH)
    else:
        # Without the snapshot the schema has to be created, so the API answers
        # with empty collections rather than failing on a missing table.
        logger.error("bundled database not found; starting with an empty schema")
        os.environ["PULSE_RUN_STARTUP_MIGRATIONS"] = "1"

    os.environ["DATABASE_URL"] = f"sqlite:///{TMP_DB_PATH}"
    # The path is handled here, so the backend's Postgres-only guard is waived.
    os.environ["PULSE_ALLOW_SQLITE_TESTING"] = "1"


async def app(scope, receive, send):
    """Lazy ASGI wrapper: build the app on first use, and never leak a crash."""
    global _real_app

    try:
        if _real_app is None:
            _prepare_database()
            from backend.main import app as fastapi_app

            _real_app = fastapi_app

        await _real_app(scope, receive, send)
        return
    except Exception:
        # Logged for the platform, never described to the caller: a traceback
        # in the response body is exactly the "HTTP 500:" detail the editorial
        # review asked to keep off the screen.
        logger.exception("failed to start or serve the application")

    if scope["type"] == "http":
        await send(
            {
                "type": "http.response.start",
                "status": 503,
                "headers": [(b"content-type", b"application/json; charset=utf-8")],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b'{"detail":"service_unavailable"}',
            }
        )


__all__ = ["app"]
