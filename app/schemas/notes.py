from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class NotesDocument(BaseModel):
    user_id: UUID
    tree: Any
    version: int
    updated_at: datetime

    class Config:
        from_attributes = True


class NotesUpdate(BaseModel):
    tree: Any
    base_version: int


class NotesConflict(BaseModel):
    status: str = "conflict"
    detail: str = "Document version is out of date."
    document: NotesDocument
