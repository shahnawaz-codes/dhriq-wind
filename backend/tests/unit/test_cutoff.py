# SYNTHETIC unit tests for cutoff logic
from datetime import UTC, date, datetime, timedelta

import pytest
from app.domain.cutoff import (
    compute_decision_cutoff,
    get_delivery_date,
    parse_cutoff_time,
)


def test_standard_january_cutoff():
    # Delivery date 2026-01-15 at default 09:00 Europe/London
    d = date(2026, 1, 15)
    cutoff = compute_decision_cutoff(d, "09:00", "Europe/London")
    assert cutoff == datetime(2026, 1, 14, 9, 0, tzinfo=UTC)
    assert cutoff.tzinfo == UTC


def test_year_boundary_cutoff():
    # Delivery date 2026-01-01 at 09:00 Europe/London -> crosses year/month boundary
    d = date(2026, 1, 1)
    cutoff = compute_decision_cutoff(d, "09:00", "Europe/London")
    assert cutoff == datetime(2025, 12, 31, 9, 0, tzinfo=UTC)


def test_custom_cutoff_times():
    d = date(2026, 1, 10)
    # 00:00 cutoff
    c_00 = compute_decision_cutoff(d, "00:00", "Europe/London")
    assert c_00 == datetime(2026, 1, 9, 0, 0, tzinfo=UTC)

    # 18:30 cutoff
    c_18 = compute_decision_cutoff(d, "18:30", "Europe/London")
    assert c_18 == datetime(2026, 1, 9, 18, 30, tzinfo=UTC)

    # 23:59 cutoff
    c_23 = compute_decision_cutoff(d, "23:59", "Europe/London")
    assert c_23 == datetime(2026, 1, 9, 23, 59, tzinfo=UTC)


def test_invalid_cutoff_time_strings():
    d = date(2026, 1, 10)
    invalid_inputs = ["25:00", "09:60", "9:00", "09-00", "noon", "", "-01:00"]
    for bad in invalid_inputs:
        with pytest.raises(ValueError):
            compute_decision_cutoff(d, bad, "Europe/London")
        with pytest.raises(ValueError):
            parse_cutoff_time(bad)


def test_get_delivery_date_utc_and_london():
    # In January (GMT), local date == UTC date
    t1 = datetime(2026, 1, 5, 23, 0, tzinfo=UTC)
    assert get_delivery_date(t1, "Europe/London") == date(2026, 1, 5)

    # In summer BST (UTC+1), 2026-07-05 23:30 UTC is 2026-07-06 00:30 BST
    t2 = datetime(2026, 7, 5, 23, 30, tzinfo=UTC)
    assert get_delivery_date(t2, "Europe/London") == date(2026, 7, 6)

    # Naive instant raises ValueError
    with pytest.raises(ValueError, match="Instant must be timezone-aware"):
        get_delivery_date(datetime(2026, 1, 5, 23, 0))


def test_dst_transitions_handling():
    # Requirement 8: Test timezone-aware calculations across DST boundaries.
    # Note: zoneinfo does not automatically reject ambiguous/nonexistent times,
    # so we test explicit conversion behavior.

    # 1. Delivery on 2026-03-31 (BST). D-1 is 2026-03-30 (BST).
    # 09:00 BST -> 08:00 UTC (BST is UTC+1)
    cutoff_bst = compute_decision_cutoff(date(2026, 3, 31), "09:00", "Europe/London")
    assert cutoff_bst == datetime(2026, 3, 30, 8, 0, tzinfo=UTC)

    # 2. Delivery on 2026-03-30 (first full day of BST).
    # D-1 is 2026-03-29 (the spring clock-change day).
    # At 09:00 local time on 2026-03-29, clocks have already sprung forward at 01:00 GMT to 02:00 BST.
    # So 09:00 local is 08:00 UTC.
    cutoff_spring = compute_decision_cutoff(date(2026, 3, 30), "09:00", "Europe/London")
    assert cutoff_spring == datetime(2026, 3, 29, 8, 0, tzinfo=UTC)

    # 3. Delivery on 2026-10-26 (first day back in GMT).
    # D-1 is 2026-10-25 (autumn clock change day, clocks fell back at 02:00 BST to 01:00 GMT).
    # At 09:00 local time on 2026-10-25, the UK is in GMT (UTC+0).
    cutoff_autumn = compute_decision_cutoff(
        date(2026, 10, 26), "09:00", "Europe/London"
    )
    assert cutoff_autumn == datetime(2026, 10, 25, 9, 0, tzinfo=UTC)

    # 4. Ambiguous local time during autumn fall-back (2026-10-25 01:30 local).
    # At 02:00 BST, clocks fall back to 01:00 GMT, so 01:30 occurs twice.
    # Specification (§9.2) mandates explicit fold=0 (first occurrence, BST UTC+1).
    # So 01:30 BST -> 00:30 UTC.
    cutoff_ambiguous = compute_decision_cutoff(
        date(2026, 10, 26), "01:30", "Europe/London"
    )
    assert cutoff_ambiguous == datetime(2026, 10, 25, 0, 30, tzinfo=UTC)

    # 5. Nonexistent local time during spring gap (2026-03-29 01:30 local).
    # At 01:00 GMT, clocks jump to 02:00 BST, so 01:30 does not exist locally.
    # Specification (§9.2) mandates explicit fold=0 (pre-transition offset +00:00).
    # So 01:30 GMT -> 01:30 UTC.
    cutoff_gap = compute_decision_cutoff(date(2026, 3, 30), "01:30", "Europe/London")
    assert cutoff_gap == datetime(2026, 3, 29, 1, 30, tzinfo=UTC)


def test_dst_delivery_date_period_counts():
    # TESTING.md §5.1:
    # Grouping 24-hour UTC blocks by Europe/London delivery date yields:
    # - 23 hourly delivery periods on 2026-03-29 (spring forward: 01:00-02:00 skipped)
    # - 25 hourly delivery periods on 2026-10-25 (fall back: 01:00-02:00 repeated)
    from collections import Counter

    # Generate UTC hourly instants for 2026-03-28 00:00 to 2026-03-31 00:00 (72 hours)
    spring_instants = [
        datetime(2026, 3, 28, 0, 0, tzinfo=UTC) + timedelta(hours=i) for i in range(72)
    ]
    spring_counts = Counter(
        get_delivery_date(t, "Europe/London") for t in spring_instants
    )
    assert spring_counts[date(2026, 3, 28)] == 24
    assert spring_counts[date(2026, 3, 29)] == 23  # Spring clock change day
    assert spring_counts[date(2026, 3, 30)] == 24

    # Generate UTC hourly instants for autumn transition starting at 2026-10-23 23:00 UTC
    # (which is 2026-10-24 00:00 BST) for 73 consecutive hourly periods
    autumn_instants = [
        datetime(2026, 10, 23, 23, 0, tzinfo=UTC) + timedelta(hours=i)
        for i in range(73)
    ]
    autumn_counts = Counter(
        get_delivery_date(t, "Europe/London") for t in autumn_instants
    )
    assert autumn_counts[date(2026, 10, 24)] == 24  # Standard BST day
    assert autumn_counts[date(2026, 10, 25)] == 25  # Autumn clock change day (25 hours)
    assert autumn_counts[date(2026, 10, 26)] == 24  # Standard GMT day
