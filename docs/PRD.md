# PRD.md — Product Requirements Document

> Related: [FORECAST_LOGIC](FORECAST_LOGIC.md) · [API_SPEC](API_SPEC.md) · [UI_UX](UI_UX.md) · [PHASES](PHASES.md)

## 1. Problem statement
A UK energy utility buys electricity on the **day-ahead market**. The buyer decides on day D−1 how much extra power (e.g. from thermal plants) to buy for day D, after subtracting expected wind output. Wind is weather-driven, so they rely on **forecasts**. They need to (a) see the latest forecast that was **available at decision time**, and (b) know **how wrong** such forecasts typically are.

## 2. Business context
- Client: UK utility; team: day-ahead power procurement. We pitch a pilot-stage web portal.
- Scope limit set by the challenge: national-level wind only, Elexon data only, January 2026.
- Over-forecast wind → under-buy → expensive balancing later. Under-forecast → over-buy. Quantified error helps size a safety margin.

## 3. Target users
| User | Need |
|---|---|
| Procurement analyst (primary) | Quickly judge forecast quality; see exact forecast used; export-like detail for audit |
| Procurement team lead | One-screen summary of error size and bias to set buffers |
| Technical reviewer (hiring) | Clear, correct, explainable logic and clean code |

## 4. Product goals
1. Show, for each January 2026 hourly period, the forecast that was eligible at the decision cutoff next to the actual wind generation.
2. Quantify accuracy (MAE, RMSE, bias; P1: P90, MAE %).
3. Make assumptions and data provenance visible and changeable (cutoff time).
4. Deliver a polished MVP within 16 hours, deployed publicly.

## 5. Non-goals
Other fuel types or regions · weather data · price data · trading optimisation or buy-quantity recommendations · own forecasting model · user accounts · database · real-time/live data · mobile-native app · dark mode (P2 only) · forecast horizons beyond what WINDFOR provides.

## 6. Requirement priorities
P0 = must ship · P1 = important, ship if on schedule · P2 = optional.

## 7. Functional requirements

| ID | Pri | Requirement |
|---|---|---|
| FR-01 | P0 | Backend fetches FUELHH and WINDFOR from Elexon for the January 2026 window and keeps only `fuelType = WIND` actuals |
| FR-02 | P0 | Backend normalises, validates and de-duplicates rows per [FORECAST_LOGIC §8](FORECAST_LOGIC.md) |
| FR-03 | P0 | For each delivery period, select the latest forecast with `publishTime <= cutoff` (BR-02..BR-04) |
| FR-04 | P0 | Match selected forecast to actual by `startTime`; mark missing periods |
| FR-05 | P0 | Compute MAE, RMSE, mean error (bias = actual − forecast) over matched periods |
| FR-06 | P0 | Endpoints: `/api/health`, `/api/meta`, `/api/summary`, `/api/series`, `/api/records` per [API_SPEC](API_SPEC.md) |
| FR-07 | P0 | Dashboard KPI cards with MAE, RMSE, bias, matched count, units and tooltips |
| FR-08 | P0 | Actual-vs-forecast time-series chart with tooltip showing actual, forecast, error, and forecast `publishTime` |
| FR-09 | P0 | Date range filter limited to the January 2026 window |
| FR-10 | P0 | Records table with sort and pagination; columns: start time, actual, forecast, error, abs error, forecast publish time, status |
| FR-11 | P0 | Visible assumptions banner: cutoff rule, timezone, "provisional" label |
| FR-12 | P0 | Provenance/freshness: source, datasets, fetched-at, data-quality counts |
| FR-13 | P0 | Loading, empty and error states for every data panel |
| FR-14 | P0 | Dockerfiles + Docker Compose; public deployment (frontend + backend) |
| FR-15 | P0 | Cutoff time selector in UI and backend (re-computes everything via `cutoff_time`) |
| FR-16 | P1 | Daily granularity toggle with daily MAE/bias |
| FR-17 | P1 | Extra metrics: P90 absolute error, MAE % of mean actual, coverage % |
| FR-18 | P1 | Forecast vintages panel (which `publishTime`s were used, how many periods each) |
| FR-19 | P1 | Table filters: status, minimum absolute error |
| FR-20 | P1 | Chart zoom/brush over time |
| FR-21 | P2 | Cutoff sensitivity (`/api/sensitivity`) |
| FR-22 | P2 | CSV export of records |
| FR-23 | P2 | Playwright E2E test; dark mode |

## 8. Non-functional requirements

| ID | Pri | Requirement |
|---|---|---|
| NFR-01 | P0 | Correctness over features: metrics reproducible by hand on a small fixture |
| NFR-02 | P0 | No fabricated data anywhere in the running app |
| NFR-03 | P0 | Warm API responses < 500 ms; first full load of January data < 60 s (show loading state) |
| NFR-04 | P0 | Elexon failures handled explicitly (retry, timeout, clear error, stale cache fallback) |
| NFR-05 | P0 | Business logic is pure, typed and unit-tested (≥ 90% line coverage on `domain/`) |
| NFR-06 | P0 | Accessibility: WCAG 2.2 AA target (see [UI_UX §10](UI_UX.md)) |
| NFR-07 | P0 | Desktop-first; usable down to 360 px width |
| NFR-08 | P0 | Config through env vars; no secrets (none needed) |
| NFR-09 | P0 | Public repo, anonymous name, README with AI disclosure and no personal identifiers |
| NFR-10 | P1 | Structured logs; request ids |

## 9. User stories and acceptance criteria

| ID | Story | Acceptance criteria |
|---|---|---|
| US-01 | As an analyst I want to see which forecast was available at decision time so I can trust the comparison | AC: each record shows `forecast_publish_time` ≤ `cutoff_time`; assumptions banner states the rule; no record uses a later publication (test: FR-03) |
| US-02 | As an analyst I want MAE, RMSE and bias for January so I can size buffers | AC: values match hand-calculated results on the fixture; units shown as MW; empty data shows "No data", not 0 |
| US-03 | As an analyst I want to see actual vs forecast over time and inspect any point | AC: chart renders ≤ 744 points; tooltip shows actual, forecast, error, publish time; gaps shown for missing data |
| US-04 | As an analyst I want to drill into individual periods | AC: table sorts by every column, paginates, shows status for missing periods |
| US-05 | As a team lead I want to know the data is real and current | AC: provenance shows Elexon, datasets, fetched-at time; data-quality counts visible |
| US-06 | As an analyst I want to change the cutoff time | AC: changing it updates KPIs, chart, table within 2 s; URL/state reflects value |
| US-07 | As a reviewer I want to run the app with one command | AC: `docker compose up --build` serves UI and API; README steps verified in a clean checkout |

## 10. Core user journeys
1. **Quick quality check:** open dashboard → read assumptions banner → read KPIs → glance at chart.
2. **Investigate a bad day:** switch to daily view → find high-MAE day → set date range to that day → sort table by abs error → inspect forecast publish times.
3. **Challenge the assumption:** change cutoff time → see KPIs change → conclude how sensitive accuracy is to timing.

## 11. Data requirements and success criteria

**Data:** see [DATA_DICTIONARY](DATA_DICTIONARY.md). Real Elexon data only.

**Success criteria (all must hold):**
- [ ] P0 requirements implemented and verified against their acceptance criteria.
- [ ] Public frontend URL loads in incognito and shows real January 2026 results.
- [ ] Metrics verified by unit tests plus one manual spreadsheet cross-check on a sample day.
- [ ] README, 10-minute video and form submitted; total time ≤ 16 h.

## 12. Risks and unresolved questions

| ID | Question / risk | Impact | Provisional handling |
|---|---|---|---|
| Q-01 | "Decisions made in January" = decision date or delivery date? | Window shifts by one day | Delivery date in January; configurable |
| Q-02 | Exact decision cutoff time? | Changes selected forecasts and all metrics | 09:00 Europe/London on D−1; configurable; P0 UI selector |
| Q-03 | Is `publishTime == cutoff` eligible? | Edge cases only | Inclusive |
| Q-04 | Exact FUELHH stream parameters and whether a `fuelType` server filter exists | Fetch code | **Verified in Phase 1:** `settlementDateFrom/To` + `fuelType=WIND` works server-side and produces exact identical rows to client-side filtering |
| Q-05 | Is January 2026 data complete in both datasets? | Coverage, credibility | **Verified in Phase 1:** 100% complete; 0 missing settlement periods in FUELHH, 0 missing hours in WINDFOR |
| Q-06 | WINDFOR duplicates/revisions semantics and the real publication pattern in Jan 2026 | Selection correctness | **Verified in Phase 1:** 8 runs/day (02:30, 04:30, 07:30, 09:30, 11:30, 15:30, 18:30, 22:30 UTC); 0 duplicate `(startTime, publishTime)` pairs |
| Q-07 | WINDFOR `generation` unit is MW? | Metrics | **Verified in Phase 1:** integer MW (actuals 1.7k–17.8k MW, forecasts 2.2k–21.4k MW) |
| Q-08 | Response size, speed, rate limiting of stream endpoints | Load time | **Verified in Phase 1:** full month in ~1.9s–2.3s; no 429s or rate limit headers in burst test |
| Q-09 | Heroku has no free tier; cost/credit for backend | Deployment | Fallback: backend on Vercel (see DEPLOYMENT) |
| Q-10 | Challenge asks for anonymous repo name; docs must not reveal identity | Submission | Keep personal data out of repo (PROJECT_RULES) |
| Q-11 | Physical meaning of WINDFOR hourly numbers (instantaneous at :00 vs 60-min average)? | Affects alignment with half-hourly FUELHH settlement | **Confirmed Decision:** Exact match on `:00:00Z` only (hourly evaluation grid, 744 periods). FUELHH `:30` excluded from metrics; no interpolation, no averaging. Highlighted for future confirmation |
| R-01 | Time overrun (16 h cap) | Fail criteria | Phase budget + contingency; P1/P2 cut first |
| R-02 | Elexon API unavailable during demo/review | Broken demo | Disk/memory cache, stale fallback, record demo early |
