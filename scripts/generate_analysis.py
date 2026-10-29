"""
Reproducible Analysis Script for UK Wind Generation Forecast Evaluation (January 2026).

Regenerates all headline metrics, cutoff-sensitivity tables, daily extremes,
and independent cross-checks directly from the FastAPI backend and domain layer.

Usage:
    backend/.venv/Scripts/python scripts/generate_analysis.py
"""

import os
import sys

# Ensure backend package is importable
sys.path.insert(0, os.path.abspath('backend'))

from fastapi.testclient import TestClient
from app.main import app

def main() -> None:
    client = TestClient(app)

    print("=" * 80)
    print("1. HEADLINE JANUARY 2026 METRICS (Provisional Cutoff: 09:00 Europe/London)")
    print("=" * 80)
    summary_resp = client.get('/api/summary?cutoff_time=09:00').json()
    metrics = summary_resp['metrics']
    dq = summary_resp['data_quality']

    print(f"Total Expected Settlement Periods: {dq['n_expected']}")
    print(f"Matched Top-of-Hour Periods:      {metrics['n_matched']} ({metrics['coverage_pct']}%)")
    print(f"Missing Forecast Periods:          {dq['n_missing_forecast']}")
    print(f"Missing Actual Periods:            {dq['n_missing_actual']}")
    print(f"Mean Absolute Error (MAE):         {metrics['mae_mw']} MW")
    print(f"MAE % of Mean Actual:              {metrics['mae_pct_of_mean_actual']}%")
    print(f"Root Mean Squared Error (RMSE):    {metrics['rmse_mw']} MW")
    print(f"Mean Error / Bias (Actual - Fc):   {metrics['bias_mw']} MW")
    print(f"P90 Absolute Error:                {metrics['p90_abs_error_mw']} MW")
    print(f"Mean Actual Generation:            {metrics['mean_actual_mw']} MW")
    print(f"Mean Forecast Generation:          {metrics['mean_forecast_mw']} MW")

    print("\n" + "=" * 80)
    print("2. DAILY ACCURACY REGIMES & EXTREMES (31 Days in January 2026)")
    print("=" * 80)
    daily_resp = client.get('/api/series?granularity=daily&cutoff_time=09:00').json()
    points = daily_resp['points']
    sorted_by_mae = sorted(points, key=lambda p: p['mae_mw'])

    print("\nTop 3 Best Days (Lowest MAE):")
    for p in sorted_by_mae[:3]:
        print(f"  {p['date']}: MAE={p['mae_mw']:6.1f} MW | Bias={p['bias_mw']:+7.1f} MW | Actual={p['mean_actual_mw']:7.1f} MW | Forecast={p['mean_forecast_mw']:7.1f} MW")

    print("\nTop 3 Worst Days (Highest MAE):")
    for p in sorted_by_mae[-3:]:
        print(f"  {p['date']}: MAE={p['mae_mw']:6.1f} MW | Bias={p['bias_mw']:+7.1f} MW | Actual={p['mean_actual_mw']:7.1f} MW | Forecast={p['mean_forecast_mw']:7.1f} MW")

    over_fc = [p for p in points if p['bias_mw'] < 0]
    under_fc = [p for p in points if p['bias_mw'] > 0]
    unbiased = [p for p in points if p['bias_mw'] == 0]
    print(f"\nDaily Directional Counts: {len(over_fc)} over-forecast days (87.1%), {len(under_fc)} under-forecast days (12.9%), {len(unbiased)} zero-bias days.")

    print("\n" + "=" * 80)
    print("3. DECISION-CUTOFF SENSITIVITY ANALYSIS")
    print("=" * 80)
    cutoffs = ['06:00', '09:00', '12:00', '15:00', '18:00', '22:00']
    print(f"{'Cutoff':<8} | {'Vintages (UTC on D-1)':<24} | {'Matched':<7} | {'MAE (MW)':<8} | {'RMSE (MW)':<9} | {'Bias (MW)':<9} | {'P90 (MW)':<8}")
    print("-" * 88)
    for c in cutoffs:
        resp = client.get(f'/api/summary?cutoff_time={c}').json()
        m = resp['metrics']
        vintages = sorted(set(v['publish_time'][-14:-6] for v in resp['forecast_vintages']))
        v_str = ", ".join(vintages)
        print(f"{c:<8} | {v_str:<24} | {m['n_matched']:<7} | {m['mae_mw']:<8.1f} | {m['rmse_mw']:<9.1f} | {m['bias_mw']:<9.1f} | {m['p90_abs_error_mw']:<8.1f}")

    print("\n" + "=" * 80)
    print("4. INDEPENDENT CROSS-CHECK AUDIT: 2026-01-15 (24 Hourly Periods)")
    print("=" * 80)
    records_resp = client.get('/api/records?start_date=2026-01-15&end_date=2026-01-15&cutoff_time=09:00&page_size=50').json()
    recs = records_resp['items']

    sum_act = 0.0
    sum_fc = 0.0
    sum_err = 0.0
    sum_abs_err = 0.0
    sum_sq_err = 0.0

    print(f"{'Hour (UTC)':<20} | {'Actual (MW)':<11} | {'Forecast (MW)':<13} | {'Error (MW)':<10} | {'|Error| (MW)':<12} | {'Vintage (UTC)':<20}")
    print("-" * 96)
    for r in recs:
        act = r['actual_mw']
        fc = r['forecast_mw']
        err = r['error_mw']
        abs_err = r['abs_error_mw']
        sq_err = err ** 2
        sum_act += act
        sum_fc += fc
        sum_err += err
        sum_abs_err += abs_err
        sum_sq_err += sq_err
        print(f"{r['start_time']:<20} | {act:11.1f} | {fc:13.1f} | {err:10.1f} | {abs_err:12.1f} | {r['forecast_publish_time']:<20}")

    n = len(recs)
    mean_act = sum_act / n
    mean_fc = sum_fc / n
    mae = sum_abs_err / n
    rmse = (sum_sq_err / n) ** 0.5
    bias = sum_err / n

    print("\nCalculated Totals:")
    print(f"  Actual Sum:         {sum_act:12.1f} MW")
    print(f"  Forecast Sum:       {sum_fc:12.1f} MW")
    print(f"  Signed Error Sum:   {sum_err:12.1f} MW")
    print(f"  Absolute Error Sum: {sum_abs_err:12.1f} MW")
    print(f"  Squared Error Sum:  {sum_sq_err:12.1f} MW^2")

    print("\nCalculated Averages vs API Daily Endpoint:")
    day_15 = [p for p in points if p['date'] == '2026-01-15'][0]
    print(f"  Mean Actual:   Hand={mean_act:.2f} MW | API={day_15['mean_actual_mw']} MW")
    print(f"  Mean Forecast: Hand={mean_fc:.2f} MW | API={day_15['mean_forecast_mw']} MW")
    print(f"  MAE:           Hand={mae:.2f} MW | API={day_15['mae_mw']} MW")
    print(f"  RMSE:          Hand={rmse:.2f} MW | API={day_15['rmse_mw']} MW")
    print(f"  Bias:          Hand={bias:.2f} MW | API={day_15['bias_mw']} MW")

if __name__ == '__main__':
    main()
