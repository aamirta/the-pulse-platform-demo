import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import traceback

try:
    import shutil
    tmp_db_path = "/tmp/thepulse.db"
    source_db_path = os.path.join(ROOT_DIR, "backend", "thepulse.db")
    if os.path.exists(source_db_path):
        shutil.copyfile(source_db_path, tmp_db_path)

    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_db_path}"
    os.environ["PULSE_ALLOW_SQLITE_TESTING"] = "1"

    from backend.main import app
except Exception as e:
    error_traceback = traceback.format_exc()
    
    async def app(scope, receive, send):
        await send({
            'type': 'http.response.start',
            'status': 500,
            'headers': [
                (b'content-type', b'text/plain'),
            ],
        })
        await send({
            'type': 'http.response.body',
            'body': f"VERCEL CRASH REPORT:\n\n{error_traceback}".encode('utf-8'),
        })

__all__ = ["app"]
