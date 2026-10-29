# UK National Wind Generation Forecast Accuracy Analysis: January 2026

## 1. Executive Summary

This document presents empirical findings from evaluating Elexon BMRS national wind generation forecasts (`WINDFOR`) against actual metered generation outturn (`FUELHH`, wind fuel type) across the full month of **January 2026 (744 hourly settlement periods)**.

The primary evaluation uses a **day-ahead provisional decision cutoff of 09:00 Europe/London on $D-1$**. Under this benchmark:
- **Data Coverage:** 100.0% (744 of 744 expected top-of-hour delivery periods matched; 0 missing actuals, 0 missing forecasts).
- **Mean Absolute Error (MAE):** **2,127.5 MW** (representing **18.4%** of mean actual generation).
- **Root Mean Squared Error (RMSE):** **2,606.1 MW**.
- **Mean Error / Bias ($e = \text{Actual} - \text{Forecast}$):** **−1,851.5 MW**.
- **P90 Absolute Error:** **4,306.4 MW**.
- **Mean Actual Generation:** **11,581.1 MW**.
- **Mean Forecast Generation:** **13,432.6 MW**.

> [!IMPORTANT]
> **Provisional Assumption:** The 09:00 Europe/London cutoff on $D-1$ is an illustrative day-ahead procurement benchmark, not an official Elexon market gate-closure time.
> **Hourly Matching:** Accuracy is evaluated strictly at hourly top-of-hour intervals (`:00:00Z`). Half-hour (`:30`) actuals from FUELHH are excluded from metric calculations because WINDFOR publishes at hourly cadence and its physical definition (instantaneous spot vs. hourly average) remains unconfirmed in official BMRS documentation.

---

## 2. Accuracy & Systemic Bias Findings

### 2.1 Pronounced Over-Forecasting
Across January 2026, the national wind forecast exhibited substantial **over-forecasting**:
- The mean forecast outturn was **13,432.6 MW**, compared to an actual mean outturn of **11,581.1 MW**.
- Following the standard sign convention $e_i = \text{Actual}_i - \text{Forecast}_i$, the overall mean error (bias) was **−1,851.5 MW**.
- The ratio of $|Bias| / MAE = 1,851.5 / 2,127.5 \approx 87.0\%$, showing that the vast majority of the absolute forecast miss in January 2026 was directional over-estimation.

### 2.2 Statistical Distribution of Tail Errors (P90)
- The **P90 absolute error is 4,306.4 MW** (computed using linear interpolation, NumPy/Method 7).
- In 10% of the evaluated hours (approximately 74 hours across the month), the magnitude of the day-ahead forecast miss exceeded 4.3 GW.
- **Statistical Context:** This metric describes the upper tail of absolute forecast misses observed historically during January 2026. It serves as an empirical data point for distribution modeling, rather than a standalone operational reserve recommendation.

---

## 3. Daily Variation & Regime Breakdown

### 3.1 Bias Distribution Across Days
Evaluating daily aggregated metrics reveals that over-forecasting was persistent throughout the month:
- **27 out of 31 days (87.1%)** exhibited negative bias ($Actual < Forecast$).
- **Only 4 out of 31 days (12.9%)** exhibited positive bias ($Actual > Forecast$).
- **0 days** exhibited neutral/zero bias.

### 3.2 Best Days (Lowest MAE)
Days with the lowest forecast errors in the sample:

| Date | MAE (MW) | Bias (MW) | Mean Actual (MW) | Mean Forecast (MW) | Observed Outturn |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **2026-01-19** | **683.6** | +683.6 | 6,479.6 | 5,796.0 | Moderate generation; slight under-forecast |
| **2026-01-16** | **810.0** | −348.8 | 7,581.6 | 7,930.4 | Stable mid-merit generation; well-tracked ramp |
| **2026-01-09** | **876.8** | −816.4 | 10,745.4 | 11,561.8 | Consistent wind generation profile |

### 3.3 Worst Days (Highest MAE)
Days with the highest forecast errors in the sample:

| Date | MAE (MW) | Bias (MW) | Mean Actual (MW) | Mean Forecast (MW) | Observed Outturn |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **2026-01-28** | **5,329.0** | −5,329.0 | 5,805.6 | 11,134.6 | Forecast predicted ~11.1 GW; actual dropped to 5.8 GW |
| **2026-01-12** | **4,875.4** | −4,875.4 | 14,445.0 | 19,320.5 | Forecast predicted ~19.3 GW; actual was 14.4 GW |
| **2026-01-11** | **4,853.0** | −4,853.0 | 13,506.0 | 18,359.0 | Forecast predicted ~18.4 GW; actual was 13.5 GW |

*Empirical observation:* On all three worst days, $\text{MAE} = -\text{Bias}$, which mathematically proves that the forecast was strictly higher than actual generation for **every single hour** of those days ($Actual < Forecast$ across all 24 periods).

---

## 4. Decision Cutoff Sensitivity Analysis

By evaluating multiple decision cutoff times on $D-1$, we observe how accuracy metrics change as the decision point moves closer to delivery:

| Cutoff Time (Europe/London) | Selected Vintages (UTC on $D-1$) | Matched Periods | MAE (MW) | RMSE (MW) | Bias (MW) | P90 Abs Error (MW) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **06:00** | 04:30 | 744 (100%) | 2,128.6 | 2,632.0 | −1,798.0 | 4,379.1 |
| **09:00 (Default)** | 07:30 | 744 (100%) | 2,127.5 | 2,606.1 | −1,851.5 | 4,306.4 |
| **12:00** | 09:30, 11:30 | 744 (100%) | 2,002.9 | 2,470.1 | −1,805.9 | 4,000.0 |
| **15:00** | 11:30, 12:25 | 744 (100%) | 2,005.2 | 2,471.9 | −1,811.1 | 4,000.0 |
| **18:00** | 15:30 | 744 (100%) | 1,968.3 | 2,434.7 | −1,816.5 | 4,024.6 |
| **22:00** | 18:30 | 744 (100%) | 1,963.9 | 2,434.9 | −1,795.3 | 4,009.1 |

### Observed Sensitivity Patterns:
1. **Early Morning Invariance:** Between 06:00 and 09:00, MAE changes by only 1.1 MW (2,128.6 to 2,127.5 MW), reflecting minor updates between the 04:30 and 07:30 UTC publication runs.
2. **Midday Improvement:** At 12:00, MAE drops by **124.6 MW** (to 2,002.9 MW) and P90 absolute error drops by **306.4 MW** (to 4,000.0 MW) once mid-morning publications (09:30/11:30 UTC) become available.
3. **Evening Diminishing Returns:** Delaying the cutoff to 18:00 or 22:00 yields an additional ~39 MW improvement in MAE, reaching a floor near 1,964 MW.
4. **Persistent Over-Forecasting:** Across all tested cutoff times from 06:00 to 22:00, the mean bias remains consistently negative (between −1,795 MW and −1,852 MW). This indicates that the over-forecasting tendency was present across successive forecast publication vintages throughout the month.

---

## 5. Forecast Vintage Selection Pattern

Under the default `09:00 Europe/London` cutoff on $D-1$:
- For **all 31 days** in January 2026, the backend selected the **`07:30 UTC` publication** on $D-1$.
- WINDFOR publishes at regular daily intervals (including ~04:30, 07:30, 09:30, 11:30, 15:30, 18:30, and 21:30 UTC).
- Because `07:30 UTC` is the latest publication timestamp at or before `09:00 Europe/London` (which equals 09:00 UTC in January), it was selected uniformly across all 31 days.
- This creates an effective day-ahead forecast horizon ranging from **16.5 hours** (for delivery period 00:00 UTC) to **40.5 hours** (for delivery period 23:00 UTC).

---

## 6. Independent Hand-Calculation Cross-Check: 2026-01-15

To verify computation integrity and ensure the API produces exact mathematical results, all 24 hours of **January 15, 2026** were extracted and recomputed independently from raw matched records:

### 6.1 Hour-by-Hour Raw Data (2026-01-15)

| Delivery Time (UTC) | Actual (MW) | Forecast (MW) | Error ($A - F$) (MW) | Abs Error (MW) | Squared Error ($\text{MW}^2$) | Selected Vintage ($D-1$) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 2026-01-15 00:00 | 14,602.0 | 15,834.0 | −1,232.0 | 1,232.0 | 1,517,824.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 01:00 | 14,200.0 | 15,478.0 | −1,278.0 | 1,278.0 | 1,633,284.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 02:00 | 14,534.0 | 15,066.0 | −532.0 | 532.0 | 283,024.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 03:00 | 14,028.0 | 14,655.0 | −627.0 | 627.0 | 393,129.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 04:00 | 13,901.0 | 14,497.0 | −596.0 | 596.0 | 355,216.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 05:00 | 13,704.0 | 14,419.0 | −715.0 | 715.0 | 511,225.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 06:00 | 13,256.0 | 14,017.0 | −761.0 | 761.0 | 579,121.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 07:00 | 13,401.0 | 13,411.0 | −10.0 | 10.0 | 100.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 08:00 | 12,719.0 | 12,931.0 | −212.0 | 212.0 | 44,944.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 09:00 | 12,242.0 | 12,576.0 | −334.0 | 334.0 | 111,556.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 10:00 | 9,807.0 | 12,081.0 | −2,274.0 | 2,274.0 | 5,171,076.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 11:00 | 9,930.0 | 11,578.0 | −1,648.0 | 1,648.0 | 2,715,904.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 12:00 | 9,742.0 | 11,049.0 | −1,307.0 | 1,307.0 | 1,708,249.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 13:00 | 8,843.0 | 10,378.0 | −1,535.0 | 1,535.0 | 2,356,225.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 14:00 | 8,384.0 | 9,619.0 | −1,235.0 | 1,235.0 | 1,525,225.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 15:00 | 8,482.0 | 9,050.0 | −568.0 | 568.0 | 322,624.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 16:00 | 8,543.0 | 8,864.0 | −321.0 | 321.0 | 103,041.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 17:00 | 8,266.0 | 8,870.0 | −604.0 | 604.0 | 364,816.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 18:00 | 7,672.0 | 8,962.0 | −1,290.0 | 1,290.0 | 1,664,100.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 19:00 | 7,631.0 | 9,130.0 | −1,499.0 | 1,499.0 | 2,247,001.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 20:00 | 7,592.0 | 9,059.0 | −1,467.0 | 1,467.0 | 2,152,089.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 21:00 | 7,603.0 | 9,049.0 | −1,446.0 | 1,446.0 | 2,090,916.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 22:00 | 7,685.0 | 9,091.0 | −1,406.0 | 1,406.0 | 1,976,836.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 23:00 | 7,258.0 | 8,966.0 | −1,708.0 | 1,708.0 | 2,917,264.0 | 2026-01-14 07:30 UTC |

### 6.2 Mathematical Verification & Reconciliation

- **Actual Sum:** $\sum \text{Actual} = 254,025.0\text{ MW} \implies \text{Mean Actual} = 254,025.0 / 24 = \mathbf{10,584.375\text{ MW}}$
- **Forecast Sum:** $\sum \text{Forecast} = \mathbf{278,630.0\text{ MW}} \implies \text{Mean Forecast} = 278,630.0 / 24 = \mathbf{11,609.583\text{ MW}}$
- **Signed Error Sum:** $\sum (A - F) = \mathbf{−24,605.0\text{ MW}} \implies \text{Bias} = -24,605.0 / 24 = \mathbf{−1,025.208\text{ MW}}$
- **Absolute Error Sum:** $\sum |A - F| = \mathbf{24,605.0\text{ MW}} \implies \text{MAE} = 24,605.0 / 24 = \mathbf{1,025.208\text{ MW}}$
- **Squared Error Sum:** $\sum (A - F)^2 = \mathbf{32,744,789.0\text{ MW}^2} \implies \text{RMSE} = \sqrt{32,744,789.0 / 24} = \mathbf{1,168.061\text{ MW}}$

| Metric | Hand-Calculated Value | API Daily Endpoint (`/api/series?granularity=daily`) | Agreement |
| :--- | :--- | :--- | :---: |
| **Mean Actual** | 10,584.375 MW | 10,584.4 MW | **Exact** |
| **Mean Forecast** | 11,609.583 MW | 11,609.6 MW | **Exact** |
| **MAE** | 1,025.208 MW | 1,025.2 MW | **Exact** |
| **RMSE** | 1,168.061 MW | 1,168.1 MW | **Exact** |
| **Bias** | −1,025.208 MW | −1,025.2 MW | **Exact** |

---

## 7. Reproducibility

Every table and figure in this report can be programmatically reproduced from scratch using the automated verification script:

```bash
# Execute against live Elexon data via FastAPI backend
backend/.venv/Scripts/python scripts/generate_analysis.py
```

The script queries the `/api/summary`, `/api/series`, and `/api/records` endpoints, calculates sample sums, runs the sensitivity iterations, and outputs the exact tables above.

---

## 8. Limitations & Methodology Disclosures

1. **Provisional Cutoff Assumption:**
   The 09:00 Europe/London cutoff on $D-1$ is a chosen analytical benchmark reflecting typical morning trading decision workflows. Market participants operating under different gate closures (e.g., 12:00 Day-Ahead Auction or 1-hour ahead gate closure) can utilize the interactive cutoff selector to obtain their specific accuracy profile.
2. **Hourly Grid & Half-Hour Exclusion Limitation:**
   Accuracy is measured strictly at hourly top-of-hour points (`:00:00Z`). Elexon BMRS documentation does not specify whether `WINDFOR` represents instantaneous power at `:00` or an integrated hourly average. Because `:30` FUELHH readings represent distinct half-hour physical settlement periods, interpolating or averaging actuals without documented basis was rejected to avoid introducing artificial distortion.
3. **Single Winter Month Scope:**
   January represents a high-wind winter regime characterized by active Atlantic storm depressions. Results should not be generalized to summer low-wind regimes without evaluating additional seasonal data.
