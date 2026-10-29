# SYNTHETIC unit tests for grid generation, matching, and :30 exclusion guard
from datetime import UTC, date, datetime

from app.domain.matching import build_comparison_records
from app.domain.models import ActualPoint, ForecastPoint, RecordStatus


def test_january_2026_grid_length_744():
    # January 1 to 31 (inclusive) produces exactly 744 hourly points (31 * 24)
    records = build_comparison_records(
        actuals=[],
        forecasts=[],
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        cutoff_time_str="09:00",
        tz_name="Europe/London",
    )
    assert len(records) == 744
    assert records[0].start_time == datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    assert records[-1].start_time == datetime(2026, 1, 31, 23, 0, tzinfo=UTC)
    # Empty inputs -> all missing_both
    assert all(r.status == RecordStatus.MISSING_BOTH for r in records)


def test_matching_statuses():
    # 4 hourly periods on 2026-01-15
    t_matched = datetime(2026, 1, 15, 10, 0, tzinfo=UTC)
    t_miss_fc = datetime(2026, 1, 15, 11, 0, tzinfo=UTC)
    t_miss_ac = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
    t_miss_both = datetime(2026, 1, 15, 13, 0, tzinfo=UTC)

    actuals = [
        ActualPoint(start_time=t_matched, generation_mw=5000.0),
        ActualPoint(start_time=t_miss_fc, generation_mw=4500.0),
    ]

    # Forecasts eligible before 2026-01-14T09:00Z
    cutoff_time = datetime(2026, 1, 14, 7, 30, tzinfo=UTC)
    forecasts = [
        ForecastPoint(
            start_time=t_matched, publish_time=cutoff_time, generation_mw=4800.0
        ),
        ForecastPoint(
            start_time=t_miss_ac, publish_time=cutoff_time, generation_mw=5200.0
        ),
    ]

    records = build_comparison_records(
        actuals=actuals,
        forecasts=forecasts,
        start_date=date(2026, 1, 15),
        end_date=date(2026, 1, 15),
        cutoff_time_str="09:00",
        tz_name="Europe/London",
    )

    rec_by_time = {r.start_time: r for r in records}

    # 1. Matched
    r1 = rec_by_time[t_matched]
    assert r1.status == RecordStatus.MATCHED
    assert r1.actual_mw == 5000.0
    assert r1.forecast_mw == 4800.0
    assert r1.error_mw == 200.0
    assert r1.abs_error_mw == 200.0
    # Horizon: (2026-01-15 10:00 - 2026-01-14 07:30) = 26.5 hours
    assert r1.forecast_horizon_hours == 26.5

    # 2. Missing forecast
    r2 = rec_by_time[t_miss_fc]
    assert r2.status == RecordStatus.MISSING_FORECAST
    assert r2.actual_mw == 4500.0
    assert r2.forecast_mw is None
    assert r2.error_mw is None

    # 3. Missing actual
    r3 = rec_by_time[t_miss_ac]
    assert r3.status == RecordStatus.MISSING_ACTUAL
    assert r3.actual_mw is None
    assert r3.forecast_mw == 5200.0
    assert r3.error_mw is None

    # 4. Missing both
    r4 = rec_by_time[t_miss_both]
    assert r4.status == RecordStatus.MISSING_BOTH
    assert r4.actual_mw is None
    assert r4.forecast_mw is None


def test_half_hour_actuals_strictly_excluded_from_grid():
    # User Requirement 2: Never include :30 actuals in metrics or matching grid.
    t_00 = datetime(2026, 1, 15, 10, 0, tzinfo=UTC)
    t_30 = datetime(2026, 1, 15, 10, 30, tzinfo=UTC)

    # Actuals contain both :00 and :30 periods
    actuals = [
        ActualPoint(start_time=t_00, generation_mw=5000.0),
        ActualPoint(start_time=t_30, generation_mw=5200.0),
    ]

    forecasts = [
        ForecastPoint(
            start_time=t_00,
            publish_time=datetime(2026, 1, 14, 7, 30, tzinfo=UTC),
            generation_mw=4800.0,
        )
    ]

    records = build_comparison_records(
        actuals=actuals,
        forecasts=forecasts,
        start_date=date(2026, 1, 15),
        end_date=date(2026, 1, 15),
        cutoff_time_str="09:00",
        tz_name="Europe/London",
    )

    # 1 day = exactly 24 hourly records
    assert len(records) == 24
    # Ensure no :30 timestamp appears in the grid
    for r in records:
        assert r.start_time.minute == 0
        assert r.start_time.second == 0

    # Record at 10:00 matches only the :00 actual (5000.0), not the :30 actual (5200.0)
    rec_10 = next(r for r in records if r.start_time == t_00)
    assert rec_10.status == RecordStatus.MATCHED
    assert rec_10.actual_mw == 5000.0
    assert rec_10.error_mw == 200.0
