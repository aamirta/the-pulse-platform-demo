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
            
            # Aggressively search for the database file in case Vercel flattened the directory structure
            found_db_path = None
            for root, dirs, files in os.walk(ROOT_DIR):
                if "thepulse.db" in files:
                    found_db_path = os.path.join(root, "thepulse.db")
                    break
            
            if found_db_path:
                shutil.copyfile(found_db_path, tmp_db_path)
            else:
                # If we still can't find it, we force create_all to at least prevent 500 errors 
                # (even if the tables are empty, it will return an empty list instead of crashing)
                os.environ["PULSE_RUN_STARTUP_MIGRATIONS"] = "1"
            
            os.environ["DATABASE_URL"] = f"sqlite:///{tmp_db_path}"
            
            # Since we manually handle the database path, we must ensure the backend allows SQLite
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
