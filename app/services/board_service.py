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
        self.history_table_name = "board_document_history"

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

    def update(
        self,
        user_id: UUID,
        state: Any,
        base_version: Optional[int] = None,
        allow_empty_overwrite: bool = False,
    ) -> Optional[dict]:
        # Single RPC handles: get-or-create + version check + empty-overwrite
        # guard + UPDATE. History is written by a BEFORE UPDATE trigger so the
        # API doesn't wait for it.
        response = self.db.rpc(
            "update_board_state",
            {
                "p_user_id": str(user_id),
                "p_state": state,
                "p_base_version": base_version,
                "p_allow_empty_overwrite": allow_empty_overwrite,
            },
        )
        rows = response.data or []
        if not rows:
            return None
        row = rows[0]
        status = row.get("result_status")
        if status == "version_conflict":
            raise BoardVersionConflictError
        if status == "unversioned_overwrite":
            raise BoardUnversionedUpdateError
        if status == "unsafe_empty":
            raise BoardUnsafeOverwriteError
        return {
            "user_id": row.get("user_id"),
            "state": row.get("state"),
            "version": row.get("version"),
            "updated_at": row.get("updated_at"),
        }


class BoardVersionConflictError(Exception):
    pass


class BoardUnsafeOverwriteError(Exception):
    pass


class BoardUnversionedUpdateError(Exception):
    pass
