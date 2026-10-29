# PHASES.md — Implementation Plan (16-hour cap)

> Rule: working end-to-end data flow (Elexon → backend → simple UI) before polish.
> Related: [PRD](PRD.md) · [ARCHITECTURE](ARCHITECTURE.md) · [PROJECT_RULES](PROJECT_RULES.md) · [TESTING](TESTING.md)

## Time budget

| Phase | Name | Hours | Type |
|---|---|---|---|
| 0 | Documentation pack (this) | 0.5 | Mandatory |
| 1 | API investigation | 1.0 | Mandatory |
| 2 | Data modelling + forecast-selection logic | 1.5 | Mandatory |
| 3 | Python backend | 2.5 | Mandatory |
| 4 | React dashboard | 3.5 | Mandatory |
| 5 | Forecast accuracy analysis | 1.0 | Mandatory |
| 6 | Testing and validation | 1.5 | Mandatory |
| 7 | Docker and deployment | 1.5 | Mandatory |
| 8 | README, demo video, submission | 1.5 | Mandatory |
| — | Contingency | 1.0 | Reserve (may fund P1 items) |
| | **Total committed** | **15.5** | **Hard cap 16.0** |

Optional work (P1/P2) may only use contingency hours. If a phase overruns by > 25%, cut P1/P2 items first. Track actual hours in a table at the bottom of this file as you go.

---

## Phase 1 — API investigation (1.0 h)
- **Objective:** Replace every [VERIFY] in DATA_DICTIONARY with facts from real calls.
- **Tasks:** call both stream endpoints for Jan 2026 with `curl`; save small real samples; check parameter names, response shape (array vs `{data}`), timestamp format, fuelType values, row counts, duplicates, publication times pattern, units, response time, pagination/truncation, gaps in Jan 2026; check whether FUELHH `fuelType` filter works (optional).
- **Dependencies:** internet.
- **Outputs:** `docs/API_FINDINGS.md`; `backend/tests/fixtures/real_*.json` (tiny captured samples); updated DATA_DICTIONARY and Open Questions.
- **Acceptance:** every [VERIFY] item resolved or explicitly recorded as unresolved; January 2026 availability stated yes/no/partial with counts.
- **Verification:** re-run the curl commands saved in API_FINDINGS.md and get the same shape.

## Phase 2 — Data modelling and forecast selection (1.5 h)
- **Objective:** Pure, tested domain code per FORECAST_LOGIC.
- **Tasks:** `models.py`, `normalize.py` (parse, validate, dedupe), `cutoff.py`, `selection.py`, `matching.py` (grid + join), `metrics.py`; synthetic fixtures; tests first for cutoff boundaries and metrics.
- **Dependencies:** Phase 1 (field names).
- **Outputs:** `backend/app/domain/*`, `backend/tests/unit/*`.
- **Acceptance:** all tests in TESTING §3–§7 pass; coverage of `domain/` ≥ 90%; no I/O in domain.
- **Verification:** `pytest backend/tests/unit -q`; hand-calc one fixture and compare.

## Phase 3 — Python backend (2.5 h)
- **Objective:** Working API on real data.
- **Tasks:** `config.py`; `elexon_client.py` (chunking, retry, timeouts); `data_store.py` (cache, lock, preload, stale fallback); routes `health/meta/summary/series/records`; Pydantic schemas; error handlers; CORS; logging.
- **Dependencies:** Phase 2.
- **Outputs:** `backend/app/**`, `backend/requirements.txt`, `.env.example`.
- **Acceptance:** API_SPEC behaviour for all P0 endpoints; real January data returned; errors per spec.
- **Verification:** `uvicorn` + curl each endpoint; integration tests with mocked Elexon (respx); one manual real run.
- **Milestone:** first end-to-end data flow achieved here.

## Phase 4 — React dashboard (3.5 h)
- **Objective:** Usable, polished dashboard per UI_UX.
- **Tasks:** Vite+TS scaffold; design tokens; typed API client; layout shell; assumptions banner; cutoff time selector (P0); KPI cards; chart; records table (server sort/paging); date range filter; loading/empty/error states; provenance footer; responsive CSS. P1 (contingency): daily toggle, vintages panel, table filters, zoom.
- **Dependencies:** Phase 3 (or API mock server using real captured shapes only for layout work; remove before finish).
- **Outputs:** `frontend/src/**`.
- **Acceptance:** all P0 UI requirements FR-07..FR-15; Lighthouse accessibility ≥ 90; keyboard usable.
- **Verification:** run against real backend; check states by stopping backend and by empty date range.

## Phase 5 — Forecast accuracy analysis (1.0 h)
- **Objective:** Understand and explain the real results.
- **Tasks:** compute January metrics; find best/worst days (daily MAE); check bias direction; check forecast vintages used; cross-check one day in a spreadsheet; (P0) try several cutoffs via selector to see sensitivity; write findings into `docs/ANALYSIS_NOTES.md` using only real computed numbers.
- **Dependencies:** Phase 3 (and 4 for screenshots).
- **Outputs:** `docs/ANALYSIS_NOTES.md` (talking points for the video).
- **Acceptance:** each claim in the notes is traceable to an API response; manual cross-check matches within rounding.
- **Verification:** reviewer can reproduce numbers from `/api/summary`.

## Phase 6 — Testing and validation (1.5 h)
- **Objective:** Confidence in critical paths.
- **Tasks:** fill gaps in unit tests; API integration tests; frontend component tests (KPI cards, table states, filter validation, formatters); smoke script; lint/type checks (ruff, mypy optional, `tsc`, eslint).
- **Dependencies:** Phases 3–4.
- **Outputs:** tests, `scripts/smoke.sh`, CI-less run instructions in README.
- **Acceptance:** all tests green; the checklist in TESTING §12 ticked.
- **Verification:** run full test commands from a clean clone.

## Phase 7 — Docker and deployment (1.5 h)
- **Objective:** Public working URL.
- **Tasks:** Dockerfiles, compose, `heroku.yml`, `vercel.json`; deploy backend then frontend; set env vars and CORS; verify in incognito.
- **Dependencies:** Phase 6.
- **Outputs:** live URLs, DEPLOYMENT.md verified.
- **Acceptance:** DEPLOYMENT verification checklist complete.
- **Verification:** `docker compose up --build` from clean clone; open public URL in incognito.

## Phase 8 — README, video, submission (1.5 h)
- **Objective:** Complete submission.
- **Tasks:** finish README (structure, setup, URL, AI disclosure); record 10-min video (VIDEO_DEMO); upload unlisted; anonymous public repo; submit form; test all links in incognito.
- **Dependencies:** Phase 7.
- **Outputs:** repo, video URL, form submission.
- **Acceptance:** VIDEO_DEMO submission checklist all ticked.
- **Verification:** open every submitted URL in incognito.

## Mandatory vs optional

| Mandatory (P0) | Optional (P1, from contingency) | Optional (P2) |
|---|---|---|
| Phases 0–8 core items, cutoff selector (FR-15) | daily view, extra metrics, vintages, table filters, zoom, disk snapshot | sensitivity endpoint, CSV export, Playwright, dark mode |

## Hours log (fill during work)

| Phase | Planned | Actual | Notes |
|---|---|---|---|
| 0 | 0.5 | 0.5 | Project rules, architecture, and docs review |
| 1 | 1.0 | 1.0 | Elexon BMRS API investigation & real samples |
| 2 | 1.5 | 1.5 | Pure domain logic, matching, metrics & 100% tests |
| 3 | 2.5 | 2.0 | FastAPI backend, caching, error handling & integration tests |
| 4 | 3.5 | 2.5 | React + Vite + TS dashboard, charts, table & RTL tests |
| 5 | 1.0 | 0.5 | Accuracy analysis, sensitivity table, ANALYSIS_NOTES.md |
| 6 | 1.5 | 1.0 | Testing & validation, conftest, smoke.sh, smoke.py, 100% domain cov |
| 7 | 1.5 | 1.0 | Dockerfiles, Compose, Nginx, Heroku/Vercel manifests, deployment audit |
| 8 | 1.5 | | |
