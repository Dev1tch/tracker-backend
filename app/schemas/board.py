from datetime import datetime
from typing import Any, Optional
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
    # Accepted-but-ignored (kept for backward compat with cached clients).
    base_version: Optional[int] = None
