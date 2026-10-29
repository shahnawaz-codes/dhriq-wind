import asyncio
import logging
from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class ElexonClientError(Exception):
    """Base exception for Elexon API interactions."""


class ElexonUpstreamError(ElexonClientError):
    """Raised when Elexon returns an unrecoverable 5xx or retries are exhausted."""


class ElexonClient:
    """HTTP client for fetching FUELHH and WINDFOR streams from Elexon Insights API."""

    def __init__(
        self,
        settings: Settings | None = None,
        client: httpx.AsyncClient | None = None,
    ):
        self.settings = settings or get_settings()
        self._custom_client = client

    def _get_client(self) -> httpx.AsyncClient:
        if self._custom_client is not None:
            return self._custom_client
        return httpx.AsyncClient(timeout=self.settings.elexon_timeout_seconds)

    async def _fetch_with_retry(
        self,
        url: str,
        params: dict[str, Any],
        client: httpx.AsyncClient,
    ) -> list[dict[str, Any]]:
        """Fetch an endpoint with retry, exponential backoff, and 429/5xx resilience."""
        max_retries = self.settings.elexon_max_retries
        backoff = 0.5

        for attempt in range(max_retries + 1):
            try:
                logger.debug(
                    "Requesting Elexon URL=%s params=%s attempt=%d",
                    url,
                    params,
                    attempt + 1,
                )
                response = await client.get(url, params=params)

                if response.status_code == 200:
                    try:
                        data = response.json()
                    except Exception as e:
                        raise ElexonUpstreamError(
                            f"Failed to parse JSON response from {url}: {e}"
                        ) from e

                    # Elexon may return plain array or {"data": [...]}
                    if isinstance(data, list):
                        return data
                    if isinstance(data, dict) and "data" in data:
                        raw_data = data["data"]
                        if isinstance(raw_data, list):
                            return raw_data
                        return []
                    logger.warning(
                        "Unexpected response structure from %s: %s",
                        url,
                        type(data),
                    )
                    return []

                # Handle 429 Rate Limit
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    sleep_time = float(retry_after) if retry_after else backoff
                    logger.warning(
                        "Elexon 429 Too Many Requests. Retrying in %.2f s (attempt %d/%d)",
                        sleep_time,
                        attempt + 1,
                        max_retries,
                    )
                    if attempt < max_retries:
                        await asyncio.sleep(sleep_time)
                        backoff *= 2
                        continue
                    raise ElexonUpstreamError(
                        f"Elexon rate limit exceeded (429) after {max_retries} retries"
                    )

                # Handle 5xx Upstream Server Error
                if response.status_code >= 500:
                    logger.warning(
                        "Elexon server error HTTP %d. Retrying in %.2f s (attempt %d/%d)",
                        response.status_code,
                        backoff,
                        attempt + 1,
                        max_retries,
                    )
                    if attempt < max_retries:
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue
                    raise ElexonUpstreamError(
                        f"Elexon returned HTTP {response.status_code} after {max_retries} retries"
                    )

                # Non-retryable 4xx
                raise ElexonClientError(
                    f"Elexon client error HTTP {response.status_code}: {response.text[:200]}"
                )

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                logger.warning(
                    "Network error connecting to Elexon (%s). Retrying in %.2f s (attempt %d/%d)",
                    e,
                    backoff,
                    attempt + 1,
                    max_retries,
                )
                if attempt < max_retries:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                raise ElexonUpstreamError(
                    f"Elexon connection failed after {max_retries} retries: {e}"
                ) from e

        raise ElexonUpstreamError("Max retries exceeded")

    async def fetch_fuelhh_wind(
        self,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """Fetch FUELHH records filtered to fuelType=WIND over chunked date ranges."""
        url = f"{self.settings.elexon_base_url.rstrip('/')}/datasets/FUELHH"
        chunk_days = self.settings.elexon_chunk_days
        all_rows: list[dict[str, Any]] = []

        manage_client = self._custom_client is None
        client = self._get_client()

        try:
            current_start = start_date
            while current_start <= end_date:
                current_end = min(
                    current_start + timedelta(days=chunk_days - 1), end_date
                )
                params = {
                    "settlementDateFrom": current_start.isoformat(),
                    "settlementDateTo": current_end.isoformat(),
                    "fuelType": "WIND",
                    "format": "json",
                }
                chunk_rows = await self._fetch_with_retry(url, params, client)
                all_rows.extend(chunk_rows)
                current_start = current_end + timedelta(days=1)

            return all_rows
        finally:
            if manage_client:
                await client.aclose()

    async def fetch_windfor(
        self,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """Fetch WINDFOR forecast records over chunked publication datetime ranges.

        Includes lookback days prior to start_date.
        """
        url = f"{self.settings.elexon_base_url.rstrip('/')}/datasets/WINDFOR"
        lookback_start = datetime(
            start_date.year,
            start_date.month,
            start_date.day,
            0,
            0,
            0,
            tzinfo=UTC,
        ) - timedelta(days=self.settings.forecast_publish_lookback_days)

        fetch_end = datetime(
            end_date.year,
            end_date.month,
            end_date.day,
            23,
            59,
            59,
            tzinfo=UTC,
        )

        chunk_delta = timedelta(days=self.settings.elexon_chunk_days)
        all_rows: list[dict[str, Any]] = []

        manage_client = self._custom_client is None
        client = self._get_client()

        try:
            current_from = lookback_start
            while current_from <= fetch_end:
                current_to = min(current_from + chunk_delta, fetch_end)
                params = {
                    "publishDateTimeFrom": current_from.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "publishDateTimeTo": current_to.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "format": "json",
                }
                chunk_rows = await self._fetch_with_retry(url, params, client)
                all_rows.extend(chunk_rows)
                current_from = current_to + timedelta(seconds=1)

            return all_rows
        finally:
            if manage_client:
                await client.aclose()
