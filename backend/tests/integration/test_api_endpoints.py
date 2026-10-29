from datetime import UTC, date, datetime
from unittest.mock import AsyncMock

import app.services.data_store as ds_module
import pytest
from app.config import Settings
from app.domain.models import ActualPoint, ForecastPoint, NormalizationStats
from app.main import create_app
from app.services.data_store import (
    CachedData,
    DataNotReadyError,
    DataStore,
    UpstreamError,
)
from fastapi.testclient import TestClient


@pytest.fixture
def mock_cached_data():
    t_00 = datetime(2026, 1, 15, 10, 0, tzinfo=UTC)
    t_30 = datetime(2026, 1, 15, 10, 30, tzinfo=UTC)
    t_11 = datetime(2026, 1, 15, 11, 0, tzinfo=UTC)

    # Actuals: 10:00 is 5000 MW, 11:00 is 4000 MW
    actuals = [
        ActualPoint(start_time=t_00, generation_mw=5000.0),
        ActualPoint(start_time=t_11, generation_mw=4000.0),
    ]

    # Forecasts:
    # Early forecast published at 07:30 UTC
    # Late forecast published at 10:30 UTC
    forecasts = [
        # For 10:00
        ForecastPoint(
            start_time=t_00,
            publish_time=datetime(2026, 1, 14, 7, 30, tzinfo=UTC),
            generation_mw=4800.0,
        ),
        ForecastPoint(
            start_time=t_00,
            publish_time=datetime(2026, 1, 14, 10, 30, tzinfo=UTC),
            generation_mw=5100.0,
        ),
        # For 11:00
        ForecastPoint(
            start_time=t_11,
            publish_time=datetime(2026, 1, 14, 7, 30, tzinfo=UTC),
            generation_mw=3900.0,
        ),
    ]

    actual_half_hours = {
        t_30: 5050.0,
    }

    stats = NormalizationStats(
        raw_actual_rows=10,
        raw_forecast_rows=10,
        wind_actual_rows=2,
        duplicate_actual_rows=0,
        duplicate_forecast_rows=0,
        conflicting_forecast_rows=0,
        invalid_actual_rows=0,
        invalid_forecast_rows=0,
    )

    return CachedData(
        actuals=actuals,
        forecasts=forecasts,
        actual_half_hours=actual_half_hours,
        stats=stats,
        fetched_at=datetime(2026, 1, 16, 0, 0, tzinfo=UTC),
        is_stale=False,
    )


@pytest.fixture
def app_client(mock_cached_data):
    settings = Settings(
        delivery_window_start=date(2026, 1, 1),
        delivery_window_end=date(2026, 1, 31),
        decision_cutoff_local_time="09:00",
        decision_timezone="Europe/London",
        preload_on_startup=False,
        cors_allowed_origins=["http://localhost:5173"],
    )

    store = DataStore(settings=settings)
    store._cached = mock_cached_data
    store.get_data = AsyncMock(return_value=mock_cached_data)

    app = create_app()
    app.dependency_overrides = {}

    # Override data store singleton
    import app.services.data_store as ds_module

    original_store = ds_module._data_store_instance
    ds_module._data_store_instance = store

    client = TestClient(app)
    yield client

    ds_module._data_store_instance = original_store


def test_health_endpoint(app_client):
    res = app_client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert data["data_loaded"] is True
    assert res.headers["Cache-Control"] == "no-store"


def test_meta_endpoint(app_client):
    res = app_client.get("/api/meta")
    assert res.status_code == 200
    data = res.json()
    assert data["window"]["expected_periods"] == 744
    assert data["window"]["start_date"] == "2026-01-01"
    assert data["window"]["end_date"] == "2026-01-31"
    assert data["assumptions"]["cutoff_time_default"] == "09:00"
    assert data["assumptions"]["cutoff_timezone"] == "Europe/London"
    assert data["assumptions"]["cutoff_inclusive"] is True
    assert data["assumptions"]["status"] == "provisional"
    assert data["provenance"]["source"] == "Elexon Insights API"
    assert "public, max-age=300" in res.headers["Cache-Control"]


def test_summary_and_cutoff_recalculation(app_client):
    # With default cutoff 09:00 on D-1:
    # 10:00 uses 07:30 run (4800 MW), actual 5000 -> error 5000 - 4800 = +200 MW
    # 11:00 uses 07:30 run (3900 MW), actual 4000 -> error 4000 - 3900 = +100 MW
    # Bias = (200 + 100) / 2 = +150 MW
    res1 = app_client.get(
        "/api/summary?start_date=2026-01-15&end_date=2026-01-15&cutoff_time=09:00"
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["metrics"]["n_matched"] == 2
    assert data1["metrics"]["bias_mw"] == 150.0
    assert data1["metrics"]["mae_mw"] == 150.0
    assert len(data1["forecast_vintages"]) == 1
    assert data1["forecast_vintages"][0]["periods_count"] == 2

    # With later cutoff 12:00 on D-1:
    # 10:00 now selects 10:30 run (5100 MW), actual 5000 -> error 5000 - 5100 = -100 MW
    # 11:00 still uses 07:30 run (3900 MW), actual 4000 -> error 4000 - 3900 = +100 MW
    # Recalculated Bias = (-100 + 100) / 2 = 0.0 MW
    res2 = app_client.get(
        "/api/summary?start_date=2026-01-15&end_date=2026-01-15&cutoff_time=12:00"
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["metrics"]["bias_mw"] == 0.0
    assert data2["metrics"]["mae_mw"] == 100.0  # (100 + 100) / 2
    # Two distinct vintages selected now (07:30 and 10:30)
    assert len(data2["forecast_vintages"]) == 2


def test_series_hourly_and_daily(app_client):
    # Hourly series
    res_hourly = app_client.get(
        "/api/series?start_date=2026-01-15&end_date=2026-01-15&granularity=hourly"
    )
    assert res_hourly.status_code == 200
    data_h = res_hourly.json()
    assert data_h["granularity"] == "hourly"
    assert data_h["unit"] == "MW"
    assert len(data_h["points"]) == 24  # 1 day has 24 hourly periods

    # 10:00 point has matched status and :30 context actual (5050 MW)
    p_10 = next(p for p in data_h["points"] if "10:00:00" in p["start_time"])
    assert p_10["actual_mw"] == 5000.0
    assert p_10["forecast_mw"] == 4800.0
    assert p_10["status"] == "matched"
    assert p_10["actual_half_hour_context_mw"] == 5050.0

    # Daily series
    res_daily = app_client.get(
        "/api/series?start_date=2026-01-15&end_date=2026-01-15&granularity=daily"
    )
    assert res_daily.status_code == 200
    data_d = res_daily.json()
    assert data_d["granularity"] == "daily"
    assert len(data_d["points"]) == 1
    d_point = data_d["points"][0]
    assert d_point["date"] == "2026-01-15"
    assert d_point["n_matched"] == 2
    assert d_point["mae_mw"] == 150.0


def test_records_pagination_and_sorting(app_client):
    res = app_client.get(
        "/api/records?start_date=2026-01-15&end_date=2026-01-15&page=1&page_size=10&sort_by=actual_mw&sort_dir=desc"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total_items"] == 24
    assert data["total_pages"] == 3
    items = data["items"]
    assert len(items) == 10

    # Sorting puts null values last regardless of direction
    # First items should be 5000, 4000, then nulls
    assert items[0]["actual_mw"] == 5000.0
    assert items[1]["actual_mw"] == 4000.0
    assert items[2]["actual_mw"] is None

    # Filter by status=matched
    res_matched = app_client.get(
        "/api/records?start_date=2026-01-15&end_date=2026-01-15&status=matched"
    )
    assert res_matched.status_code == 200
    data_m = res_matched.json()
    assert data_m["total_items"] == 2
    assert all(i["status"] == "matched" for i in data_m["items"])

    # Page beyond last -> items: []
    res_beyond = app_client.get(
        "/api/records?start_date=2026-01-15&end_date=2026-01-15&page=100&page_size=10"
    )
    assert res_beyond.status_code == 200
    assert res_beyond.json()["items"] == []


def test_validation_errors_return_400_with_unified_error_shape(app_client):
    # 1. Start date after end date
    r1 = app_client.get("/api/summary?start_date=2026-01-15&end_date=2026-01-10")
    assert r1.status_code == 400
    d1 = r1.json()
    assert d1["error"]["code"] == "INVALID_PARAMETER"
    assert "start_date" in d1["error"]["message"]
    assert d1["error"]["details"][0]["field"] == "start_date"

    # 2. Date outside window
    r2 = app_client.get("/api/summary?start_date=2025-12-31")
    assert r2.status_code == 400
    d2 = r2.json()
    assert d2["error"]["code"] == "INVALID_PARAMETER"

    # 3. Invalid cutoff time
    r3 = app_client.get("/api/summary?cutoff_time=25:00")
    assert r3.status_code == 400
    d3 = r3.json()
    assert d3["error"]["code"] == "INVALID_PARAMETER"
    assert d3["error"]["details"][0]["field"] == "cutoff_time"

    # 4. Bad sort_by field
    r4 = app_client.get("/api/records?sort_by=nonexistent")
    assert r4.status_code == 400
    d4 = r4.json()
    assert d4["error"]["code"] == "INVALID_PARAMETER"

    # 5. page_size > 500
    r5 = app_client.get("/api/records?page_size=501")
    assert r5.status_code == 400
    d5 = r5.json()
    assert d5["error"]["code"] == "INVALID_PARAMETER"

    # 6. end_date beyond window
    r6 = app_client.get("/api/summary?end_date=2026-02-05")
    assert r6.status_code == 400
    assert r6.json()["error"]["code"] == "INVALID_PARAMETER"

    # 7. min_abs_error_mw negative
    r7 = app_client.get("/api/records?min_abs_error_mw=-10")
    assert r7.status_code == 400
    assert r7.json()["error"]["code"] == "INVALID_PARAMETER"

    # 8. invalid status
    r8 = app_client.get("/api/records?status=invalid_status")
    assert r8.status_code == 400
    assert r8.json()["error"]["code"] == "INVALID_PARAMETER"

    # 9. invalid sort_dir
    r9 = app_client.get("/api/records?sort_dir=sideways")
    assert r9.status_code == 400
    assert r9.json()["error"]["code"] == "INVALID_PARAMETER"

    # 10. page < 1
    r10 = app_client.get("/api/records?page=0")
    assert r10.status_code == 400
    assert r10.json()["error"]["code"] == "INVALID_PARAMETER"

    # 11. invalid granularity
    r11 = app_client.get("/api/series?granularity=weekly")
    assert r11.status_code == 400
    assert r11.json()["error"]["code"] == "INVALID_PARAMETER"


def test_records_filters_min_abs_error_and_asc_sort(app_client):
    # min_abs_error_mw = 150 (only 10:00 period error 200 >= 150; 11:00 error 100 < 150)
    res = app_client.get(
        "/api/records?start_date=2026-01-15&end_date=2026-01-15&min_abs_error_mw=150&sort_by=actual_mw&sort_dir=asc"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_items"] == 1
    assert data["items"][0]["actual_mw"] == 5000.0


def test_upstream_error_mapped_to_502(app_client):
    store = ds_module._data_store_instance
    original_get_data = store.get_data
    store.get_data = AsyncMock(side_effect=UpstreamError("Upstream connection down"))

    try:
        res = app_client.get("/api/summary")
        assert res.status_code == 502
        data = res.json()
        assert data["error"]["code"] == "UPSTREAM_ERROR"
        assert "Elexon Insights API" in data["error"]["message"]
    finally:
        store.get_data = original_get_data


def test_data_not_ready_mapped_to_503(app_client):
    store = ds_module._data_store_instance
    original_get_data = store.get_data
    store.get_data = AsyncMock(side_effect=DataNotReadyError("Loading"))

    try:
        res = app_client.get("/api/summary")
        assert res.status_code == 503
        assert res.headers["Retry-After"] == "5"
        data = res.json()
        assert data["error"]["code"] == "DATA_NOT_READY"
    finally:
        store.get_data = original_get_data


def test_generic_server_error_mapped_to_500(app_client):
    store = ds_module._data_store_instance
    original_get_data = store.get_data
    store.get_data = AsyncMock(side_effect=ZeroDivisionError("Unexpected boom"))

    # Pass raise_server_exceptions=False to let FastAPI exception handler return 500 response
    client_no_raise = TestClient(app_client.app, raise_server_exceptions=False)
    try:
        res = client_no_raise.get("/api/summary")
        assert res.status_code == 500
        data = res.json()
        assert data["error"]["code"] == "INTERNAL_ERROR"
        assert "ZeroDivisionError" not in data["error"]["message"]
    finally:
        store.get_data = original_get_data


def test_stale_cache_observable_to_consumers(app_client):
    # Requirement 4: Stale cache fallback must be observable in API responses
    # and cannot be mistaken for fresh data.
    store = ds_module._data_store_instance
    original_cached = store._cached

    # Mark cached data as stale
    stale_data = original_cached._replace(is_stale=True)
    store._cached = stale_data
    store.get_data = AsyncMock(return_value=stale_data)

    try:
        # 1. /api/meta shows stale=True
        res_meta = app_client.get("/api/meta")
        assert res_meta.status_code == 200
        assert res_meta.json()["provenance"]["stale"] is True

        # 2. /api/summary shows stale=True and warning in data_quality.warnings
        res_summary = app_client.get("/api/summary")
        assert res_summary.status_code == 200
        body = res_summary.json()
        assert body["provenance"]["stale"] is True
        assert any("stale" in w.lower() for w in body["data_quality"]["warnings"])
    finally:
        store._cached = original_cached
        store.get_data = AsyncMock(return_value=original_cached)


def test_404_not_found(app_client):
    res = app_client.get("/api/nonexistent_route")
    assert res.status_code == 404
    data = res.json()
    assert data["error"]["code"] == "NOT_FOUND"


def test_cors_headers(app_client):
    # Allowed origin gets Access-Control-Allow-Origin
    res_allowed = app_client.get(
        "/api/health", headers={"Origin": "http://localhost:5173"}
    )
    assert (
        res_allowed.headers.get("access-control-allow-origin")
        == "http://localhost:5173"
    )

    # Disallowed origin does not get Access-Control-Allow-Origin
    res_disallowed = app_client.get(
        "/api/health", headers={"Origin": "http://evil-origin.com"}
    )
    assert "access-control-allow-origin" not in res_disallowed.headers
