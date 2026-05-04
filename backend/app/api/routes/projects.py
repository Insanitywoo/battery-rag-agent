from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_project
from app.db.session import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.project import ProjectCreateRequest, ProjectDetailResponse, ProjectResponse
from app.services.rag import summarize_knowledge_base_status

router = APIRouter(prefix="/projects", tags=["projects"])


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


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectDetailResponse:
    project = get_owned_project(db, current_user.id, project_id)
    knowledge_base = summarize_knowledge_base_status(db, user_id=current_user.id, project_id=project_id)
    return ProjectDetailResponse.model_validate(
        {
            "id": project.id,
            "owner_id": project.owner_id,
            "name": project.name,
            "description": project.description,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "knowledge_base": knowledge_base.model_dump(),
        }
    )


@router.delete("/{project_id}", response_model=MessageResponse)
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    project = get_owned_project(db, current_user.id, project_id)
    db.delete(project)
    db.commit()
    return MessageResponse(message="Project deleted.")
