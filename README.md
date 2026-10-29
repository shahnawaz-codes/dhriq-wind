# UK Wind Generation Forecast Accuracy Dashboard

A full-stack analytical dashboard evaluating UK national day-ahead wind generation forecasts against actual metered generation outturn across **January 2026** (744 hourly settlement periods).

Built for electricity procurement and trading teams to evaluate day-ahead forecast risks, measure systemic bias, and inform procurement risk buffers.

---

## Architecture & Technology Stack

- **Frontend:** React 19, TypeScript, Vite, Recharts, TanStack Query, CSS Design Tokens.
- **Backend:** Python 3.13, FastAPI, Pydantic v2, HTTPX (async client with retries and chunking), Starlette.
- **Domain Layer:** Pure, side-effect-free matching and metric calculation engine with 100% test coverage.
- **Containerization:** Production Dockerfiles (`python:3.13-slim`, multi-stage `node:22-alpine` $\to$ `nginx-unprivileged:alpine-slim`), Docker Compose.
- **Testing & Quality:** Pytest, pytest-cov, Respx, Vitest, React Testing Library, Oxlint.
- **Data Source:** Real Elexon BMRS API (`WINDFOR` forecast stream and `FUELHH` actuals stream, wind fuel type).

---

## Core Features (P0)

1. **Configurable Day-Ahead Decision Cutoff:**
   Interactive selector using `Europe/London` time (defaulting to the provisional benchmark of **09:00 on $D-1$**). Dynamically recomputes forecast vintage selection and all accuracy KPIs.
2. **KPI Accuracy Metrics:**
   - **MAE:** Mean Absolute Error (2,127.5 MW / 18.4% of mean actual).
   - **RMSE:** Root Mean Squared Error (2,606.1 MW).
   - **Bias:** Directional mean error ($e = \text{Actual} - \text{Forecast} = -1,851.5\text{ MW}$).
   - **Matched Periods:** Displays both count and percentage: `744 (100.0%)`.
   - **P90 Absolute Error:** Statistical measure of tail miss (4,306.4 MW).
   - **Data Coverage:** 100.0% completeness across expected January periods.
3. **Hourly Actual vs. Forecast Chart:**
   Visual time-series chart with tooltips detailing publication vintages and forecast horizons. Missing data points are rendered strictly as line gaps (`connectNulls={false}`)—never zero-imputed.
4. **Daily Aggregation View:**
   One-click segmented toggle displaying daily mean actuals vs. forecasts alongside daily MAE and bias.
5. **Comparison Records Table:**
   Server-side paginated, filterable (by matching status and minimum absolute error), and sortable with `aria-sort`.
6. **Integrity & Provenance:**
   Transparent data-quality metrics (duplicate/invalid row counts), live vs. stale cache indicators, and an interactive Methodology & Business Rules modal.

---

## Project Structure

```text
.
├── docker-compose.yml           # Local multi-container orchestration
├── heroku.yml                   # Container stack manifest for backend
├── .env.example                 # Environment variables template
├── docs/                        # Complete architecture and specifications pack
│   ├── FORECAST_LOGIC.md        # Mathematical specification & matching business rules
│   ├── ANALYSIS_NOTES.md        # Evidence-based January 2026 findings & sensitivity analysis
│   ├── API_SPEC.md              # OpenAPI endpoint schemas & error codes
│   ├── ARCHITECTURE.md          # System architecture & decision records
│   ├── DEPLOYMENT.md            # Deployment guide & production checklists
│   └── TESTING.md               # Test matrices, coverage goals, and checklists
├── scripts/
│   ├── generate_analysis.py     # Automated script reproducing all headline metrics & audits
│   ├── smoke.py                 # Cross-platform end-to-end smoke verification script
│   └── smoke.sh                 # Shell / CI end-to-end smoke script
├── backend/
│   ├── Dockerfile               # Production unprivileged container image
│   ├── requirements.txt         # Pinned production dependencies
│   ├── requirements-dev.txt     # Test & linting dependencies
│   ├── app/
│   │   ├── main.py              # FastAPI app lifecycle, CORS, and unified error handlers
│   │   ├── config.py            # Pydantic Settings management
│   │   ├── api/                 # Endpoints (/meta, /summary, /series, /records, /health)
│   │   ├── domain/              # Pure domain logic (cutoff, matching, metrics, normalize)
│   │   └── services/            # Elexon async HTTP client and cached data store
│   └── tests/                   # 54 passing unit, integration, and smoke tests (94% coverage)
└── frontend/
    ├── Dockerfile               # Multi-stage production build (Node -> Nginx)
    ├── nginx.conf               # Static file server with SPA routing fallback
    ├── vercel.json              # Vercel SPA client-side rewrite configuration
    ├── package.json             # React 19, Recharts, TanStack Query, Vitest
    ├── src/
    │   ├── api/                 # Typed API client and response interfaces
    │   ├── components/          # Reusable UI components, KPI cards, charts, tables
    │   └── styles/              # Design tokens and responsive CSS
    └── test/                    # Vitest + React Testing Library component tests
```

---

## Local Development (Without Docker)

### 1. Start Backend (Terminal 1)
```powershell
cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```
- API is running at: `http://127.0.0.1:8000`
- Interactive Swagger docs: `http://127.0.0.1:8000/docs`

### 2. Start Frontend (Terminal 2)
```powershell
cd frontend
npm run dev
```
- Dashboard is running at: `http://localhost:5173`
- The Vite development server automatically proxies `/api` calls to `http://127.0.0.1:8000`.

---

## Local Development (With Docker Compose)

```bash
docker compose up --build
```
- Frontend: `http://localhost:8080`
- Backend API Docs: `http://localhost:8000/docs`

---

## Verification & Testing

### Run Backend Tests & Coverage
```powershell
cd backend
.\.venv\Scripts\pytest -q --cov=app --cov-report=term-missing
```
*Result: 54 passed, 100% domain coverage, 94% overall backend coverage.*

### Run Frontend Tests, Linting & Build
```powershell
cd frontend
npm run lint      # Oxlint: 0 warnings, 0 errors
npm run build     # TypeScript compilation (tsc -b) & Vite bundle
npm test          # Vitest: 21 component & client tests passed
```

### Run End-to-End Smoke Tests
```powershell
backend\.venv\Scripts\python scripts\smoke.py http://127.0.0.1:8000
# or via bash:
bash scripts/smoke.sh http://127.0.0.1:8000
```

---

## Key Analysis Findings (January 2026)

- **Systemic Over-Forecasting:** 27 out of 31 days (87.1%) exhibited negative bias ($Actual < Forecast$). Average bias was **−1,851.5 MW**.
- **Tail Miss Magnitude (P90):** The 90th percentile of absolute error was **4,306.4 MW**.
- **Cutoff Horizon Sensitivity:** Moving the decision cutoff later in the day reduces MAE from **2,128.6 MW** (at 06:00) to **1,963.9 MW** (at 22:00), with the primary step improvement occurring at midday (12:00) when mid-morning NWP cycles become eligible.
- See [`docs/ANALYSIS_NOTES.md`](docs/ANALYSIS_NOTES.md) for full tables, sensitivity data, and exact mathematical cross-checks.

---

## Methodology & Important Disclosures

- **Provisional Benchmark:** 09:00 Europe/London on $D-1$ is an illustrative day-ahead trading decision benchmark, not an official Elexon market gate-closure time.
- **Hourly Evaluation Grid:** Accuracy is evaluated strictly at hourly top-of-hour points (`:00:00Z`). Elexon BMRS documentation does not state whether `WINDFOR` is an instantaneous spot reading or an hourly integrated average. Because FUELHH `:30` readings represent distinct half-hour physical settlement periods, interpolating or averaging actuals without documented basis was rejected to avoid introducing artificial distortion.
- **Data Completeness:** 744 of 744 expected top-of-hour periods matched (100.0% coverage).
