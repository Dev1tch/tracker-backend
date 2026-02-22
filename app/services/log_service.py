from typing import List, Optional
from uuid import UUID
from datetime import date
from app.core.supabase_client import supabase
from app.schemas.habit import HabitLogCreate, HabitLogUpdate

class LogService:
    def __init__(self):
        self.table_name = "habit_logs"

    def create(self, log_data: HabitLogCreate):
        # Habit ownership is checked in the router before calling this
        response = supabase.create(self.table_name, log_data.model_dump(mode='json'))
        return response.data[0] if response.data else None

    def get_logs(self, user_id: UUID, habit_id: Optional[UUID] = None, day: Optional[date] = None):
        # Filter logs by habits owned by the user using an inner join
        # Note: We use direct client for complex join filtering
        query = supabase.client.table(self.table_name).select("*, habits!inner(user_id)")
        query = query.eq("habits.user_id", str(user_id))
        
        if habit_id:
            query = query.eq("habit_id", str(habit_id))
        if day:
            query = query.eq("date", str(day))
        
        response = query.execute()
        return response.data

    def update(self, log_id: UUID, log_update: HabitLogUpdate):
        # Ownership check is done in the router
        response = supabase.update(
            self.table_name, 
            filters={"id": str(log_id)}, 
            data=log_update.model_dump(mode='json', exclude_unset=True)
        )
        return response.data[0] if response.data else None

    def delete(self, log_id: UUID):
        # Ownership check is done in the router
        response = supabase.delete(self.table_name, filters={"id": str(log_id)})
        return len(response.data) > 0 if response.data else False

    def get_by_id(self, log_id: UUID):
        """Fetch a log with its habit info to check ownership."""
        response = supabase.client.table(self.table_name)\
            .select("*, habits!inner(user_id)")\
            .eq("id", str(log_id))\
            .execute()
        return response.data[0] if response.data else None
