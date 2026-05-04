from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_project
from app.db.session import get_db
from app.models.user import User
from app.schemas.project import KnowledgeBaseBuildResponse
from app.services.rag import KnowledgeBaseError, build_project_knowledge_base

router = APIRouter(prefix="/projects/{project_id}/knowledge-base", tags=["knowledge-base"])


@router.post("/build", response_model=KnowledgeBaseBuildResponse)
def build_knowledge_base(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeBaseBuildResponse:
    get_owned_project(db, current_user.id, project_id)

    try:
        summary = build_project_knowledge_base(db, user_id=current_user.id, project_id=project_id)
    except KnowledgeBaseError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return KnowledgeBaseBuildResponse(
        message="Project knowledge base build completed.",
        knowledge_base=summary,
    )
