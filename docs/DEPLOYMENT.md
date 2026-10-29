# DEPLOYMENT.md

> Related: [ARCHITECTURE §10–11](ARCHITECTURE.md) · [TESTING](TESTING.md) · [PROJECT_RULES](PROJECT_RULES.md)
> Frontend and backend are **separate deployments**. Do not assume they share a host.

## 1. Environment variables

### Backend (`backend/`, see `.env.example`)

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8000` | Set automatically by Heroku |
| `ELEXON_BASE_URL` | `https://data.elexon.co.uk/bmrs/api/v1` | Elexon Insights API base (verify in Phase 1) |
| `ELEXON_TIMEOUT_SECONDS` | `30` | per request |
| `ELEXON_MAX_RETRIES` | `3` | |
| `ELEXON_CHUNK_DAYS` | `7` | request window size |
| `DELIVERY_WINDOW_START` / `DELIVERY_WINDOW_END` | `2026-01-01` / `2026-01-31` | inclusive dates (Q-01) |
| `DECISION_CUTOFF_LOCAL_TIME` | `09:00` | provisional (Q-02) |
| `DECISION_TIMEZONE` | `Europe/London` | |
| `FORECAST_PUBLISH_LOOKBACK_DAYS` | `2` | |
| `CACHE_TTL_SECONDS` | `86400` | |
| `CACHE_DIR` | `/tmp/wind-cache` | P1 snapshot |
| `PRELOAD_ON_STARTUP` | `true` | |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,http://localhost:8080` | comma-separated; add the Vercel URL in production |
| `LOG_LEVEL` | `INFO` | |

### Frontend (`frontend/`)

| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend origin, no trailing slash. **Baked in at build time** |

No secrets exist in this project. Never commit `.env`.

## 2. Local development (without Docker)
```bash
# Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp ../.env.example .env        # optional
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend && npm ci && npm run dev    # http://localhost:5173
```

## 3. Dockerfile responsibilities

| File | Does | Must not |
|---|---|---|
| `backend/Dockerfile` | Install pinned Python deps, copy `app/`, create non-root user, `CMD uvicorn ... --port ${PORT:-8000}`, `HEALTHCHECK` on `/api/health` | contain secrets or tests |
| `frontend/Dockerfile` | Stage 1: `npm ci && npm run build` with `ARG VITE_API_BASE_URL`; Stage 2: nginx serves `dist`, SPA fallback | run the dev server |

## 4. Docker Compose
```bash
cp .env.example .env
docker compose up --build        # UI http://localhost:8080, API http://localhost:8000/docs
docker compose down
```
Services:
- `backend`: port 8000, Python healthcheck on `/api/health`, runs as non-root user `appuser`.
- `frontend`: port 8080, `depends_on: backend: condition: service_healthy`, build arg `VITE_API_BASE_URL=http://localhost:8000`, served by `nginxinc/nginx-unprivileged:alpine-slim`.
- `CORS_ALLOWED_ORIGINS`: configured for `http://localhost:8080,http://localhost:5173,http://127.0.0.1:8080,http://127.0.0.1:5173`.

> [!NOTE]
> On Windows development hosts, ensure Docker Desktop is started before running `docker compose up --build`. The Docker CLI version is 29.6.1.

## 5. Backend hosting — Heroku (container stack)
Files: `heroku.yml` at repo root:
```yaml
build:
  docker:
    web: backend/Dockerfile
```
Steps (summary):
1. `heroku create <anonymous-app-name>` then `heroku stack:set container`.
2. `heroku config:set CORS_ALLOWED_ORIGINS=https://<vercel-url> ...` (all variables from §1 that differ from defaults).
3. Deploy: `git push heroku main` (or GitHub integration).
4. Check `https://<app>.herokuapp.com/api/health` and `/api/meta`.

Notes: Eco/Basic dynos cost money and Eco dynos sleep when idle (first request is slow; preload helps). Use an anonymous app name. If Heroku is not available, see §7.

## 6. Frontend hosting — Vercel
1. Import the GitHub repo; **Root Directory = `frontend`**; framework Vite; build `npm run build`; output `dist`.
2. Set `VITE_API_BASE_URL=https://<heroku-app>.herokuapp.com` (Production + Preview).
3. `frontend/vercel.json`: SPA rewrite to `/index.html`.
4. Redeploy after changing the env var (it is baked in at build time).
5. Add the Vercel production URL to backend `CORS_ALLOWED_ORIGINS`.

> [!NOTE]
> When deploying via Vercel CLI (`npx vercel`), authenticate via `vercel login` or set `VERCEL_TOKEN` in CI/CD.

## 7. Alternative Hosting Platforms
If Heroku is not available due to paid dyno requirements:
- **Render.com / Fly.io:** Directly deploys `backend/Dockerfile` with container healthchecks and auto-injects `$PORT`.
- **Vercel (Backend + Frontend Monorepo):** Exposing the FastAPI ASGI app via Python serverless functions. Notice that in-memory cache resets on cold starts.
- **Self-Hosted / VPS Docker Compose:** Run `docker compose up -d` on any Linux VPS (Ubuntu/Debian) running Docker Engine.

## 8. CORS and health checks
- CORS: allow-list only; methods `GET, OPTIONS`; no credentials. Verify with `curl -H "Origin: https://<vercel-url>" -i <backend>/api/meta` → `access-control-allow-origin` present; a different origin → absent.
- Health: `/api/health` (no upstream call). Docker `HEALTHCHECK` and Heroku use it. `data_loaded=false` just after boot is normal.

## 9. Verification checklist

**Production build**
- [x] `npm run build` succeeds with `VITE_API_BASE_URL` configurable at build time
- [x] Dockerfiles validated (`backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf`, `docker-compose.yml`, `heroku.yml`, `frontend/vercel.json`)
- [x] Local smoke verification (`scripts/smoke.sh` and `scripts/smoke.py`) passing 100% against backend

**Public URLs (Pending platform credentials)**
- [ ] Backend `/api/health` → `status: ok`
- [ ] Backend `/api/summary` returns non-null MAE with real data
- [ ] `scripts/smoke.sh https://<backend>` passes
- [ ] Frontend loads, KPIs and chart appear, no CORS or mixed-content errors in the console
- [ ] Cold-start behaviour acceptable (loading message, then data)

**Incognito access**
- [ ] Frontend URL opens in an incognito window without login
- [ ] Backend `/docs` or `/api/health` opens in incognito
- [ ] GitHub repo opens in incognito (public)
- [ ] YouTube video opens in incognito (unlisted link works)
- [ ] No personal info visible on any page (anonymity rule R21)
