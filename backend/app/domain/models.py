from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum


class RecordStatus(str, Enum):
    """Status of each expected delivery period in the comparison grid."""

    MATCHED = "matched"
    MISSING_FORECAST = "missing_forecast"
    MISSING_ACTUAL = "missing_actual"
    MISSING_BOTH = "missing_both"


@dataclass(frozen=True)
class ActualPoint:
    """Normalised actual wind generation observation."""

    start_time: datetime  # UTC timezone-aware
    generation_mw: float  # >= 0.0, finite
    publish_time: datetime | None = None  # UTC if present, used to break duplicate ties


@dataclass(frozen=True)
class ForecastPoint:
    """Normalised forecast wind generation point."""

    start_time: datetime  # UTC delivery instant
    publish_time: datetime  # UTC creation/publication instant
    generation_mw: float  # >= 0.0, finite


@dataclass(frozen=True)
class ComparisonRecord:
    """Evaluation record for a single expected hourly delivery period."""

    start_time: datetime  # UTC instant
    delivery_date: date  # Calendar date in Europe/London
    cutoff_time: datetime  # UTC decision cutoff
    actual_mw: float | None
    forecast_mw: float | None
    forecast_publish_time: datetime | None
    forecast_horizon_hours: float | None
    error_mw: float | None  # actual - forecast (positive = under-forecast)
    abs_error_mw: float | None  # |error_mw|
    status: RecordStatus


@dataclass(frozen=True)
class MetricsSummary:
    """Aggregated forecast accuracy metrics over matched periods."""

    n_expected: int
    n_matched: int
    coverage_pct: float
    mae_mw: float | None
    rmse_mw: float | None
    bias_mw: float | None
    mae_pct: float | None
    p90_abs_error_mw: float | None
    mean_actual_mw: float | None
    mean_forecast_mw: float | None


@dataclass(frozen=True)
class DailyMetrics:
    """Metrics aggregated for a single delivery date."""

    date: date
    n_expected: int
    n_matched: int
    coverage_pct: float
    mae_mw: float | None
    rmse_mw: float | None
    bias_mw: float | None
    mean_actual_mw: float | None
    mean_forecast_mw: float | None
    cutoff_time: datetime


@dataclass
class NormalizationStats:
    """Tracking statistics and warnings for data normalization and deduplication."""

    raw_actual_rows: int = 0
    raw_forecast_rows: int = 0
    wind_actual_rows: int = 0
    invalid_actual_rows: int = 0
    invalid_forecast_rows: int = 0
    duplicate_actual_rows: int = 0
    duplicate_forecast_rows: int = 0
    conflicting_forecast_rows: int = 0
    warnings: list[str] = field(default_factory=list)
