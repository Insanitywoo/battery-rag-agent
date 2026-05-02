from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_project
from app.db.session import get_db
from app.models.document import Document, DocumentStatus
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.document import DocumentResponse
from app.services.storage import delete_stored_file, save_upload_file

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])


def _get_owned_document(db: Session, *, user_id: str, project_id: str, document_id: str) -> Document:
    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == user_id,
            Document.project_id == project_id,
        )
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return document


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    project_id: str,
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    get_owned_project(db, current_user.id, project_id)

    if not upload.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required.")

    stored_file = save_upload_file(upload, user_id=current_user.id, project_id=project_id)
    document = Document(
        user_id=current_user.id,
        project_id=project_id,
        filename=str(stored_file["filename"]),
        original_filename=str(stored_file["original_filename"]),
        file_type=str(stored_file["file_type"]),
        mime_type=str(stored_file["mime_type"]),
        file_size=int(stored_file["file_size"]),
        storage_path=str(stored_file["storage_path"]),
        status=DocumentStatus.UPLOADED.value,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Document]:
    get_owned_project(db, current_user.id, project_id)
    return list(
        db.scalars(
            select(Document)
            .where(Document.user_id == current_user.id, Document.project_id == project_id)
            .order_by(Document.created_at.desc())
        )
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    project_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    get_owned_project(db, current_user.id, project_id)
    return _get_owned_document(db, user_id=current_user.id, project_id=project_id, document_id=document_id)


@router.delete("/{document_id}", response_model=MessageResponse)
def delete_document(
    project_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    get_owned_project(db, current_user.id, project_id)
    document = _get_owned_document(db, user_id=current_user.id, project_id=project_id, document_id=document_id)
    delete_stored_file(document.storage_path)
    db.delete(document)
    db.commit()
    return MessageResponse(message="Document deleted.")
