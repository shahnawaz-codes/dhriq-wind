# SYNTHETIC unit tests for normalization, parsing, validation and deduplication
from datetime import UTC, datetime

from app.domain.normalize import normalize_actuals, normalize_forecasts, parse_timestamp


def test_parse_timestamp_formats():
    # ISO-8601 with Z
    t1 = parse_timestamp("2026-01-01T00:00:00Z")
    assert t1 == datetime(2026, 1, 1, 0, 0, tzinfo=UTC)

    # ISO-8601 with milliseconds
    t2 = parse_timestamp("2026-01-01T00:00:00.000Z")
    assert t2 == datetime(2026, 1, 1, 0, 0, tzinfo=UTC)

    # Space-separated
    t3 = parse_timestamp("2026-01-01 00:00:00Z")
    assert t3 == datetime(2026, 1, 1, 0, 0, tzinfo=UTC)

    # Offset notation
    t4 = parse_timestamp("2026-01-01T00:00:00+00:00")
    assert t4 == datetime(2026, 1, 1, 0, 0, tzinfo=UTC)

    # Naive or unparseable rejects
    assert parse_timestamp("2026-01-01T00:00:00") is None
    assert parse_timestamp("invalid-date") is None
    assert parse_timestamp(None) is None


def test_normalize_actuals_filters_non_wind():
    raw_rows = [
        {
            "dataset": "FUELHH",
            "startTime": "2026-01-01T00:00:00Z",
            "fuelType": "CCGT",
            "generation": 4000,
        },
        {
            "dataset": "FUELHH",
            "startTime": "2026-01-01T00:00:00Z",
            "fuelType": "WIND",
            "generation": 12000,
        },
        {
            "dataset": "FUELHH",
            "startTime": "2026-01-01T00:00:00Z",
            "fuelType": "NUCLEAR",
            "generation": 5000,
        },
    ]
    actuals, stats = normalize_actuals(raw_rows)
    assert len(actuals) == 1
    assert actuals[0].generation_mw == 12000.0
    assert stats.raw_actual_rows == 3
    assert stats.wind_actual_rows == 1


def test_normalize_actuals_valid_zero_and_invalid_generation():
    raw_rows = [
        # Valid zero generation
        {
            "dataset": "FUELHH",
            "startTime": "2026-01-01T00:00:00Z",
            "fuelType": "WIND",
            "generation": 0,
        },
        # Null generation
        {
            "dataset": "FUELHH",
            "startTime": "2026-01-01T01:00:00Z",
            "fuelType": "WIND",
            "generation": None,
        },
        # Negative generation
        {
            "dataset": "FUELHH",
            "startTime": "2026-01-01T02:00:00Z",
            "fuelType": "WIND",
            "generation": -10,
        },
        # NaN / inf
        {
            "dataset": "FUELHH",
            "startTime": "2026-01-01T03:00:00Z",
            "fuelType": "WIND",
            "generation": float("nan"),
        },
        {
            "dataset": "FUELHH",
            "startTime": "2026-01-01T04:00:00Z",
            "fuelType": "WIND",
            "generation": float("inf"),
        },
        # Non-numeric string
        {
            "dataset": "FUELHH",
            "startTime": "2026-01-01T05:00:00Z",
            "fuelType": "WIND",
            "generation": "bad",
        },
        # Invalid timestamp
        {
            "dataset": "FUELHH",
            "startTime": "invalid-time",
            "fuelType": "WIND",
            "generation": 100,
        },
    ]
    actuals, stats = normalize_actuals(raw_rows)
    assert len(actuals) == 1
    assert actuals[0].generation_mw == 0.0
    assert stats.invalid_actual_rows == 6


def test_normalize_actuals_deduplication():
    # Duplicate same startTime
    raw_rows = [
        {
            "dataset": "FUELHH",
            "startTime": "2026-01-01T00:00:00Z",
            "publishTime": "2026-01-01T00:30:00Z",
            "fuelType": "WIND",
            "generation": 10000,
        },
        {
            "dataset": "FUELHH",
            "startTime": "2026-01-01T00:00:00Z",
            "publishTime": "2026-01-01T01:00:00Z",  # later publish wins
            "fuelType": "WIND",
            "generation": 10500,
        },
    ]
    actuals, stats = normalize_actuals(raw_rows)
    assert len(actuals) == 1
    assert actuals[0].generation_mw == 10500.0
    assert stats.duplicate_actual_rows == 1
    assert len(stats.warnings) == 1
    assert "differing values" in stats.warnings[0].lower()


def test_normalize_forecasts_deduplication():
    # Identical duplicate
    raw_rows_identical = [
        {
            "dataset": "WINDFOR",
            "startTime": "2026-01-01T00:00:00Z",
            "publishTime": "2025-12-31T07:30:00Z",
            "generation": 8000,
        },
        {
            "dataset": "WINDFOR",
            "startTime": "2026-01-01T00:00:00Z",
            "publishTime": "2025-12-31T07:30:00Z",
            "generation": 8000,
        },
    ]
    fcs1, stats1 = normalize_forecasts(raw_rows_identical)
    assert len(fcs1) == 1
    assert stats1.duplicate_forecast_rows == 1
    assert stats1.conflicting_forecast_rows == 0
    assert len(stats1.warnings) == 0

    # Conflicting duplicate (different generation)
    raw_rows_conflict = [
        {
            "dataset": "WINDFOR",
            "startTime": "2026-01-01T00:00:00Z",
            "publishTime": "2025-12-31T07:30:00Z",
            "generation": 8000,
        },
        {
            "dataset": "WINDFOR",
            "startTime": "2026-01-01T00:00:00Z",
            "publishTime": "2025-12-31T07:30:00Z",
            "generation": 8500,
        },
    ]
    fcs2, stats2 = normalize_forecasts(raw_rows_conflict)
    assert len(fcs2) == 1
    assert fcs2[0].generation_mw == 8500.0
    assert stats2.conflicting_forecast_rows == 1
    assert len(stats2.warnings) == 1


def test_normalize_invalid_and_non_dict_rows():
    # Non-dict items
    actuals, a_stats = normalize_actuals(["not-a-dict", 123, None])
    assert len(actuals) == 0
    assert a_stats.invalid_actual_rows == 3

    forecasts, f_stats = normalize_forecasts(
        [
            "not-a-dict",
            {
                "dataset": "WINDFOR",
                "startTime": "invalid-time",
                "publishTime": "2025-12-31T07:30:00Z",
                "generation": 100,
            },
            {
                "dataset": "WINDFOR",
                "startTime": "2026-01-01T00:00:00Z",
                "publishTime": "invalid-time",
                "generation": 100,
            },
            {
                "dataset": "WINDFOR",
                "startTime": "2026-01-01T00:00:00Z",
                "publishTime": "2025-12-31T07:30:00Z",
                "generation": -10,
            },
            {
                "dataset": "WINDFOR",
                "startTime": "2026-01-01T00:00:00Z",
                "publishTime": "2025-12-31T07:30:00Z",
                "generation": None,
            },
        ]
    )
    assert len(forecasts) == 0
    assert f_stats.invalid_forecast_rows == 5


def test_normalize_actuals_publish_time_tie_breaks():
    # 1. Existing has None, candidate has publish_time
    r1 = [
        {
            "dataset": "FUELHH",
            "startTime": "2026-01-01T00:00:00Z",
            "publishTime": None,
            "fuelType": "WIND",
            "generation": 1000,
        },
        {
            "dataset": "FUELHH",
            "startTime": "2026-01-01T00:00:00Z",
            "publishTime": "2026-01-01T00:30:00Z",
            "fuelType": "WIND",
            "generation": 1200,
        },
    ]
    a1, s1 = normalize_actuals(r1)
    assert a1[0].generation_mw == 1200.0
    assert s1.duplicate_actual_rows == 1

    # 2. Both have None publish_time (last received wins)
    r2 = [
        {
            "dataset": "FUELHH",
            "startTime": "2026-01-01T00:00:00Z",
            "publishTime": None,
            "fuelType": "WIND",
            "generation": 1000,
        },
        {
            "dataset": "FUELHH",
            "startTime": "2026-01-01T00:00:00Z",
            "publishTime": None,
            "fuelType": "WIND",
            "generation": 1300,
        },
    ]
    a2, s2 = normalize_actuals(r2)
    assert a2[0].generation_mw == 1300.0
    assert s2.duplicate_actual_rows == 1
