from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class KnowledgeBaseStatusResponse(BaseModel):
    total_documents: int
    processed_documents: int
    embedded_documents: int
    total_chunks: int
    indexed_chunks: int
    can_chat: bool
    needs_rebuild: bool
    last_embedded_at: datetime | None


class ProjectDetailResponse(ProjectResponse):
    knowledge_base: KnowledgeBaseStatusResponse


class KnowledgeBaseBuildResponse(BaseModel):
    message: str
    knowledge_base: KnowledgeBaseStatusResponse
