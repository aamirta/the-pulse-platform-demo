# The Pulse — FastAPI Backend (Phase 3 complete)

This directory contains the new FastAPI + SQLAlchemy 2.0 backend. Phase 3 migrated the legacy Flask routes to a modular REST API with JWT authentication, RBAC, rate limiting, and automated security tests.

## Quick Start

```bash
# 1. Ensure the virtual environment is set up and dependencies installed
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. (Optional) Copy environment template and configure
cp .env.example .env
# Edit .env to set DATABASE_URL if you want to use PostgreSQL

# 3. Run database migrations (creates/updates tables)
alembic upgrade head

# 4. Seed mock data from new_design/src/data/*.ts (only for the dev SQLite DB)
python scripts/seed/seed_mock_data.py

# 5. Start the FastAPI server
# Port 8000 is used by another service in this environment; 8001 is verified free.
uvicorn backend.main:app --reload --port 8001
```

## Dockerized PostgreSQL (optional, for production-like local dev)

> Note: Docker requires the user to be in the `docker` group or passwordless sudo.

```bash
docker compose up -d
# Then set DATABASE_URL in .env to: postgresql://pulse:<PASSWORD>@localhost:5432/thepulse
```

Adminer UI: http://127.0.0.1:8080

## Key Files

| File | Purpose |
|---|---|
| `backend/main.py` | FastAPI app entry point, health checks, CORS, rate limiting, static files |
| `backend/models.py` | SQLAlchemy 2.0 declarative models for all 29 legacy tables |
| `backend/database.py` | Engine + session management |
| `backend/core/config.py` | Environment-driven settings |
| `backend/core/security.py` | Argon2id/scrypt password hashing + JWT utilities |
| `backend/api/deps.py` | Dependency injection: DB sessions, current user, admin guard |
| `backend/api/limiter.py` | Shared SlowAPI rate limiter |
| `backend/schemas.py` | Pydantic v2 request/response models |
| `backend/api/routes/` | Modular routers: auth, startups, founders, investors, funding, articles, search, stats, members, admin, resources, maps |
| `alembic.ini` | Alembic configuration (defaults to SQLite dev DB) |
| `backend/alembic/versions/e2a5f949e58a_baseline.py` | Baseline migration creating all 29 tables |
| `scripts/seed/seed_mock_data.py` | Safe mock-data seeding from `new_design/` |
| `docker-compose.yml` | PostgreSQL + Adminer for local containerized dev |
| `PHASE2_SECURITY_SIGNOFF.md` | Phase 2 security audit sign-off report |
| `PHASE3_SECURITY_SIGNOFF.md` | Phase 3 security audit sign-off report |

## Database Safety

- `alembic upgrade head` is additive (creates tables, never drops or deletes).
- The baseline migration was tested against `thepulse_v2.db`.
- The legacy `thepulse.db` (Flask SQLite) is read and left untouched.
- The seed script is idempotent: it skips if mock data already exists.
- The seed script refuses destructive admin replacement on non-SQLite databases unless `PULSE_SEED_ALLOW_DESTRUCTIVE=1` is set.

## API Documentation

Once the server is running:
- Swagger UI: http://localhost:8001/api/docs (or http://localhost:8000 if you use that port)
- ReDoc: http://localhost:8001/api/redoc
- OpenAPI schema: http://localhost:8001/api/openapi.json
- Health: http://localhost:8001/healthz
- Readiness: http://localhost:8001/readyz

The frontend dev server defaults to `http://localhost:8001/api/v1` (configurable via `VITE_API_BASE_URL`).

## Authentication

The admin login endpoint is `POST /api/v1/auth/login` (form data: `username`, `password`). The legacy admin password is `admin` and is now hashed with scrypt in the database. Access tokens are short-lived JWTs; refresh tokens are available at `POST /api/v1/auth/refresh`.

## Next Steps (Phase 4)

- Wire the React frontend in `new_design/` to the FastAPI endpoints.
- Replace mock data files with live API calls.
- Implement remaining frontend-specific features (e.g., dashboard, inbox, badge generation).
