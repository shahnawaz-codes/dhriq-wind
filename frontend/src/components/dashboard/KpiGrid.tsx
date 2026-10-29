import React from 'react';
import type { DataQualitySummary, SummaryMetrics } from '../../api/types';
import { KpiCard } from './KpiCard';

interface KpiGridProps {
  metrics: SummaryMetrics | null;
  dataQuality: DataQualitySummary | null;
  isLoading?: boolean;
}

export const KpiGrid: React.FC<KpiGridProps> = ({ metrics, dataQuality, isLoading }) => {
  if (isLoading || !metrics || !dataQuality) {
    return (
      <div className="kpi-grid skeleton-container" aria-busy="true" aria-label="Loading KPIs">
        {[1, 2, 3, 4, 5, 6, 7].map((i) => (
          <div key={i} className="card kpi-card skeleton-card">
            <div className="skeleton-line skeleton-title" />
            <div className="skeleton-line skeleton-value" />
            <div className="skeleton-line skeleton-sub" />
          </div>
        ))}
      </div>
    );
  }

  // Bias badge
  let biasBadge: { text: string; variant: 'neutral' | 'warning' | 'danger' | 'success' } | undefined;
  let biasSecondary = 'Average error';
  if (metrics.bias_mw !== null && metrics.bias_mw !== undefined) {
    if (metrics.bias_mw > 0) {
      biasBadge = { text: 'Under-forecast', variant: 'warning' };
      biasSecondary = 'Forecasts too low on average';
    } else if (metrics.bias_mw < 0) {
      biasBadge = { text: 'Over-forecast', variant: 'danger' };
      biasSecondary = 'Forecasts too high on average';
    } else {
      biasBadge = { text: 'Unbiased', variant: 'success' };
      biasSecondary = 'Zero mean error';
    }
  }

  // Matched Periods formatted as "744 (100.0%)"
  const matchedValue =
    metrics.n_matched !== null && metrics.coverage_pct !== null
      ? `${metrics.n_matched} (${metrics.coverage_pct.toFixed(1)}%)`
      : metrics.n_matched !== null
      ? `${metrics.n_matched}`
      : null;

  return (
    <div className="kpi-grid" role="region" aria-label="Forecast Accuracy KPIs">
      {/* 1. MAE */}
      <KpiCard
        label="MAE"
        value={metrics.mae_mw}
        unit="MW"
        secondaryText="Mean Absolute Error"
        tooltip="Mean Absolute Error: the average magnitude of the forecast miss, in MW, ignoring direction."
      />

      {/* 2. RMSE */}
      <KpiCard
        label="RMSE"
        value={metrics.rmse_mw}
        unit="MW"
        secondaryText="Penalises large misses"
        tooltip="Root Mean Squared Error, in MW. Like MAE, but squares errors before averaging to penalise larger deviations."
      />

      {/* 3. Bias */}
      <KpiCard
        label="Mean Error (Bias)"
        value={metrics.bias_mw}
        unit="MW"
        badge={biasBadge}
        secondaryText={biasSecondary}
        tooltip="Mean of (actual − forecast), in MW. Positive means forecasts were too low on average (under-forecast); negative means too high (over-forecast)."
      />

      {/* 4. Matched Periods */}
      <KpiCard
        label="Matched Periods"
        value={matchedValue}
        secondaryText={`out of ${dataQuality.n_expected} expected hours`}
        badge={{
          text: metrics.n_matched === dataQuality.n_expected ? 'Complete' : 'Gaps present',
          variant: metrics.n_matched === dataQuality.n_expected ? 'success' : 'warning',
        }}
        tooltip="Count and percentage of evaluated hourly periods that have both an actual and an eligible forecast selected under the active cutoff."
      />

      {/* 5. P90 Absolute Error */}
      <KpiCard
        label="P90 Abs Error"
        value={metrics.p90_abs_error_mw}
        unit="MW"
        secondaryText="90% of misses ≤ this size"
        tooltip="90% of evaluated hourly periods had an error at or below this size (Method 7 / linear interpolation). Useful for sizing reserve procurement buffers."
      />

      {/* 6. MAE % */}
      <KpiCard
        label="MAE % of Actual"
        value={metrics.mae_pct_of_mean_actual !== null ? `${metrics.mae_pct_of_mean_actual.toFixed(1)}%` : null}
        secondaryText={`Mean actual: ${metrics.mean_actual_mw ? Math.round(metrics.mean_actual_mw).toLocaleString() : '—'} MW`}
        tooltip="MAE as a percentage of the average actual generation during the selected period. Unstable if actual is near zero."
      />

      {/* 7. Coverage */}
      <KpiCard
        label="Data Coverage"
        value={metrics.coverage_pct !== null ? `${metrics.coverage_pct.toFixed(1)}%` : null}
        secondaryText={`${dataQuality.n_missing_forecast} missing forecasts`}
        badge={{
          text: metrics.coverage_pct === 100 ? '100% Data' : 'Incomplete',
          variant: metrics.coverage_pct === 100 ? 'success' : 'neutral',
        }}
        tooltip="Percentage of expected periods that have both valid metered actuals and an eligible forecast."
      />
    </div>
  );
};

