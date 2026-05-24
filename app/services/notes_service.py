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

    def update(self, user_id: UUID, tree: Any) -> Optional[dict]:
        """Unconditionally overwrite the user's notes document. Bumps
        ``version`` (kept for ordering/debug; clients no longer base writes
        on it) and ``updated_at`` to now. Single RPC = one round-trip."""
        response = self.db.rpc(
            "update_notes_tree",
            {"p_user_id": str(user_id), "p_tree": tree},
        )
        rows = response.data or []
        if not rows:
            return None
        row = rows[0]
        return {
            "user_id": row.get("user_id"),
            "tree": row.get("tree"),
            "version": row.get("version"),
            "updated_at": row.get("updated_at"),
        }
