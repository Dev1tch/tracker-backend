from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from app.core.supabase_client import SupabaseClient


class NotesService:
    def __init__(self, db: SupabaseClient):
        self.db = db
        self.table_name = "notes_documents"

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def get_or_create(self, user_id: UUID) -> dict:
        existing = self.db.read(self.table_name, filters={"user_id": str(user_id)})
        if existing.data:
            return existing.data[0]

        seed = {
            "user_id": str(user_id),
            "tree": [],
            "version": 0,
            "updated_at": self._now_iso(),
        }
        created = self.db.create(self.table_name, seed)
        if created.data:
            return created.data[0]
        # Fallback: re-read in case the row was created concurrently.
        retry = self.db.read(self.table_name, filters={"user_id": str(user_id)})
        return retry.data[0] if retry.data else seed

    def update(
        self, user_id: UUID, tree: Any, base_version: int
    ) -> tuple[str, Optional[dict]]:
        """Returns ("ok", doc) on success or ("conflict", current_doc) on
        version mismatch. Caller maps conflict to a 409."""
        current = self.get_or_create(user_id)
        if int(current.get("version", 0)) != int(base_version):
            return "conflict", current

        next_version = int(current.get("version", 0)) + 1
        updated = self.db.update(
            self.table_name,
            filters={"user_id": str(user_id)},
            data={
                "tree": tree,
                "version": next_version,
                "updated_at": self._now_iso(),
            },
        )
        if updated.data:
            return "ok", updated.data[0]

        # Defensive: re-read to return the persisted row.
        retry = self.db.read(self.table_name, filters={"user_id": str(user_id)})
        return ("ok", retry.data[0]) if retry.data else ("ok", current)
