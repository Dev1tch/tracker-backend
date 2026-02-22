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
        # Check if log already exists for this date
        existing = supabase.read(
            self.table_name, 
            filters={"habit_id": str(log_data.habit_id), "date": str(log_data.date)}
        )
        
        if existing.data:
            # Update the existing log instead of creating a new one
            response = supabase.update(
                self.table_name,
                filters={"id": existing.data[0]["id"]},
                data=log_data.model_dump(mode='json')
            )
            return response.data[0] if response.data else None
            
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

    def get_logs_by_timeframe(self, user_id: UUID, start_date: date, end_date: date, habit_ids: Optional[List[UUID]] = None):
        # 1. Fetch habits for the user
        habit_query = supabase.client.table("habits").select("*").eq("user_id", str(user_id))
        if habit_ids:
            str_habit_ids = [str(hid) for hid in habit_ids]
            habit_query = habit_query.in_("id", str_habit_ids)
        habits = habit_query.execute().data

        if not habits:
            return []

        # 2. Fetch logs for these habits in the timeframe
        fetched_habit_ids = [h["id"] for h in habits]
        log_query = supabase.client.table(self.table_name).select("*")
        log_query = log_query.in_("habit_id", fetched_habit_ids)
        log_query = log_query.gte("date", str(start_date))
        log_query = log_query.lte("date", str(end_date))
        logs = log_query.execute().data

        # 3. Group logs by habit_id
        from collections import defaultdict
        logs_by_habit = defaultdict(list)
        for log in logs:
            logs_by_habit[log["habit_id"]].append(log)

        # 4. Attach logs to habits
        for habit in habits:
            habit["logs"] = logs_by_habit.get(habit["id"], [])
            
        return habits

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
