from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

from app.domain.cutoff import compute_decision_cutoff, get_delivery_date
from app.domain.models import ActualPoint, ComparisonRecord, ForecastPoint, RecordStatus
from app.domain.selection import select_forecast_for_period


def build_comparison_records(
    actuals: list[ActualPoint],
    forecasts: list[ForecastPoint],
    start_date: date,
    end_date: date,
    cutoff_time_str: str = "09:00",
    tz_name: str = "Europe/London",
) -> list[ComparisonRecord]:
    """Build the expected hourly evaluation grid and match actuals to selected forecasts.

    Implements BR-01 (hourly grid), BR-02 (decision cutoff), BR-03/BR-04 (selection),
    BR-06 (exact startTime matching), and BR-07 (missing statuses).
    Excludes half-hour (:30) actuals from the evaluation grid.
    """
    # Index actuals by start_time (only top-of-hour :00:00Z will match the grid)
    actuals_by_start = {a.start_time: a for a in actuals}

    # Group forecasts by start_time
    forecasts_by_start = defaultdict(list)
    for f in forecasts:
        forecasts_by_start[f.start_time].append(f)

    # Cache cutoff computation per delivery date
    cutoffs_by_date: dict[date, datetime] = {}

    # Build expected grid T = every 1-hour UTC instant in [start_date, end_date + 1 day)
    grid_start = datetime(
        start_date.year, start_date.month, start_date.day, 0, 0, tzinfo=UTC
    )
    grid_end = datetime(
        end_date.year, end_date.month, end_date.day, 0, 0, tzinfo=UTC
    ) + timedelta(days=1)

    records: list[ComparisonRecord] = []
    current_instant = grid_start

    while current_instant < grid_end:
        t = current_instant
        d = get_delivery_date(t, tz_name)

        if d not in cutoffs_by_date:
            cutoffs_by_date[d] = compute_decision_cutoff(d, cutoff_time_str, tz_name)
        cutoff_utc = cutoffs_by_date[d]

        # Look up actual for exact instant t (:00:00Z)
        ac = actuals_by_start.get(t)

        # Select latest eligible forecast for instant t
        fc = select_forecast_for_period(t, forecasts_by_start.get(t, []), cutoff_utc)

        if ac is not None and fc is not None:
            status = RecordStatus.MATCHED
            actual_mw = ac.generation_mw
            forecast_mw = fc.generation_mw
            forecast_pub = fc.publish_time
            horizon_hours = (t - fc.publish_time).total_seconds() / 3600.0
            error_mw = actual_mw - forecast_mw  # BR-10: actual - forecast
            abs_error_mw = abs(error_mw)
        elif ac is not None and fc is None:
            status = RecordStatus.MISSING_FORECAST
            actual_mw = ac.generation_mw
            forecast_mw = None
            forecast_pub = None
            horizon_hours = None
            error_mw = None
            abs_error_mw = None
        elif ac is None and fc is not None:
            status = RecordStatus.MISSING_ACTUAL
            actual_mw = None
            forecast_mw = fc.generation_mw
            forecast_pub = fc.publish_time
            horizon_hours = (t - fc.publish_time).total_seconds() / 3600.0
            error_mw = None
            abs_error_mw = None
        else:
            status = RecordStatus.MISSING_BOTH
            actual_mw = None
            forecast_mw = None
            forecast_pub = None
            horizon_hours = None
            error_mw = None
            abs_error_mw = None

        records.append(
            ComparisonRecord(
                start_time=t,
                delivery_date=d,
                cutoff_time=cutoff_utc,
                actual_mw=actual_mw,
                forecast_mw=forecast_mw,
                forecast_publish_time=forecast_pub,
                forecast_horizon_hours=horizon_hours,
                error_mw=error_mw,
                abs_error_mw=abs_error_mw,
                status=status,
            )
        )

        current_instant += timedelta(hours=1)

    return records
