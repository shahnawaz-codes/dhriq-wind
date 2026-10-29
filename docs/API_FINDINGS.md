# API_FINDINGS.md — Elexon API Investigation Results (Phase 1)

This document records the empirical results of querying the live Elexon Insights API (`https://data.elexon.co.uk/bmrs/api/v1`) for January 2026 data, conducted during Phase 1.

---

## 1. Summary of Datasets & Endpoints Tested

| Dataset | Stream Endpoint | Key Query Parameters | Status Code | Response Shape |
|---|---|---|---|---|
| **FUELHH** | `/datasets/FUELHH/stream` | `settlementDateFrom=2026-01-01&settlementDateTo=2026-01-31&fuelType=WIND` | `200 OK` | Plain JSON array `[...]` |
| **WINDFOR** | `/datasets/WINDFOR/stream` | `publishDateTimeFrom=2025-12-30T00:00:00Z&publishDateTimeTo=2026-01-31T23:59:59Z` | `200 OK` | Plain JSON array `[...]` |

---

## 2. Curl Commands Executed and Empirical Results

### 2.1 FUELHH (Actual Half-Hourly Generation)

#### Command 1: Full January 2026 Wind Generation (Server-Side Filter)
```bash
curl -s -i "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream?settlementDateFrom=2026-01-01&settlementDateTo=2026-01-31&fuelType=WIND"
```
**Results:**
- **HTTP Status:** `200 OK`
- **Elapsed time:** ~1.91s
- **Transfer:** Chunked transfer encoding (`Transfer-Encoding: chunked`)
- **Row count:** **1,488 rows** (exactly 31 days × 48 settlement periods).
- **Start times:** Half-hourly resolution (`:00:00Z` and `:30:00Z`).
- **Completeness:** 100% complete for all 31 days in January 2026 (periods 1 to 48 for each day).
- **Missing periods:** 0
- **Negative or null values:** 0 (Min: 1,695 MW, Max: 17,805 MW).
- **Duplicates:** 0 duplicate `startTime` rows.

#### Command 2: Full January 2026 All Fuels (Verifying Server-Side Filter Fidelity)
```bash
curl -s "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream?settlementDateFrom=2026-01-01&settlementDateTo=2026-01-31"
```
**Results:**
- **Total rows returned:** 29,760 rows across 20 fuel types (`BIOMASS`, `CCGT`, `COAL`, `INTELEC`, `INTEW`, `INTFR`, `INTGRNL`, `INTIFA2`, `INTIRL`, `INTNED`, `INTNEM`, `INTNSL`, `INTVKL`, `NPSHYD`, `NUCLEAR`, `OCGT`, `OIL`, `OTHER`, `PS`, `WIND`).
- **Wind rows count in unfiltered response:** 1,488 rows.
- **Verification:** Filtering `fuelType == "WIND"` on the full response yields the exact identical rows as passing `&fuelType=WIND` query parameter.

#### Command 3: Parameter Verification (`publishDateTimeFrom`/`To`)
```bash
curl -s "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream?publishDateTimeFrom=2026-01-01T00:00:00Z&publishDateTimeTo=2026-01-01T02:00:00Z&fuelType=WIND"
```
**Results:**
- Accepted and works as expected (returns rows published within the given window).
- For historical delivery windows, `settlementDateFrom` and `settlementDateTo` is the preferred and cleanest parameter set.

---

### 2.2 WINDFOR (Wind Generation Forecasts)

#### Command 1: Full Range for January 2026 Evaluation (with 2-day lookback)
```bash
curl -s -i "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream?publishDateTimeFrom=2025-12-30T00:00:00Z&publishDateTimeTo=2026-01-31T23:59:59Z"
```
**Results:**
- **HTTP Status:** `200 OK`
- **Elapsed time:** ~2.30s - 2.43s
- **Row count:** **19,272 rows** (18,104 rows if querying strictly from `2026-01-01T00:00:00Z`).
- **Unique publish times:** 264 distinct forecast publications.
- **Unique target start times within Jan 2026:** **744** (covers all 31 days × 24 hours).
- **Missing hours in Jan 2026:** 0 (all 744 hours from `2026-01-01T00:00:00Z` to `2026-01-31T23:00:00Z` are covered).
- **Negative or null values:** 0 (Min: 2,250 MW, Max: 21,353 MW).
- **Duplicates:** 0 duplicate `(startTime, publishTime)` pairs.

#### Command 2: WINDFOR Parameter Sensitivity
```bash
curl -s "https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream?settlementDateFrom=2026-01-01&settlementDateTo=2026-01-01"
```
**Results:**
- Without `publishDateTimeFrom`/`To`, `settlementDateFrom`/`To` is ignored and returns the latest available forecast batch (73 rows). `publishDateTimeFrom` and `publishDateTimeTo` are **mandatory** to retrieve historical forecast time-series.

---

## 3. Data Structure & Field Schemas

### 3.1 Response Shapes
- Both stream endpoints (`/datasets/FUELHH/stream` and `/datasets/WINDFOR/stream`) return a **bare JSON array**:
  ```json
  [
    { ... },
    { ... }
  ]
  ```
  *(Note: Non-stream endpoints like `/datasets/WINDFOR` return `{"data": [...]}`).*

### 3.2 FUELHH Field Inventory
| Field | JSON Type | Empirical Example | Nullable? | Notes |
|---|---|---|---|---|
| `dataset` | string | `"FUELHH"` | No | Constant identifier |
| `publishTime` | string | `"2026-01-01T00:30:00Z"` | No | ISO-8601 UTC timestamp |
| `startTime` | string | `"2026-01-01T00:00:00Z"` | No | ISO-8601 UTC timestamp; 30-min resolution |
| `settlementDate` | string | `"2026-01-01"` | No | `YYYY-MM-DD` |
| `settlementPeriod` | integer | `1` | No | 1 to 48 |
| `fuelType` | string | `"WIND"` | No | Filtered to `"WIND"` |
| `generation` | integer | `13756` | No | Megawatts (MW), average over the half-hour |

### 3.3 WINDFOR Field Inventory
| Field | JSON Type | Empirical Example | Nullable? | Notes |
|---|---|---|---|---|
| `dataset` | string | `"WINDFOR"` | No | Constant identifier |
| `publishTime` | string | `"2025-12-31T07:30:00Z"` | No | ISO-8601 UTC timestamp |
| `startTime` | string | `"2025-12-31T00:00:00Z"` | No | ISO-8601 UTC timestamp; **hourly resolution (:00:00Z)** |
| `generation` | integer | `5044` | No | Megawatts (MW) forecast |

*(Note: `settlementDate` and `settlementPeriod` do NOT exist on WINDFOR stream rows).*

---

## 4. Key Behavioral Patterns

### 4.1 Publication Cadence of WINDFOR
Forecasts are published **8 times daily**, typically at:
- `02:30:00Z`
- `04:30:00Z`
- `07:30:00Z`
- `09:30:00Z`
- `11:30:00Z` (with occasional slight operational shifts, e.g. 12:25:00Z on 2026-01-09)
- `15:30:00Z`
- `18:30:00Z`
- `22:30:00Z`

Each publication outputs a trajectory of **73 hourly forecast points** spanning from roughly `publishTime - 5.5 hours` to `publishTime + 66.5 hours`.

### 4.2 Decision Cutoff Interaction
- Under the default business rule (**D−1 at 09:00 Europe/London / UTC**):
  The latest eligible publication available before 09:00 UTC on day D−1 is almost always the **07:30:00Z** publication of D−1.
  *(The 09:30:00Z publication is published after the 09:00 cutoff and is therefore correctly excluded to prevent data leakage).*

---

## 5. Network, Latency & Rate Limits

- **Auth:** No API key required; open access.
- **Latency:**
  - FUELHH (31 days, ~1.5k rows): ~1.9s.
  - WINDFOR (33 days, ~19.3k rows): ~2.3s.
- **Burst Test:** 5 sequential calls executed with 0 errors, averaging 0.85s per request.
- **Rate Limit Headers:** No `X-RateLimit-*` or `Retry-After` headers were returned.
- **HTTP 429:** No 429 responses were observed during testing. However, client-side caching and retry with exponential backoff remain best practice.

---

## 6. Critical Resolution Discrepancy & Impact on Plan

> [!WARNING] Hourly WINDFOR vs Half-Hourly FUELHH Resolution
> - **FUELHH** is published at **30-minute intervals** (`:00:00Z` and `:30:00Z`), totaling **1,488 periods** in January 2026.
> - **WINDFOR** is published at **60-minute intervals** (`:00:00Z` only), totaling **744 hourly periods** in January 2026. There are **zero `:30:00Z` timestamps** in WINDFOR.

### Decision Adopted:
Following review of Phase 1 findings, the project adopted **Option A with an hourly evaluation grid**:
1. **Evaluation Grid (BR-01):** 744 top-of-hour periods in January 2026 (`:00:00Z` timestamps; 31 days × 24 hours).
2. **Matching (BR-06):** Exact `startTime` match only. FUELHH `:30` records are **not** used in metrics (no interpolation, persistence, or averaging).
3. **Context Field (P1):** `/api/series` adds an optional `actual_half_hour_context_mw` field to pass `:30` actuals for UI visual context only; this never enters error calculations.
4. **Open Question (Q-11):** Documented in [PRD §12](PRD.md#12-risks-and-unresolved-questions) and [FORECAST_LOGIC §4](FORECAST_LOGIC.md) that the physical meaning of WINDFOR (instantaneous at :00 vs 60-min average) remains unconfirmed and will be confirmed in subsequent steps.

---

## 7. WINDFOR Lookback Verification & Early Cutoff Analysis

We evaluated the sufficiency of the 2-day lookback window (`2025-12-30T00:00:00Z` to `2026-01-31T23:59:59Z`) across all 744 expected hourly delivery periods of January 2026 under varying decision cutoffs:

| Cutoff Time (D−1) | Matched Periods | Missing Forecast | Coverage (%) | Finding |
|---|---|---|---|---|
| `00:00 UTC` | 682 | 62 | 91.7% | 62 periods on Jan 1–2 require publications from D−2 late evening (29 Dec), falling outside the 2-day lookback |
| `03:00 UTC` | 744 | 0 | 100.0% | 100% covered |
| `06:00 UTC` | 744 | 0 | 100.0% | 100% covered |
| `09:00 UTC` (default) | 744 | 0 | 100.0% | 100% covered (picks 07:30 UTC publication of D−1) |
| `12:00 UTC` | 744 | 0 | 100.0% | 100% covered |
| `18:00 UTC` | 744 | 0 | 100.0% | 100% covered (picks 15:30 UTC publication of D−1) |
| `23:00 UTC` | 744 | 0 | 100.0% | 100% covered (picks 22:30 UTC publication of D−1) |

**Conclusion & Limitation:**
- For all practical daytime cutoffs (`≥ 03:00 UTC`), the 2-day lookback is **100% sufficient**.
- For early midnight cutoffs (`00:00 UTC`), 62 periods lack an eligible forecast in the 2-day lookback window. The system must handle this gracefully as `missing_forecast` without unhandled errors or data leakage (documented test requirement in `TESTING.md`).

---

## 8. Verification of Real Test Fixtures

Two real fixtures were extracted from live API calls and verified:

### 8.1 `backend/tests/fixtures/real_fuelhh_wind_sample.json`
- **Source:** `https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream?settlementDateFrom=2026-01-01&settlementDateTo=2026-01-01&fuelType=WIND`
- **Row count:** Exactly 48 rows (settlement periods 1 to 48 for date `2026-01-01`).
- **Cadence:** Uniform 1,800 seconds (30 minutes) between start times (`00:00:00Z` to `23:30:00Z`).
- **Fields:** `dataset` (str), `publishTime` (str), `startTime` (str), `settlementDate` (str), `settlementPeriod` (int), `fuelType` (str), `generation` (int).
- **Values:** Min `13,756 MW`, Max `16,408 MW`, zero nulls, zero negative numbers.

### 8.2 `backend/tests/fixtures/real_windfor_sample.json`
- **Source:** `https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream?publishDateTimeFrom=2025-12-31T07:30:00Z&publishDateTimeTo=2025-12-31T07:30:00Z`
- **Row count:** Exactly 48 rows (from the forecast run published `2025-12-31T07:30:00Z` covering target delivery periods from `2025-12-30T21:00:00Z` to `2026-01-01T20:00:00Z`).
- **Cadence:** Uniform 3,600 seconds (60 minutes) between start times.
- **Fields:** `dataset` (str), `publishTime` (str), `startTime` (str), `generation` (int).
- **Values:** Min `5,044 MW`, Max `20,028 MW`, zero nulls, zero negative numbers.

