from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO
from math import floor
from pathlib import Path
import re
import statistics
from textwrap import dedent
from typing import Literal
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.experiment_dataset import ExperimentDataset
from app.models.experiment_output import ExperimentOutput
from app.schemas.experiment import (
    ExperimentChartType,
    ExperimentDatasetColumnResponse,
    ExperimentDatasetDetailResponse,
    ExperimentDatasetResponse,
    ExperimentOutputResponse,
    ExperimentStatsMetricResponse,
)
from app.services.agent_framework import DEFAULT_MANUAL_CONFIRMATION_WARNING
from app.services.storage import delete_stored_file, ensure_storage_root, resolve_storage_path, save_upload_file


CSV_MIME_TYPES = {"text/csv", "application/csv", "text/plain"}
SUPPORTED_OUTPUT_TYPES = {"stats_summary", "line_chart", "bar_chart", "result_analysis"}
MANUAL_CONFIRMATION_TEXT = "Need manual confirmation before turning this experiment analysis into a paper claim."


class ExperimentError(Exception):
    pass


@dataclass(frozen=True)
class ParsedDataset:
    columns: list[str]
    rows: list[dict[str, str]]
    row_count: int
    inferred_types: dict[str, str]


@dataclass(frozen=True)
class ChartPoint:
    label: str
    value: float


@dataclass(frozen=True)
class ChartSummary:
    chart_type: ExperimentChartType
    x_field: str
    y_field: str
    point_count: int
    min_value: float
    max_value: float
    title: str


@dataclass(frozen=True)
class ExperimentAnalysisResult:
    title: str
    content_markdown: str
    warnings: list[str]
    stats_payload: dict[str, dict[str, float | int]]


def _safe_chart_filename(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "experiment-chart"


def _sanitize_csv_error(message: str) -> str:
    sanitized = re.sub(r"[A-Za-z]:\\[^\"'\r\n]+", "[path]", message)
    return sanitized[:400]


def _is_numeric(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def _infer_column_type(values: list[str]) -> str:
    non_empty = [value for value in values if value.strip()]
    if not non_empty:
        return "empty"
    if all(_is_numeric(value) for value in non_empty):
        return "numeric"
    unique_values = {value.strip() for value in non_empty}
    if len(unique_values) <= 20 and all(len(value) <= 80 for value in unique_values):
        return "categorical"
    return "text"


def _parse_csv_text(text: str) -> ParsedDataset:
    reader = csv.DictReader(StringIO(text))
    if not reader.fieldnames:
        raise ExperimentError("The CSV file must include a header row.")

    columns = [field.strip() for field in reader.fieldnames if field and field.strip()]
    if not columns:
        raise ExperimentError("The CSV header row is empty.")

    rows: list[dict[str, str]] = []
    collected: dict[str, list[str]] = {column: [] for column in columns}
    row_count = 0

    try:
        for raw_row in reader:
            if raw_row is None:
                continue
            normalized_row: dict[str, str] = {}
            for column in columns:
                value = raw_row.get(column)
                normalized_value = (value or "").strip()
                normalized_row[column] = normalized_value
                collected[column].append(normalized_value)
            rows.append(normalized_row)
            row_count += 1
    except csv.Error as exc:
        raise ExperimentError(f"Failed to parse CSV content: {_sanitize_csv_error(str(exc))}") from exc

    inferred_types = {column: _infer_column_type(values) for column, values in collected.items()}
    return ParsedDataset(columns=columns, rows=rows, row_count=row_count, inferred_types=inferred_types)


def _load_parsed_dataset(dataset: ExperimentDataset) -> ParsedDataset:
    path = resolve_storage_path(dataset.storage_path)
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError as exc:
        raise ExperimentError("Failed to read the stored CSV dataset.") from exc
    return _parse_csv_text(text)


def _dataset_columns_payload(parsed: ParsedDataset) -> list[dict[str, str]]:
    return [
        {"name": column, "inferred_type": parsed.inferred_types.get(column, "text")}
        for column in parsed.columns
    ]


def _validate_csv_upload(upload: UploadFile) -> None:
    filename = (upload.filename or "").lower()
    if not filename.endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Experiment analysis accepts CSV files only.")
    normalized_mime = (upload.content_type or "").lower()
    if normalized_mime not in CSV_MIME_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported CSV MIME type.")


def _ensure_owned_dataset(db: Session, *, user_id: str, project_id: str, dataset_id: str) -> ExperimentDataset:
    dataset = db.scalar(
        select(ExperimentDataset).where(
            ExperimentDataset.id == dataset_id,
            ExperimentDataset.user_id == user_id,
            ExperimentDataset.project_id == project_id,
        )
    )
    if dataset is None:
        raise ExperimentError("Experiment dataset not found.")
    return dataset


def get_owned_experiment_output(
    db: Session,
    *,
    user_id: str,
    project_id: str,
    output_id: str,
) -> ExperimentOutput:
    output = db.scalar(
        select(ExperimentOutput).where(
            ExperimentOutput.id == output_id,
            ExperimentOutput.user_id == user_id,
            ExperimentOutput.project_id == project_id,
        )
    )
    if output is None:
        raise ExperimentError("Experiment output not found.")
    return output


def list_experiment_datasets(db: Session, *, user_id: str, project_id: str) -> list[ExperimentDataset]:
    return list(
        db.scalars(
            select(ExperimentDataset)
            .where(
                ExperimentDataset.user_id == user_id,
                ExperimentDataset.project_id == project_id,
            )
            .order_by(ExperimentDataset.updated_at.desc(), ExperimentDataset.created_at.desc())
        )
    )


def list_experiment_outputs(db: Session, *, user_id: str, project_id: str) -> list[ExperimentOutput]:
    return list(
        db.scalars(
            select(ExperimentOutput)
            .where(
                ExperimentOutput.user_id == user_id,
                ExperimentOutput.project_id == project_id,
            )
            .order_by(ExperimentOutput.updated_at.desc(), ExperimentOutput.created_at.desc())
        )
    )


def build_dataset_response(dataset: ExperimentDataset) -> ExperimentDatasetResponse:
    columns = [
        ExperimentDatasetColumnResponse(
            name=str(column.get("name", "")),
            inferred_type=str(column.get("inferred_type", "text")),  # type: ignore[arg-type]
        )
        for column in (dataset.columns_json or [])
    ]
    return ExperimentDatasetResponse(
        id=dataset.id,
        user_id=dataset.user_id,
        project_id=dataset.project_id,
        filename=dataset.filename,
        original_filename=dataset.original_filename,
        file_size=dataset.file_size,
        storage_path=dataset.storage_path,
        columns=columns,
        row_count=dataset.row_count,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
    )


def build_dataset_detail_response(dataset: ExperimentDataset) -> ExperimentDatasetDetailResponse:
    parsed = _load_parsed_dataset(dataset)
    settings = get_settings()
    preview_rows = [
        {column: row.get(column) or None for column in parsed.columns}
        for row in parsed.rows[: settings.experiment_preview_rows]
    ]
    summary = build_dataset_response(dataset)
    return ExperimentDatasetDetailResponse(
        **summary.model_dump(),
        preview_rows=preview_rows,
    )


def _coerce_stats_payload(stats_json: dict[str, object] | None) -> dict[str, ExperimentStatsMetricResponse] | None:
    if not stats_json:
        return None
    coerced: dict[str, ExperimentStatsMetricResponse] = {}
    for key, value in stats_json.items():
        if not isinstance(value, dict):
            continue
        if {"count", "mean", "min", "max", "std"}.issubset(value.keys()):
            coerced[key] = ExperimentStatsMetricResponse(
                count=int(value["count"]),
                mean=float(value["mean"]),
                min=float(value["min"]),
                max=float(value["max"]),
                std=float(value["std"]),
            )
    return coerced or None


def build_experiment_output_response(output: ExperimentOutput) -> ExperimentOutputResponse:
    return ExperimentOutputResponse(
        id=output.id,
        user_id=output.user_id,
        project_id=output.project_id,
        dataset_id=output.dataset_id,
        output_type=output.output_type,  # type: ignore[arg-type]
        title=output.title,
        content_markdown=output.content_markdown,
        chart_path=output.chart_path,
        stats_json=_coerce_stats_payload(output.stats_json),
        created_at=output.created_at,
        updated_at=output.updated_at,
    )


def create_experiment_dataset(
    db: Session,
    *,
    user_id: str,
    project_id: str,
    upload: UploadFile,
) -> ExperimentDataset:
    _validate_csv_upload(upload)
    stored = save_upload_file(upload, user_id=user_id, project_id=project_id)
    if str(stored["file_type"]).lower() != "csv":
        delete_stored_file(str(stored["storage_path"]))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Experiment analysis accepts CSV files only.")

    try:
        parsed = _parse_csv_text(resolve_storage_path(str(stored["storage_path"])).read_text(encoding="utf-8-sig", errors="replace"))
    except ExperimentError as exc:
        delete_stored_file(str(stored["storage_path"]))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except OSError as exc:
        delete_stored_file(str(stored["storage_path"]))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to read the stored CSV dataset.") from exc

    dataset = ExperimentDataset(
        user_id=user_id,
        project_id=project_id,
        filename=str(stored["filename"]),
        original_filename=str(stored["original_filename"]),
        file_size=int(stored["file_size"]),
        storage_path=str(stored["storage_path"]),
        columns_json=_dataset_columns_payload(parsed),
        row_count=parsed.row_count,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def delete_experiment_dataset(db: Session, dataset: ExperimentDataset) -> None:
    for output in list(dataset.outputs):
        if output.chart_path:
            delete_stored_file(output.chart_path)
    delete_stored_file(dataset.storage_path)
    db.delete(dataset)
    db.commit()


def delete_experiment_output(db: Session, output: ExperimentOutput) -> None:
    if output.chart_path:
        delete_stored_file(output.chart_path)
    db.delete(output)
    db.commit()


def _numeric_column_values(parsed: ParsedDataset, column: str) -> list[float]:
    values: list[float] = []
    for row in parsed.rows:
        raw = row.get(column, "").strip()
        if not raw:
            continue
        if not _is_numeric(raw):
            continue
        values.append(float(raw))
    return values


def _stats_payload(parsed: ParsedDataset) -> dict[str, dict[str, float | int]]:
    payload: dict[str, dict[str, float | int]] = {}
    for column in parsed.columns:
        if parsed.inferred_types.get(column) != "numeric":
            continue
        values = _numeric_column_values(parsed, column)
        if not values:
            continue
        payload[column] = {
            "count": len(values),
            "mean": round(statistics.fmean(values), 6),
            "min": round(min(values), 6),
            "max": round(max(values), 6),
            "std": round(statistics.stdev(values), 6) if len(values) > 1 else 0.0,
        }
    return payload


def generate_stats_output(
    db: Session,
    *,
    user_id: str,
    project_id: str,
    dataset_id: str,
) -> ExperimentOutput:
    dataset = _ensure_owned_dataset(db, user_id=user_id, project_id=project_id, dataset_id=dataset_id)
    parsed = _load_parsed_dataset(dataset)
    stats_payload = _stats_payload(parsed)
    if not stats_payload:
        raise ExperimentError("No numeric columns were available for descriptive statistics.")

    table_lines = [
        "| Column | Count | Mean | Min | Max | Std |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for column, metric in stats_payload.items():
        table_lines.append(
            f"| {column} | {metric['count']} | {metric['mean']} | {metric['min']} | {metric['max']} | {metric['std']} |"
        )

    output = ExperimentOutput(
        user_id=user_id,
        project_id=project_id,
        dataset_id=dataset.id,
        output_type="stats_summary",
        title=f"Statistics Summary: {dataset.original_filename}",
        content_markdown="\n".join(
            [
                f"# Statistics Summary: {dataset.original_filename}",
                "",
                f"- Rows: {dataset.row_count}",
                f"- Numeric columns: {len(stats_payload)}",
                "",
                *table_lines,
            ]
        ),
        stats_json=stats_payload,
    )
    db.add(output)
    db.commit()
    db.refresh(output)
    return output


def _build_chart_storage_path(user_id: str, project_id: str, *, stem: str) -> tuple[Path, str]:
    storage_root = ensure_storage_root()
    relative_path = Path(user_id) / project_id / "experiment_outputs" / f"{uuid4().hex}-{stem}.svg"
    absolute_path = (storage_root / relative_path).resolve()
    try:
        absolute_path.relative_to(storage_root)
    except ValueError as exc:
        raise ExperimentError("Invalid chart storage path.") from exc
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    return absolute_path, relative_path.as_posix()


def _normalize_points(points: list[ChartPoint], *, width: int, height: int) -> list[tuple[float, float]]:
    if not points:
        return []
    values = [point.value for point in points]
    minimum = min(values)
    maximum = max(values)
    span = maximum - minimum or 1.0
    x_step = width / max(1, len(points) - 1)
    normalized: list[tuple[float, float]] = []
    for index, point in enumerate(points):
        x = index * x_step
        y = height - (((point.value - minimum) / span) * height)
        normalized.append((x, y))
    return normalized


def _svg_line_chart(points: list[ChartPoint], summary: ChartSummary) -> str:
    plot_width = 700
    plot_height = 280
    offset_x = 70
    offset_y = 40
    normalized = _normalize_points(points, width=plot_width, height=plot_height)
    polyline_points = " ".join(
        f"{offset_x + x:.2f},{offset_y + y:.2f}" for x, y in normalized
    )
    labels: list[str] = []
    label_step = max(1, floor(len(points) / 6))
    for index, point in enumerate(points):
        if index % label_step != 0 and index != len(points) - 1:
            continue
        x_position = offset_x + normalized[index][0]
        labels.append(
            f'<text x="{x_position:.2f}" y="{offset_y + plot_height + 22}" font-size="11" text-anchor="middle" fill="#475569">{point.label[:18]}</text>'
        )

    circles = "\n".join(
        f'<circle cx="{offset_x + x:.2f}" cy="{offset_y + y:.2f}" r="4" fill="#0f172a" />'
        for x, y in normalized
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="860" height="420" viewBox="0 0 860 420">
  <rect width="860" height="420" rx="28" fill="#f8fafc" />
  <text x="70" y="28" font-size="20" font-family="Arial, sans-serif" fill="#0f172a">{summary.title}</text>
  <line x1="{offset_x}" y1="{offset_y}" x2="{offset_x}" y2="{offset_y + plot_height}" stroke="#94a3b8" stroke-width="2" />
  <line x1="{offset_x}" y1="{offset_y + plot_height}" x2="{offset_x + plot_width}" y2="{offset_y + plot_height}" stroke="#94a3b8" stroke-width="2" />
  <polyline points="{polyline_points}" fill="none" stroke="#2563eb" stroke-width="3" />
  {circles}
  {''.join(labels)}
  <text x="70" y="390" font-size="12" font-family="Arial, sans-serif" fill="#475569">X: {summary.x_field}</text>
  <text x="170" y="390" font-size="12" font-family="Arial, sans-serif" fill="#475569">Y: {summary.y_field}</text>
  <text x="300" y="390" font-size="12" font-family="Arial, sans-serif" fill="#475569">Points: {summary.point_count}</text>
</svg>"""


def _svg_bar_chart(points: list[ChartPoint], summary: ChartSummary) -> str:
    plot_width = 700
    plot_height = 280
    offset_x = 70
    offset_y = 40
    values = [point.value for point in points]
    minimum = min(values)
    maximum = max(values)
    span = maximum - minimum or 1.0
    bar_width = max(16.0, plot_width / max(1, len(points)) - 12)
    step = plot_width / max(1, len(points))
    bars: list[str] = []
    labels: list[str] = []
    for index, point in enumerate(points):
        normalized_height = ((point.value - minimum) / span) * plot_height if span else plot_height / 2
        x_position = offset_x + (index * step) + 6
        y_position = offset_y + (plot_height - normalized_height)
        bars.append(
            f'<rect x="{x_position:.2f}" y="{y_position:.2f}" width="{bar_width:.2f}" height="{normalized_height:.2f}" rx="8" fill="#0ea5e9" />'
        )
        labels.append(
            f'<text x="{x_position + (bar_width / 2):.2f}" y="{offset_y + plot_height + 22}" font-size="11" text-anchor="middle" fill="#475569">{point.label[:12]}</text>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="860" height="420" viewBox="0 0 860 420">
  <rect width="860" height="420" rx="28" fill="#f8fafc" />
  <text x="70" y="28" font-size="20" font-family="Arial, sans-serif" fill="#0f172a">{summary.title}</text>
  <line x1="{offset_x}" y1="{offset_y}" x2="{offset_x}" y2="{offset_y + plot_height}" stroke="#94a3b8" stroke-width="2" />
  <line x1="{offset_x}" y1="{offset_y + plot_height}" x2="{offset_x + plot_width}" y2="{offset_y + plot_height}" stroke="#94a3b8" stroke-width="2" />
  {''.join(bars)}
  {''.join(labels)}
  <text x="70" y="390" font-size="12" font-family="Arial, sans-serif" fill="#475569">X: {summary.x_field}</text>
  <text x="170" y="390" font-size="12" font-family="Arial, sans-serif" fill="#475569">Y: {summary.y_field}</text>
  <text x="300" y="390" font-size="12" font-family="Arial, sans-serif" fill="#475569">Points: {summary.point_count}</text>
</svg>"""


def _chart_points(parsed: ParsedDataset, *, x_field: str, y_field: str, chart_type: ExperimentChartType) -> list[ChartPoint]:
    if x_field not in parsed.columns or y_field not in parsed.columns:
        raise ExperimentError("The selected chart fields do not exist in this dataset.")
    if parsed.inferred_types.get(y_field) != "numeric":
        raise ExperimentError("The Y-axis field must be numeric.")

    settings = get_settings()
    if chart_type == "line":
        points: list[ChartPoint] = []
        for row in parsed.rows:
            x_value = row.get(x_field, "").strip()
            y_raw = row.get(y_field, "").strip()
            if not x_value or not y_raw or not _is_numeric(y_raw):
                continue
            points.append(ChartPoint(label=x_value, value=float(y_raw)))
        if len(points) < 2:
            raise ExperimentError("A line chart needs at least two valid rows.")
        return points[: settings.experiment_chart_point_limit]

    buckets: dict[str, list[float]] = {}
    for row in parsed.rows:
        x_value = row.get(x_field, "").strip()
        y_raw = row.get(y_field, "").strip()
        if not x_value or not y_raw or not _is_numeric(y_raw):
            continue
        buckets.setdefault(x_value, []).append(float(y_raw))
    if not buckets:
        raise ExperimentError("A bar chart needs at least one valid field pair.")
    points = [
        ChartPoint(label=label, value=round(statistics.fmean(values), 6))
        for label, values in buckets.items()
    ]
    return points[: settings.experiment_chart_point_limit]


def generate_chart_output(
    db: Session,
    *,
    user_id: str,
    project_id: str,
    dataset_id: str,
    chart_type: ExperimentChartType,
    x_field: str,
    y_field: str,
    title: str | None,
) -> ExperimentOutput:
    dataset = _ensure_owned_dataset(db, user_id=user_id, project_id=project_id, dataset_id=dataset_id)
    parsed = _load_parsed_dataset(dataset)
    points = _chart_points(parsed, x_field=x_field, y_field=y_field, chart_type=chart_type)
    resolved_title = title.strip() if title and title.strip() else f"{chart_type.title()} Chart: {dataset.original_filename}"
    summary = ChartSummary(
        chart_type=chart_type,
        x_field=x_field,
        y_field=y_field,
        point_count=len(points),
        min_value=min(point.value for point in points),
        max_value=max(point.value for point in points),
        title=resolved_title,
    )
    svg = _svg_line_chart(points, summary) if chart_type == "line" else _svg_bar_chart(points, summary)
    chart_file_path, relative_chart_path = _build_chart_storage_path(
        user_id,
        project_id,
        stem=_safe_chart_filename(resolved_title),
    )
    chart_file_path.write_text(svg, encoding="utf-8")

    output = ExperimentOutput(
        user_id=user_id,
        project_id=project_id,
        dataset_id=dataset.id,
        output_type="line_chart" if chart_type == "line" else "bar_chart",
        title=resolved_title,
        content_markdown=dedent(
            f"""\
            # {resolved_title}

            - Dataset: {dataset.original_filename}
            - Chart type: {chart_type}
            - X field: {x_field}
            - Y field: {y_field}
            - Points rendered: {summary.point_count}
            - Value range: {summary.min_value} to {summary.max_value}
            """
        ).strip(),
        chart_path=relative_chart_path,
    )
    db.add(output)
    db.commit()
    db.refresh(output)
    return output


class ExperimentAnalysisSkill:
    skill_name = "experiment_analysis"

    def execute(
        self,
        *,
        dataset: ExperimentDataset,
        parsed: ParsedDataset,
        prompt: str | None,
        chart_outputs: list[ExperimentOutput],
    ) -> ExperimentAnalysisResult:
        stats_payload = _stats_payload(parsed)
        warnings: list[str] = []
        if dataset.row_count < 3:
            warnings.append("The dataset has very few rows, so trend language should be treated cautiously.")
        if not stats_payload:
            warnings.append("No numeric columns were available, so the analysis stays descriptive and limited.")
        warnings.append(MANUAL_CONFIRMATION_TEXT)
        if DEFAULT_MANUAL_CONFIRMATION_WARNING not in warnings:
            warnings.append(DEFAULT_MANUAL_CONFIRMATION_WARNING)

        dataset_facts = [
            f"- Rows available: {dataset.row_count}",
            f"- Columns: {', '.join(parsed.columns)}",
        ]
        if prompt:
            dataset_facts.append(f"- User framing: {prompt.strip()}")

        numeric_summaries: list[str] = []
        for column, metric in stats_payload.items():
            numeric_summaries.append(
                f"- `{column}` ranges from {metric['min']} to {metric['max']} with mean {metric['mean']} and std {metric['std']}."
            )

        chart_notes: list[str] = []
        for output in chart_outputs[:3]:
            if output.output_type not in {"line_chart", "bar_chart"}:
                continue
            chart_notes.append(f"- Saved {output.output_type.replace('_', ' ')}: {output.title}")

        body_sections = [
            f"# Experiment Result Analysis: {dataset.original_filename}",
            "## Dataset Facts",
            "\n".join(dataset_facts),
            "## Numeric Summary",
            "\n".join(numeric_summaries) if numeric_summaries else "- Numeric evidence is not available in this dataset.",
            "## Chart Notes",
            "\n".join(chart_notes) if chart_notes else "- No saved charts were available during this analysis run.",
            "## Results Draft",
            (
                "The current dataset supports a bounded descriptive analysis only. "
                "Observed differences should be discussed as dataset-level patterns rather than final scientific conclusions."
            ),
            "## Manual Confirmation",
            "\n".join(f"- {warning}" for warning in warnings),
        ]
        return ExperimentAnalysisResult(
            title=f"Experiment Analysis: {dataset.original_filename}",
            content_markdown="\n\n".join(body_sections),
            warnings=list(dict.fromkeys(warnings)),
            stats_payload=stats_payload,
        )


def generate_analysis_output(
    db: Session,
    *,
    user_id: str,
    project_id: str,
    dataset_id: str,
    title: str | None,
    prompt: str | None,
) -> ExperimentOutput:
    dataset = _ensure_owned_dataset(db, user_id=user_id, project_id=project_id, dataset_id=dataset_id)
    parsed = _load_parsed_dataset(dataset)
    chart_outputs = list(
        db.scalars(
            select(ExperimentOutput)
            .where(
                ExperimentOutput.user_id == user_id,
                ExperimentOutput.project_id == project_id,
                ExperimentOutput.dataset_id == dataset_id,
                ExperimentOutput.output_type.in_(("line_chart", "bar_chart")),
            )
            .order_by(ExperimentOutput.updated_at.desc())
        )
    )
    skill = ExperimentAnalysisSkill()
    result = skill.execute(dataset=dataset, parsed=parsed, prompt=prompt, chart_outputs=chart_outputs)
    output = ExperimentOutput(
        user_id=user_id,
        project_id=project_id,
        dataset_id=dataset.id,
        output_type="result_analysis",
        title=title.strip() if title and title.strip() else result.title,
        content_markdown=result.content_markdown,
        stats_json=result.stats_payload or None,
    )
    db.add(output)
    db.commit()
    db.refresh(output)
    return output


def _export_header(output: ExperimentOutput, dataset: ExperimentDataset) -> list[str]:
    return [
        f"# {output.title}",
        "",
        f"- Dataset: {dataset.original_filename}",
        f"- Output type: `{output.output_type}`",
        f"- Rows: {dataset.row_count}",
        "",
    ]


def render_markdown_export(output: ExperimentOutput, dataset: ExperimentDataset) -> str:
    sections = _export_header(output, dataset)
    if output.content_markdown:
        sections.append(output.content_markdown)
        sections.append("")
    if output.stats_json:
        sections.extend(
            [
                "## Statistics Payload",
                "| Column | Count | Mean | Min | Max | Std |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for column, value in output.stats_json.items():
            if not isinstance(value, dict):
                continue
            if {"count", "mean", "min", "max", "std"}.issubset(value.keys()):
                sections.append(
                    f"| {column} | {value['count']} | {value['mean']} | {value['min']} | {value['max']} | {value['std']} |"
                )
        sections.append("")
    if output.chart_path:
        sections.append(f"- Saved chart path: `{output.chart_path}`")
    return "\n".join(sections).strip()


def render_latex_export(output: ExperimentOutput, dataset: ExperimentDataset) -> str:
    lines = [
        "% Generated by Battery-RAG Agent",
        "\\begin{table}[ht]",
        "\\centering",
        f"\\caption{{{output.title.replace('_', ' ')}}}",
        "\\begin{tabular}{lrrrrr}",
        "\\hline",
        "Column & Count & Mean & Min & Max & Std \\\\",
        "\\hline",
    ]
    added_stats = False
    if output.stats_json:
        for column, value in output.stats_json.items():
            if not isinstance(value, dict):
                continue
            if {"count", "mean", "min", "max", "std"}.issubset(value.keys()):
                lines.append(
                    f"{column} & {value['count']} & {value['mean']} & {value['min']} & {value['max']} & {value['std']} \\\\"
                )
                added_stats = True
    if not added_stats:
        lines.append(
            f"Dataset rows & {dataset.row_count} & 0 & 0 & 0 & 0 \\\\"
        )
    lines.extend(
        [
            "\\hline",
            "\\end{tabular}",
            f"\\label{{tab:{_safe_chart_filename(output.title)}}}",
            "\\end{table}",
        ]
    )
    return "\n".join(lines)


def build_export_filename(output: ExperimentOutput, extension: Literal["md", "tex"]) -> str:
    return f"{_safe_chart_filename(output.title)}.{extension}"


def build_chart_file_response(output: ExperimentOutput) -> FileResponse:
    if not output.chart_path:
        raise ExperimentError("This experiment output does not include a saved chart.")
    path = resolve_storage_path(output.chart_path)
    return FileResponse(path=path, media_type="image/svg+xml", filename=path.name)
