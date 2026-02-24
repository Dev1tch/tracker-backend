from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.service_provider import ServiceProvider
from app.schemas.task import (
    BulkDeleteRequest,
    BulkStatusUpdateRequest,
    Task,
    TaskCreate,
    TaskType,
    TaskTypeCreate,
    TaskUpdate,
)
from app.schemas.user import User
from app.services.task_service import TaskService

router = APIRouter()


@router.get("/", response_model=list[Task], status_code=status.HTTP_200_OK)
def get_all_tasks(
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(ServiceProvider.get_task_service),
):
    return task_service.get_all(current_user.id)


@router.post("/", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(ServiceProvider.get_task_service),
):
    data = task_service.create(current_user.id, task)
    if not data:
        raise HTTPException(
            status_code=400,
            detail="Could not create task. Check task data and parent task reference.",
        )
    return data


@router.delete("/bulk", status_code=status.HTTP_200_OK)
def delete_tasks_bulk(
    request: BulkDeleteRequest,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(ServiceProvider.get_task_service),
):
    deleted_count = task_service.delete_tasks_bulk(current_user.id, request.task_ids)
    return {"status": "success", "deleted_count": deleted_count}


@router.patch("/bulk/status", status_code=status.HTTP_200_OK)
def update_tasks_status_bulk(
    request: BulkStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(ServiceProvider.get_task_service),
):
    updated_count = task_service.update_tasks_status_bulk(
        current_user.id, request.task_ids, request.status
    )
    return {"status": "success", "updated_count": updated_count}


@router.get("/types", response_model=list[TaskType], status_code=status.HTTP_200_OK)
def get_all_task_types(
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(ServiceProvider.get_task_service),
):
    return task_service.get_all_task_types(current_user.id)


@router.post("/types", response_model=TaskType, status_code=status.HTTP_201_CREATED)
def create_task_type(
    task_type: TaskTypeCreate,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(ServiceProvider.get_task_service),
):
    data = task_service.create_task_type(current_user.id, task_type)
    if not data:
        raise HTTPException(status_code=400, detail="Could not create task type")
    return data


@router.delete("/types/{task_type_id}", status_code=status.HTTP_200_OK)
def delete_task_type(
    task_type_id: UUID,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(ServiceProvider.get_task_service),
):
    success = task_service.delete_task_type(current_user.id, task_type_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task type not found")
    return {"status": "success"}


@router.get("/{task_id}", response_model=Task, status_code=status.HTTP_200_OK)
def get_task_by_id(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(ServiceProvider.get_task_service),
):
    data = task_service.get_by_id(current_user.id, task_id)
    if not data:
        raise HTTPException(status_code=404, detail="Task not found")
    return data


@router.put("/{task_id}", response_model=Task, status_code=status.HTTP_200_OK)
def update_task(
    task_id: UUID,
    task: TaskUpdate,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(ServiceProvider.get_task_service),
):
    data = task_service.update(current_user.id, task_id, task)
    if not data:
        raise HTTPException(status_code=404, detail="Task not found or could not be updated")
    return data
