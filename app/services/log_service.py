from typing import List, Optional
from uuid import UUID
from datetime import date
from app.core.supabase_client import supabase
from app.schemas.habit import HabitLogCreate, HabitLogUpdate

class LogService:
    def __init__(self):
        self.table_name = "habit_logs"

    def create(self, log_data: HabitLogCreate):
        response = supabase.create(self.table_name, log_data.model_dump(mode='json'))
        return response.data[0] if response.data else None

    def get_logs(self, habit_id: Optional[UUID] = None, day: Optional[date] = None):
        filters = {}
        if habit_id:
            filters["habit_id"] = str(habit_id)
        if day:
            filters["date"] = day
        response = supabase.read(self.table_name, filters=filters if filters else None)
        return response.data

    def update(self, log_id: UUID, log_update: HabitLogUpdate):
        response = supabase.update(
            self.table_name, 
            filters={"id": str(log_id)}, 
            data=log_update.model_dump(mode='json', exclude_unset=True)
        )
        return response.data[0] if response.data else None

    def delete(self, log_id: UUID):
        response = supabase.delete(self.table_name, filters={"id": str(log_id)})
        return len(response.data) > 0 if response.data else False

