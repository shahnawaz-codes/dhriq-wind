# UI_UX.md — Design System and UX

> Users: electricity procurement analysts who must judge forecast quality fast.
> Rule: every element supports a decision. No decoration. **No invented or hardcoded numbers shown as real data.**
> Related: [PRD](PRD.md) · [API_SPEC](API_SPEC.md) · [FORECAST_LOGIC](FORECAST_LOGIC.md)

## 1. Visual direction
Calm, professional energy-analytics look: light neutral background, white cards, thin borders, one strong blue and one amber for the two data series, generous whitespace, tabular numbers. No gradients, illustrations, or animations except a subtle loading skeleton. (Dark mode: P2.)

## 2. Layout (desktop ≥ 1024 px)

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Header: "UK Wind Forecast Accuracy"  · Jan 2026 · UTC label         │
├──────────────────────────────────────────────────────────────────────┤
│ Assumptions banner (provisional cutoff rule, how forecasts selected) │
├──────────────────────────────────────────────────────────────────────┤
│ Filters: [Start date] [End date] [Cutoff time (P0)] [Granularity P1] │
├───────────┬───────────┬───────────┬───────────┬──────────────────────┤
│ MAE (MW)  │ RMSE (MW) │ Bias (MW) │ Matched   │ P90 / MAE% (P1)      │
├───────────┴───────────┴───────────┴───────────┴──────────────────────┤
│ Chart: Actual vs forecast (MW)                          [zoom P1]    │
├──────────────────────────────────────────┬───────────────────────────┤
│ Records table (sort, page, filters)      │ Side panel (P1):          │
│                                          │ Forecast vintages, data   │
│                                          │ quality                   │
├──────────────────────────────────────────┴───────────────────────────┤
│ Footer: Source Elexon Insights API · FUELHH, WINDFOR · fetched at … │
└──────────────────────────────────────────────────────────────────────┘
```
Single page, no router needed. Data-quality and provenance may be a collapsible panel in the footer for P0 (side panel is P1).

## 3. Navigation
One-page dashboard with anchored sections (Summary, Chart, Records, Data & method). Skip-to-content link. A "Method" popover/drawer explains forecast selection in 5 lines and links to the README.

## 4. Typography
System UI stack: `Inter, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` (Inter optional via local font; no external CDN needed). Numbers use `font-variant-numeric: tabular-nums`.

| Token | Size / line | Use |
|---|---|---|
| `--text-xs` | 12 / 16 | captions, axis labels |
| `--text-sm` | 14 / 20 | table, helper text |
| `--text-md` | 16 / 24 | body |
| `--text-lg` | 20 / 28 | section titles |
| `--text-xl` | 28 / 36 | KPI values |

## 5. Spacing scale
4-point scale: `--space-1: 4px, -2: 8, -3: 12, -4: 16, -5: 24, -6: 32, -7: 48`. Card padding `--space-5`; grid gap `--space-4`; border radius `6px`.

## 6. Color tokens

| Token | Value | Use | Contrast note |
|---|---|---|---|
| `--bg` | `#F6F8FA` | page | |
| `--surface` | `#FFFFFF` | cards | |
| `--border` | `#D0D7DE` | borders | |
| `--text` | `#1F2933` | body | ≥ 12:1 on surface |
| `--text-muted` | `#52606D` | secondary | ≥ 6:1 |
| `--actual` | `#1B5E9E` | actual series | solid line |
| `--forecast` | `#C2570C` | forecast series | **dashed** line (not colour alone) |
| `--error-pos` | `#0F766E` | actual > forecast (under-forecast) | always with sign/label |
| `--error-neg` | `#B42318` | actual < forecast (over-forecast) | always with sign/label |
| `--warning-bg` / `--warning-text` | `#FFF4E5` / `#7A4100` | assumptions, stale data | |
| `--danger-bg` / `--danger-text` | `#FEECEB` / `#8A1C14` | errors | |
| `--focus` | `#0B5FFF` | focus ring 2 px | |

Verify all text/background pairs ≥ 4.5:1 (3:1 for large text and chart lines) with a contrast tool in Phase 4.

## 7. Components

| Component | Notes |
|---|---|
| `AppHeader`, `AssumptionsBanner` | Banner text from `/api/meta` `assumptions`; labelled "Provisional" with a link to Method |
| `FilterBar` | Native `<input type="date">` with `min/max` = window; inline validation message; P0 cutoff `<input type="time">` with "Apply"; granularity segmented control (P1) |
| `KpiCard` | Label, value + unit, one-line meaning, info tooltip (focusable button). `null` shows "—" with "No matched periods" |
| `ActualForecastChart` | Recharts line chart, two series, `connectNulls={false}`, Y axis "MW", X axis UTC time, legend, custom tooltip |
| `RecordsTable` | Semantic `<table>`, sortable headers (buttons with `aria-sort`), pager, status chips with text |
| `StatusChip` | `matched`, `missing forecast`, `missing actual`, `missing both` (text + icon, not colour only) |
| `VintagesPanel` (P1) | List of `publish_time` used and periods count |
| `DataQualityPanel` | Counts of expected/matched/missing/invalid/duplicates + warnings |
| `ProvenanceFooter` | Source, datasets, fetched at (UTC), cache age, stale warning, Elexon attribution |
| `StateViews` | `Loading` skeleton, `EmptyState`, `ErrorState` (message + Retry) |

## 8. Chart interaction
- Hover/focus shows tooltip: time (UTC), actual MW, forecast MW, error MW (signed), forecast `publishTime` (UTC), horizon in hours.
- Missing points: gap in line; tooltip says "No actual" / "No forecast eligible at cutoff".
- Legend toggles series (keyboard accessible).
- P1: `Brush` for zoom; "Reset zoom" button. Daily granularity switches to daily mean lines + MAE column in tooltip.
- Chart has a text summary above it (e.g. "Showing 744 hourly periods, 1–31 Jan 2026 UTC") and the table is the accessible data alternative.
- Axis uses fixed unit "MW"; Y axis starts at 0.

## 9. Table behaviour
- Columns: Start time (UTC), Actual (MW), Forecast (MW), Error (MW, signed), Abs error (MW), Forecast published (UTC), Horizon (h), Status.
- Server-side sort (click header toggles asc/desc), page size select 25/50/100, shows "Showing x–y of N".
- P1 filters: status select, minimum absolute error.
- Numbers right-aligned, 1 decimal for MW; dates `YYYY-MM-DD HH:mm`.
- Null cells display "—".

## 10. Date and period selection
Start/end date inputs limited to the window; invalid ranges (end < start) disable Apply and show message. Quick presets (P1): "Whole January", "Week 1–4". Cutoff time (P0) default from `/api/meta`; changing it shows a "Recalculating…" state; a "Reset to default" action appears when changed.

## 11. States

| State | Behaviour |
|---|---|
| Loading | Skeletons for KPIs/chart/table; text "Loading data from Elexon… first load can take up to a minute" if > 3 s; `aria-live="polite"` |
| Empty | "No matched periods for this selection." with suggestion to widen dates; KPIs "—" |
| Error | Plain message, error code, Retry button; no stack traces |
| Stale data | Amber banner: "Showing cached data from <time>. Elexon could not be reached." |
| 503 not ready | Auto-retry every 5 s, up to 12 times, with message |

## 12. Responsive behaviour
- ≥ 1024: layout above. 640–1023: KPI cards 2 per row, side panel moves below table. < 640: single column, table scrolls horizontally inside its own container, filters stack; chart min-height 280 px.

## 13. Accessibility (WCAG 2.2 AA target)
- Full keyboard use; visible 2 px focus ring; logical tab order; skip link.
- Landmarks (`header`, `main`, `footer`), one `h1`, ordered headings.
- Colour never the only signal (dashed forecast line, status text, signed numbers).
- Tooltips open on focus and hover and close with Esc.
- Form labels, error text linked with `aria-describedby`.
- Loading/error regions use `aria-live`.
- Minimum target size 24×24 px. Respect `prefers-reduced-motion`.
- Test: keyboard-only pass + axe/Lighthouse in Phase 4/6.

## 14. Clear units and explanatory text (copy)

| Item | Tooltip text |
|---|---|
| MAE | "Mean Absolute Error: the average size of the miss, in MW, ignoring direction." |
| RMSE | "Root Mean Squared Error, in MW. Like MAE but penalises large misses more." |
| Bias | "Mean of (actual − forecast), in MW. Positive: forecasts were too low on average. Negative: too high." |
| P90 (P1) | "90% of evaluated hourly periods had an error at or below this size." |
| Matched | "Hourly periods that have both an actual and an eligible forecast." |
| Cutoff | "Only forecasts published at or before this time on the day before delivery are used. This is a provisional assumption." |

## 15. Data freshness and provenance indicators
Always visible in footer and in an info popover: source (Elexon Insights API), datasets (FUELHH wind, WINDFOR), "Fetched at <UTC>", "Cache age <n> min", stale flag, and the data window. Chart subtitle shows the active cutoff rule.

## 16. Do / Don't
- Do show "—" and explain when data is missing. Don't show 0.
- Do keep all numbers from the API. Don't compute metrics in React.
- Don't use placeholder numbers in the UI, even while building (use skeletons).
