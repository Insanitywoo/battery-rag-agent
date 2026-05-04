from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.chat import SourceReferenceResponse


AgentTaskType = Literal[
    "research_qa",
    "paper_summary",
    "multi_paper_compare",
    "literature_review",
    "writing_outline",
    "evidence_check",
]


class AgentResultSection(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=20000)


class AgentRunRequest(BaseModel):
    user_input: str = Field(min_length=1, max_length=12000)
    task_type: AgentTaskType | None = None


class AgentResultPayload(BaseModel):
    routed_task_type: AgentTaskType
    route_confidence: float = Field(ge=0.0, le=1.0)
    route_reason: str = Field(min_length=1, max_length=2000)
    answer: str | None = None
    result: str | None = None
    sections: list[AgentResultSection] = Field(default_factory=list)
    document_scope: list[str] = Field(default_factory=list)
    sources: list[SourceReferenceResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    clarification: str | None = None
    supported_claims: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)


class AgentTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    project_id: str
    task_type: AgentTaskType
    status: str
    user_input: str
    result_json: AgentResultPayload | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
