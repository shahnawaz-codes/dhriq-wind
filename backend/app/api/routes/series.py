from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.api.errors import InvalidParameterError
from app.api.schemas import (
    DailySeriesPoint,
    HourlySeriesPoint,
    SeriesResponse,
)
from app.api.validation import validate_shared_params
from app.config import get_settings
from app.domain.matching import build_comparison_records
from app.domain.metrics import compute_daily_metrics
from app.services.data_store import get_data_store

router = APIRouter()


@router.get("/series", response_model=SeriesResponse)
async def get_series(
    response: Response,
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    cutoff_time: Annotated[str | None, Query()] = None,
    granularity: Annotated[str, Query()] = "hourly",
) -> SeriesResponse:
    """Return time-series data for chart visualization (hourly or daily)."""
    response.headers["Cache-Control"] = "public, max-age=300"
    if granularity not in {"hourly", "daily"}:
        raise InvalidParameterError(
            f"Invalid granularity {granularity!r}. Must be 'hourly' or 'daily'.",
            field="granularity",
        )

    settings = get_settings()
    eff_start, eff_end, eff_cutoff = validate_shared_params(
        settings, start_date, end_date, cutoff_time
    )

    store = get_data_store(settings)
    cached = await store.get_data()

    records = build_comparison_records(
        actuals=cached.actuals,
        forecasts=cached.forecasts,
        start_date=eff_start,
        end_date=eff_end,
        cutoff_time_str=eff_cutoff,
        tz_name=settings.decision_timezone,
    )

    if granularity == "hourly":
        points = []
        for r in records:
            # Lookup optional :30 context actual (start_time + 30 min)
            half_hour_key = r.start_time + timedelta(minutes=30)
            context_half_hour = cached.actual_half_hours.get(half_hour_key)

            st_iso = r.start_time.isoformat().replace("+00:00", "Z")
            pub_iso = (
                r.forecast_publish_time.isoformat().replace("+00:00", "Z")
                if r.forecast_publish_time is not None
                else None
            )

            points.append(
                HourlySeriesPoint(
                    start_time=st_iso,
                    actual_mw=round(r.actual_mw, 1)
                    if r.actual_mw is not None
                    else None,
                    forecast_mw=round(r.forecast_mw, 1)
                    if r.forecast_mw is not None
                    else None,
                    forecast_publish_time=pub_iso,
                    status=r.status.value,
                    actual_half_hour_context_mw=(
                        round(context_half_hour, 1)
                        if context_half_hour is not None
                        else None
                    ),
                )
            )

        return SeriesResponse(granularity="hourly", unit="MW", points=points)

    # Daily granularity
    daily_metrics_list = compute_daily_metrics(records)
    daily_points = []
    for dm in daily_metrics_list:
        cutoff_iso = dm.cutoff_time.isoformat().replace("+00:00", "Z")
        daily_points.append(
            DailySeriesPoint(
                date=dm.date.isoformat(),
                n_matched=dm.n_matched,
                mean_actual_mw=round(dm.mean_actual_mw, 1)
                if dm.mean_actual_mw is not None
                else None,
                mean_forecast_mw=round(dm.mean_forecast_mw, 1)
                if dm.mean_forecast_mw is not None
                else None,
                mae_mw=round(dm.mae_mw, 1) if dm.mae_mw is not None else None,
                rmse_mw=round(dm.rmse_mw, 1) if dm.rmse_mw is not None else None,
                bias_mw=round(dm.bias_mw, 1) if dm.bias_mw is not None else None,
                cutoff_time=cutoff_iso,
            )
        )

    return SeriesResponse(granularity="daily", unit="MW", points=daily_points)
