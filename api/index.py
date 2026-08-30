import os
import sys
import traceback

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

_real_app = None

async def app(scope, receive, send):
    """Lazy ASGI wrapper to catch and display Vercel boot errors."""
    global _real_app
    
    try:
        if _real_app is None:
            import shutil
            tmp_db_path = "/tmp/thepulse.db"
            source_db_path = os.path.join(ROOT_DIR, "backend", "thepulse.db")
            
            if os.path.exists(source_db_path):
                shutil.copyfile(source_db_path, tmp_db_path)
            
            os.environ["DATABASE_URL"] = f"sqlite:///{tmp_db_path}"
            os.environ["PULSE_ALLOW_SQLITE_TESTING"] = "1"
            
            from backend.main import app as fastapi_app
            _real_app = fastapi_app
            
        await _real_app(scope, receive, send)
        
    except Exception as e:
        error_traceback = traceback.format_exc()
        if scope["type"] == "http":
            await send({
                'type': 'http.response.start',
                'status': 500,
                'headers': [(b'content-type', b'text/plain')],
            })
            await send({
                'type': 'http.response.body',
                'body': f"VERCEL CRASH REPORT:\n\n{error_traceback}".encode('utf-8'),
            })

__all__ = ["app"]
