from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ExternalProvider = Literal["all", "crossref", "arxiv"]


class ExternalReferenceCandidateBase(BaseModel):
    source: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=1000)
    authors: list[str] = Field(default_factory=list, max_length=50)
    year: int | None = Field(default=None, ge=0, le=9999)
    venue: str | None = Field(default=None, max_length=512)
    doi: str | None = Field(default=None, max_length=255)
    url: str | None = Field(default=None, max_length=2000)
    abstract: str | None = None
    warnings: list[str] = Field(default_factory=list)


class ExternalReferenceSearchRequest(BaseModel):
    query: str | None = Field(default=None, max_length=300)
    doi: str | None = Field(default=None, max_length=255)
    provider: ExternalProvider = "all"
    limit: int = Field(default=6, ge=1, le=10)

    @model_validator(mode="after")
    def validate_search_input(self) -> "ExternalReferenceSearchRequest":
        if not (self.query and self.query.strip()) and not (self.doi and self.doi.strip()):
            raise ValueError("Provide a title, keyword, or DOI before searching external references.")
        return self


class ExternalReferenceSearchCandidateResponse(ExternalReferenceCandidateBase):
    dedupe_key: str = Field(min_length=1, max_length=1200)


class ExternalReferenceSearchResponse(BaseModel):
    results: list[ExternalReferenceSearchCandidateResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ExternalReferenceSaveRequest(ExternalReferenceCandidateBase):
    pass


class ExternalReferenceContextResponse(ExternalReferenceCandidateBase):
    id: str
    label: Literal["external reference"] = "external reference"


class ExternalReferenceResponse(ExternalReferenceCandidateBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    project_id: str
    bibtex: str
    created_at: datetime
    updated_at: datetime
