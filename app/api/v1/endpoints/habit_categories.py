from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.schemas.habit import HabitCategory, HabitCategoryCreate, HabitCategoryUpdate
from app.schemas.user import User
from app.core.service_provider import ServiceProvider
from app.services.category_service import CategoryService
from app.api.deps import get_current_user
from uuid import UUID

router = APIRouter()

@router.post("/", response_model=HabitCategory)
def create_category(
    category: HabitCategoryCreate, 
    current_user: User = Depends(get_current_user),
    service: CategoryService = Depends(ServiceProvider.get_category_service)
):
    data = service.create(current_user.id, category)
    if not data:
        raise HTTPException(status_code=400, detail="Could not create category")
    return data

@router.get("/", response_model=List[HabitCategory])
def get_categories(
    current_user: User = Depends(get_current_user),
    service: CategoryService = Depends(ServiceProvider.get_category_service)
):
    return service.get_all(current_user.id)

@router.get("/{category_id}", response_model=HabitCategory)
def get_category(
    category_id: UUID, 
    current_user: User = Depends(get_current_user),
    service: CategoryService = Depends(ServiceProvider.get_category_service)
):
    data = service.get_by_id(current_user.id, category_id)
    if not data:
        raise HTTPException(status_code=404, detail="Category not found")
    return data

@router.delete("/{category_id}")
def delete_category(
    category_id: UUID, 
    current_user: User = Depends(get_current_user),
    service: CategoryService = Depends(ServiceProvider.get_category_service)
):
    success = service.delete(current_user.id, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found or could not be deleted")
    return {"status": "success"}

@router.put("/{category_id}", response_model=HabitCategory)
def update_category(
    category_id: UUID,
    category_update: HabitCategoryUpdate,
    current_user: User = Depends(get_current_user),
    service: CategoryService = Depends(ServiceProvider.get_category_service)
):
    updated_category = service.update(current_user.id, category_id, category_update)
    if not updated_category:
        raise HTTPException(status_code=404, detail="Category not found or could not be updated")
    return updated_category
