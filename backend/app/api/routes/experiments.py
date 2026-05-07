from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_project
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.experiment import (
    ExperimentAnalysisRequest,
    ExperimentChartRequest,
    ExperimentDatasetDetailResponse,
    ExperimentDatasetResponse,
    ExperimentOutputResponse,
)
from app.services.experiments import (
    ExperimentError,
    build_chart_file_response,
    build_dataset_detail_response,
    build_dataset_response,
    build_experiment_output_response,
    build_export_filename,
    create_experiment_dataset,
    delete_experiment_dataset,
    delete_experiment_output,
    generate_analysis_output,
    generate_chart_output,
    generate_stats_output,
    get_owned_experiment_output,
    list_experiment_datasets,
    list_experiment_outputs,
    render_latex_export,
    render_markdown_export,
    _ensure_owned_dataset,
)


router = APIRouter(prefix="/projects/{project_id}/experiments", tags=["experiments"])


@router.post("/datasets", response_model=ExperimentDatasetResponse, status_code=status.HTTP_201_CREATED)
def upload_experiment_dataset(
    project_id: str,
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExperimentDatasetResponse:
    get_owned_project(db, current_user.id, project_id)
    dataset = create_experiment_dataset(db, user_id=current_user.id, project_id=project_id, upload=upload)
    return build_dataset_response(dataset)


@router.get("/datasets", response_model=list[ExperimentDatasetResponse])
def get_experiment_datasets(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ExperimentDatasetResponse]:
    get_owned_project(db, current_user.id, project_id)
    return [
        build_dataset_response(dataset)
        for dataset in list_experiment_datasets(db, user_id=current_user.id, project_id=project_id)
    ]


@router.get("/datasets/{dataset_id}", response_model=ExperimentDatasetDetailResponse)
def get_experiment_dataset_detail(
    project_id: str,
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExperimentDatasetDetailResponse:
    get_owned_project(db, current_user.id, project_id)
    try:
        dataset = _ensure_owned_dataset(db, user_id=current_user.id, project_id=project_id, dataset_id=dataset_id)
    except ExperimentError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return build_dataset_detail_response(dataset)


@router.delete("/datasets/{dataset_id}", response_model=MessageResponse)
def remove_experiment_dataset(
    project_id: str,
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    get_owned_project(db, current_user.id, project_id)
    try:
        dataset = _ensure_owned_dataset(db, user_id=current_user.id, project_id=project_id, dataset_id=dataset_id)
    except ExperimentError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    delete_experiment_dataset(db, dataset)
    return MessageResponse(message="Experiment dataset deleted.")


@router.post("/datasets/{dataset_id}/stats", response_model=ExperimentOutputResponse, status_code=status.HTTP_201_CREATED)
def create_stats_output(
    project_id: str,
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExperimentOutputResponse:
    get_owned_project(db, current_user.id, project_id)
    try:
        output = generate_stats_output(db, user_id=current_user.id, project_id=project_id, dataset_id=dataset_id)
    except ExperimentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return build_experiment_output_response(output)


@router.post("/datasets/{dataset_id}/charts", response_model=ExperimentOutputResponse, status_code=status.HTTP_201_CREATED)
def create_chart_output(
    project_id: str,
    dataset_id: str,
    payload: ExperimentChartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExperimentOutputResponse:
    get_owned_project(db, current_user.id, project_id)
    try:
        output = generate_chart_output(
            db,
            user_id=current_user.id,
            project_id=project_id,
            dataset_id=dataset_id,
            chart_type=payload.chart_type,
            x_field=payload.x_field,
            y_field=payload.y_field,
            title=payload.title,
        )
    except ExperimentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return build_experiment_output_response(output)


@router.post("/datasets/{dataset_id}/analysis", response_model=ExperimentOutputResponse, status_code=status.HTTP_201_CREATED)
def create_analysis_output(
    project_id: str,
    dataset_id: str,
    payload: ExperimentAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExperimentOutputResponse:
    get_owned_project(db, current_user.id, project_id)
    try:
        output = generate_analysis_output(
            db,
            user_id=current_user.id,
            project_id=project_id,
            dataset_id=dataset_id,
            title=payload.title,
            prompt=payload.prompt,
        )
    except ExperimentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return build_experiment_output_response(output)


@router.get("/outputs", response_model=list[ExperimentOutputResponse])
def get_experiment_outputs(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ExperimentOutputResponse]:
    get_owned_project(db, current_user.id, project_id)
    return [
        build_experiment_output_response(output)
        for output in list_experiment_outputs(db, user_id=current_user.id, project_id=project_id)
    ]


@router.delete("/outputs/{output_id}", response_model=MessageResponse)
def remove_experiment_output(
    project_id: str,
    output_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    get_owned_project(db, current_user.id, project_id)
    try:
        output = get_owned_experiment_output(db, user_id=current_user.id, project_id=project_id, output_id=output_id)
    except ExperimentError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    delete_experiment_output(db, output)
    return MessageResponse(message="Experiment output deleted.")


@router.get("/outputs/{output_id}/chart")
def get_experiment_output_chart(
    project_id: str,
    output_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_owned_project(db, current_user.id, project_id)
    try:
        output = get_owned_experiment_output(db, user_id=current_user.id, project_id=project_id, output_id=output_id)
        return build_chart_file_response(output)
    except ExperimentError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/outputs/{output_id}/export/markdown")
def export_experiment_output_markdown(
    project_id: str,
    output_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    get_owned_project(db, current_user.id, project_id)
    try:
        output = get_owned_experiment_output(db, user_id=current_user.id, project_id=project_id, output_id=output_id)
        dataset = _ensure_owned_dataset(db, user_id=current_user.id, project_id=project_id, dataset_id=output.dataset_id)
    except ExperimentError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(
        content=render_markdown_export(output, dataset),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{build_export_filename(output, "md")}"'},
    )


@router.get("/outputs/{output_id}/export/latex")
def export_experiment_output_latex(
    project_id: str,
    output_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    get_owned_project(db, current_user.id, project_id)
    try:
        output = get_owned_experiment_output(db, user_id=current_user.id, project_id=project_id, output_id=output_id)
        dataset = _ensure_owned_dataset(db, user_id=current_user.id, project_id=project_id, dataset_id=output.dataset_id)
    except ExperimentError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(
        content=render_latex_export(output, dataset),
        media_type="application/x-tex; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{build_export_filename(output, "tex")}"'},
    )
