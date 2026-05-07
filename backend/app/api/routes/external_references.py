from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_project
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.external_reference import (
    ExternalReferenceResponse,
    ExternalReferenceSaveRequest,
    ExternalReferenceSearchRequest,
    ExternalReferenceSearchResponse,
)
from app.services.external_references import (
    ExternalReferenceCandidate,
    ExternalToolError,
    ExternalSearchInput,
    build_external_reference_export_filename,
    build_external_reference_response,
    build_external_references_export,
    build_search_candidate_response,
    get_external_tool_registry,
    get_saved_external_reference,
    list_saved_external_references,
    persist_external_reference,
)


router = APIRouter(prefix="/projects/{project_id}/external-references", tags=["external-references"])


@router.post("/search", response_model=ExternalReferenceSearchResponse)
def search_external_references(
    project_id: str,
    payload: ExternalReferenceSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExternalReferenceSearchResponse:
    get_owned_project(db, current_user.id, project_id)
    registry = get_external_tool_registry()
    try:
        results, warnings = registry.search(
            provider=payload.provider,
            search_input=ExternalSearchInput(
                query=payload.query.strip() if payload.query else None,
                doi=payload.doi.strip() if payload.doi else None,
                limit=payload.limit,
            ),
        )
    except ExternalToolError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ExternalReferenceSearchResponse(
        results=[build_search_candidate_response(candidate) for candidate in results],
        warnings=warnings,
    )


@router.post("", response_model=ExternalReferenceResponse, status_code=status.HTTP_201_CREATED)
def save_external_reference(
    project_id: str,
    payload: ExternalReferenceSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExternalReferenceResponse:
    get_owned_project(db, current_user.id, project_id)
    candidate = ExternalReferenceCandidate(
        source=payload.source,
        title=payload.title,
        authors=list(payload.authors),
        year=payload.year,
        venue=payload.venue,
        doi=payload.doi,
        url=payload.url,
        abstract=payload.abstract,
        warnings=list(payload.warnings),
    )
    reference = persist_external_reference(
        db,
        user_id=current_user.id,
        project_id=project_id,
        candidate=candidate,
    )
    return ExternalReferenceResponse.model_validate(build_external_reference_response(reference))


@router.get("", response_model=list[ExternalReferenceResponse])
def list_external_references(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ExternalReferenceResponse]:
    get_owned_project(db, current_user.id, project_id)
    references = list_saved_external_references(db, user_id=current_user.id, project_id=project_id)
    return [ExternalReferenceResponse.model_validate(build_external_reference_response(reference)) for reference in references]


@router.delete("/{reference_id}", response_model=MessageResponse)
def delete_external_reference(
    project_id: str,
    reference_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    get_owned_project(db, current_user.id, project_id)
    reference = get_saved_external_reference(
        db,
        user_id=current_user.id,
        project_id=project_id,
        reference_id=reference_id,
    )
    if reference is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="External reference not found.")
    db.delete(reference)
    db.commit()
    return MessageResponse(message="External reference deleted.")


@router.get("/export/bibtex")
def export_external_references_bibtex(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    get_owned_project(db, current_user.id, project_id)
    references = list_saved_external_references(db, user_id=current_user.id, project_id=project_id)
    return Response(
        content=build_external_references_export(references),
        media_type="application/x-bibtex; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{build_external_reference_export_filename(project_id)}"',
        },
    )
