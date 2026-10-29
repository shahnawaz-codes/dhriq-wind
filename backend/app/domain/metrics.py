import math
from collections import defaultdict

from app.domain.models import (
    ComparisonRecord,
    DailyMetrics,
    MetricsSummary,
    RecordStatus,
)


def compute_percentile_linear(sorted_values: list[float], percentile: float) -> float:
    """Compute percentile using linear interpolation (NumPy 'linear' method).

    Args:
        sorted_values: List of floats already sorted in ascending order.
        percentile: Float between 0.0 and 100.0.
    """
    n = len(sorted_values)
    if n == 0:
        raise ValueError("Cannot compute percentile of an empty list.")
    if n == 1:
        return float(sorted_values[0])

    q = (percentile / 100.0) * (n - 1)
    i = math.floor(q)
    fraction = q - i

    if i >= n - 1:
        return float(sorted_values[-1])

    return float(
        sorted_values[i] + fraction * (sorted_values[i + 1] - sorted_values[i])
    )


def compute_metrics(records: list[ComparisonRecord]) -> MetricsSummary:
    """Compute aggregated accuracy metrics over matched records (BR-09, FORECAST_LOGIC §7).

    Returns None for error metrics if no matched periods exist (never returns 0 as fallback).
    """
    n_expected = len(records)
    matched = [r for r in records if r.status == RecordStatus.MATCHED]
    n_matched = len(matched)

    if n_matched == 0:
        coverage_pct = 0.0
        return MetricsSummary(
            n_expected=n_expected,
            n_matched=0,
            coverage_pct=coverage_pct,
            mae_mw=None,
            rmse_mw=None,
            bias_mw=None,
            mae_pct=None,
            p90_abs_error_mw=None,
            mean_actual_mw=None,
            mean_forecast_mw=None,
        )

    coverage_pct = (n_matched / n_expected * 100.0) if n_expected > 0 else 0.0

    errors = [r.error_mw for r in matched if r.error_mw is not None]
    abs_errors = [r.abs_error_mw for r in matched if r.abs_error_mw is not None]
    actuals = [r.actual_mw for r in matched if r.actual_mw is not None]
    forecasts = [r.forecast_mw for r in matched if r.forecast_mw is not None]

    mae_mw = sum(abs_errors) / n_matched
    rmse_mw = math.sqrt(sum(e**2 for e in errors) / n_matched)
    bias_mw = sum(errors) / n_matched  # positive = under-forecast (forecasts too low)
    mean_actual_mw = sum(actuals) / n_matched
    mean_forecast_mw = sum(forecasts) / n_matched

    mae_pct = (mae_mw / mean_actual_mw * 100.0) if mean_actual_mw > 0 else None

    sorted_abs = sorted(abs_errors)
    p90_abs_error_mw = compute_percentile_linear(sorted_abs, 90.0)

    return MetricsSummary(
        n_expected=n_expected,
        n_matched=n_matched,
        coverage_pct=coverage_pct,
        mae_mw=mae_mw,
        rmse_mw=rmse_mw,
        bias_mw=bias_mw,
        mae_pct=mae_pct,
        p90_abs_error_mw=p90_abs_error_mw,
        mean_actual_mw=mean_actual_mw,
        mean_forecast_mw=mean_forecast_mw,
    )


def compute_daily_metrics(records: list[ComparisonRecord]) -> list[DailyMetrics]:
    """Compute accuracy metrics grouped by delivery date."""
    records_by_date = defaultdict(list)
    for r in records:
        records_by_date[r.delivery_date].append(r)

    daily_list: list[DailyMetrics] = []

    for d in sorted(records_by_date.keys()):
        day_records = records_by_date[d]
        summary = compute_metrics(day_records)
        cutoff_time = day_records[0].cutoff_time

        daily_list.append(
            DailyMetrics(
                date=d,
                n_expected=summary.n_expected,
                n_matched=summary.n_matched,
                coverage_pct=summary.coverage_pct,
                mae_mw=summary.mae_mw,
                rmse_mw=summary.rmse_mw,
                bias_mw=summary.bias_mw,
                mean_actual_mw=summary.mean_actual_mw,
                mean_forecast_mw=summary.mean_forecast_mw,
                cutoff_time=cutoff_time,
            )
        )

    return daily_list
