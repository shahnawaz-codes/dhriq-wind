from collections import Counter
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.api.schemas import (
    DataQualitySummary,
    ForecastVintage,
    ProvenanceMeta,
    RangeModel,
    SummaryAssumptions,
    SummaryMetrics,
    SummaryResponse,
)
from app.api.validation import validate_shared_params
from app.config import get_settings
from app.domain.matching import build_comparison_records
from app.domain.metrics import compute_metrics
from app.domain.models import RecordStatus
from app.services.data_store import get_data_store

router = APIRouter()


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    response: Response,
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    cutoff_time: Annotated[str | None, Query()] = None,
) -> SummaryResponse:
    """Return KPI metrics, data quality summary, and forecast vintages."""
    response.headers["Cache-Control"] = "public, max-age=300"
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

    metrics = compute_metrics(records)

    # Forecast vintages (distinct publish times for matched records within range)
    vintage_counts = Counter(
        r.forecast_publish_time.isoformat()
        for r in records
        if r.status == RecordStatus.MATCHED and r.forecast_publish_time is not None
    )
    # Sort newest first, limit 100
    sorted_vintages = [
        ForecastVintage(publish_time=pub_time, periods_count=cnt)
        for pub_time, cnt in sorted(vintage_counts.items(), reverse=True)[:100]
    ]

    # Data quality counts
    n_missing_actual = sum(
        1 for r in records if r.status == RecordStatus.MISSING_ACTUAL
    )
    n_missing_forecast = sum(
        1 for r in records if r.status == RecordStatus.MISSING_FORECAST
    )
    n_missing_both = sum(1 for r in records if r.status == RecordStatus.MISSING_BOTH)

    warnings: list[str] = []
    if metrics.n_matched == 0:
        warnings.append(
            "No matched forecast-actual periods found for the selected range."
        )
    if n_missing_forecast > 0:
        warnings.append(
            f"{n_missing_forecast} periods have no eligible forecast before the cutoff."
        )
    if n_missing_actual > 0:
        warnings.append(
            f"{n_missing_actual} periods are missing actual generation data."
        )
    if cached.is_stale:
        warnings.append(
            "Serving stale cached data; upstream Elexon API could not be reached on last refresh."
        )

    dq = DataQualitySummary(
        n_expected=metrics.n_expected,
        n_matched=metrics.n_matched,
        n_missing_actual=n_missing_actual,
        n_missing_forecast=n_missing_forecast,
        n_missing_both=n_missing_both,
        invalid_actual_rows=cached.stats.invalid_actual_rows,
        invalid_forecast_rows=cached.stats.invalid_forecast_rows,
        duplicate_actual_rows=cached.stats.duplicate_actual_rows,
        duplicate_forecast_rows=cached.stats.duplicate_forecast_rows,
        conflicting_forecast_rows=cached.stats.conflicting_forecast_rows,
        warnings=warnings,
    )

    prov = store.get_provenance()

    return SummaryResponse(
        range=RangeModel(start_date=eff_start, end_date=eff_end),
        assumptions=SummaryAssumptions(
            cutoff_time=eff_cutoff,
            cutoff_timezone=settings.decision_timezone,
            cutoff_inclusive=True,
        ),
        metrics=SummaryMetrics(
            n_matched=metrics.n_matched,
            mae_mw=round(metrics.mae_mw, 1) if metrics.mae_mw is not None else None,
            rmse_mw=round(metrics.rmse_mw, 1) if metrics.rmse_mw is not None else None,
            bias_mw=round(metrics.bias_mw, 1) if metrics.bias_mw is not None else None,
            mae_pct_of_mean_actual=(
                round(metrics.mae_pct, 1) if metrics.mae_pct is not None else None
            ),
            p90_abs_error_mw=(
                round(metrics.p90_abs_error_mw, 1)
                if metrics.p90_abs_error_mw is not None
                else None
            ),
            mean_actual_mw=(
                round(metrics.mean_actual_mw, 1)
                if metrics.mean_actual_mw is not None
                else None
            ),
            mean_forecast_mw=(
                round(metrics.mean_forecast_mw, 1)
                if metrics.mean_forecast_mw is not None
                else None
            ),
            coverage_pct=(
                round(metrics.coverage_pct, 1)
                if metrics.coverage_pct is not None
                else None
            ),
        ),
        forecast_vintages=sorted_vintages,
        data_quality=dq,
        provenance=ProvenanceMeta(
            source=prov["source"],
            datasets=prov["datasets"],
            fetched_at=prov["fetched_at"],
            cache_age_seconds=prov["cache_age_seconds"],
            stale=prov["stale"],
        ),
    )
