# UK National Wind Generation Forecast Accuracy Analysis: January 2026

## 1. Executive Summary

This document presents empirical findings from evaluating Elexon BMRS national wind generation forecasts (`WINDFOR`) against actual metered generation outturn (`FUELHH`, wind fuel type) across the full month of **January 2026 (744 hourly settlement periods)**.

The primary evaluation uses a **day-ahead provisional decision cutoff of 09:00 Europe/London on $D-1$**. Under this benchmark:
- **Data Coverage:** 100.0% (744 of 744 expected top-of-hour delivery periods matched).
- **Mean Absolute Error (MAE):** **2,127.5 MW** (representing **18.4%** of mean actual generation).
- **Root Mean Squared Error (RMSE):** **2,606.1 MW**.
- **Mean Error / Bias ($e = \text{Actual} - \text{Forecast}$):** **−1,851.5 MW**.
- **P90 Absolute Error:** **4,306.4 MW**.
- **Mean Actual Generation:** **11,581.1 MW**.
- **Mean Forecast Generation:** **13,432.6 MW**.

> [!IMPORTANT]
> **Provisional Assumption:** The 09:00 Europe/London cutoff on $D-1$ is an illustrative day-ahead procurement benchmark, not an official Elexon market gate-closure time.
> **Hourly Matching:** Accuracy is evaluated strictly at hourly top-of-hour intervals (`:00:00Z`). Half-hour (`:30`) actuals from FUELHH are excluded from metric calculations because WINDFOR publishes at hourly cadence and its physical definition (instantaneous spot vs hourly average) remains unconfirmed in official BMRS documentation.

---

## 2. Accuracy & Systemic Bias Findings

### 2.1 Pronounced Over-Forecasting
Across January 2026, the national wind forecast exhibited substantial and systemic **over-forecasting**:
- The mean forecast outturn was **13,432.6 MW**, compared to an actual mean outturn of **11,581.1 MW**.
- Following the standard sign convention $e_i = \text{Actual}_i - \text{Forecast}_i$, the overall mean error (bias) was **−1,851.5 MW**.
- The ratio of $|Bias| / MAE = 1,851.5 / 2,127.5 \approx 87.0\%$, demonstrating that the vast majority of the absolute error was directional over-estimation rather than random symmetric noise.

### 2.2 Tail Risk & Reserve Sizing
- The **P90 absolute error is 4,306.4 MW** (computed using linear interpolation, NumPy/Method 7).
- In 10% of the hours (approximately 74 hours over the month), the day-ahead forecast missed actual generation by more than 4.3 GW.
- **Commercial Risk Buffer Implication:** Traders or system operators procuring power based solely on day-ahead wind forecasts would have experienced severe deficit volume in the balancing mechanism. Sizing procurement buffers to cover the P90 tail (4.3 GW) or adjusting the forecast baseline downward by the ~1.85 GW systemic bias is essential to avoid punitive cash-out prices.

---

## 3. Daily Variation & Extreme Regimes

### 3.1 Bias Distribution Across Days
Evaluating daily aggregated metrics reveals that the over-forecasting tendency was persistent across the month:
- **27 out of 31 days (87.1%)** had a negative bias (forecast higher than actual).
- **Only 4 out of 31 days (12.9%)** had a positive bias (forecast lower than actual).

### 3.2 Best Days (Lowest MAE)
On calm or stable meteorological days, day-ahead forecasts performed with high precision:

| Date | MAE (MW) | Bias (MW) | Mean Actual (MW) | Mean Forecast (MW) | Regime Characteristics |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **2026-01-19** | **683.6** | +683.6 | 6,479.6 | 5,796.0 | Moderate generation; slight under-forecast |
| **2026-01-16** | **810.0** | −348.8 | 7,581.6 | 7,930.4 | Stable mid-merit generation; well-tracked ramp |
| **2026-01-09** | **876.8** | −816.4 | 10,745.4 | 11,561.8 | Consistent high-pressure wind profile |

### 3.3 Worst Days (Highest MAE)
The largest forecast errors coincided with high-generation storm systems and rapid frontal passages where weather models anticipated higher sustained generation than materialized:

| Date | MAE (MW) | Bias (MW) | Mean Actual (MW) | Mean Forecast (MW) | Regime Characteristics |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **2026-01-28** | **5,329.0** | −5,329.0 | 5,805.6 | 11,134.6 | Massive over-prediction; actual wind dropped |
| **2026-01-12** | **4,875.4** | −4,875.4 | 14,445.0 | 19,320.5 | Forecast predicted ~19.3 GW near-capacity; outturn 14.4 GW |
| **2026-01-11** | **4,853.0** | −4,853.0 | 13,506.0 | 18,359.0 | Prolonged gale forecast over-estimated peak generation |

Notice that for each of the worst days, $\text{MAE} = -\text{Bias}$, meaning that for **every single hour of that day**, the forecast exceeded the actual outturn ($Actual < Forecast$ across all 24 hours).

---

## 4. Decision Cutoff Sensitivity Analysis

By testing multiple decision cutoff times on $D-1$, we measure how forecast accuracy evolves as the trading decision horizon moves closer to the delivery date:

| Cutoff Time (Europe/London) | Selected Vintages (UTC on $D-1$) | Matched Periods | MAE (MW) | RMSE (MW) | Bias (MW) | P90 Abs Error (MW) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **06:00** | 04:30 | 744 (100%) | 2,128.6 | 2,632.0 | −1,798.0 | 4,379.1 |
| **09:00 (Default)** | 07:30 | 744 (100%) | 2,127.5 | 2,606.1 | −1,851.5 | 4,306.4 |
| **12:00** | 09:30, 11:30 | 744 (100%) | 2,002.9 | 2,470.1 | −1,805.9 | 4,000.0 |
| **15:00** | 11:30, 12:25 | 744 (100%) | 2,005.2 | 2,471.9 | −1,811.1 | 4,000.0 |
| **18:00** | 15:30 | 744 (100%) | 1,968.3 | 2,434.7 | −1,816.5 | 4,024.6 |
| **22:00** | 18:30 | 744 (100%) | 1,963.9 | 2,434.9 | −1,795.3 | 4,009.1 |

### Key Cutoff Takeaways:
1. **Marginal difference between 06:00 and 09:00:** Moving from 06:00 to 09:00 yields only a 1.1 MW MAE improvement, as both cutoffs rely on early morning NWP updates.
2. **Step change at 12:00:** MAE improves by **124.6 MW** (from 2,127.5 MW to 2,002.9 MW) and P90 absolute error drops by **306.4 MW** (from 4,306.4 MW to 4,000.0 MW) once midday 09:30/11:30 vintages become available.
3. **Diminishing returns in evening:** Further delaying the decision cutoff to 18:00 or 22:00 yields an additional ~39 MW improvement in MAE, reaching a floor near 1,964 MW.
4. **Persistent Over-Forecasting:** Regardless of cutoff time (from 06:00 to 22:00), the negative bias remains virtually unchanged around **−1,800 MW**. The over-forecasting bias is structural in the January 2026 weather forecast models, not an artifact of lead time.

---

## 5. Forecast Vintage Selection Pattern

Under the default `09:00 Europe/London` cutoff on $D-1$:
- For **all 31 days** in January 2026, the backend selected the **`07:30 UTC` publication** on $D-1$.
- WINDFOR consistently publishes around 04:30, 07:30, 09:30, 11:30, 15:30, 18:30, and 21:30 UTC.
- Because `07:30 UTC` is the latest publication at or before `09:00 Europe/London` (09:00 UTC in January), it is selected uniformly across the entire month.
- This creates an effective day-ahead forecast horizon of **16.5 hours** (for delivery period 00:00 UTC) to **40.5 hours** (for delivery period 23:00 UTC).

---

## 6. Independent Hand-Calculation Cross-Check: 2026-01-15

To guarantee absolute mathematical integrity and verify that the API reproduces pure calculations without artifact errors, all 24 hours of **January 15, 2026** were verified independently from raw records:

### 6.1 Hour-by-Hour Raw Data (2026-01-15)

| Delivery Time (UTC) | Actual (MW) | Forecast (MW) | Error ($A - F$) (MW) | Abs Error (MW) | Selected Vintage ($D-1$) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 2026-01-15 00:00 | 14,602.0 | 15,834.0 | −1,232.0 | 1,232.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 01:00 | 14,200.0 | 15,478.0 | −1,278.0 | 1,278.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 02:00 | 14,534.0 | 15,066.0 | −532.0 | 532.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 03:00 | 14,028.0 | 14,655.0 | −627.0 | 627.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 04:00 | 13,901.0 | 14,497.0 | −596.0 | 596.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 05:00 | 13,704.0 | 14,419.0 | −715.0 | 715.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 06:00 | 13,256.0 | 14,017.0 | −761.0 | 761.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 07:00 | 13,401.0 | 13,411.0 | −10.0 | 10.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 08:00 | 12,719.0 | 12,931.0 | −212.0 | 212.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 09:00 | 12,242.0 | 12,576.0 | −334.0 | 334.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 10:00 | 9,807.0 | 12,081.0 | −2,274.0 | 2,274.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 11:00 | 9,930.0 | 11,578.0 | −1,648.0 | 1,648.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 12:00 | 9,742.0 | 11,049.0 | −1,307.0 | 1,307.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 13:00 | 8,843.0 | 10,378.0 | −1,535.0 | 1,535.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 14:00 | 8,384.0 | 9,619.0 | −1,235.0 | 1,235.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 15:00 | 8,482.0 | 9,050.0 | −568.0 | 568.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 16:00 | 8,543.0 | 8,864.0 | −321.0 | 321.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 17:00 | 8,266.0 | 8,870.0 | −604.0 | 604.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 18:00 | 7,672.0 | 8,962.0 | −1,290.0 | 1,290.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 19:00 | 7,631.0 | 9,130.0 | −1,499.0 | 1,499.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 20:00 | 7,592.0 | 9,059.0 | −1,467.0 | 1,467.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 21:00 | 7,603.0 | 9,049.0 | −1,446.0 | 1,446.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 22:00 | 7,685.0 | 9,091.0 | −1,406.0 | 1,406.0 | 2026-01-14 07:30 UTC |
| 2026-01-15 23:00 | 7,258.0 | 8,966.0 | −1,708.0 | 1,708.0 | 2026-01-14 07:30 UTC |

### 6.2 Comparison of Calculations

- $\sum \text{Actual} = 254,025.0 \implies \text{Mean Actual} = 254,025.0 / 24 = 10,584.375\text{ MW}$
- $\sum \text{Forecast} = 276,630.0 \implies \text{Mean Forecast} = 276,630.0 / 24 = 11,609.583\text{ MW}$
- $\sum \text{Error} = -24,605.0 \implies \text{Bias} = -24,605.0 / 24 = -1,025.208\text{ MW}$
- $\sum |\text{Error}| = 24,605.0 \implies \text{MAE} = 24,605.0 / 24 = 1,025.208\text{ MW}$
- $\sum \text{Error}^2 = 32,744,819.0 \implies \text{RMSE} = \sqrt{32,744,819.0 / 24} = 1,168.060\text{ MW}$

| Metric | Hand-Calculated (exact) | API Reported (`/api/series?granularity=daily`) | Agreement |
| :--- | :--- | :--- | :---: |
| **Mean Actual** | 10,584.38 MW | 10,584.4 MW | **Exact** |
| **Mean Forecast** | 11,609.58 MW | 11,609.6 MW | **Exact** |
| **MAE** | 1,025.21 MW | 1,025.2 MW | **Exact** |
| **RMSE** | 1,168.06 MW | 1,168.1 MW | **Exact** |
| **Bias** | −1,025.21 MW | −1,025.2 MW | **Exact** |

---

## 7. Data Coverage and Pipeline Integrity

1. **Grid Completeness:**
   - Evaluated range: `2026-01-01T00:00:00Z` to `2026-01-31T23:00:00Z`.
   - Expected periods ($31 \times 24$): **744 hours**.
   - Matched periods: **744 hours (100.0%)**.
   - Missing actuals: **0**.
   - Missing forecasts: **0**.
   - Missing both: **0**.
2. **Filtering and Row Hygiene:**
   - 1,488 rows received from Elexon FUELHH for January 2026 (744 top-of-hour rows and 744 half-hour `:30` rows).
   - Only top-of-hour rows entered metric calculations.
   - 0 duplicate rows, 0 invalid rows, 0 conflicting vintages.

---

## 8. Limitations & Methodology Disclosures

1. **Provisional Cutoff Notice:**
   The 09:00 Europe/London cutoff on $D-1$ is a chosen analytical benchmark reflecting typical morning trading decision workflows. Market participants operating under different gate closures (e.g., 12:00 Day-Ahead Auction or gate closure 1 hour prior to delivery) can utilize the interactive cutoff selector to obtain their specific accuracy profile.
2. **Instantaneous vs. Hourly Average Ambiguity:**
   Elexon documentation does not definitively state whether `WINDFOR` represents instantaneous expected generation at `:00` or an integrated hourly average. Because `:30` FUELHH readings represent distinct half-hour physical settlement periods, interpolating or averaging actuals without documented basis was rejected to avoid introducing artificial distortion.
3. **Single Winter Month Scope:**
   January represents a high-wind winter regime characterized by active Atlantic storm depressions. Results should not be generalized directly to summer low-wind regimes without evaluating additional seasonal data.
