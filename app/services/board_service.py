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

    def _is_empty_state(self, state: Any) -> bool:
        if not isinstance(state, dict):
            return False
        return (
            not state.get("nodes")
            and not state.get("edges")
            and not state.get("frames")
        )

    def update(
        self,
        user_id: UUID,
        state: Any,
        base_version: Optional[int] = None,
        allow_empty_overwrite: bool = False,
    ) -> Optional[dict]:
        current = self.get_or_create(user_id)
        current_version = int(current.get("version", 0))
        current_state = current.get("state") or EMPTY_BOARD_STATE

        if base_version is not None and int(base_version) != current_version:
            raise BoardVersionConflictError

        if base_version is None and not self._is_empty_state(current_state):
            raise BoardUnversionedUpdateError

        if (
            self._is_empty_state(state)
            and not self._is_empty_state(current_state)
            and not allow_empty_overwrite
            and base_version is None
        ):
            raise BoardUnsafeOverwriteError

        self.db.create(
            self.history_table_name,
            {
                "user_id": str(user_id),
                "state": current_state,
                "version": current_version,
            },
        )

        next_version = int(current.get("version", 0)) + 1
        updated = self.db.update(
            self.table_name,
            filters={
                "user_id": str(user_id),
                **({"version": current_version} if base_version is not None else {}),
            },
            data={
                "state": state,
                "version": next_version,
                "updated_at": self._now_iso(),
            },
        )
        if updated.data:
            return updated.data[0]
        if base_version is not None:
            raise BoardVersionConflictError
        retry = self.db.read(self.table_name, filters={"user_id": str(user_id)})
        return retry.data[0] if retry.data else current


class BoardVersionConflictError(Exception):
    pass


class BoardUnsafeOverwriteError(Exception):
    pass


class BoardUnversionedUpdateError(Exception):
    pass
