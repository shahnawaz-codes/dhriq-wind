# API_SPEC.md — Application API (proposed)

> These are **our backend endpoints** (FastAPI). They are NOT Elexon endpoints (see [DATA_DICTIONARY §3](DATA_DICTIONARY.md)).
> All examples use **placeholders** like `<float>`. They show the shape only; they are not real results.
> Related: [FORECAST_LOGIC](FORECAST_LOGIC.md) · [ARCHITECTURE](ARCHITECTURE.md) · [TESTING](TESTING.md)

## 1. Conventions

| Item | Rule |
|---|---|
| Base path | `/api` |
| Format | JSON, UTF-8 |
| Datetimes | ISO-8601 UTC with `Z` (e.g. `2026-01-15T12:00:00Z`) |
| Dates | `YYYY-MM-DD` = delivery date in `Europe/London` |
| Units | Generation, errors, RMSE, MAE: **MW**. Percent fields end with `_pct` |
| Null | Metrics with no data are `null`, never `0` |
| Auth | None (public read-only data) |
| Interactive docs | FastAPI `/docs` (kept enabled) |
| Priority | P0 = `health`, `meta`, `summary`, `series`, `records`. P2 = `sensitivity` |

### Shared query parameters (`summary`, `series`, `records`)

| Param | Type | Default | Validation |
|---|---|---|---|
| `start_date` | date | `DELIVERY_WINDOW_START` | must be within configured window; `start_date <= end_date` |
| `end_date` | date | `DELIVERY_WINDOW_END` | within window |
| `cutoff_time` | `HH:MM` | `DECISION_CUTOFF_LOCAL_TIME` | `00:00`–`23:59`, interpreted in `Europe/London` on D−1 |

### Common error body

```json
{ "error": { "code": "INVALID_PARAMETER", "message": "end_date must be on or after start_date", "details": [{ "field": "end_date" }] } }
```

| HTTP | `code` | When |
|---|---|---|
| 400 | `INVALID_PARAMETER` | bad date/time format, out of window, start > end, bad enum, `page_size` too large |
| 404 | `NOT_FOUND` | unknown route |
| 502 | `UPSTREAM_ERROR` | Elexon failed and no cached data exists |
| 503 | `DATA_NOT_READY` | first load still running (`Retry-After: 5`) |
| 500 | `INTERNAL_ERROR` | unexpected; no stack trace in body |

(FastAPI's default 422 is mapped to 400 `INVALID_PARAMETER` by a custom handler so the frontend handles one shape.)

---

## 2. `GET /api/health`
**Purpose:** liveness for Docker/Heroku. Must not call Elexon.

Response `200`:
```json
{ "status": "ok", "version": "<semver>", "data_loaded": true }
```
`data_loaded=false` while the first fetch is running; status stays `ok`.

---

## 3. `GET /api/meta`
**Purpose:** let the UI draw filters, assumptions and provenance before loading analytics.

Response `200`:
```jsonc
{
  "window": { "start_date": "2026-01-01", "end_date": "2026-01-31", "expected_periods": 744 },
  "assumptions": {
    "cutoff_time_default": "09:00",
    "cutoff_timezone": "Europe/London",
    "cutoff_rule": "Forecast eligible if publishTime <= (delivery date - 1 day) at cutoff_time; latest eligible publishTime is selected",
    "cutoff_inclusive": true,
    "status": "provisional"
  },
  "provenance": {
    "source": "Elexon Insights API", "datasets": ["FUELHH", "WINDFOR"],
    "fetched_at": "<ISO datetime>", "cache_age_seconds": "<int>", "stale": false
  }
}
```

---

## 4. `GET /api/summary`
**Purpose:** KPI cards, data-quality panel, forecast vintages.
**Params:** shared params only.

Response `200`:
```jsonc
{
  "range": { "start_date": "2026-01-01", "end_date": "2026-01-31" },
  "assumptions": { "cutoff_time": "09:00", "cutoff_timezone": "Europe/London", "cutoff_inclusive": true },
  "metrics": {
    "n_matched": "<int>",
    "mae_mw": "<float|null>",
    "rmse_mw": "<float|null>",
    "bias_mw": "<float|null>",            // mean(actual - forecast)
    "mae_pct_of_mean_actual": "<float|null>",
    "p90_abs_error_mw": "<float|null>",
    "mean_actual_mw": "<float|null>",
    "mean_forecast_mw": "<float|null>",
    "coverage_pct": "<float|null>"
  },
  "forecast_vintages": [ { "publish_time": "<ISO>", "periods_count": "<int>" } ],
  "data_quality": { "n_expected": "<int>", "n_matched": "<int>", "n_missing_actual": "<int>", "n_missing_forecast": "<int>", "n_missing_both": "<int>",
                    "invalid_actual_rows": "<int>", "invalid_forecast_rows": "<int>", "duplicate_actual_rows": "<int>",
                    "duplicate_forecast_rows": "<int>", "conflicting_forecast_rows": "<int>", "warnings": ["<string>"] },
  "provenance": { "...": "same object as /api/meta" }
}
```
`forecast_vintages` = distinct selected `publish_time` values within the range with the number of periods using each (limit 100, newest first).

Example: `GET /api/summary?start_date=2026-01-05&end_date=2026-01-11&cutoff_time=09:00`

---

## 5. `GET /api/series`
**Purpose:** chart data.

| Param | Type | Default | Notes |
|---|---|---|---|
| shared | | | |
| `granularity` | `hourly` \| `daily` | `hourly` | |

`hourly` response (max 744 points for January, no pagination):
```jsonc
{
  "granularity": "hourly",
  "unit": "MW",
  "points": [
    {
      "start_time": "<ISO>",
      "actual_mw": "<float|null>",
      "forecast_mw": "<float|null>",
      "forecast_publish_time": "<ISO|null>",
      "status": "matched",
      "actual_half_hour_context_mw": "<float|null>"  // Optional (P1) context only: FUELHH actual for startTime + 30 min (e.g. :30). NOT part of metrics or error calculation
    }
  ]
}
```
`daily` response (≤ 31 points):
```jsonc
{
  "granularity": "daily", "unit": "MW",
  "points": [
    { "date": "2026-01-01", "n_matched": "<int>", "mean_actual_mw": "<float|null>", "mean_forecast_mw": "<float|null>",
      "mae_mw": "<float|null>", "rmse_mw": "<float|null>", "bias_mw": "<float|null>", "cutoff_time": "<ISO UTC>" }
  ]
}
```
Missing values are `null` so the chart shows gaps (do not interpolate).

---

## 6. `GET /api/records`
**Purpose:** detailed table, server-side filter/sort/page.

| Param | Type | Default | Validation |
|---|---|---|---|
| shared | | | |
| `status` | `all` \| `matched` \| `missing_forecast` \| `missing_actual` \| `missing_both` | `all` | enum |
| `min_abs_error_mw` | float | none | ≥ 0 |
| `sort_by` | `start_time` \| `actual_mw` \| `forecast_mw` \| `error_mw` \| `abs_error_mw` \| `forecast_publish_time` \| `forecast_horizon_hours` | `start_time` | enum |
| `sort_dir` | `asc` \| `desc` | `asc` | |
| `page` | int | 1 | ≥ 1 |
| `page_size` | int | 50 | 1–500 |

Response `200`:
```jsonc
{
  "page": 1, "page_size": 50, "total_items": "<int>", "total_pages": "<int>",
  "items": [
    { "start_time": "<ISO>", "delivery_date": "2026-01-01", "cutoff_time": "<ISO>",
      "actual_mw": "<float|null>", "forecast_mw": "<float|null>",
      "forecast_publish_time": "<ISO|null>", "forecast_horizon_hours": "<float|null>",
      "error_mw": "<float|null>", "abs_error_mw": "<float|null>", "status": "matched" }
  ]
}
```
Sorting puts `null` values last regardless of direction. Page beyond last → `items: []` (not an error). Optional P2: `format=csv` export.

---

## 7. `GET /api/sensitivity` (P2, not in MVP)
Returns MAE/RMSE/bias for a list of cutoff times (`cutoff_times=06:00,09:00,12:00,...`) so users can see how the cutoff assumption changes results. Build only if time remains.

## 8. Caching headers
`summary/series/records/meta`: `Cache-Control: public, max-age=300` (data is historical). `health`: `no-store`.
