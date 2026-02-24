from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class TaskPriority(str, Enum):
    URGENT = "URGENT"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


class TaskOrganizationStatus(str, Enum):
    TO_DO = "TO_DO"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    IN_REVIEW = "IN_REVIEW"
    ARCHIVED = "ARCHIVED"


class TaskTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    is_active: bool = True


class TaskTypeCreate(TaskTypeBase):
    pass


class TaskType(TaskTypeBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    task_type_id: Optional[UUID] = None
    parent_task_id: Optional[UUID] = None
    status: TaskOrganizationStatus = TaskOrganizationStatus.TO_DO
    priority: TaskPriority = TaskPriority.NORMAL
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    task_type_id: Optional[UUID] = None
    parent_task_id: Optional[UUID] = None
    status: Optional[TaskOrganizationStatus] = None
    priority: Optional[TaskPriority] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    pause_start_date: Optional[datetime] = None
    total_pause_time_minutes: Optional[int] = None
    total_spent_time_minutes: Optional[int] = None
    is_parent: Optional[bool] = None


class Task(TaskBase):
    id: UUID
    user_id: UUID
    completed_at: Optional[datetime] = None
    pause_start_date: Optional[datetime] = None
    total_pause_time_minutes: int = 0
    total_spent_time_minutes: int = 0
    is_parent: bool = False
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BulkDeleteRequest(BaseModel):
    task_ids: list[UUID]


class BulkStatusUpdateRequest(BaseModel):
    task_ids: list[UUID]
    status: TaskOrganizationStatus
