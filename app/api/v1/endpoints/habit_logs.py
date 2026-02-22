from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.schemas.habit import HabitLog, HabitLogCreate, HabitLogUpdate
from app.core.service_provider import ServiceProvider
from app.services.log_service import LogService
from uuid import UUID
from datetime import date

router = APIRouter()

@router.post("/", response_model=HabitLog)
def create_log(
    log: HabitLogCreate, 
    service: LogService = Depends(ServiceProvider.get_log_service)
):
    data = service.create(log)
    if not data:
        raise HTTPException(status_code=400, detail="Could not create habit log")
    return data

@router.get("/", response_model=List[HabitLog])
def get_logs(
    habit_id: Optional[UUID] = None,
    day: Optional[date] = None,
    service: LogService = Depends(ServiceProvider.get_log_service)
):
    return service.get_logs(habit_id=habit_id, day=day)

@router.patch("/{log_id}", response_model=HabitLog)
def update_log(
    log_id: UUID, 
    log_update: HabitLogUpdate, 
    service: LogService = Depends(ServiceProvider.get_log_service)
):
    data = service.update(log_id, log_update)
    if not data:
        raise HTTPException(status_code=404, detail="Log not found or could not be updated")
    return data

@router.delete("/{log_id}")
def delete_log(
    log_id: UUID, 
    service: LogService = Depends(ServiceProvider.get_log_service)
):
    success = service.delete(log_id)
    if not success:
        raise HTTPException(status_code=404, detail="Log not found or could not be deleted")
    return {"status": "success"}
