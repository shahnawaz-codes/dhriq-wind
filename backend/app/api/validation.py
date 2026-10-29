from datetime import date

from app.api.errors import InvalidParameterError
from app.config import Settings
from app.domain.cutoff import parse_cutoff_time


def validate_shared_params(
    settings: Settings,
    start_date: date | None = None,
    end_date: date | None = None,
    cutoff_time: str | None = None,
) -> tuple[date, date, str]:
    """Validate shared date range and cutoff_time parameters."""
    eff_start = start_date or settings.delivery_window_start
    eff_end = end_date or settings.delivery_window_end
    eff_cutoff = cutoff_time or settings.decision_cutoff_local_time

    # Range window checks
    if eff_start < settings.delivery_window_start:
        raise InvalidParameterError(
            f"start_date {eff_start} is before configured window start {settings.delivery_window_start}",
            field="start_date",
        )
    if eff_end > settings.delivery_window_end:
        raise InvalidParameterError(
            f"end_date {eff_end} is after configured window end {settings.delivery_window_end}",
            field="end_date",
        )
    if eff_start > eff_end:
        raise InvalidParameterError(
            f"start_date ({eff_start}) cannot be after end_date ({eff_end})",
            field="start_date",
        )

    # Cutoff time checks
    try:
        parse_cutoff_time(eff_cutoff)
    except ValueError as e:
        raise InvalidParameterError(str(e), field="cutoff_time") from e

    return eff_start, eff_end, eff_cutoff


VALID_RECORD_STATUSES = {
    "all",
    "matched",
    "missing_forecast",
    "missing_actual",
    "missing_both",
}

VALID_SORT_FIELDS = {
    "start_time",
    "actual_mw",
    "forecast_mw",
    "error_mw",
    "abs_error_mw",
    "forecast_publish_time",
    "forecast_horizon_hours",
}


def validate_records_params(
    status: str,
    min_abs_error_mw: float | None,
    sort_by: str,
    sort_dir: str,
    page: int,
    page_size: int,
) -> None:
    if status not in VALID_RECORD_STATUSES:
        raise InvalidParameterError(
            f"Invalid status {status!r}. Must be one of {sorted(VALID_RECORD_STATUSES)}",
            field="status",
        )
    if min_abs_error_mw is not None and min_abs_error_mw < 0:
        raise InvalidParameterError(
            f"min_abs_error_mw ({min_abs_error_mw}) must be >= 0",
            field="min_abs_error_mw",
        )
    if sort_by not in VALID_SORT_FIELDS:
        raise InvalidParameterError(
            f"Invalid sort_by {sort_by!r}. Must be one of {sorted(VALID_SORT_FIELDS)}",
            field="sort_by",
        )
    if sort_dir not in {"asc", "desc"}:
        raise InvalidParameterError(
            f"Invalid sort_dir {sort_dir!r}. Must be 'asc' or 'desc'",
            field="sort_dir",
        )
    if page < 1:
        raise InvalidParameterError(
            f"page ({page}) must be >= 1",
            field="page",
        )
    if page_size < 1 or page_size > 500:
        raise InvalidParameterError(
            f"page_size ({page_size}) must be between 1 and 500",
            field="page_size",
        )
