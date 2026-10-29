import math
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.api.schemas import RecordItem, RecordsResponse
from app.api.validation import validate_records_params, validate_shared_params
from app.config import get_settings
from app.domain.matching import build_comparison_records
from app.domain.models import ComparisonRecord
from app.services.data_store import get_data_store

router = APIRouter()


def _get_sort_key(record: ComparisonRecord, field: str):
    val = getattr(record, field, None)
    return val


@router.get("/records", response_model=RecordsResponse)
async def get_records(
    response: Response,
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    cutoff_time: Annotated[str | None, Query()] = None,
    status: Annotated[str, Query()] = "all",
    min_abs_error_mw: Annotated[float | None, Query()] = None,
    sort_by: Annotated[str, Query()] = "start_time",
    sort_dir: Annotated[str, Query()] = "asc",
    page: Annotated[int, Query()] = 1,
    page_size: Annotated[int, Query()] = 50,
) -> RecordsResponse:
    """Return paginated, filtered, and sorted comparison records."""
    response.headers["Cache-Control"] = "public, max-age=300"
    settings = get_settings()
    eff_start, eff_end, eff_cutoff = validate_shared_params(
        settings, start_date, end_date, cutoff_time
    )
    validate_records_params(
        status=status,
        min_abs_error_mw=min_abs_error_mw,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
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

    # Filter by status
    filtered = records
    if status != "all":
        filtered = [r for r in filtered if r.status.value == status]

    # Filter by min_abs_error_mw
    if min_abs_error_mw is not None:
        filtered = [
            r
            for r in filtered
            if r.abs_error_mw is not None and r.abs_error_mw >= min_abs_error_mw
        ]

    # Sorting with "null values last regardless of direction"
    is_desc = sort_dir == "desc"
    if is_desc:
        # Descending: items with values come first (True > False), then sorted descending
        filtered.sort(
            key=lambda r: (
                getattr(r, sort_by) is not None,
                getattr(r, sort_by),
            ),
            reverse=True,
        )
    else:
        # Ascending: items with values come first (False < True), then sorted ascending
        filtered.sort(
            key=lambda r: (
                getattr(r, sort_by) is None,
                getattr(r, sort_by),
            )
        )

    total_items = len(filtered)
    total_pages = max(1, math.ceil(total_items / page_size)) if total_items > 0 else 1

    start_idx = (page - 1) * page_size
    page_records = (
        filtered[start_idx : start_idx + page_size] if start_idx < total_items else []
    )

    items = []
    for r in page_records:
        st_iso = r.start_time.isoformat().replace("+00:00", "Z")
        cutoff_iso = r.cutoff_time.isoformat().replace("+00:00", "Z")
        pub_iso = (
            r.forecast_publish_time.isoformat().replace("+00:00", "Z")
            if r.forecast_publish_time is not None
            else None
        )

        items.append(
            RecordItem(
                start_time=st_iso,
                delivery_date=r.delivery_date.isoformat(),
                cutoff_time=cutoff_iso,
                actual_mw=round(r.actual_mw, 1) if r.actual_mw is not None else None,
                forecast_mw=round(r.forecast_mw, 1)
                if r.forecast_mw is not None
                else None,
                forecast_publish_time=pub_iso,
                forecast_horizon_hours=(
                    round(r.forecast_horizon_hours, 1)
                    if r.forecast_horizon_hours is not None
                    else None
                ),
                error_mw=round(r.error_mw, 1) if r.error_mw is not None else None,
                abs_error_mw=round(r.abs_error_mw, 1)
                if r.abs_error_mw is not None
                else None,
                status=r.status.value,
            )
        )

    return RecordsResponse(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        items=items,
    )
