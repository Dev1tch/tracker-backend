from datetime import datetime
from typing import Any, Optional
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
    # base_version is accepted but ignored. Kept optional so older clients
    # in the wild don't get 422s while their bundle is still cached.
    base_version: Optional[int] = None
