# UK Wind Generation Forecast Accuracy Dashboard

> **Status: documentation phase.** The documentation pack is complete; application code is not written yet. Sections marked *(planned)* describe the intended result. Update this README as implementation proceeds.

## Overview
A web app for electricity procurement teams who buy power on the UK **day-ahead market**. It shows, for **January 2026**, the national wind forecast that was *available at the decision cutoff* next to the actual wind generation, and measures forecast accuracy (MAE, RMSE, bias). Data comes only from Elexon (FUELHH actuals for `fuelType = WIND`, WINDFOR forecasts).

## Business problem and solution
Buyers decide one day before delivery how much extra power to buy after counting on wind. Wind is uncertain, so they need to know (1) which forecast they had at decision time and (2) how large the typical error is. The dashboard picks, for every hourly period (evaluated at top-of-hour timestamps), the latest forecast published at or before the cutoff (default: 09:00 `Europe/London` on the day before delivery — a **provisional assumption**, configurable) and compares it to the actual output.

## Main features
- Real Elexon data, no fabricated values
- Cutoff time selector (re-computes accuracy for any morning/afternoon cutoff time)
- KPI cards: MAE, RMSE, mean error (bias), matched periods *(P1: P90 error, MAE %, coverage)*
- Actual vs forecast time-series chart with forecast publication time in tooltips
- Records table with sorting and pagination
- Visible assumptions, data-quality counts and provenance
- *(P1)* daily view, forecast vintages, table filters, chart zoom

## Technology stack
React + Vite + TypeScript · Recharts · TanStack Query · Python 3.12 + FastAPI + httpx + Pydantic · pytest · Vitest + React Testing Library · Docker + Docker Compose · Vercel (frontend) + Heroku container (backend). No database.

## Project structure *(planned)*
```text
.
├── README.md
├── docker-compose.yml
├── heroku.yml
├── .env.example
├── docs/                    # documentation pack (see docs/INDEX.md)
├── scripts/smoke.sh         # end-to-end smoke test
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt, requirements-dev.txt
│   ├── app/
│   │   ├── main.py, config.py
│   │   ├── api/             # routes, schemas, error handlers
│   │   ├── services/        # elexon_client.py, data_store.py
│   │   └── domain/          # models, normalize, cutoff, selection, matching, metrics (pure)
│   └── tests/               # unit/, integration/, fixtures/
└── frontend/
    ├── Dockerfile, nginx.conf, vercel.json
    ├── package.json, vite.config.ts
    └── src/                 # api/, components/, hooks/, lib/, styles/, types/
```

## Local setup *(planned)*
```bash
# Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm ci && npm run dev      # http://localhost:5173
```

## Environment variables
Full list with defaults: [docs/DEPLOYMENT.md §1](docs/DEPLOYMENT.md). Copy `.env.example` to `.env`. Main ones: `ELEXON_BASE_URL`, `DECISION_CUTOFF_LOCAL_TIME`, `DELIVERY_WINDOW_START/END`, `CORS_ALLOWED_ORIGINS`, `VITE_API_BASE_URL`. No secrets are needed (Elexon's API is public).

## Docker
```bash
cp .env.example .env
docker compose up --build      # UI: http://localhost:8080   API docs: http://localhost:8000/docs
```

## Tests
```bash
cd backend && pytest -q --cov=app && ruff check . && mypy app/domain
cd frontend && npm test && npm run lint && npm run typecheck
./scripts/smoke.sh http://localhost:8000
```
Details: [docs/TESTING.md](docs/TESTING.md).

## Deployment
Frontend on Vercel, backend (Docker) on Heroku. Steps: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

**Public deployment URL:** `TODO: https://<frontend>.vercel.app`
**Backend API URL:** `TODO: https://<backend>.herokuapp.com/api/health`
**Demo video (unlisted):** `TODO`

## Known limitations
- Decision cutoff time and the meaning of "decisions made in January" are **not specified** by the challenge; defaults are provisional ([docs/FORECAST_LOGIC.md](docs/FORECAST_LOGIC.md)).
- National-level wind only; January 2026 only; no prices, weather or buy recommendations.
- First load fetches data from Elexon and can take time; Eco-tier Heroku dynos sleep when idle.
- Elexon API facts marked *VERIFY* in the data dictionary are confirmed in Phase 1 (`docs/API_FINDINGS.md`).
- No authentication or rate limiting (public read-only data).

## AI tools disclosure
AI tools were used in this project. **Claude (Anthropic)** assisted with: drafting the requirements and architecture documentation, and *(update as you go)* generating and reviewing code and tests. All AI output was reviewed, tested and edited by the author, who is responsible for the final result. Elexon's official API documentation was the source for data-contract decisions. *(Edit this section to match your real usage before submitting.)*

## Data source and attribution
Contains data from the Elexon Insights Solution (BMRS), used under the BMRS Data Licence Terms.

## Documentation
Start at the [documentation index](docs/INDEX.md).
