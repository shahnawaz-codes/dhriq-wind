# SYNTHETIC unit tests for forecast accuracy metrics calculations
import json
import math
from datetime import UTC, date, datetime
from pathlib import Path

from app.domain.matching import build_comparison_records
from app.domain.metrics import (
    compute_daily_metrics,
    compute_metrics,
    compute_percentile_linear,
)
from app.domain.models import ActualPoint, ComparisonRecord, ForecastPoint, RecordStatus


def test_hand_calculated_synthetic_fixture():
    # Load synthetic hand-calc fixture
    fixture_path = (
        Path(__file__).parent.parent / "fixtures" / "synthetic_hand_calc.json"
    )
    with open(fixture_path, "r", encoding="utf-8") as f:
        fixture = json.load(f)

    records = []
    cutoff = datetime(2026, 1, 14, 9, 0, tzinfo=UTC)
    for p in fixture["periods"]:
        st = datetime.fromisoformat(p["start_time"])
        status = RecordStatus(p["expected_status"])
        ac = p["actual_mw"]
        fc = p["forecast_mw"]
        err = p["expected_error_mw"]
        abs_err = p["expected_abs_error_mw"]
        records.append(
            ComparisonRecord(
                start_time=st,
                delivery_date=date(2026, 1, 15),
                cutoff_time=cutoff,
                actual_mw=ac,
                forecast_mw=fc,
                forecast_publish_time=cutoff if fc is not None else None,
                forecast_horizon_hours=25.0 if fc is not None else None,
                error_mw=err,
                abs_error_mw=abs_err,
                status=status,
            )
        )

    summary = compute_metrics(records)
    expected = fixture["expected_metrics"]

    assert summary.n_expected == expected["n_expected"]
    assert summary.n_matched == expected["n_matched"]
    assert math.isclose(summary.coverage_pct, expected["coverage_pct"], rel_tol=1e-7)
    assert math.isclose(
        summary.mean_actual_mw, expected["mean_actual_mw"], rel_tol=1e-7
    )
    assert math.isclose(
        summary.mean_forecast_mw, expected["mean_forecast_mw"], rel_tol=1e-7
    )
    assert math.isclose(summary.bias_mw, expected["bias_mw"], rel_tol=1e-7)
    assert math.isclose(summary.mae_mw, expected["mae_mw"], rel_tol=1e-7)
    assert math.isclose(summary.rmse_mw, expected["rmse_mw"], rel_tol=1e-7)
    assert math.isclose(summary.mae_pct, expected["mae_pct"], rel_tol=1e-7)
    assert math.isclose(
        summary.p90_abs_error_mw, expected["p90_abs_error_mw"], rel_tol=1e-7
    )


def test_empty_records_and_no_matched_handling():
    # Never return 0 as a metric when data is missing (BR-07, §8)
    summary_empty = compute_metrics([])
    assert summary_empty.n_expected == 0
    assert summary_empty.n_matched == 0
    assert summary_empty.coverage_pct == 0.0
    assert summary_empty.mae_mw is None
    assert summary_empty.rmse_mw is None
    assert summary_empty.bias_mw is None
    assert summary_empty.mae_pct is None
    assert summary_empty.p90_abs_error_mw is None

    # Records with only missing statuses
    missing_rec = ComparisonRecord(
        start_time=datetime(2026, 1, 15, 10, 0, tzinfo=UTC),
        delivery_date=date(2026, 1, 15),
        cutoff_time=datetime(2026, 1, 14, 9, 0, tzinfo=UTC),
        actual_mw=None,
        forecast_mw=None,
        forecast_publish_time=None,
        forecast_horizon_hours=None,
        error_mw=None,
        abs_error_mw=None,
        status=RecordStatus.MISSING_BOTH,
    )
    summary_missing = compute_metrics([missing_rec])
    assert summary_missing.n_expected == 1
    assert summary_missing.n_matched == 0
    assert summary_missing.coverage_pct == 0.0
    assert summary_missing.mae_mw is None


def test_zero_actual_division_guard():
    # If mean_actual_mw == 0, mae_pct should be None, not ZeroDivisionError
    rec = ComparisonRecord(
        start_time=datetime(2026, 1, 15, 10, 0, tzinfo=UTC),
        delivery_date=date(2026, 1, 15),
        cutoff_time=datetime(2026, 1, 14, 9, 0, tzinfo=UTC),
        actual_mw=0.0,
        forecast_mw=10.0,
        forecast_publish_time=datetime(2026, 1, 14, 7, 30, tzinfo=UTC),
        forecast_horizon_hours=26.5,
        error_mw=-10.0,
        abs_error_mw=10.0,
        status=RecordStatus.MATCHED,
    )
    summary = compute_metrics([rec])
    assert summary.mean_actual_mw == 0.0
    assert summary.mae_pct is None


def test_percentile_linear_method():
    # Empty list raises ValueError
    import pytest

    with pytest.raises(ValueError, match="Cannot compute percentile of an empty list"):
        compute_percentile_linear([], 90.0)

    # Single element
    assert compute_percentile_linear([50.0], 90.0) == 50.0

    # 10 sorted elements 10 to 100
    values = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    # q = 0.90 * (10 - 1) = 8.1
    # Y[8] = 90.0, Y[9] = 100.0, frac = 0.1
    # 90.0 + 0.1 * 10.0 = 91.0
    assert math.isclose(compute_percentile_linear(values, 90.0), 91.0)

    # 100th percentile (boundary i >= n - 1)
    assert compute_percentile_linear(values, 100.0) == 100.0


def test_half_hour_actuals_never_enter_metrics():
    # User Requirement 2: Never include :30 actuals in metrics.
    # Feed actuals with both :00 and :30
    t_00 = datetime(2026, 1, 15, 10, 0, tzinfo=UTC)
    t_30 = datetime(2026, 1, 15, 10, 30, tzinfo=UTC)

    actuals_with_30 = [
        ActualPoint(start_time=t_00, generation_mw=100.0),
        ActualPoint(start_time=t_30, generation_mw=999.0),  # This must NEVER be used
    ]
    actuals_without_30 = [
        ActualPoint(start_time=t_00, generation_mw=100.0),
    ]

    forecasts = [
        ForecastPoint(
            start_time=t_00,
            publish_time=datetime(2026, 1, 14, 7, 30, tzinfo=UTC),
            generation_mw=80.0,
        )
    ]

    records_with_30 = build_comparison_records(
        actuals=actuals_with_30,
        forecasts=forecasts,
        start_date=date(2026, 1, 15),
        end_date=date(2026, 1, 15),
        cutoff_time_str="09:00",
        tz_name="Europe/London",
    )
    records_without_30 = build_comparison_records(
        actuals=actuals_without_30,
        forecasts=forecasts,
        start_date=date(2026, 1, 15),
        end_date=date(2026, 1, 15),
        cutoff_time_str="09:00",
        tz_name="Europe/London",
    )

    metrics_with_30 = compute_metrics(records_with_30)
    metrics_without_30 = compute_metrics(records_without_30)

    assert metrics_with_30.mae_mw == metrics_without_30.mae_mw == 20.0
    assert metrics_with_30.bias_mw == metrics_without_30.bias_mw == 20.0
    assert metrics_with_30.rmse_mw == metrics_without_30.rmse_mw == 20.0
    assert metrics_with_30.mean_actual_mw == metrics_without_30.mean_actual_mw == 100.0


def test_daily_metrics_aggregation():
    # 2 days: Day 1 with 2 matched, Day 2 with 1 matched
    cutoff = datetime(2026, 1, 14, 9, 0, tzinfo=UTC)
    records = [
        ComparisonRecord(
            start_time=datetime(2026, 1, 15, 10, 0, tzinfo=UTC),
            delivery_date=date(2026, 1, 15),
            cutoff_time=cutoff,
            actual_mw=100.0,
            forecast_mw=80.0,
            forecast_publish_time=cutoff,
            forecast_horizon_hours=25.0,
            error_mw=20.0,
            abs_error_mw=20.0,
            status=RecordStatus.MATCHED,
        ),
        ComparisonRecord(
            start_time=datetime(2026, 1, 15, 11, 0, tzinfo=UTC),
            delivery_date=date(2026, 1, 15),
            cutoff_time=cutoff,
            actual_mw=200.0,
            forecast_mw=150.0,
            forecast_publish_time=cutoff,
            forecast_horizon_hours=26.0,
            error_mw=50.0,
            abs_error_mw=50.0,
            status=RecordStatus.MATCHED,
        ),
        ComparisonRecord(
            start_time=datetime(2026, 1, 16, 10, 0, tzinfo=UTC),
            delivery_date=date(2026, 1, 16),
            cutoff_time=datetime(2026, 1, 15, 9, 0, tzinfo=UTC),
            actual_mw=300.0,
            forecast_mw=330.0,
            forecast_publish_time=datetime(2026, 1, 15, 7, 30, tzinfo=UTC),
            forecast_horizon_hours=26.5,
            error_mw=-30.0,
            abs_error_mw=30.0,
            status=RecordStatus.MATCHED,
        ),
    ]

    daily = compute_daily_metrics(records)
    assert len(daily) == 2
    d1 = next(d for d in daily if d.date == date(2026, 1, 15))
    d2 = next(d for d in daily if d.date == date(2026, 1, 16))

    assert d1.n_matched == 2
    assert d1.mae_mw == 35.0  # (20 + 50) / 2
    assert d1.bias_mw == 35.0

    assert d2.n_matched == 1
    assert d2.mae_mw == 30.0
    assert d2.bias_mw == -30.0
