from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


DocumentStatusValue = Literal["uploaded", "processing", "processed", "failed"]


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    project_id: str
    filename: str
    original_filename: str
    file_type: str
    mime_type: str
    file_size: int
    storage_path: str
    status: DocumentStatusValue
    created_at: datetime
    updated_at: datetime
