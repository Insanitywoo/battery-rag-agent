from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_project
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.writing import WritingArtifactResponse, WritingRunRequest
from app.services.writing import (
    MarkdownExportSkill,
    WritingExecutionError,
    build_writing_artifact_response,
    get_owned_writing_artifact,
    get_writing_executor,
    list_writing_artifacts,
)


router = APIRouter(prefix="/projects/{project_id}/writing", tags=["writing"])


@router.post("/run", response_model=WritingArtifactResponse, status_code=status.HTTP_201_CREATED)
def run_writing_task(
    project_id: str,
    payload: WritingRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WritingArtifactResponse:
    get_owned_project(db, current_user.id, project_id)
    executor = get_writing_executor()
    try:
        artifact, warnings = executor.run(
            db,
            user_id=current_user.id,
            project_id=project_id,
            topic=payload.topic,
            research_direction=payload.research_direction,
            requirements=payload.requirements,
            requested_task_type=payload.task_type,
        )
    except WritingExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return build_writing_artifact_response(artifact, warnings=warnings)


@router.get("/artifacts", response_model=list[WritingArtifactResponse])
def get_writing_artifacts(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WritingArtifactResponse]:
    get_owned_project(db, current_user.id, project_id)
    return [
        build_writing_artifact_response(artifact)
        for artifact in list_writing_artifacts(db, user_id=current_user.id, project_id=project_id)
    ]


@router.get("/artifacts/{artifact_id}", response_model=WritingArtifactResponse)
def get_writing_artifact(
    project_id: str,
    artifact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WritingArtifactResponse:
    get_owned_project(db, current_user.id, project_id)
    try:
        artifact = get_owned_writing_artifact(
            db,
            user_id=current_user.id,
            project_id=project_id,
            artifact_id=artifact_id,
        )
    except WritingExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return build_writing_artifact_response(artifact)


@router.delete("/artifacts/{artifact_id}", response_model=MessageResponse)
def delete_writing_artifact(
    project_id: str,
    artifact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    get_owned_project(db, current_user.id, project_id)
    try:
        artifact = get_owned_writing_artifact(
            db,
            user_id=current_user.id,
            project_id=project_id,
            artifact_id=artifact_id,
        )
    except WritingExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    db.delete(artifact)
    db.commit()
    return MessageResponse(message="Writing artifact deleted.")


@router.get("/artifacts/{artifact_id}/export/markdown")
def export_writing_artifact_markdown(
    project_id: str,
    artifact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    get_owned_project(db, current_user.id, project_id)
    try:
        artifact = get_owned_writing_artifact(
            db,
            user_id=current_user.id,
            project_id=project_id,
            artifact_id=artifact_id,
        )
    except WritingExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    export_skill = MarkdownExportSkill()
    artifact_payload = build_writing_artifact_response(artifact)
    return Response(
        content=export_skill.render(artifact_payload),
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{export_skill.build_filename(artifact_payload)}"',
        },
    )
