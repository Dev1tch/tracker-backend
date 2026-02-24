from typing import Optional
from uuid import UUID
from app.core.supabase_client import SupabaseClient
from app.schemas.habit import HabitCreate, HabitUpdate

class HabitService:
    def __init__(self, db: SupabaseClient):
        self.db = db
        self.table_name = "habits"

    def create(self, user_id: UUID, habit_data: HabitCreate):
        data = habit_data.model_dump(mode='json')
        data["user_id"] = str(user_id)
        response = self.db.create(self.table_name, data)
        return response.data[0] if response.data else None

    def get_habits(self, user_id: UUID, category_id: Optional[UUID] = None, is_active: Optional[bool] = None):
        filters = {"user_id": str(user_id)}
        if category_id:
            filters["category_id"] = str(category_id)
        if is_active is not None:
            filters["is_active"] = is_active
        response = self.db.read(self.table_name, filters=filters)
        return response.data

    def get_by_id(self, user_id: UUID, habit_id: UUID):
        response = self.db.read(
            self.table_name, 
            filters={"id": str(habit_id), "user_id": str(user_id)}
        )
        return response.data[0] if response.data else None

    def update(self, user_id: UUID, habit_id: UUID, habit_update: HabitUpdate):
        response = self.db.update(
            self.table_name, 
            filters={"id": str(habit_id), "user_id": str(user_id)}, 
            data=habit_update.model_dump(mode='json', exclude_unset=True)
        )
        return response.data[0] if response.data else None

    def delete(self, user_id: UUID, habit_id: UUID):
        response = self.db.delete(
            self.table_name, 
            filters={"id": str(habit_id), "user_id": str(user_id)}
        )
        return len(response.data) > 0 if response.data else False
