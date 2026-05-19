from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class ProjectMemberRole(str, Enum):
    OWNER = "OWNER"
    MEMBER = "MEMBER"


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class Project(ProjectBase):
    id: UUID
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectMember(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID
    role: ProjectMemberRole
    invited_by_user_id: Optional[UUID] = None
    joined_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectInviteRequest(BaseModel):
    email: EmailStr


class ProjectInvitation(BaseModel):
    id: UUID
    project_id: UUID
    email: EmailStr
    invited_by_user_id: UUID
    accepted_by_user_id: Optional[UUID] = None
    accepted_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectInviteResponse(BaseModel):
    invitation: ProjectInvitation
    member: Optional[ProjectMember] = None
