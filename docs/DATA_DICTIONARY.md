# DATA_DICTIONARY.md — Source Data and Internal Models

> Related: [FORECAST_LOGIC](FORECAST_LOGIC.md) · [API_SPEC](API_SPEC.md) · [ARCHITECTURE](ARCHITECTURE.md)

## 1. How this was verified

| Level | Meaning |
|---|---|
| **OFFICIAL** | Seen in official Elexon documentation text (bmrs.elexon.co.uk / developer.data.elexon.co.uk) |
| **SECONDARY** | Seen only in third-party code/docs (e.g. public repos, scrapers). Treat as likely, not certain |
| **VERIFIED (Phase 1)** | Verified against live Elexon API for January 2026 in Phase 1 (see [API_FINDINGS.md](API_FINDINGS.md)) |

Phase 1 live API calls were executed against `https://data.elexon.co.uk/bmrs/api/v1` for January 2026. All [VERIFY] items have been confirmed or clarified below. Full curl commands, responses, and raw fixtures are documented in `docs/API_FINDINGS.md` and `backend/tests/fixtures/`.

## 2. Source datasets

| Dataset | Purpose | Challenge URL | Base URL (SECONDARY + OFFICIAL portal) |
|---|---|---|---|
| FUELHH | Actual half-hourly generation by fuel type; we use `fuelType = WIND` | `.../datasets/FUELHH/stream` | `https://data.elexon.co.uk/bmrs/api/v1` |
| WINDFOR | Wind generation forecasts with publication time | `.../datasets/WINDFOR/stream` | same |

- Elexon says all its APIs are public and **no API key is required** (OFFICIAL, developer portal home).
- Stream endpoints return **JSON only**, "minimal", "optimised", and the portal says there are "no restrictions or limits on data return" (OFFICIAL). **VERIFIED:** Stream endpoints return plain unpaginated JSON arrays. Full month requests (~1.5k FUELHH rows in ~1.9s, ~19.3k WINDFOR rows in ~2.3s) return cleanly in a single request without truncation or 429 errors. Retry with exponential backoff is still recommended.
- Dataset endpoints filter by **publish time** (OFFICIAL: "request data based on published times").

## 3. Source endpoints (Elexon — not our API)

| Endpoint | Query parameters | Status |
|---|---|---|
| `GET /datasets/WINDFOR/stream` | `publishDateTimeFrom`, `publishDateTimeTo` (ISO date-time) | **VERIFIED:** Mandatory for historical forecast time series. Both start and end must be specified (e.g. `2025-12-30T00:00:00Z` to `2026-01-31T23:59:59Z`). Without them, only the latest forecast batch is returned |
| `GET /datasets/FUELHH/stream` | `settlementDateFrom`, `settlementDateTo` (`yyyy-MM-dd`) | **VERIFIED:** Preferred and fully functional for delivery dates (`2026-01-01` to `2026-01-31`). Accepts `fuelType=WIND` directly. (`publishDateTimeFrom/To` also works) |
| FUELHH `fuelType` filter on stream | `&fuelType=WIND` | **VERIFIED:** Works server-side! Querying `fuelType=WIND` reduces payload from 29,760 to exactly 1,488 rows and matches client-side filtering byte-for-byte. Code will query `fuelType=WIND` and enforce client-side validation as safety |
| Pagination | none for stream endpoints | **VERIFIED:** Stream endpoints return the complete dataset in a single array; no pagination or truncation observed |

## 4. Source fields

### 4.1 WINDFOR stream row (VERIFIED against live API)

| Field | Type (JSON) | Meaning | Required | Nullable? |
|---|---|---|---|---|
| `dataset` | string | constant `"WINDFOR"` | yes | **No** (never null in Jan 2026 data) |
| `publishTime` | string, ISO date-time | when the forecast was created | **yes** | **No** (never null, format `YYYY-MM-DDTHH:MM:SSZ`) |
| `startTime` | string, ISO date-time | start of delivery period | **yes** | **No** (never null, format `YYYY-MM-DDTHH:MM:SSZ`). **NOTE:** WINDFOR produces hourly resolution (`:00:00Z` only; 0 half-hour points) |
| `generation` | integer/number | forecast wind generation | **yes** | **No** (never null, non-negative, range 2,250–21,353 MW) |

- The stream response has **no** `settlementDate` / `settlementPeriod`.
- Stream response is a **bare JSON array** `[...]`; the non-stream endpoint wraps rows in `{"data": [...]}`. Parser handles both shapes.
- Publication cadence: **8 times a day** at `02:30`, `04:30`, `07:30`, `09:30`, `11:30` (with occasional slight operational shifts, e.g. `12:25` on 9 Jan), `15:30`, `18:30`, and `22:30 UTC`. Each run produces 73 hourly points (~2.5 days ahead).
- Unit: **MW** (verified integer values 2,250–21,353 MW).

### 4.2 FUELHH stream row (VERIFIED against live API)

| Field | Type | Meaning | Notes |
|---|---|---|---|
| `dataset` | string | `"FUELHH"` | Constant identifier |
| `publishTime` | string | when the record was published | Format `YYYY-MM-DDTHH:MM:SSZ`, non-null (typically 30 min after `startTime`) |
| `startTime` | string | start of the half-hour period | Format `YYYY-MM-DDTHH:MM:SSZ`, 30-min resolution (`:00:00Z` and `:30:00Z`), non-null |
| `settlementDate` | string `yyyy-MM-dd` | settlement date | Non-null, `2026-01-01` to `2026-01-31` |
| `settlementPeriod` | integer 1–48 | settlement period index | Non-null, 1 to 48 for all 31 days |
| `fuelType` | string | e.g. `WIND`, `CCGT` ... | Non-null; filtered to `"WIND"` |
| `generation` | integer | MW | Non-null, non-negative, range 1,695–17,805 MW |

### 4.3 Units and timestamps

- Generation unit: **MW** (average power over the period).
- Timestamps: strictly ISO-8601 UTC ending in `Z` (`YYYY-MM-DDTHH:MM:SSZ`, no milliseconds). Parser still accepts optional milliseconds or space separator as defensive programming.

## 5. Normalised internal models (proposed application models)

Python (`backend/app/domain/models.py`, frozen dataclasses or Pydantic models); TypeScript mirrors in `frontend/src/types/api.ts`.

### `ActualPoint`
| Field | Type | Notes |
|---|---|---|
| `start_time` | `datetime` (UTC, tz-aware) | from `startTime` |
| `generation_mw` | `float` | from `generation`, valid (≥ 0, finite) |
| `publish_time` | `datetime \| None` | from `publishTime` if present, used only to break duplicate ties |

### `ForecastPoint`
| Field | Type | Notes |
|---|---|---|
| `start_time` | `datetime` (UTC) | from `startTime` |
| `publish_time` | `datetime` (UTC) | from `publishTime` |
| `generation_mw` | `float` | valid (≥ 0, finite) |

### `ComparisonRecord` (derived — one per expected period)
| Field | Type | Derived from |
|---|---|---|
| `start_time` | datetime UTC | grid |
| `delivery_date` | date (Europe/London) | `start_time` |
| `cutoff_time` | datetime UTC | BR-02 |
| `actual_mw` | float \| null | `ActualPoint` |
| `forecast_mw` | float \| null | selected `ForecastPoint` |
| `forecast_publish_time` | datetime \| null | selected `ForecastPoint.publish_time` |
| `forecast_horizon_hours` | float \| null | `start_time − publish_time` |
| `error_mw` | float \| null | `actual − forecast` |
| `abs_error_mw` | float \| null | `abs(error)` |
| `status` | enum | `matched`, `missing_forecast`, `missing_actual`, `missing_both` |

### `DataQuality`
`raw_actual_rows`, `raw_forecast_rows`, `wind_actual_rows`, `invalid_actual_rows`, `invalid_forecast_rows`, `duplicate_actual_rows`, `duplicate_forecast_rows`, `conflicting_forecast_rows`, `n_expected`, `n_matched`, `n_missing_actual`, `n_missing_forecast`, `n_missing_both`, `warnings[]` (all integers except `warnings`).

### `DataProvenance`
`source` (`"Elexon Insights API"`), `datasets` (`["FUELHH","WINDFOR"]`), `base_url`, `fetched_at` (UTC), `cache_age_seconds`, `stale` (bool), `licence_note` (string pointing to BMRS Data Licence Terms).

## 6. Source field vs derived field

| Application field | Source or derived |
|---|---|
| `start_time`, `generation_mw` (actual), `publish_time`, `generation_mw` (forecast) | **Source** (renamed to snake_case, validated) |
| `delivery_date`, `cutoff_time`, `forecast_horizon_hours`, `error_mw`, `abs_error_mw`, `status` | **Derived by app** |
| All metrics (MAE, RMSE, bias, P90, coverage, MAE %) | **Derived by app** |

## 7. Matching, missing and duplicate rules
See [FORECAST_LOGIC §4 and §8](FORECAST_LOGIC.md). Summary: join on exact `start_time`; forecast chosen by BR-03/BR-04; missing → status + exclusion; duplicates → deterministic keep-rule + counters.

## 8. Timezone conventions
Storage and API: UTC. Business logic: `Europe/London` for cutoff and delivery date only. Display: UTC with an explicit label. See [FORECAST_LOGIC §9](FORECAST_LOGIC.md).

## 9. January 2026 boundaries (provisional, Q-01)

| Item | Value |
|---|---|
| Delivery window (UTC) | `2026-01-01T00:00:00Z` ≤ `startTime` < `2026-02-01T00:00:00Z` |
| Expected periods (evaluation grid) | 31 × 24 = **744** (hourly top-of-hour periods `:00:00Z`; raw FUELHH stream has 1,488 half-hour rows) |
| Cutoff for first delivery day (1 Jan) | `2025-12-31T09:00:00Z` (default rule) |
| Cutoff for last delivery day (31 Jan) | `2026-01-30T09:00:00Z` |
| WINDFOR `publishDateTimeFrom` request | `2025-12-30T00:00:00Z` (window start − `FORECAST_PUBLISH_LOOKBACK_DAYS`) |
| WINDFOR `publishDateTimeTo` request | `2026-01-31T00:00:00Z` (end of D−1 for the last delivery day) |
| FUELHH `settlementDateFrom/To` request | `2026-01-01` / `2026-01-31` |
| DST in window | none (GMT all month) |

**Alternative reading (Q-01):** "decisions made in January" = decision dates 1–31 Jan → delivery dates 2 Jan–1 Feb. Switch by changing `DELIVERY_WINDOW_START/END` to `2026-01-02`/`2026-02-01`; no code change should be needed. Decide this with the challenge owner if possible; otherwise state the choice in the demo.
