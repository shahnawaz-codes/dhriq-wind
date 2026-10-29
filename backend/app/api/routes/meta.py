from fastapi import APIRouter, Response

from app.api.schemas import (
    AssumptionsMeta,
    MetaResponse,
    ProvenanceMeta,
    WindowMeta,
)
from app.config import get_settings
from app.services.data_store import get_data_store

router = APIRouter()


@router.get("/meta", response_model=MetaResponse)
async def get_meta(response: Response) -> MetaResponse:
    """Returns evaluation window, assumptions, and upstream provenance."""
    response.headers["Cache-Control"] = "public, max-age=300"
    settings = get_settings()
    store = get_data_store(settings)
    prov = store.get_provenance()

    # January 2026 expected periods is 744 (31 days * 24 hours)
    expected_periods = 744

    return MetaResponse(
        window=WindowMeta(
            start_date=settings.delivery_window_start,
            end_date=settings.delivery_window_end,
            expected_periods=expected_periods,
        ),
        assumptions=AssumptionsMeta(
            cutoff_time_default=settings.decision_cutoff_local_time,
            cutoff_timezone=settings.decision_timezone,
            cutoff_rule=(
                "Forecast eligible if publishTime <= (delivery date - 1 day) "
                "at cutoff_time; latest eligible publishTime is selected"
            ),
            cutoff_inclusive=True,
            status="provisional",
        ),
        provenance=ProvenanceMeta(
            source=prov["source"],
            datasets=prov["datasets"],
            fetched_at=prov["fetched_at"],
            cache_age_seconds=prov["cache_age_seconds"],
            stale=prov["stale"],
        ),
    )
