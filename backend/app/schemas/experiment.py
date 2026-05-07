from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ExperimentColumnType = Literal["numeric", "categorical", "text", "empty"]
ExperimentOutputType = Literal["stats_summary", "line_chart", "bar_chart", "result_analysis"]
ExperimentChartType = Literal["line", "bar"]


class ExperimentDatasetColumnResponse(BaseModel):
    name: str
    inferred_type: ExperimentColumnType


class ExperimentDatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    project_id: str
    filename: str
    original_filename: str
    file_size: int
    storage_path: str
    columns: list[ExperimentDatasetColumnResponse] = Field(default_factory=list)
    row_count: int
    created_at: datetime
    updated_at: datetime


class ExperimentDatasetDetailResponse(ExperimentDatasetResponse):
    preview_rows: list[dict[str, str | None]] = Field(default_factory=list)


class ExperimentStatsMetricResponse(BaseModel):
    count: int
    mean: float
    min: float
    max: float
    std: float


class ExperimentOutputResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    project_id: str
    dataset_id: str
    output_type: ExperimentOutputType
    title: str
    content_markdown: str | None
    chart_path: str | None
    stats_json: dict[str, ExperimentStatsMetricResponse] | None = None
    created_at: datetime
    updated_at: datetime


class ExperimentChartRequest(BaseModel):
    chart_type: ExperimentChartType
    x_field: str = Field(min_length=1, max_length=255)
    y_field: str = Field(min_length=1, max_length=255)
    title: str | None = Field(default=None, max_length=255)


class ExperimentAnalysisRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    prompt: str | None = Field(default=None, max_length=3000)
