from datetime import UTC, date, datetime
from unittest.mock import AsyncMock

import app.services.data_store as ds_module
import pytest
from app.config import Settings
from app.domain.models import ActualPoint, ForecastPoint, NormalizationStats
from app.main import create_app
from app.services.data_store import CachedData, DataStore
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

    ds_module._data_store_instance = store

    test_app = create_app()
    with TestClient(test_app) as client:
        yield client

    ds_module._data_store_instance = None
