from typing import List, Optional
from uuid import UUID
from app.core.supabase_client import supabase
from app.schemas.habit import HabitCategoryCreate

class CategoryService:
    def __init__(self):
        self.table_name = "habit_categories"

    def create(self, category_data: HabitCategoryCreate):
        response = supabase.create(self.table_name, category_data.model_dump(mode='json'))
        return response.data[0] if response.data else None

    def get_all(self):
        response = supabase.read(self.table_name)
        return response.data

    def get_by_id(self, category_id: UUID):
        response = supabase.read(self.table_name, filters={"id": str(category_id)})
        return response.data[0] if response.data else None

    def delete(self, category_id: UUID):
        response = supabase.delete(self.table_name, filters={"id": str(category_id)})
        return len(response.data) > 0 if response.data else False

