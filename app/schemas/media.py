from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class MediaObject(BaseModel):
    id: UUID
    user_id: UUID
    kind: str
    storage_path: str
    url: str
    mime: Optional[str] = None
    size_bytes: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
