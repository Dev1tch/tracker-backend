from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.service_provider import ServiceProvider
from app.schemas.project import (
    Project,
    ProjectCreate,
    ProjectInvitation,
    ProjectInviteRequest,
    ProjectInviteResponse,
    ProjectMember,
    ProjectUpdate,
)
from app.schemas.task import Task
from app.schemas.user import User
from app.services.project_notification_service import ProjectNotificationService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService

router = APIRouter()


def _display_name(user: User) -> str:
    parts = [user.first_name, user.last_name]
    name = " ".join(part for part in parts if part)
    return name or user.email


@router.get("/", response_model=list[Project], status_code=status.HTTP_200_OK)
def get_all_projects(
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(ServiceProvider.get_project_service),
):
    return project_service.get_all(current_user.id)


@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(ServiceProvider.get_project_service),
):
    data = project_service.create(current_user.id, project)
    if not data:
        raise HTTPException(status_code=400, detail="Could not create project")
    return data


@router.get("/{project_id}", response_model=Project, status_code=status.HTTP_200_OK)
def get_project_by_id(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(ServiceProvider.get_project_service),
):
    data = project_service.get_by_id(current_user.id, project_id)
    if not data:
        raise HTTPException(status_code=404, detail="Project not found")
    return data


@router.put("/{project_id}", response_model=Project, status_code=status.HTTP_200_OK)
def update_project(
    project_id: UUID,
    project: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(ServiceProvider.get_project_service),
):
    data = project_service.update(current_user.id, project_id, project)
    if not data:
        raise HTTPException(status_code=404, detail="Project not found")
    return data


@router.delete("/{project_id}", status_code=status.HTTP_200_OK)
def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(ServiceProvider.get_project_service),
):
    success = project_service.delete(current_user.id, project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "success"}


@router.get(
    "/{project_id}/tasks",
    response_model=list[Task],
    status_code=status.HTTP_200_OK,
)
def get_project_tasks(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(ServiceProvider.get_task_service),
):
    data = task_service.get_all(current_user.id, project_id=project_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return data


@router.get(
    "/{project_id}/members",
    response_model=list[ProjectMember],
    status_code=status.HTTP_200_OK,
)
def get_project_members(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(ServiceProvider.get_project_service),
):
    data = project_service.get_members(current_user.id, project_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return data


@router.delete(
    "/{project_id}/members/{member_id}",
    status_code=status.HTTP_200_OK,
)
def remove_project_member(
    project_id: UUID,
    member_id: UUID,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(ServiceProvider.get_project_service),
):
    success = project_service.remove_member(current_user.id, project_id, member_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project member not found")
    return {"status": "success"}


@router.post(
    "/{project_id}/invite",
    response_model=ProjectInviteResponse,
    status_code=status.HTTP_201_CREATED,
)
def invite_project_member(
    project_id: UUID,
    request: ProjectInviteRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    project_service: ProjectService = Depends(ServiceProvider.get_project_service),
    notifications: ProjectNotificationService = Depends(
        ServiceProvider.get_project_notification_service
    ),
):
    data = project_service.invite_by_email(current_user.id, project_id, request.email)
    if not data:
        raise HTTPException(status_code=404, detail="Project not found")
    if not data["invitation"]:
        raise HTTPException(status_code=400, detail="Could not create project invitation")

    project = data["project"]
    background_tasks.add_task(
        notifications.send_project_invite_email,
        recipient_email=request.email,
        project_name=project["name"],
        inviter_name=_display_name(current_user),
    )

    return {
        "invitation": ProjectInvitation(**data["invitation"]),
        "member": ProjectMember(**data["member"]) if data["member"] else None,
    }
