from datetime import datetime
from typing import Optional
from uuid import UUID

from postgrest.exceptions import APIError

from app.core.supabase_client import SupabaseClient
from app.schemas.project import ProjectCreate, ProjectMemberRole, ProjectUpdate


class ProjectService:
    def __init__(self, db: SupabaseClient):
        self.db = db
        self.table_name = "task_projects"
        self.member_table = "task_project_users"
        self.invitation_table = "task_project_invitations"
        self.user_table = "users"

    def _now_iso(self) -> str:
        return datetime.utcnow().isoformat()

    def _get_membership(self, user_id: UUID, project_id: UUID) -> Optional[dict]:
        response = self.db.read(
            self.member_table,
            filters={"project_id": str(project_id), "user_id": str(user_id)},
            limit=1,
        )
        return response.data[0] if response.data else None

    def user_can_access(self, user_id: UUID, project_id: UUID) -> bool:
        return bool(self._get_membership(user_id, project_id))

    def get_user_project_ids(self, user_id: UUID) -> list[str]:
        response = self.db.read(
            self.member_table,
            select="project_id",
            filters={"user_id": str(user_id)},
        )
        return [row["project_id"] for row in response.data]

    def get_all(self, user_id: UUID) -> list[dict]:
        project_ids = self.get_user_project_ids(user_id)
        if not project_ids:
            return []

        response = (
            self.db.table(self.table_name)
            .select("*")
            .in_("id", project_ids)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    def get_by_id(self, user_id: UUID, project_id: UUID) -> Optional[dict]:
        if not self.user_can_access(user_id, project_id):
            return None

        response = self.db.read(self.table_name, filters={"id": str(project_id)}, limit=1)
        return response.data[0] if response.data else None

    def create(self, user_id: UUID, project_data: ProjectCreate) -> Optional[dict]:
        data = project_data.model_dump(mode="json")
        data["owner_id"] = str(user_id)

        response = self.db.create(self.table_name, data)
        project = response.data[0] if response.data else None
        if not project:
            return None

        self.db.create(
            self.member_table,
            {
                "project_id": project["id"],
                "user_id": str(user_id),
                "role": ProjectMemberRole.OWNER.value,
            },
        )
        return project

    def update(
        self, user_id: UUID, project_id: UUID, project_data: ProjectUpdate
    ) -> Optional[dict]:
        project = self.get_by_id(user_id, project_id)
        if not project:
            return None

        data = project_data.model_dump(mode="json", exclude_unset=True)
        if not data:
            return project

        data["updated_at"] = self._now_iso()
        response = self.db.update(
            self.table_name,
            filters={"id": str(project_id)},
            data=data,
        )
        return response.data[0] if response.data else None

    def delete(self, user_id: UUID, project_id: UUID) -> bool:
        membership = self._get_membership(user_id, project_id)
        if not membership or membership["role"] != ProjectMemberRole.OWNER.value:
            return False

        response = self.db.delete(self.table_name, filters={"id": str(project_id)})
        return bool(response.data)

    def get_members(self, user_id: UUID, project_id: UUID) -> Optional[list[dict]]:
        if not self.user_can_access(user_id, project_id):
            return None

        response = self.db.read(
            self.member_table,
            filters={"project_id": str(project_id)},
            order="created_at.asc",
        )
        members = response.data
        if not members:
            return []

        user_ids = [member["user_id"] for member in members]
        users_response = (
            self.db.table(self.user_table)
            .select("id,email,first_name,last_name")
            .in_("id", user_ids)
            .execute()
        )
        users_by_id = {user["id"]: user for user in users_response.data}

        return [
            {
                **member,
                "email": users_by_id.get(member["user_id"], {}).get("email"),
                "first_name": users_by_id.get(member["user_id"], {}).get("first_name"),
                "last_name": users_by_id.get(member["user_id"], {}).get("last_name"),
            }
            for member in members
        ]

    def invite_by_email(
        self, inviter_id: UUID, project_id: UUID, email: str
    ) -> Optional[dict]:
        project = self.get_by_id(inviter_id, project_id)
        if not project:
            return None

        normalized_email = email.strip().lower()
        invite_data = {
            "project_id": str(project_id),
            "email": normalized_email,
            "invited_by_user_id": str(inviter_id),
        }

        try:
            invitation_response = self.db.create(self.invitation_table, invite_data)
            invitation = invitation_response.data[0] if invitation_response.data else None
        except APIError:
            invitation_lookup = self.db.read(
                self.invitation_table,
                filters={"project_id": str(project_id), "email": normalized_email},
                limit=1,
            )
            invitation = invitation_lookup.data[0] if invitation_lookup.data else None

        member = None
        user_response = self.db.read(
            self.user_table,
            filters={"email": normalized_email},
            limit=1,
        )
        invited_user = user_response.data[0] if user_response.data else None
        if invited_user:
            member = self._add_member(
                project_id=project_id,
                user_id=UUID(invited_user["id"]),
                invited_by_user_id=inviter_id,
                role=ProjectMemberRole.MEMBER,
            )

            if invitation and not invitation.get("accepted_at"):
                accepted_response = self.db.update(
                    self.invitation_table,
                    filters={"id": invitation["id"]},
                    data={
                        "accepted_by_user_id": invited_user["id"],
                        "accepted_at": self._now_iso(),
                    },
                )
                invitation = (
                    accepted_response.data[0] if accepted_response.data else invitation
                )

        return {"project": project, "invitation": invitation, "member": member}

    def accept_pending_invitations_for_user(self, user_id: UUID, email: str) -> int:
        normalized_email = email.strip().lower()
        response = (
            self.db.table(self.invitation_table)
            .select("*")
            .eq("email", normalized_email)
            .is_("accepted_at", "null")
            .execute()
        )

        accepted_count = 0
        for invitation in response.data:
            member = self._add_member(
                project_id=UUID(invitation["project_id"]),
                user_id=user_id,
                invited_by_user_id=UUID(invitation["invited_by_user_id"]),
                role=ProjectMemberRole.MEMBER,
            )
            if not member:
                continue

            self.db.update(
                self.invitation_table,
                filters={"id": invitation["id"]},
                data={
                    "accepted_by_user_id": str(user_id),
                    "accepted_at": self._now_iso(),
                },
            )
            accepted_count += 1

        return accepted_count

    def _add_member(
        self,
        project_id: UUID,
        user_id: UUID,
        invited_by_user_id: Optional[UUID],
        role: ProjectMemberRole,
    ) -> Optional[dict]:
        data = {
            "project_id": str(project_id),
            "user_id": str(user_id),
            "role": role.value,
            "invited_by_user_id": (
                str(invited_by_user_id) if invited_by_user_id else None
            ),
        }
        try:
            response = self.db.create(self.member_table, data)
            return response.data[0] if response.data else None
        except APIError:
            response = self.db.read(
                self.member_table,
                filters={"project_id": str(project_id), "user_id": str(user_id)},
                limit=1,
            )
            return response.data[0] if response.data else None
