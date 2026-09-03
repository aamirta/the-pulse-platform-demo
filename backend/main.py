"""FastAPI application entry point."""

import contextlib
import os
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from backend.api.limiter import limiter
from backend.api.routes import (
    admin,
    articles,
    assistant,
    auth,
    cofounders,
    dashboard,
    dealroom,
    dealroom_posts,
    entity_claims,
    experts,
    founders,
    funding_rounds,
    graph,
    incubators,
    investors,
    maps,
    members,
    resources,
    search,
    startups,
    stats,
    talents,
)
from backend.core.config import PROJECT_ROOT, settings
from backend.database import engine
from backend.models import Base


def _run_migrations() -> None:
    """Apply Alembic migrations on startup, stamping the baseline for legacy databases."""
    try:
        from sqlalchemy import inspect

        from alembic import command, config

        # Resolve alembic.ini from the project root rather than the process CWD.
        # Serverless runtimes invoke the app from an arbitrary working directory,
        # where a relative path silently misses and every migration is skipped.
        alembic_cfg = config.Config(str(PROJECT_ROOT / "alembic.ini"))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

        with engine.connect() as connection:
            inspector = inspect(connection)
            tables = inspector.get_table_names()
            has_version = "alembic_version" in tables
            has_user = "User" in tables

            if not has_version and has_user:
                command.stamp(alembic_cfg, "head", sql=False)
                return

        command.upgrade(alembic_cfg, "head")
    except Exception as exc:
        print(f"Startup migration skipped/warning: {exc}")


# Run migrations on startup, then create any tables the migrations may not cover.
# Both steps are skipped when PULSE_RUN_STARTUP_MIGRATIONS is "0", which is how
# the Vercel deployment is configured: a serverless function would otherwise pay
# for a schema inspection on every cold start, and concurrent instances would
# race each other to hold the Alembic lock. There, migrations are applied once
# from a developer machine against the hosted database before deploying.
if os.environ.get("PULSE_RUN_STARTUP_MIGRATIONS", "1") != "0":
    _run_migrations()
    Base.metadata.create_all(bind=engine, checkfirst=True)

app = FastAPI(
    title="The Pulse API",
    description="Modern FastAPI backend for the Moroccan startup ecosystem platform.",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def _security_headers_middleware(request: Request, call_next: Any) -> Response:
    """Add baseline security headers to every response."""
    response: Response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    # HSTS is intentionally omitted here; it should be added by the TLS terminator
    # (reverse proxy / load balancer) to avoid forcing HTTPS on local dev.
    return response


@app.get("/healthz", tags=["health"])
def healthz() -> str:
    """Liveness probe."""
    return "ok"


@app.get("/readyz", tags=["health"])
def readyz() -> JSONResponse:
    """Readiness probe - verifies database connectivity."""
    try:
        from sqlalchemy import text

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return JSONResponse(content={"status": "ready"}, status_code=200)
    except Exception:
        return JSONResponse(
            content={"status": "not ready"},
            status_code=503,
        )


@app.get("/api/v1/ping", tags=["health"])
def ping() -> dict[str, Any]:
    """Simple API ping."""
    return {"message": "pong"}


# ---------------------------------------------------------------------------
# Domain routers
# ---------------------------------------------------------------------------
app.include_router(auth.router, prefix="/api/v1")
app.include_router(startups.router, prefix="/api/v1")
app.include_router(founders.router, prefix="/api/v1")
app.include_router(experts.router, prefix="/api/v1")
app.include_router(cofounders.router, prefix="/api/v1")
app.include_router(talents.router, prefix="/api/v1")
app.include_router(investors.router, prefix="/api/v1")
app.include_router(funding_rounds.router, prefix="/api/v1")
app.include_router(incubators.router, prefix="/api/v1")
app.include_router(articles.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")
app.include_router(graph.router, prefix="/api/v1")
app.include_router(members.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(resources.router, prefix="/api/v1")
app.include_router(maps.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(assistant.router, prefix="/api/v1")
app.include_router(dealroom.router, prefix="/api/v1")
app.include_router(dealroom_posts.router, prefix="/api/v1")
app.include_router(entity_claims.router, prefix="/api/v1")

# Serve static files (React build, uploads, etc.)
with contextlib.suppress(Exception):
    app.mount(
        "/static",
        StaticFiles(directory=str(settings.UPLOAD_FOLDER.parent)),
        name="static",
    )
