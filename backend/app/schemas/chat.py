from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ChatRole = Literal["user", "assistant"]


class SourceReferenceResponse(BaseModel):
    document_id: str
    document_name: str
    page_number: int | None
    chunk_id: str
    chunk_index: int
    excerpt: str


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    project_id: str
    session_id: str
    role: ChatRole
    content: str
    sources_json: list[SourceReferenceResponse] | None
    created_at: datetime


class ChatSessionSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    project_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ChatSessionDetailResponse(ChatSessionSummaryResponse):
    messages: list[ChatMessageResponse]


class ChatSessionCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class ChatQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=8000)
