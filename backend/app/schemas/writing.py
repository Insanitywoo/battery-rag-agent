from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.chat import SourceReferenceResponse


WritingArtifactType = Literal[
    "outline",
    "introduction_outline",
    "related_work",
    "method_framework",
    "conclusion",
    "citation_check",
]


class WritingRunRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=300)
    task_type: WritingArtifactType | None = None
    research_direction: str | None = Field(default=None, max_length=300)
    requirements: str | None = Field(default=None, max_length=6000)


class WritingArtifactResponse(BaseModel):
    id: str
    user_id: str
    project_id: str
    artifact_type: WritingArtifactType
    title: str
    content_markdown: str
    sources: list[SourceReferenceResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
