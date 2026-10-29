import math
from datetime import UTC, datetime
from typing import Any

from app.domain.models import ActualPoint, ForecastPoint, NormalizationStats


def parse_timestamp(val: Any) -> datetime | None:
    """Parse an ISO-8601 timestamp string into a timezone-aware UTC datetime.

    Accepts '...Z', '...+00:00', with or without milliseconds, and space-separated.
    Rejects naive datetimes or unparseable formats.
    """
    if not val or not isinstance(val, str):
        return None

    cleaned = val.strip()
    # Normalize space separator to 'T'
    if " " in cleaned:
        cleaned = cleaned.replace(" ", "T")

    # Replace 'Z' suffix with '+00:00' for fromisoformat compatibility
    if cleaned.endswith(("Z", "z")):
        cleaned = cleaned[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(cleaned)
    except ValueError:
        return None

    if dt.tzinfo is None:
        # Naive datetime is rejected
        return None

    return dt.astimezone(UTC)


def _is_valid_generation(val: Any) -> bool:
    """Check if a generation value is a valid, non-negative, finite number."""
    if val is None or isinstance(val, bool):
        return False
    if not isinstance(val, (int, float)):
        return False
    if math.isnan(val) or math.isinf(val):
        return False
    return val >= 0


def normalize_actuals(
    raw_rows: list[dict[str, Any]],
) -> tuple[list[ActualPoint], NormalizationStats]:
    """Parse, filter, validate and deduplicate raw FUELHH actual rows.

    Enforces:
    - fuelType == 'WIND' filter (challenge specification)
    - Valid non-negative finite generation (BR-08)
    - Timezone-aware UTC timestamps
    - Deduplication by startTime, keeping latest publishTime or last received (BR-05, §8)
    """
    stats = NormalizationStats()
    stats.raw_actual_rows = len(raw_rows)

    actuals_by_start: dict[datetime, ActualPoint] = {}

    for row in raw_rows:
        if not isinstance(row, dict):
            stats.invalid_actual_rows += 1
            continue

        fuel_type = str(row.get("fuelType", "")).strip().upper()
        if fuel_type != "WIND":
            # Ignore non-wind actuals
            continue

        stats.wind_actual_rows += 1

        start_dt = parse_timestamp(row.get("startTime"))
        if start_dt is None:
            stats.invalid_actual_rows += 1
            continue

        gen = row.get("generation")
        if not _is_valid_generation(gen):
            stats.invalid_actual_rows += 1
            continue

        pub_dt = parse_timestamp(row.get("publishTime"))
        candidate = ActualPoint(
            start_time=start_dt,
            generation_mw=float(gen),
            publish_time=pub_dt,
        )

        if start_dt in actuals_by_start:
            stats.duplicate_actual_rows += 1
            existing = actuals_by_start[start_dt]
            if not math.isclose(existing.generation_mw, candidate.generation_mw):
                stats.warnings.append(
                    f"Duplicate actual row for startTime {start_dt.isoformat()} with differing values: "
                    f"{existing.generation_mw} vs {candidate.generation_mw}"
                )
            # Keep latest publish_time if present, else keep last received
            if (
                (
                    candidate.publish_time is not None
                    and existing.publish_time is not None
                    and candidate.publish_time > existing.publish_time
                )
                or existing.publish_time is None
                and candidate.publish_time is not None
            ):
                actuals_by_start[start_dt] = candidate
            elif (
                candidate.publish_time == existing.publish_time
                or candidate.publish_time is None
            ):
                # Last received wins
                actuals_by_start[start_dt] = candidate
        else:
            actuals_by_start[start_dt] = candidate

    sorted_actuals = sorted(actuals_by_start.values(), key=lambda a: a.start_time)
    return sorted_actuals, stats


def normalize_forecasts(
    raw_rows: list[dict[str, Any]],
) -> tuple[list[ForecastPoint], NormalizationStats]:
    """Parse, validate and deduplicate raw WINDFOR forecast rows.

    Enforces:
    - Valid non-negative finite generation (BR-08)
    - Valid start and publication timestamps
    - Deduplication by (startTime, publishTime) pair (BR-05, §8)
    """
    stats = NormalizationStats()
    stats.raw_forecast_rows = len(raw_rows)

    fcs_by_pair: dict[tuple[datetime, datetime], ForecastPoint] = {}

    for row in raw_rows:
        if not isinstance(row, dict):
            stats.invalid_forecast_rows += 1
            continue

        start_dt = parse_timestamp(row.get("startTime"))
        pub_dt = parse_timestamp(row.get("publishTime"))
        if start_dt is None or pub_dt is None:
            stats.invalid_forecast_rows += 1
            continue

        gen = row.get("generation")
        if not _is_valid_generation(gen):
            stats.invalid_forecast_rows += 1
            continue

        candidate = ForecastPoint(
            start_time=start_dt,
            publish_time=pub_dt,
            generation_mw=float(gen),
        )

        pair = (start_dt, pub_dt)
        if pair in fcs_by_pair:
            existing = fcs_by_pair[pair]
            if not math.isclose(existing.generation_mw, candidate.generation_mw):
                stats.conflicting_forecast_rows += 1
                stats.warnings.append(
                    f"Conflicting forecast row for startTime {start_dt.isoformat()} and "
                    f"publishTime {pub_dt.isoformat()} with differing values: "
                    f"{existing.generation_mw} vs {candidate.generation_mw}"
                )
            else:
                stats.duplicate_forecast_rows += 1
            # Keep last received
            fcs_by_pair[pair] = candidate
        else:
            fcs_by_pair[pair] = candidate

    return list(fcs_by_pair.values()), stats
