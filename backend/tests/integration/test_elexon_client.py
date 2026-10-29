from datetime import date

import httpx
import pytest
import respx
from app.config import Settings
from app.services.elexon_client import (
    ElexonClient,
    ElexonClientError,
    ElexonUpstreamError,
)


@pytest.fixture
def custom_settings():
    return Settings(
        elexon_base_url="https://mock.elexon.co.uk/api/v1",
        elexon_max_retries=2,
        elexon_timeout_seconds=2.0,
        elexon_chunk_days=7,
        forecast_publish_lookback_days=2,
        delivery_window_start=date(2026, 1, 1),
        delivery_window_end=date(2026, 1, 31),
    )


@pytest.mark.anyio
@respx.mock
async def test_fuelhh_chunking_and_wind_filter(custom_settings):
    # Window of 10 days: 2026-01-01 to 2026-01-10 -> 2 chunks (Jan 1-7, Jan 8-10)
    route = respx.get("https://mock.elexon.co.uk/api/v1/datasets/FUELHH").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "startTime": "2026-01-01T00:00:00Z",
                        "fuelType": "WIND",
                        "generation": 5000,
                    }
                ]
            },
        )
    )

    client = ElexonClient(settings=custom_settings)
    rows = await client.fetch_fuelhh_wind(date(2026, 1, 1), date(2026, 1, 10))

    assert route.call_count == 2
    assert len(rows) == 2  # 1 row per chunk
    # Verify first chunk params
    first_call = route.calls[0]
    assert first_call.request.url.params["settlementDateFrom"] == "2026-01-01"
    assert first_call.request.url.params["settlementDateTo"] == "2026-01-07"
    assert first_call.request.url.params["fuelType"] == "WIND"
    assert first_call.request.url.params["format"] == "json"

    # Verify second chunk params
    second_call = route.calls[1]
    assert second_call.request.url.params["settlementDateFrom"] == "2026-01-08"
    assert second_call.request.url.params["settlementDateTo"] == "2026-01-10"


@pytest.mark.anyio
@respx.mock
async def test_windfor_lookback_and_chunking(custom_settings):
    # 2-day delivery window: Jan 1 to Jan 2. Lookback 2 days -> starts Dec 30 00:00:00Z
    route = respx.get("https://mock.elexon.co.uk/api/v1/datasets/WINDFOR").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "startTime": "2026-01-01T10:00:00Z",
                    "publishTime": "2025-12-31T07:30:00Z",
                    "generation": 4500,
                }
            ],
        )
    )

    client = ElexonClient(settings=custom_settings)
    rows = await client.fetch_windfor(date(2026, 1, 1), date(2026, 1, 2))

    # Total duration: Dec 30 to Jan 2 is ~4 days (< 7 day chunk) -> 1 chunk
    assert route.call_count == 1
    call = route.calls[0]
    assert call.request.url.params["publishDateTimeFrom"] == "2025-12-30T00:00:00Z"
    assert call.request.url.params["publishDateTimeTo"] == "2026-01-02T23:59:59Z"
    assert len(rows) == 1


@pytest.mark.anyio
@respx.mock
async def test_retry_on_500_server_error(custom_settings):
    # Route fails with 500 twice, then succeeds on 3rd attempt
    route = respx.get("https://mock.elexon.co.uk/api/v1/datasets/FUELHH")
    route.side_effect = [
        httpx.Response(500, text="Internal Server Error"),
        httpx.Response(502, text="Bad Gateway"),
        httpx.Response(
            200,
            json={
                "data": [
                    {
                        "startTime": "2026-01-01T00:00:00Z",
                        "fuelType": "WIND",
                        "generation": 100,
                    }
                ]
            },
        ),
    ]

    client = ElexonClient(settings=custom_settings)
    rows = await client.fetch_fuelhh_wind(date(2026, 1, 1), date(2026, 1, 1))

    assert route.call_count == 3
    assert len(rows) == 1


@pytest.mark.anyio
@respx.mock
async def test_retry_exhausted_raises_upstream_error(custom_settings):
    # Fails with 500 continuously -> exceeds max_retries=2 (total 3 attempts)
    respx.get("https://mock.elexon.co.uk/api/v1/datasets/FUELHH").mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )

    client = ElexonClient(settings=custom_settings)
    with pytest.raises(
        ElexonUpstreamError, match="Elexon returned HTTP 503 after 2 retries"
    ):
        await client.fetch_fuelhh_wind(date(2026, 1, 1), date(2026, 1, 1))


@pytest.mark.anyio
@respx.mock
async def test_4xx_client_error_fails_immediately_without_retry(custom_settings):
    # 404 or 400 fails immediately without burning retries
    route = respx.get("https://mock.elexon.co.uk/api/v1/datasets/FUELHH").mock(
        return_value=httpx.Response(404, text="Dataset not found")
    )

    client = ElexonClient(settings=custom_settings)
    with pytest.raises(ElexonClientError, match="Elexon client error HTTP 404"):
        await client.fetch_fuelhh_wind(date(2026, 1, 1), date(2026, 1, 1))

    assert route.call_count == 1
