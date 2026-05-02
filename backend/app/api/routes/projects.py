from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.project import ProjectCreateRequest, ProjectResponse

router = APIRouter(prefix="/projects", tags=["projects"])


def _get_owned_project(db: Session, owner_id: str, project_id: str) -> Project:
    project = db.scalar(select(Project).where(Project.id == project_id, Project.owner_id == owner_id))
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project = Project(
        owner_id=current_user.id,
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Project]:
    return list(
        db.scalars(
            select(Project).where(Project.owner_id == current_user.id).order_by(Project.created_at.desc())
        )
    )


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    return _get_owned_project(db, current_user.id, project_id)


@router.delete("/{project_id}", response_model=MessageResponse)
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    project = _get_owned_project(db, current_user.id, project_id)
    db.delete(project)
    db.commit()
    return MessageResponse(message="Project deleted.")
