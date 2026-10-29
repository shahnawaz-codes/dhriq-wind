import asyncio
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock

import pytest
from app.config import Settings
from app.services.data_store import DataStore, UpstreamError


@pytest.fixture
def custom_settings():
    return Settings(
        cache_ttl_seconds=3600,
        delivery_window_start=date(2026, 1, 1),
        delivery_window_end=date(2026, 1, 2),
    )


@pytest.mark.anyio
async def test_data_store_caching_and_freshness(custom_settings):
    client = AsyncMock()
    client.fetch_fuelhh_wind.return_value = [
        {
            "startTime": "2026-01-01T10:00:00Z",
            "fuelType": "WIND",
            "generation": 5000,
        },
        {
            "startTime": "2026-01-01T10:30:00Z",
            "fuelType": "WIND",
            "generation": 5200,
        },
    ]
    client.fetch_windfor.return_value = [
        {
            "startTime": "2026-01-01T10:00:00Z",
            "publishTime": "2025-12-31T07:30:00Z",
            "generation": 4800,
        }
    ]

    store = DataStore(settings=custom_settings, client=client)
    assert not store.is_loaded

    # First fetch loads from client
    data1 = await store.get_data()
    assert store.is_loaded
    assert len(data1.actuals) == 2  # raw normalized actuals retain valid wind rows
    assert len(data1.forecasts) == 1
    # :30 stored in actual_half_hours dict
    t_30 = datetime(2026, 1, 1, 10, 30, tzinfo=UTC)
    assert data1.actual_half_hours.get(t_30) == 5200.0
    assert client.fetch_fuelhh_wind.call_count == 1

    # Second fetch returns cached data without calling client again
    data2 = await store.get_data()
    assert data2.fetched_at == data1.fetched_at
    assert client.fetch_fuelhh_wind.call_count == 1


@pytest.mark.anyio
async def test_data_store_single_flight_locking(custom_settings):
    client = AsyncMock()

    # Add small delay to simulate network call
    async def _mock_fuelhh(*args, **kwargs):
        await asyncio.sleep(0.05)
        return [
            {"startTime": "2026-01-01T00:00:00Z", "fuelType": "WIND", "generation": 100}
        ]

    async def _mock_windfor(*args, **kwargs):
        await asyncio.sleep(0.05)
        return [
            {
                "startTime": "2026-01-01T00:00:00Z",
                "publishTime": "2025-12-31T07:30:00Z",
                "generation": 100,
            }
        ]

    client.fetch_fuelhh_wind.side_effect = _mock_fuelhh
    client.fetch_windfor.side_effect = _mock_windfor

    store = DataStore(settings=custom_settings, client=client)

    # Launch 5 concurrent calls
    tasks = [store.get_data() for _ in range(5)]
    results = await asyncio.gather(*tasks)

    # All should receive identical cached data
    assert len(results) == 5
    assert client.fetch_fuelhh_wind.call_count == 1
    assert client.fetch_windfor.call_count == 1


@pytest.mark.anyio
async def test_data_store_stale_fallback_when_cache_exists(custom_settings):
    client = AsyncMock()
    # First call succeeds
    client.fetch_fuelhh_wind.return_value = [
        {"startTime": "2026-01-01T00:00:00Z", "fuelType": "WIND", "generation": 200}
    ]
    client.fetch_windfor.return_value = []

    store = DataStore(settings=custom_settings, client=client)
    data1 = await store.get_data()
    assert not data1.is_stale

    # Upstream fails on second call
    client.fetch_fuelhh_wind.side_effect = RuntimeError("Upstream network drop")

    # Force refresh
    data2 = await store.get_data(force_refresh=True)
    # Stale cache served with is_stale=True
    assert data2.is_stale
    assert len(data2.actuals) == 1
    assert data2.actuals[0].generation_mw == 200.0


@pytest.mark.anyio
async def test_data_store_raises_upstream_error_when_no_cache(custom_settings):
    client = AsyncMock()
    client.fetch_fuelhh_wind.side_effect = RuntimeError("Fatal connection failure")
    client.fetch_windfor.return_value = []

    store = DataStore(settings=custom_settings, client=client)

    with pytest.raises(UpstreamError, match="Failed to load data from Elexon"):
        await store.get_data()
