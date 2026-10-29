from datetime import datetime

from app.domain.models import ForecastPoint


def select_forecast_for_period(
    start_time: datetime,
    forecasts: list[ForecastPoint],
    cutoff_time: datetime,
) -> ForecastPoint | None:
    """Select the latest forecast published at or before cutoff for a given delivery time.

    Implements BR-03 (inclusive eligibility filter) and BR-04 (latest publishTime selection).
    Never falls back to a forecast published after cutoff (prevents data leakage).
    """
    eligible = [
        fp
        for fp in forecasts
        if fp.start_time == start_time and fp.publish_time <= cutoff_time
    ]

    if not eligible:
        return None

    # Pick the one with the maximum publish_time.
    # Python max with key preserves stability or picks greatest.
    return max(eligible, key=lambda fp: fp.publish_time)
