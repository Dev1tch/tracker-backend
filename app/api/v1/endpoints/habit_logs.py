from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from app.schemas.habit import HabitLog, HabitLogCreate, HabitLogUpdate
from app.schemas.user import User
from app.core.service_provider import ServiceProvider
from app.services.log_service import LogService
from app.services.habit_service import HabitService
from app.api.deps import get_current_user
from uuid import UUID
from datetime import date

router = APIRouter()

@router.post("/", response_model=HabitLog)
def create_log(
    log: HabitLogCreate, 
    current_user: User = Depends(get_current_user),
    log_service: LogService = Depends(ServiceProvider.get_log_service),
    habit_service: HabitService = Depends(ServiceProvider.get_habit_service)
):
    # Check if user owns the habit
    habit = habit_service.get_by_id(current_user.id, log.habit_id)
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You do not have permission to log for this habit"
        )
    
    data = log_service.create(log)
    if not data:
        raise HTTPException(status_code=400, detail="Could not create habit log")
    return data

@router.get("/", response_model=List[HabitLog])
def get_logs(
    habit_id: Optional[UUID] = None,
    day: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    log_service: LogService = Depends(ServiceProvider.get_log_service)
):
    return log_service.get_logs(current_user.id, habit_id=habit_id, day=day)

@router.patch("/{log_id}", response_model=HabitLog)
def update_log(
    log_id: UUID, 
    log_update: HabitLogUpdate, 
    current_user: User = Depends(get_current_user),
    log_service: LogService = Depends(ServiceProvider.get_log_service)
):
    # Check if the log belongs to a habit owned by the user
    log = log_service.get_by_id(log_id)
    if not log or log["habits"]["user_id"] != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Log not found or access denied"
        )
    
    data = log_service.update(log_id, log_update)
    if not data:
        raise HTTPException(status_code=404, detail="Could not update log")
    return data

@router.delete("/{log_id}")
def delete_log(
    log_id: UUID, 
    current_user: User = Depends(get_current_user),
    log_service: LogService = Depends(ServiceProvider.get_log_service)
):
    # Check ownership
    log = log_service.get_by_id(log_id)
    if not log or log["habits"]["user_id"] != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Log not found or access denied"
        )
        
    success = log_service.delete(log_id)
    if not success:
        raise HTTPException(status_code=404, detail="Could not delete log")
    return {"status": "success"}
