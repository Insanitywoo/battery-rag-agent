from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_project
from app.db.session import get_db
from app.models.user import User
from app.schemas.agent import AgentRunRequest, AgentTaskResponse
from app.services.agent_framework import get_agent_executor


router = APIRouter(prefix="/projects/{project_id}/agent", tags=["agent"])


@router.post("/run", response_model=AgentTaskResponse)
def run_agent_task(
    project_id: str,
    payload: AgentRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentTaskResponse:
    get_owned_project(db, current_user.id, project_id)
    executor = get_agent_executor()
    return executor.run(
        db,
        user_id=current_user.id,
        project_id=project_id,
        user_input=payload.user_input,
        requested_task_type=payload.task_type,
    )
