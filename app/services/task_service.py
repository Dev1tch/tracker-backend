from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.core.supabase_client import SupabaseClient
from app.schemas.task import (
    TaskCreate,
    TaskOrganizationStatus,
    TaskTypeCreate,
    TaskUpdate,
)


class TaskService:
    def __init__(self, db: SupabaseClient):
        self.db = db
        self.table_name = "tasks"
        self.task_type_table = "task_types"
        self.project_member_table = "task_project_users"

    def _parse_datetime(self, value: object) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, str):
            normalized = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)
        else:
            return None

        if dt.tzinfo is not None:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

    def _now(self) -> datetime:
        return datetime.utcnow()

    def _now_iso(self) -> str:
        return self._now().isoformat()

    def _get_task_for_user(
        self, user_id: UUID, task_id: UUID, include_deleted: bool = False
    ) -> Optional[dict]:
        filters = {"id": str(task_id)}
        if not include_deleted:
            filters["is_deleted"] = False

        response = self.db.read(self.table_name, filters=filters)
        task = response.data[0] if response.data else None
        if not task or not self._can_access_task(user_id, task):
            return None
        return task

    def _can_access_project(self, user_id: UUID, project_id: str) -> bool:
        response = self.db.read(
            self.project_member_table,
            filters={"project_id": project_id, "user_id": str(user_id)},
            limit=1,
        )
        return bool(response.data)

    def _can_access_task(self, user_id: UUID, task: dict) -> bool:
        if task.get("user_id") == str(user_id):
            return True

        project_id = task.get("project_id")
        if not project_id:
            return False

        return self._can_access_project(user_id, project_id)

    def _get_project_ids_for_user(self, user_id: UUID) -> list[str]:
        response = self.db.read(
            self.project_member_table,
            select="project_id",
            filters={"user_id": str(user_id)},
        )
        return [row["project_id"] for row in response.data]

    def _refresh_parent_flag(self, parent_task_id: Optional[str]) -> None:
        if not parent_task_id:
            return

        children_response = self.db.read(
            self.table_name,
            filters={
                "parent_task_id": parent_task_id,
                "is_deleted": False,
            },
            limit=1,
        )
        has_children = bool(children_response.data)

        self.db.update(
            self.table_name,
            filters={"id": parent_task_id},
            data={"is_parent": has_children, "updated_at": self._now_iso()},
        )

    def _build_status_updates(
        self, task: dict, new_status: TaskOrganizationStatus
    ) -> dict:
        now = self._now()
        updates: dict = {}

        start_date = self._parse_datetime(task.get("start_date"))
        pause_start_date = self._parse_datetime(task.get("pause_start_date"))
        total_pause_time_minutes = int(task.get("total_pause_time_minutes") or 0)

        if new_status == TaskOrganizationStatus.IN_PROGRESS:
            if not start_date:
                updates["start_date"] = now.isoformat()
            elif pause_start_date:
                paused_minutes = int((now - pause_start_date).total_seconds() / 60)
                total_pause_time_minutes += max(paused_minutes, 0)
                updates["total_pause_time_minutes"] = total_pause_time_minutes
                updates["pause_start_date"] = None

        elif new_status == TaskOrganizationStatus.PAUSED:
            if not pause_start_date:
                updates["pause_start_date"] = now.isoformat()

        elif new_status == TaskOrganizationStatus.COMPLETED:
            if pause_start_date:
                paused_minutes = int((now - pause_start_date).total_seconds() / 60)
                total_pause_time_minutes += max(paused_minutes, 0)
                updates["total_pause_time_minutes"] = total_pause_time_minutes
                updates["pause_start_date"] = None

            if not start_date:
                start_date = now
                updates["start_date"] = now.isoformat()

            total_minutes = int((now - start_date).total_seconds() / 60)
            updates["completed_at"] = now.isoformat()
            updates["total_spent_time_minutes"] = max(
                total_minutes - total_pause_time_minutes, 0
            )

        updates["status"] = new_status.value
        return updates

    def _set_parent_on_create_or_move(
        self,
        user_id: UUID,
        parent_task_id: Optional[str],
        project_id: Optional[str],
    ) -> bool:
        if not parent_task_id:
            return True

        parent_task = self._get_task_for_user(user_id, UUID(parent_task_id))
        if not parent_task:
            return False

        if parent_task.get("project_id") != project_id:
            return False

        self.db.update(
            self.table_name,
            filters={"id": parent_task_id},
            data={"is_parent": True, "updated_at": self._now_iso()},
        )
        return True

    def get_by_id(self, user_id: UUID, task_id: UUID) -> Optional[dict]:
        return self._get_task_for_user(user_id, task_id)

    def get_all(
        self, user_id: UUID, project_id: Optional[UUID] = None
    ) -> Optional[list[dict]]:
        if project_id and not self._can_access_project(user_id, str(project_id)):
            return None

        project_ids = self._get_project_ids_for_user(user_id)
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("is_deleted", False)
            .order("created_at", desc=True)
        )
        if project_id:
            query = query.eq("project_id", str(project_id))
        elif project_ids:
            project_id_list = ",".join(project_ids)
            query = query.or_(f"user_id.eq.{user_id},project_id.in.({project_id_list})")
        else:
            query = query.eq("user_id", str(user_id))

        response = query.execute()
        return response.data

    def create(self, user_id: UUID, task_data: TaskCreate) -> Optional[dict]:
        data = task_data.model_dump(mode="json")
        data["user_id"] = str(user_id)
        data.setdefault("is_deleted", False)
        data.setdefault("is_parent", False)
        data.setdefault("total_pause_time_minutes", 0)
        data.setdefault("total_spent_time_minutes", 0)

        project_id = data.get("project_id")
        if project_id and not self._can_access_project(user_id, project_id):
            return None

        parent_task_id = data.get("parent_task_id")
        if parent_task_id and not self._set_parent_on_create_or_move(
            user_id, parent_task_id, project_id
        ):
            return None

        status = TaskOrganizationStatus(data.get("status", TaskOrganizationStatus.TO_DO))
        if status != TaskOrganizationStatus.TO_DO:
            status_updates = self._build_status_updates(data, status)
            data.update(status_updates)

        response = self.db.create(self.table_name, data)
        return response.data[0] if response.data else None

    def update(self, user_id: UUID, task_id: UUID, task_data: TaskUpdate) -> Optional[dict]:
        current = self._get_task_for_user(user_id, task_id)
        if not current:
            return None

        data = task_data.model_dump(mode="json", exclude_unset=True)
        if not data:
            return current

        old_parent_task_id = current.get("parent_task_id")
        new_parent_task_id = data.get("parent_task_id", old_parent_task_id)
        new_project_id = data.get("project_id", current.get("project_id"))

        if "project_id" in data and new_project_id:
            if not self._can_access_project(user_id, new_project_id):
                return None

        if "project_id" in data and new_parent_task_id:
            if not self._set_parent_on_create_or_move(
                user_id, new_parent_task_id, new_project_id
            ):
                return None

        if "parent_task_id" in data:
            if new_parent_task_id == str(task_id):
                return None
            if new_parent_task_id and not self._set_parent_on_create_or_move(
                user_id, new_parent_task_id, new_project_id
            ):
                return None

        if "status" in data and data["status"] is not None:
            new_status = TaskOrganizationStatus(data["status"])
            if new_status.value != current.get("status"):
                status_updates = self._build_status_updates(current, new_status)
                data.update(status_updates)

        data["updated_at"] = self._now_iso()

        response = self.db.update(
            self.table_name,
            filters={"id": str(task_id)},
            data=data,
        )
        updated = response.data[0] if response.data else None

        if old_parent_task_id and old_parent_task_id != new_parent_task_id:
            self._refresh_parent_flag(old_parent_task_id)

        return updated

    def delete_tasks_bulk(self, user_id: UUID, task_ids: list[UUID]) -> int:
        if not task_ids:
            return 0

        deleted_count = 0
        processed_ids: set[str] = set()
        now_iso = self._now_iso()

        for task_id in task_ids:
            task_id_str = str(task_id)
            if task_id_str in processed_ids:
                continue

            task = self._get_task_for_user(user_id, task_id)
            if not task:
                continue

            parent_task_id = task.get("parent_task_id")
            response = self.db.update(
                self.table_name,
                filters={"id": task_id_str},
                data={"is_deleted": True, "updated_at": now_iso},
            )
            if response.data:
                deleted_count += 1
                processed_ids.add(task_id_str)

            subtasks_response = self.db.read(
                self.table_name,
                filters={
                    "parent_task_id": task_id_str,
                    "is_deleted": False,
                },
            )
            for subtask in subtasks_response.data:
                if not self._can_access_task(user_id, subtask):
                    continue

                subtask_id = subtask["id"]
                if subtask_id in processed_ids:
                    continue

                subtask_update = self.db.update(
                    self.table_name,
                    filters={"id": subtask_id},
                    data={"is_deleted": True, "updated_at": now_iso},
                )
                if subtask_update.data:
                    deleted_count += 1
                    processed_ids.add(subtask_id)

            self._refresh_parent_flag(parent_task_id)

        return deleted_count

    def update_tasks_status_bulk(
        self, user_id: UUID, task_ids: list[UUID], new_status: TaskOrganizationStatus
    ) -> int:
        if not task_ids:
            return 0

        updated_count = 0
        processed_ids: set[str] = set()

        for task_id in task_ids:
            task_id_str = str(task_id)
            if task_id_str in processed_ids:
                continue

            task = self._get_task_for_user(user_id, task_id)
            if not task:
                continue

            if new_status.value == task.get("status"):
                continue

            updates = self._build_status_updates(task, new_status)
            updates["updated_at"] = self._now_iso()

            response = self.db.update(
                self.table_name,
                filters={"id": task_id_str},
                data=updates,
            )
            if response.data:
                updated_count += 1
                processed_ids.add(task_id_str)

            subtasks_response = self.db.read(
                self.table_name,
                filters={
                    "parent_task_id": task_id_str,
                    "is_deleted": False,
                },
            )
            for subtask in subtasks_response.data:
                if not self._can_access_task(user_id, subtask):
                    continue

                subtask_id = subtask["id"]
                if subtask_id in processed_ids:
                    continue

                if new_status.value == subtask.get("status"):
                    continue

                subtask_updates = self._build_status_updates(subtask, new_status)
                subtask_updates["updated_at"] = self._now_iso()

                subtask_response = self.db.update(
                    self.table_name,
                    filters={"id": subtask_id},
                    data=subtask_updates,
                )
                if subtask_response.data:
                    updated_count += 1
                    processed_ids.add(subtask_id)

        return updated_count

    def get_all_task_types(self, user_id: UUID) -> list[dict]:
        response = self.db.read(
            self.task_type_table,
            filters={"user_id": str(user_id)},
            order="created_at.desc",
        )
        return response.data

    def get_task_type_by_id(self, user_id: UUID, task_type_id: UUID) -> Optional[dict]:
        response = self.db.read(
            self.task_type_table,
            filters={"id": str(task_type_id), "user_id": str(user_id)},
        )
        return response.data[0] if response.data else None

    def create_task_type(self, user_id: UUID, task_type_data: TaskTypeCreate) -> Optional[dict]:
        data = task_type_data.model_dump(mode="json")
        data["user_id"] = str(user_id)
        response = self.db.create(self.task_type_table, data)
        return response.data[0] if response.data else None

    def delete_task_type(self, user_id: UUID, task_type_id: UUID) -> bool:
        response = self.db.delete(
            self.task_type_table,
            filters={"id": str(task_type_id), "user_id": str(user_id)},
        )
        return len(response.data) > 0 if response.data else False
