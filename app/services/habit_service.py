from typing import List, Optional
from uuid import UUID
from app.core.supabase_client import supabase
from app.schemas.habit import HabitCreate, HabitUpdate

class HabitService:
    def __init__(self):
        self.table_name = "habits"

    def create(self, habit_data: HabitCreate):
        response = supabase.create(self.table_name, habit_data.model_dump(mode='json'))
        return response.data[0] if response.data else None

    def get_habits(self, category_id: Optional[UUID] = None, is_active: Optional[bool] = None):
        filters = {}
        if category_id:
            filters["category_id"] = str(category_id)
        if is_active is not None:
            filters["is_active"] = is_active
        response = supabase.read(self.table_name, filters=filters if filters else None)
        return response.data

    def get_by_id(self, habit_id: UUID):
        response = supabase.read(self.table_name, filters={"id": str(habit_id)})
        return response.data[0] if response.data else None

    def update(self, habit_id: UUID, habit_update: HabitUpdate):
        response = supabase.update(
            self.table_name, 
            filters={"id": str(habit_id)}, 
            data=habit_update.model_dump(mode='json', exclude_unset=True)
        )
        return response.data[0] if response.data else None

    def delete(self, habit_id: UUID):
        response = supabase.delete(self.table_name, filters={"id": str(habit_id)})
        return len(response.data) > 0 if response.data else False

