# TESTING.md

> Related: [FORECAST_LOGIC](FORECAST_LOGIC.md) · [API_SPEC](API_SPEC.md) · [PROJECT_RULES](PROJECT_RULES.md)
> Fixture rule: synthetic fixtures are labelled `SYNTHETIC`. Real captured samples (Phase 1) are labelled `REAL`. The running app never serves fixtures.

## 1. Tools and commands

| Area | Tool | Command |
|---|---|---|
| Backend unit + integration | pytest (+ `respx`, `pytest-cov`) | `cd backend && pytest -q --cov=app` |
| Backend lint/types | ruff, mypy | `ruff check . && ruff format --check . && mypy app/domain` |
| Frontend unit/component | Vitest + React Testing Library | `cd frontend && npm test` |
| Frontend lint/types | eslint, tsc | `npm run lint && npm run typecheck` |
| Smoke | shell script | `./scripts/smoke.sh http://localhost:8000` |
| Docker | compose | `docker compose up --build` |

## 2. Unit tests — general
Pure-function tests in `backend/tests/unit/`. No network, no clock (`now` passed in). Target ≥ 90% line coverage in `app/domain/`.

## 3. Metric calculation tests (`test_metrics.py`)
Use a tiny fixture and hand-calculated expected values.

| Case | Setup (actual, forecast) | Expected |
|---|---|---|
| Basic | (100,90), (50,60), (80,80) → errors +10, −10, 0 | MAE = 6.667, RMSE = 8.165, bias = 0 |
| Positive bias | (100,80), (100,90) | bias = +15, MAE = 15 |
| Negative bias | (80,100) | bias = −20 |
| Single point | (10,7) | MAE=3, RMSE=3, bias=3 |
| Empty | no matched | all metrics `None`, no exception, no divide-by-zero |
| MAE % | mean actual = 0 | `None` |
| Percentile P90 | known list | equals linear-interpolation result |
| Large values | 30,000 MW range | no overflow, float precision OK |
| Sign convention | forecast > actual | error negative (BR-10) |

## 4. Forecast selection tests (`test_selection.py`)
Default cutoff rule: delivery date D, cutoff = D−1 at 09:00 `Europe/London` (= UTC in January). Delivery period `2026-01-15T12:00Z` → cutoff `2026-01-14T09:00:00Z`.

| Test | Forecast publishTime(s) | Expected |
|---|---|---|
| Before cutoff | 2026-01-14T08:59:59Z | eligible, selected |
| **Exactly at cutoff** | 2026-01-14T09:00:00Z | eligible (inclusive), selected over earlier ones |
| After cutoff | 2026-01-14T09:00:01Z | **not eligible** |
| Mixed | 05:30, 08:30 (eligible), 10:30, next-day 03:30 (not) | selects 08:30 |
| Only late forecasts | all after cutoff | `missing_forecast`; no fallback to late forecast |
| Latest wins | two eligible publishes | greater `publishTime` wins regardless of input order |
| Different `startTime` | forecasts for other periods | ignored |
| Custom cutoff | `cutoff_time=18:00` | 16:30 publication eligible, 19:30 not |
| Each date has own cutoff | periods on 2 days | each uses its own D−1 |
| Leakage guard | publish after cutoff has "better" value | result unchanged |

Boundary behaviour (inclusive) is defined in FORECAST_LOGIC BR-03; if that rule changes, update these tests first.

## 5. Timestamp and timezone tests (`test_cutoff.py`, `test_normalize.py`)
- Parse `...Z` with and without milliseconds, and space-separated form; reject naive strings.
- January: Europe/London cutoff 09:00 == 09:00Z.
- **DST fixtures (not January):** the grid is built from the UTC window (BR-01), so its size does not change with DST. Delivery date is the local `Europe/London` date, so grouping by `delivery_date` must give 23 hourly periods on 2026-03-29 and 25 on 2026-10-25. Cutoff UTC differs from local time on those dates (BST = UTC+1). Assert these counts and the cutoff conversion.
- Window boundary: `2026-01-01T00:00Z` included, `2026-02-01T00:00Z` excluded; grid length 744.
- Cutoff for 1 Jan is 2025-12-31T09:00Z (crosses month/year).

## 6. Missing and duplicate data tests (`test_matching.py`, `test_normalize.py`)
- Missing actual → status `missing_actual`, excluded from metrics, counted.
- Missing forecast → `missing_forecast`. Both → `missing_both`.
- **Hourly matching and :30 exclusion guard:** Grid is strictly hourly (`:00:00Z`, 744 periods in Jan 2026). FUELHH `:30` actual rows are never matched in the grid and **never enter metrics calculation** (MAE, RMSE, bias). Test explicitly asserts that passing FUELHH data with `:30` records does not change the metric results compared to passing only `:00` records.
- **2-Day Lookback Coverage & Early Cutoff Boundary Tests:**
  - Test that the 2-day lookback (`FORECAST_PUBLISH_LOOKBACK_DAYS=2`) yields **100% forecast coverage (744/744)** under cutoff times between `03:00` and `23:00` UTC (including default `09:00`).
  - Test that for very early cutoffs (e.g. `00:00 UTC`), periods on Jan 1–2 lacking an eligible publication in the 2-day lookback window are cleanly flagged as `missing_forecast`, excluded from metrics, and counted in `data_quality.n_missing_forecast` without unhandled errors or data leakage.
- Duplicate forecast identical → one kept, counter +1. Duplicate with different value → last kept, `conflicting_forecast_rows` +1, warning.
- Duplicate actuals → latest `publish_time` wins; warning if values differ.
- Invalid rows: null, `"abc"`, NaN, inf, negative generation, bad timestamp → dropped and counted.
- Non-WIND fuel types are ignored; zero generation (valid) is kept.
- Empty input lists → 744 `missing_both` records, metrics `None`, warnings present.
- Rows outside window ignored.

## 7. API integration tests (`backend/tests/integration/`)
FastAPI `TestClient` + `respx` mocks of Elexon.
- Each endpoint: happy path shape matches API_SPEC (validate with Pydantic models).
- Cutoff recalculation: changing `cutoff_time` (e.g. `09:00` vs `18:00`) returns different selected forecasts, different `n_matched` / `coverage_pct`, and recalculated metrics.
- Validation: bad date, start > end, out of window, bad cutoff `25:00`, bad `sort_by`, `page_size=501` → 400 `INVALID_PARAMETER`.
- Pagination: totals, last page, beyond last page empty.
- Sorting: nulls last.
- Upstream failure: 500/timeout → retries (count calls) → 502 when no cache; stale cache served with `stale=true` when cache exists.
- Both response shapes (bare array and `{data}`) parsed.
- Chunking: multiple chunk requests, overlap deduped.
- `health` does not call Elexon.
- CORS header present for allowed origin, absent for others.

## 8. Frontend component tests (Vitest + RTL)
- `KpiCard`: value+unit, `null` → "—", tooltip opens on focus. Matched periods card displays both count and percentage (e.g. `744 (100.0%)`).
- `FilterBar`: end < start shows message and blocks apply; limits to window. Cutoff time input triggers re-fetch with `cutoff_time=HH:MM` and recalculates metrics and table.
- `RecordsTable`: header click calls sort; `aria-sort`; empty/loading/error states; null cells "—"; status chips text.
- `ActualForecastChart`: renders with data; shows empty state for no data (mock Recharts container size).
- API client: error body mapped to a typed error; 503 triggers retry logic.
- Formatters: MW 1 decimal, UTC date string.
- No test may assert fabricated "real" numbers; use clearly synthetic props.

## 9. End-to-end smoke tests
`scripts/smoke.sh <base_url>` (P0): health 200; meta has window; summary returns `n_matched > 0` (real data) and non-null MAE; series length > 0; records page 1 has ≤ 50 items; invalid param returns 400. P2: Playwright "open dashboard, KPIs visible, table sorts".

## 10. Docker verification
- [ ] `docker compose up --build` from clean clone succeeds
- [ ] `curl localhost:8000/api/health` → ok; container health status healthy
- [ ] UI at `localhost:8080` loads and calls backend (no CORS error in console)
- [ ] Images run as non-root; `docker compose down` clean

## 11. Deployment verification
See [DEPLOYMENT §9](DEPLOYMENT.md). Run `scripts/smoke.sh` against the public backend URL; load the public frontend in an incognito window.

## 12. Validation checklist before submission
- [ ] All unit, integration, component tests green
- [ ] Hand-check of one day's MAE/RMSE/bias vs spreadsheet matches
- [ ] Selection verified on a real day: chosen `publishTime` ≤ cutoff; later publish exists but is not used
- [ ] Coverage of `domain/` ≥ 90%
- [ ] Smoke script passes locally and on the public URL
