from datetime import date
from typing import Any

from pydantic import BaseModel, Field


# ---------------- Error Schemas ---------------- #
class ErrorDetail(BaseModel):
    field: str | None = None


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: ErrorPayload


# ---------------- Health & Meta ---------------- #
class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    data_loaded: bool


class WindowMeta(BaseModel):
    start_date: date
    end_date: date
    expected_periods: int


class AssumptionsMeta(BaseModel):
    cutoff_time_default: str
    cutoff_timezone: str
    cutoff_rule: str
    cutoff_inclusive: bool
    status: str = "provisional"


class ProvenanceMeta(BaseModel):
    source: str = "Elexon Insights API"
    datasets: list[str] = Field(default_factory=lambda: ["FUELHH", "WINDFOR"])
    fetched_at: str | None = None
    cache_age_seconds: int | None = None
    stale: bool = False


class MetaResponse(BaseModel):
    window: WindowMeta
    assumptions: AssumptionsMeta
    provenance: ProvenanceMeta


# ---------------- Summary ---------------- #
class RangeModel(BaseModel):
    start_date: date
    end_date: date


class SummaryAssumptions(BaseModel):
    cutoff_time: str
    cutoff_timezone: str
    cutoff_inclusive: bool


class SummaryMetrics(BaseModel):
    n_matched: int
    mae_mw: float | None = None
    rmse_mw: float | None = None
    bias_mw: float | None = None
    mae_pct_of_mean_actual: float | None = None
    p90_abs_error_mw: float | None = None
    mean_actual_mw: float | None = None
    mean_forecast_mw: float | None = None
    coverage_pct: float | None = None


class ForecastVintage(BaseModel):
    publish_time: str
    periods_count: int


class DataQualitySummary(BaseModel):
    n_expected: int
    n_matched: int
    n_missing_actual: int
    n_missing_forecast: int
    n_missing_both: int
    invalid_actual_rows: int
    invalid_forecast_rows: int
    duplicate_actual_rows: int
    duplicate_forecast_rows: int
    conflicting_forecast_rows: int
    warnings: list[str] = Field(default_factory=list)


class SummaryResponse(BaseModel):
    range: RangeModel
    assumptions: SummaryAssumptions
    metrics: SummaryMetrics
    forecast_vintages: list[ForecastVintage] = Field(default_factory=list)
    data_quality: DataQualitySummary
    provenance: ProvenanceMeta


# ---------------- Series ---------------- #
class HourlySeriesPoint(BaseModel):
    start_time: str
    actual_mw: float | None = None
    forecast_mw: float | None = None
    forecast_publish_time: str | None = None
    status: str
    actual_half_hour_context_mw: float | None = None


class DailySeriesPoint(BaseModel):
    date: str
    n_matched: int
    mean_actual_mw: float | None = None
    mean_forecast_mw: float | None = None
    mae_mw: float | None = None
    rmse_mw: float | None = None
    bias_mw: float | None = None
    cutoff_time: str


class SeriesResponse(BaseModel):
    granularity: str
    unit: str = "MW"
    points: list[Any] = Field(default_factory=list)


# ---------------- Records ---------------- #
class RecordItem(BaseModel):
    start_time: str
    delivery_date: str
    cutoff_time: str
    actual_mw: float | None = None
    forecast_mw: float | None = None
    forecast_publish_time: str | None = None
    forecast_horizon_hours: float | None = None
    error_mw: float | None = None
    abs_error_mw: float | None = None
    status: str


class RecordsResponse(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    items: list[RecordItem] = Field(default_factory=list)
