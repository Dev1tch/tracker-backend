from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from app.core.supabase_client import SupabaseClient


EMPTY_BOARD_STATE: dict = {
    "nodes": [],
    "edges": [],
    "frames": [],
    "viewport": {"x": 0, "y": 0, "zoom": 1},
}


class BoardService:
    def __init__(self, db: SupabaseClient):
        self.db = db
        self.table_name = "board_documents"

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def get_or_create(self, user_id: UUID) -> dict:
        existing = self.db.read(self.table_name, filters={"user_id": str(user_id)})
        if existing.data:
            return existing.data[0]

        seed = {
            "user_id": str(user_id),
            "state": EMPTY_BOARD_STATE,
            "version": 0,
            "updated_at": self._now_iso(),
        }
        created = self.db.create(self.table_name, seed)
        if created.data:
            return created.data[0]
        retry = self.db.read(self.table_name, filters={"user_id": str(user_id)})
        return retry.data[0] if retry.data else seed

    def update(self, user_id: UUID, state: Any) -> Optional[dict]:
        """Unconditional overwrite — clients are no longer expected to send a
        base_version (kept for ordering only)."""
        current = self.get_or_create(user_id)
        next_version = int(current.get("version", 0)) + 1
        updated = self.db.update(
            self.table_name,
            filters={"user_id": str(user_id)},
            data={
                "state": state,
                "version": next_version,
                "updated_at": self._now_iso(),
            },
        )
        if updated.data:
            return updated.data[0]
        retry = self.db.read(self.table_name, filters={"user_id": str(user_id)})
        return retry.data[0] if retry.data else current
