# SYNTHETIC unit tests for forecast selection and cutoff boundary behavior
from datetime import UTC, datetime

from app.domain.models import ForecastPoint
from app.domain.selection import select_forecast_for_period


def test_before_cutoff():
    target_time = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
    cutoff = datetime(2026, 1, 14, 9, 0, tzinfo=UTC)

    # Forecast published 1 second before cutoff
    fp = ForecastPoint(
        start_time=target_time,
        publish_time=datetime(2026, 1, 14, 8, 59, 59, tzinfo=UTC),
        generation_mw=5000.0,
    )
    selected = select_forecast_for_period(target_time, [fp], cutoff)
    assert selected == fp


def test_exactly_at_cutoff_is_eligible():
    # Boundary is inclusive (BR-03)
    target_time = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
    cutoff = datetime(2026, 1, 14, 9, 0, tzinfo=UTC)

    earlier = ForecastPoint(
        start_time=target_time,
        publish_time=datetime(2026, 1, 14, 8, 30, tzinfo=UTC),
        generation_mw=4800.0,
    )
    exact = ForecastPoint(
        start_time=target_time,
        publish_time=datetime(2026, 1, 14, 9, 0, tzinfo=UTC),
        generation_mw=5100.0,
    )
    selected = select_forecast_for_period(target_time, [earlier, exact], cutoff)
    assert selected == exact


def test_after_cutoff_is_ineligible_leakage_guard():
    target_time = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
    cutoff = datetime(2026, 1, 14, 9, 0, tzinfo=UTC)

    valid_eligible = ForecastPoint(
        start_time=target_time,
        publish_time=datetime(2026, 1, 14, 7, 30, tzinfo=UTC),
        generation_mw=4500.0,
    )
    # Published 1 second after cutoff
    late_leakage = ForecastPoint(
        start_time=target_time,
        publish_time=datetime(2026, 1, 14, 9, 0, 1, tzinfo=UTC),
        generation_mw=9999.0,
    )
    selected = select_forecast_for_period(
        target_time, [valid_eligible, late_leakage], cutoff
    )
    assert selected == valid_eligible


def test_latest_eligible_wins_regardless_of_order():
    target_time = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
    cutoff = datetime(2026, 1, 14, 9, 0, tzinfo=UTC)

    v1 = ForecastPoint(
        start_time=target_time,
        publish_time=datetime(2026, 1, 14, 2, 30, tzinfo=UTC),
        generation_mw=4000.0,
    )
    v2 = ForecastPoint(
        start_time=target_time,
        publish_time=datetime(2026, 1, 14, 4, 30, tzinfo=UTC),
        generation_mw=4200.0,
    )
    v3 = ForecastPoint(
        start_time=target_time,
        publish_time=datetime(2026, 1, 14, 7, 30, tzinfo=UTC),
        generation_mw=4600.0,
    )

    # Test with shuffled order
    assert select_forecast_for_period(target_time, [v3, v1, v2], cutoff) == v3
    assert select_forecast_for_period(target_time, [v1, v2, v3], cutoff) == v3


def test_only_late_forecasts_returns_none():
    # Never fallback to late forecast
    target_time = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
    cutoff = datetime(2026, 1, 14, 9, 0, tzinfo=UTC)

    late1 = ForecastPoint(
        start_time=target_time,
        publish_time=datetime(2026, 1, 14, 9, 30, tzinfo=UTC),
        generation_mw=5000.0,
    )
    late2 = ForecastPoint(
        start_time=target_time,
        publish_time=datetime(2026, 1, 15, 2, 30, tzinfo=UTC),
        generation_mw=5200.0,
    )
    selected = select_forecast_for_period(target_time, [late1, late2], cutoff)
    assert selected is None


def test_different_start_time_ignored():
    target_time = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
    cutoff = datetime(2026, 1, 14, 9, 0, tzinfo=UTC)

    diff_time = ForecastPoint(
        start_time=datetime(2026, 1, 15, 13, 0, tzinfo=UTC),
        publish_time=datetime(2026, 1, 14, 7, 30, tzinfo=UTC),
        generation_mw=5000.0,
    )
    selected = select_forecast_for_period(target_time, [diff_time], cutoff)
    assert selected is None


def test_empty_forecast_list():
    target_time = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
    cutoff = datetime(2026, 1, 14, 9, 0, tzinfo=UTC)
    assert select_forecast_for_period(target_time, [], cutoff) is None
