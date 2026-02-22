from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.schemas.habit import HabitCategory, HabitCategoryCreate
from app.core.service_provider import ServiceProvider
from app.services.category_service import CategoryService
from uuid import UUID

router = APIRouter()

@router.post("/", response_model=HabitCategory)
def create_category(
    category: HabitCategoryCreate, 
    service: CategoryService = Depends(ServiceProvider.get_category_service)
):
    data = service.create(category)
    if not data:
        raise HTTPException(status_code=400, detail="Could not create category")
    return data

@router.get("/", response_model=List[HabitCategory])
def get_categories(service: CategoryService = Depends(ServiceProvider.get_category_service)):
    return service.get_all()

@router.get("/{category_id}", response_model=HabitCategory)
def get_category(
    category_id: UUID, 
    service: CategoryService = Depends(ServiceProvider.get_category_service)
):
    data = service.get_by_id(category_id)
    if not data:
        raise HTTPException(status_code=404, detail="Category not found")
    return data

@router.delete("/{category_id}")
def delete_category(
    category_id: UUID, 
    service: CategoryService = Depends(ServiceProvider.get_category_service)
):
    success = service.delete(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found or could not be deleted")
    return {"status": "success"}
