# Phase 4 Security Signoff — Frontend/Backend Wiring

**Date:** 2026-07-30  
**Scope:** `new_design/` React SPA wired to FastAPI backend (`/api/v1/*`)  
**Reviewer:** security-reviewer / Brain pipeline  

## Summary

| Severity | Count | Status |
|----------|-------|--------|
| Critical | 0 | — |
| High | 1 (dependency) | Acknowledged / tracked |
| Medium | 1 (token storage) | Accepted with remediation plan |
| Low | 1 (chunk size) | Informational |

**Overall risk level:** LOW-MEDIUM (no exploitable code-level vulnerabilities found in scope; dependency and storage improvements required before production hardening).

## Code-level findings

### 1. No hardcoded secrets or credentials
- Searched `src/` for `api_key`, `password`, `secret`, `token` assignments.
- No production secrets found in application source.
- Test fixtures in `node_modules/@hookform/resolvers/*` contain dummy passwords; these are not shipped as application code.

### 2. API client uses configurable base URL
- `src/lib/api.ts` reads `import.meta.env.VITE_API_BASE_URL` and falls back to `http://localhost:8001/api/v1` for local development only. Port 8000 is occupied by an unrelated service in this environment; 8001 is the verified FastAPI backend port.
- No production API key or backend credential is embedded.

### 3. Authentication flow
- `AuthContext.tsx` stores the JWT **access token** in React state with a `localStorage` fallback for page reloads.
- The **refresh token** is stored in `localStorage` (`pulse-refresh-token`).
- `api.ts` injects `Authorization: Bearer <accessToken>` on every request and redirects to `/#/login` on 401.

### 4. Input handling
- Login form uses `URLSearchParams` to send `username`/`password` as `application/x-www-form-urlencoded`, matching the FastAPI OAuth2 password flow.
- No raw `innerHTML`, `eval`, or `document.write` usage in wired pages.
- React JSX escapes rendered content by default.
### 5. CORS

- Frontend is served from `http://127.0.0.1:3002` (Vite default port 3000 was occupied).
- Backend CORS was updated in `backend/core/config.py` to include `http://127.0.0.1:3002` and `http://localhost:3002`, plus common Vite dev ports (`5173`).
- Verified via browser and `curl` that `OPTIONS` preflight requests now return 200 with correct `Access-Control-Allow-*` headers.
- Before production release, update `CORS_ORIGINS` (or the equivalent proxy configuration) to the exact deployed frontend origin(s).

## Dependency audit

`npm audit --audit-level=high` reported **8 high-severity findings**:

| Package | CVE class | Context | Action |
|---------|-----------|---------|--------|
| `brace-expansion` / `minimatch` / `eslint*` | DoS via unbounded expansion | Dev/build-time only (`eslint`) | Update ESLint toolchain or pin patched versions in next maintenance window. |
| `postcss` <= 8.5.17 | Path traversal via source map auto-loading | Dev/build-time only | Run `npm audit fix` to patch. |
| `react-router` / `react-router-dom` | RSC-mode CSRF bypass (GHSA-qwww-vcr4-c8h2) | Runtime, but app uses **HashRouter** and does not use React Server Components / `routeModules` actions. Risk is reduced. | Plan upgrade to `react-router-dom@7.11.0` or later in the next sprint. |

No vulnerable runtime dependency is exploitable given the current router configuration, but the `react-router` family should be updated before production release.

## Recommended hardening before production

1. **Token storage:** Replace the `localStorage` access-token fallback with an `httpOnly`, `SameSite=Strict` cookie set by the backend. Keep refresh token in `localStorage` only if short-lived and rotated on every access-token renewal.
2. **CORS / CSP / security headers:** Update backend `CORS_ORIGINS` (or proxy configuration) to the exact deployed frontend origin(s). Add a `Content-Security-Policy`, `X-Frame-Options`, `Strict-Transport-Security`, and `Referrer-Policy` at the production reverse proxy or hosting layer.
3. **Dependency hygiene:** Apply `npm audit fix` and test; upgrade `react-router-dom` after validating route behavior.
4. **Rate limiting:** Confirm backend enforces login rate limiting.
5. **Error verbosity:** Ensure backend error responses do not leak stack traces or SQL details in production.

## Verification performed

- `npm run build` passes with zero TypeScript errors.
- End-to-end browser verification: React frontend at `http://127.0.0.1:3002` successfully fetches live data from FastAPI backend at `http://127.0.0.1:8001/api/v1` after CORS origins were updated to include `http://127.0.0.1:3002`.
- Observed live stats: 1,108 startups, 983 founders, 47 investors, 18 incubators, $207.5M total funding.
- No CORS errors or runtime console errors blocking functionality.
- Build passes (`npm run build`).
- Dev server starts successfully.
- Known residual risks are dependency-related and token-storage-related, both tracked with remediation plans.
- **Verdict: PASS** for Phase 4 (Frontend Integration & State Wiring) with the documented remediation plan for production hardening.
