from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class BoardDocument(BaseModel):
    user_id: UUID
    state: Any
    version: int
    updated_at: datetime

    class Config:
        from_attributes = True


class BoardUpdate(BaseModel):
    state: Any
    base_version: int


class BoardConflict(BaseModel):
    status: str = "conflict"
    detail: str = "Document version is out of date."
    document: BoardDocument
