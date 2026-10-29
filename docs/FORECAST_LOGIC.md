# FORECAST_LOGIC.md — Forecast Selection and Accuracy Evaluation

> **Most important document.** All code in `backend/app/domain/` MUST implement exactly this file.
> If a rule here changes, update this file, `TESTING.md`, `API_SPEC.md` and `DATA_DICTIONARY.md` in the same commit.
> Related: [PRD](PRD.md) · [DATA_DICTIONARY](DATA_DICTIONARY.md) · [TESTING](TESTING.md)

## 1. Status legend

| Tag | Meaning |
|---|---|
| **[CONFIRMED]** | Stated in the challenge document or official Elexon docs |
| **[PROVISIONAL]** | Our assumption. Not specified by the challenge. Must be configurable and shown in the UI |
| **[VERIFY]** | Must be checked against live Elexon data in Phase 1 |

## 2. What the challenge says (and does not say)

**[CONFIRMED] from the challenge document:**
- Buyers must buy from the UK **day-ahead market**; decisions are made **one day before the delivery day**.
- They need "the latest renewable generation forecasts **available when they need to make decisions**".
- They need to quantify forecast accuracy.
- Only Elexon FUELHH (actuals, `fuelType = WIND`) and WINDFOR (forecasts) are used. National level only.
- "Consider data relevant only for purchase decisions to be made in **January 2026**."

**NOT specified (we must not pretend otherwise):**
1. The exact clock time of the day-ahead decision.
2. Whether "decisions made in January" means decision date or delivery date in January.
3. Whether a forecast published exactly at the cutoff is eligible.

These are handled as provisional rules (Section 4) and listed in [PRD §Open questions](PRD.md#12-risks-and-unresolved-questions).

## 3. Time concepts

| Term | Source field | Meaning | Status |
|---|---|---|---|
| Delivery time | `startTime` (both datasets) | Start of the hourly delivery period in the evaluation grid (`[startTime, startTime + 1 hour)`). FUELHH provides 30-minute actuals (`:00` and `:30`), but only the top-of-hour `:00:00Z` actuals are matched in metrics | [CONFIRMED] from live API: WINDFOR is strictly hourly |
| Publication time | `publishTime` (WINDFOR) | When this forecast was created/published | [CONFIRMED] "time at which the forecast was created" |
| Decision cutoff | derived | Last moment at which information may be used for the day-ahead decision for delivery date D | [PROVISIONAL] |
| Delivery date D | derived | Calendar date of `startTime` in `Europe/London` | [PROVISIONAL] |
| Forecast horizon | derived | `startTime − publishTime` (hours) | derived |

Delivery time and publication time are **different axes**. A forecast row says: "at `publishTime`, we predict `generation` MW for `startTime`".
The same `startTime` has **many** forecast rows (one per publication). This is why a selection rule is needed.

## 4. Business rules

| ID | Rule | Status |
|---|---|---|
| **BR-01** Evaluation window | Evaluate delivery periods with `startTime` in `[2026-01-01T00:00:00Z, 2026-02-01T00:00:00Z)` at **hourly resolution** (top-of-hour timestamps `:00:00Z`). That is 31 days × 24 = **744** expected periods. Configurable via `DELIVERY_WINDOW_START` / `DELIVERY_WINDOW_END` | [PROVISIONAL] (see Q-01, Q-11) |
| **BR-02** Decision cutoff | For delivery date D, cutoff = **(D − 1 day) at 09:00 `Europe/London`**, converted to UTC. One cutoff per delivery date (all 24 hourly periods of D share it). Config: `DECISION_CUTOFF_LOCAL_TIME=09:00`, `DECISION_TIMEZONE=Europe/London`. The "D − 1" part is fixed, not configurable | [PROVISIONAL] (Q-02) |
| **BR-03** Eligibility | A forecast row is eligible for delivery period `startTime = t` iff `row.startTime == t` AND `row.publishTime <= cutoff(D(t))`. **Boundary is inclusive**: published exactly at cutoff = eligible | [PROVISIONAL] (Q-03) |
| **BR-04** Selection | Among eligible rows for `t`, select the one with the **greatest `publishTime`**. If no eligible row exists, the period has **no forecast** (never fall back to a later forecast) | follows from challenge text |
| **BR-05** Duplicates | See Section 8 | [PROVISIONAL] |
| **BR-06** Matching | Match actual and selected forecast by **exact `startTime` (UTC instant) on the hourly grid (`:00:00Z`)**. FUELHH `:30` periods are **not used in metrics**. No interpolation, no persistence, no averaging | [CONFIRMED DECISION] (Q-11) |
| **BR-07** Missing data | Periods missing an actual and/or forecast are listed in records with a status and **excluded from metrics**. Never filled with zero | [PROVISIONAL] |
| **BR-08** Invalid values | `generation` that is null, non-numeric, NaN, infinite, or negative is invalid. Row is dropped and counted in `data_quality` | [PROVISIONAL] |
| **BR-09** Metric population | Metrics use **matched periods only** (valid actual AND selected valid forecast) | [PROVISIONAL] |
| **BR-10** Error sign | `error = actual − forecast`. Positive = forecast was too low (under-forecast); negative = forecast too high (over-forecast) | [CONFIRMED] by task spec |

### Why is the evaluation grid hourly (744 periods)?
Investigation of the live Elexon API in Phase 1 ([API_FINDINGS.md](API_FINDINGS.md)) revealed that **WINDFOR data is published strictly at 1-hour intervals (`:00:00Z` only)**. There are zero half-hourly (`:30:00Z`) forecast rows in WINDFOR. Meanwhile, FUELHH actuals are reported half-hourly (`:00` and `:30`).

The exact physical meaning of the WINDFOR number is unconfirmed in official documentation: does it represent an instantaneous power level at `:00`, or an hourly average power across the 60 minutes?
- Rather than inventing or assuming a synthetic mapping (e.g. step-forward persistence, interpolation, or averaging FUELHH actuals), we adopt **Option A**: evaluate strictly at hourly points where both datasets have a native observation (`startTime == :00:00Z`).
- **FUELHH `:30` periods are excluded from metrics calculation.** They may optionally be served in the series API as context only (P1), but never enter MAE, RMSE, bias, or data quality denominators.
- This maintains 100% fidelity to Rule R10 ("Never fabricate") and provides an uncorrupted, transparent evaluation across the **744 expected hourly periods** of January 2026. This open question is documented as **Q-11** in [PRD §12](PRD.md#12-risks-and-unresolved-questions).

### Why 09:00 as the default cutoff?
It is a **placeholder** for "morning of D−1, before day-ahead auctions close". We did not verify the GB day-ahead market gate-closure time in this project, and the challenge does not give one.
In Phase 1, we confirmed that WINDFOR forecasts are published 8 times daily at `02:30`, `04:30`, `07:30`, `09:30`, `11:30`, `15:30`, `18:30`, and `22:30 UTC`.
Under a `09:00 UTC` cutoff, the latest eligible publication is the **`07:30 UTC`** publication. Under an `18:00 UTC` cutoff, it is the **`15:30 UTC`** publication. The result is sensitive to the cutoff, which is why the cutoff selector is a P0 requirement.

### Hard rule
> **Never** use the "latest forecast for the period" without the cutoff filter. That is **data leakage**: it uses information that the buyer did not have when deciding.

## 5. Algorithm (reference pseudo-code)

```text
INPUT: actuals[], forecasts[], window, cutoff_local_time, tz
1. Normalise + validate rows (Section 8), drop invalid, dedupe.
2. Build expected grid T = every 1-hour UTC instant (:00:00Z) in window.
3. For each t in T:
     D       = local_date(t, tz)
     cutoff  = to_utc(local_datetime(D - 1 day, cutoff_local_time, tz))
     F_t     = forecasts where startTime == t AND publishTime <= cutoff
     fc      = argmax(F_t, key=publishTime)   # None if F_t empty
     ac      = actual_by_start[t]             # None if missing (only :00:00Z actuals match)
     status  = matched | missing_forecast | missing_actual | missing_both
     if matched:
         error     = ac.mw - fc.mw
         abs_error = abs(error)
         horizon_h = (t - fc.publishTime) in hours
4. Metrics over matched records (Section 7).
```

Implementation modules (each independently testable, pure functions, no I/O):
`cutoff.py` (cutoff computation) · `selection.py` (steps 3 selection) · `matching.py` (grid + join) · `metrics.py` (Section 7).

## 6. Worked example (illustrative, **not real data**)

Delivery period `startTime = 2026-01-15T12:00Z`, so D = 2026-01-15 and cutoff = 2026-01-14T09:00Z (GMT = UTC in January).

| Forecast publishTime | Eligible? | Reason |
|---|---|---|
| 2026-01-14T05:30Z | yes | before cutoff |
| 2026-01-14T08:30Z | yes, **selected** | latest eligible |
| 2026-01-14T09:00Z | yes if no later eligible | exactly at cutoff (inclusive) — would be selected over 08:30 |
| 2026-01-14T10:30Z | **no** | after cutoff = leakage |
| 2026-01-15T03:30Z | **no** | after cutoff = leakage |

## 7. Metric definitions

Let matched periods i = 1..n, `e_i = actual_i − forecast_i` (MW).

| Metric | Formula | Unit | Notes |
|---|---|---|---|
| Absolute error | `|e_i|` | MW | per period |
| **MAE** | `(1/n) Σ |e_i|` | MW | |
| **RMSE** | `sqrt((1/n) Σ e_i²)` | MW | penalises large misses |
| **Mean error (bias)** | `(1/n) Σ e_i` | MW | positive = forecasts too low on average |
| MAE % of mean actual *(P1)* | `MAE / mean(actual)` × 100 | % | null if `mean(actual) == 0` |
| P90 absolute error *(P1)* | 90th percentile of `|e_i|`, linear interpolation (NumPy "linear" method) | MW | useful as a buffer size |
| Coverage | `n_matched / n_expected` × 100 | % | data completeness (n_expected = 744 for full January) |

Do **not** compute MAPE (actual can be near 0, which makes it unstable).

**Aggregation across January:** all matched hourly periods in the selected date range are pooled with equal weight. Daily values (`granularity=daily`) apply the same formulas to the periods of each delivery date. The January figure is **not** the average of daily figures (it differs if days have different `n`).

**Rounding:** compute at full precision; round only for display/JSON output to 1 decimal (MW) and 1 decimal (%).

## 8. Data quality handling

| Case | Handling |
|---|---|
| Empty actuals or forecasts | HTTP 200, `n_matched = 0`, all metrics `null`, `data_quality.warnings` explains. UI shows empty state. Never return 0 as a metric |
| Missing actual for a period | status `missing_actual`; excluded from metrics; counted |
| Missing forecast (none eligible) | status `missing_forecast`; excluded; counted |
| Null/NaN/inf/negative generation | dropped, counted in `invalid_actual_rows` / `invalid_forecast_rows` |
| Unparseable `startTime`/`publishTime` | row dropped, counted as invalid |
| Duplicate actual (same `startTime`, `fuelType=WIND`) | keep the one with latest `publishTime` if present, else the last received; count in `duplicate_actual_rows`. If values differ, add a warning |
| Duplicate forecast (same `startTime` + `publishTime`) | if same `generation`: keep one. If different: keep last received, add a warning, count in `conflicting_forecast_rows` |
| Row outside window | ignored (not counted as invalid) |
| Upstream failure | see ARCHITECTURE §Error handling; never replace with fake data |

## 9. Timezone and DST

- Elexon timestamps are verified as **UTC instants** (`YYYY-MM-DDTHH:MM:SSZ`). All internal datetimes are timezone-aware UTC.
- `Europe/London` is used **only** to compute the cutoff and the delivery date D (use `zoneinfo`, package `tzdata` in Docker).
- **January 2026 is GMT (UTC+0)**: no DST change occurs in the window (BST starts 29 March 2026), so every day has exactly 24 hourly periods (and 48 half-hour settlement periods in raw FUELHH) and local time = UTC. The code must still use proper timezone conversion so changing the window to a DST month does not silently break (test with a March/October fixture).
- Non-existent/ambiguous local cutoff times (DST gaps) are out of scope for January; add a unit test documenting the chosen behaviour (`zoneinfo` default `fold=0`).
- The API returns all instants as ISO-8601 UTC strings ending in `Z`. The UI shows UTC and labels it "UTC (= GMT in January)".

## 10. Data leakage prevention checklist

- [ ] Filter is applied on `publishTime <= cutoff`, **before** picking the maximum.
- [ ] Actual data is never used as an input to forecast selection.
- [ ] A forecast published after the cutoff never appears in `records`, `series` or `summary`.
- [ ] The response always echoes the cutoff rule used (`assumptions` object).
- [ ] Tests cover before / exactly-at / after cutoff (see [TESTING §4](TESTING.md#4-forecast-selection-tests)).

## 11. Configuration surface (single source of truth)

| Env var | Default | Used by |
|---|---|---|
| `DECISION_CUTOFF_LOCAL_TIME` | `09:00` | default cutoff when API `cutoff_time` is absent |
| `DECISION_TIMEZONE` | `Europe/London` | cutoff + delivery date |
| `DELIVERY_WINDOW_START` | `2026-01-01` | BR-01 (inclusive date) |
| `DELIVERY_WINDOW_END` | `2026-01-31` | BR-01 (inclusive date) |
| `FORECAST_PUBLISH_LOOKBACK_DAYS` | `2` | how many days before window start to request WINDFOR publications |

API clients may override the cutoff **per request** with `cutoff_time=HH:MM` (see [API_SPEC](API_SPEC.md)). The inclusive boundary (BR-03) is fixed.
