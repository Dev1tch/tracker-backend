from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.schemas.habit import Habit, HabitCreate, HabitUpdate
from app.core.service_provider import ServiceProvider
from app.services.habit_service import HabitService
from uuid import UUID

router = APIRouter()

@router.post("/", response_model=Habit)
def create_habit(
    habit: HabitCreate, 
    service: HabitService = Depends(ServiceProvider.get_habit_service)
):
    data = service.create(habit)
    if not data:
        raise HTTPException(status_code=400, detail="Could not create habit")
    return data

@router.get("/", response_model=List[Habit])
def get_habits(
    category_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    service: HabitService = Depends(ServiceProvider.get_habit_service)
):
    return service.get_habits(category_id=category_id, is_active=is_active)

@router.get("/{habit_id}", response_model=Habit)
def get_habit(
    habit_id: UUID, 
    service: HabitService = Depends(ServiceProvider.get_habit_service)
):
    data = service.get_by_id(habit_id)
    if not data:
        raise HTTPException(status_code=404, detail="Habit not found")
    return data

@router.patch("/{habit_id}", response_model=Habit)
def update_habit(
    habit_id: UUID, 
    habit_update: HabitUpdate, 
    service: HabitService = Depends(ServiceProvider.get_habit_service)
):
    data = service.update(habit_id, habit_update)
    if not data:
        raise HTTPException(status_code=404, detail="Habit not found or could not be updated")
    return data

@router.delete("/{habit_id}")
def delete_habit(
    habit_id: UUID, 
    service: HabitService = Depends(ServiceProvider.get_habit_service)
):
    success = service.delete(habit_id)
    if not success:
        raise HTTPException(status_code=404, detail="Habit not found or could not be deleted")
    return {"status": "success"}
