export interface WindowMeta {
  start_date: string;
  end_date: string;
  expected_periods: number;
}

export interface AssumptionsMeta {
  cutoff_time_default: string;
  cutoff_timezone: string;
  cutoff_rule: string;
  cutoff_inclusive: boolean;
  status: string;
}

export interface ProvenanceMeta {
  source: string;
  datasets: string[];
  fetched_at: string | null;
  cache_age_seconds: number | null;
  stale: boolean;
}

export interface MetaResponse {
  window: WindowMeta;
  assumptions: AssumptionsMeta;
  provenance: ProvenanceMeta;
}

export interface RangeModel {
  start_date: string;
  end_date: string;
}

export interface SummaryAssumptions {
  cutoff_time: string;
  cutoff_timezone: string;
  cutoff_inclusive: boolean;
}

export interface SummaryMetrics {
  n_matched: number;
  mae_mw: number | null;
  rmse_mw: number | null;
  bias_mw: number | null;
  mae_pct_of_mean_actual: number | null;
  p90_abs_error_mw: number | null;
  mean_actual_mw: number | null;
  mean_forecast_mw: number | null;
  coverage_pct: number | null;
}

export interface ForecastVintage {
  publish_time: string;
  periods_count: number;
}

export interface DataQualitySummary {
  n_expected: number;
  n_matched: number;
  n_missing_actual: number;
  n_missing_forecast: number;
  n_missing_both: number;
  invalid_actual_rows: number;
  invalid_forecast_rows: number;
  duplicate_actual_rows: number;
  duplicate_forecast_rows: number;
  conflicting_forecast_rows: number;
  warnings: string[];
}

export interface SummaryResponse {
  range: RangeModel;
  assumptions: SummaryAssumptions;
  metrics: SummaryMetrics;
  forecast_vintages: ForecastVintage[];
  data_quality: DataQualitySummary;
  provenance: ProvenanceMeta;
}

export interface HourlySeriesPoint {
  start_time: string;
  actual_mw: number | null;
  forecast_mw: number | null;
  forecast_publish_time: string | null;
  status: 'matched' | 'missing_forecast' | 'missing_actual' | 'missing_both';
  actual_half_hour_context_mw: number | null;
}

export interface DailySeriesPoint {
  date: string;
  n_matched: number;
  mean_actual_mw: number | null;
  mean_forecast_mw: number | null;
  mae_mw: number | null;
  rmse_mw: number | null;
  bias_mw: number | null;
  cutoff_time: string;
}

export interface SeriesResponse {
  granularity: 'hourly' | 'daily';
  unit: string;
  points: (HourlySeriesPoint | DailySeriesPoint)[];
}

export interface RecordItem {
  start_time: string;
  delivery_date: string;
  cutoff_time: string;
  actual_mw: number | null;
  forecast_mw: number | null;
  forecast_publish_time: string | null;
  forecast_horizon_hours: number | null;
  error_mw: number | null;
  abs_error_mw: number | null;
  status: 'matched' | 'missing_forecast' | 'missing_actual' | 'missing_both';
}

export interface RecordsResponse {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  items: RecordItem[];
}

export interface ApiErrorDetail {
  field?: string;
}

export interface ApiErrorPayload {
  code: string;
  message: string;
  details: ApiErrorDetail[];
}

export interface ApiErrorResponse {
  error: ApiErrorPayload;
}

