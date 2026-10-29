import asyncio
import logging
from datetime import UTC, datetime
from typing import NamedTuple

from app.config import Settings, get_settings
from app.domain.models import ActualPoint, ForecastPoint, NormalizationStats
from app.domain.normalize import (
    normalize_actuals,
    normalize_forecasts,
    parse_timestamp,
)
from app.services.elexon_client import ElexonClient

logger = logging.getLogger(__name__)


class CachedData(NamedTuple):
    actuals: list[ActualPoint]
    forecasts: list[ForecastPoint]
    actual_half_hours: dict[datetime, float]
    stats: NormalizationStats
    fetched_at: datetime
    is_stale: bool


class UpstreamError(Exception):
    """Raised when upstream Elexon data cannot be retrieved and no cache exists."""


class DataNotReadyError(Exception):
    """Raised when initial data loading is still in progress."""


class DataStore:
    """In-memory cache and single-flight coordinator for Elexon actuals and forecasts."""

    def __init__(
        self,
        settings: Settings | None = None,
        client: ElexonClient | None = None,
    ):
        self.settings = settings or get_settings()
        self.client = client or ElexonClient(settings=self.settings)

        self._lock = asyncio.Lock()
        self._cached: CachedData | None = None
        self._is_loading = False

    @property
    def is_loaded(self) -> bool:
        return self._cached is not None

    @property
    def is_loading(self) -> bool:
        return self._is_loading

    def get_provenance(self) -> dict:
        if self._cached is None:
            return {
                "source": "Elexon Insights API",
                "datasets": ["FUELHH", "WINDFOR"],
                "fetched_at": None,
                "cache_age_seconds": None,
                "stale": False,
            }
        now = datetime.now(UTC)
        age = int((now - self._cached.fetched_at).total_seconds())
        return {
            "source": "Elexon Insights API",
            "datasets": ["FUELHH", "WINDFOR"],
            "fetched_at": self._cached.fetched_at.isoformat(),
            "cache_age_seconds": max(0, age),
            "stale": self._cached.is_stale,
        }

    async def get_data(self, force_refresh: bool = False) -> CachedData:
        """Retrieve actuals and forecasts, refreshing from Elexon when expired or empty."""
        now = datetime.now(UTC)

        # Fast path: cache is fresh and force_refresh is False
        if not force_refresh and self._cached is not None:
            age = (now - self._cached.fetched_at).total_seconds()
            if age < self.settings.cache_ttl_seconds:
                return self._cached

        async with self._lock:
            # Recheck after acquiring lock
            now = datetime.now(UTC)
            if not force_refresh and self._cached is not None:
                age = (now - self._cached.fetched_at).total_seconds()
                if age < self.settings.cache_ttl_seconds:
                    return self._cached

            self._is_loading = True
            logger.info(
                "Refreshing Elexon data for window %s to %s",
                self.settings.delivery_window_start,
                self.settings.delivery_window_end,
            )

            try:
                # Concurrent fetch of FUELHH and WINDFOR streams
                fuelhh_task = self.client.fetch_fuelhh_wind(
                    self.settings.delivery_window_start,
                    self.settings.delivery_window_end,
                )
                windfor_task = self.client.fetch_windfor(
                    self.settings.delivery_window_start,
                    self.settings.delivery_window_end,
                )

                raw_fuelhh, raw_windfor = await asyncio.gather(
                    fuelhh_task, windfor_task
                )

                # Normalize in pure domain layer
                actuals, actual_stats = normalize_actuals(raw_fuelhh)
                forecasts, forecast_stats = normalize_forecasts(raw_windfor)

                # Extract :30 actuals for P1 optional context only (never entered into metrics)
                actual_half_hours: dict[datetime, float] = {}
                for row in raw_fuelhh:
                    if not isinstance(row, dict):
                        continue
                    if row.get("fuelType") != "WIND":
                        continue
                    st_str = row.get("startTime")
                    gen = row.get("generation")
                    if (
                        isinstance(st_str, str)
                        and isinstance(gen, (int, float))
                        and gen >= 0
                    ):
                        dt = parse_timestamp(st_str)
                        if dt is not None and dt.minute == 30:
                            actual_half_hours[dt] = float(gen)

                combined_stats = NormalizationStats(
                    raw_actual_rows=actual_stats.raw_actual_rows,
                    raw_forecast_rows=forecast_stats.raw_forecast_rows,
                    wind_actual_rows=actual_stats.wind_actual_rows,
                    duplicate_actual_rows=actual_stats.duplicate_actual_rows,
                    duplicate_forecast_rows=forecast_stats.duplicate_forecast_rows,
                    conflicting_forecast_rows=forecast_stats.conflicting_forecast_rows,
                    invalid_actual_rows=actual_stats.invalid_actual_rows,
                    invalid_forecast_rows=forecast_stats.invalid_forecast_rows,
                    warnings=actual_stats.warnings + forecast_stats.warnings,
                )

                fetch_timestamp = datetime.now(UTC)
                self._cached = CachedData(
                    actuals=actuals,
                    forecasts=forecasts,
                    actual_half_hours=actual_half_hours,
                    stats=combined_stats,
                    fetched_at=fetch_timestamp,
                    is_stale=False,
                )
                logger.info(
                    "Elexon data successfully loaded: %d actuals, %d forecasts",
                    len(actuals),
                    len(forecasts),
                )
                return self._cached

            except Exception as e:
                logger.error("Failed to fetch fresh data from Elexon: %s", e)
                # Stale cache fallback if previously cached data exists
                if self._cached is not None:
                    logger.warning(
                        "Serving stale cached data from %s", self._cached.fetched_at
                    )
                    self._cached = self._cached._replace(is_stale=True)
                    return self._cached
                # No cache exists -> Upstream error
                raise UpstreamError(f"Failed to load data from Elexon: {e}") from e

            finally:
                self._is_loading = False


_data_store_instance: DataStore | None = None


def get_data_store(settings: Settings | None = None) -> DataStore:
    global _data_store_instance
    if _data_store_instance is None:
        _data_store_instance = DataStore(settings=settings)
    return _data_store_instance
