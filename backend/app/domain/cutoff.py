import re
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def parse_cutoff_time(cutoff_str: str) -> tuple[int, int]:
    """Parse and validate a cutoff time string in HH:MM format (24-hour clock).

    Raises:
        ValueError: if the string does not match HH:MM or has invalid ranges.
    """
    if not cutoff_str or not isinstance(cutoff_str, str):
        raise ValueError(f"Invalid cutoff time: {cutoff_str!r}. Expected 'HH:MM'.")

    match = _TIME_RE.match(cutoff_str.strip())
    if not match:
        raise ValueError(
            f"Invalid cutoff time format: {cutoff_str!r}. Must be 'HH:MM' (00:00 to 23:59)."
        )

    hour, minute = int(match.group(1)), int(match.group(2))
    return hour, minute


def get_delivery_date(instant: datetime, tz_name: str = "Europe/London") -> date:
    """Return the calendar date of a delivery instant in the local timezone."""
    tz = ZoneInfo(tz_name)
    if instant.tzinfo is None:
        raise ValueError(f"Instant must be timezone-aware UTC: {instant}")
    local_dt = instant.astimezone(tz)
    return local_dt.date()


def compute_decision_cutoff(
    delivery_date: date,
    cutoff_time_str: str = "09:00",
    tz_name: str = "Europe/London",
) -> datetime:
    """Compute the UTC decision cutoff instant for a given delivery date (BR-02).

    Rule: Cutoff is (delivery_date - 1 day) at cutoff_time in Europe/London,
    converted to a timezone-aware UTC datetime.

    DST handling:
    - Ambiguous local times (fall-back transition, e.g. 01:30 during autumn change):
      fold=0 explicitly selects the first occurrence (BST / UTC+1) per FORECAST_LOGIC §9.2.
    - Nonexistent local times (spring-forward transition, e.g. 01:30 during spring gap):
      zoneinfo with fold=0 maps to the pre-transition UTC offset (+00:00).
    """
    hour, minute = parse_cutoff_time(cutoff_time_str)
    prev_day = delivery_date - timedelta(days=1)
    tz = ZoneInfo(tz_name)

    # Local datetime on D-1 with explicit fold=0 for deterministic resolution
    local_dt = datetime(
        prev_day.year,
        prev_day.month,
        prev_day.day,
        hour,
        minute,
        fold=0,
        tzinfo=tz,
    )
    # Convert to UTC instant
    return local_dt.astimezone(UTC)
