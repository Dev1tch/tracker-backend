from app.core.supabase_client import SupabaseClient
from app.services.category_service import CategoryService
from app.services.habit_service import HabitService
from app.services.log_service import LogService
from app.services.task_service import TaskService
from app.services.user_service import UserService


class ServiceProvider:
    """Central factory for creating service instances."""

    _supabase_client = SupabaseClient()

    @staticmethod
    def get_supabase_client() -> SupabaseClient:
        return ServiceProvider._supabase_client

    @staticmethod
    def get_category_service() -> CategoryService:
        return CategoryService(ServiceProvider.get_supabase_client())

    @staticmethod
    def get_habit_service() -> HabitService:
        return HabitService(ServiceProvider.get_supabase_client())

    @staticmethod
    def get_log_service() -> LogService:
        return LogService(ServiceProvider.get_supabase_client())

    @staticmethod
    def get_task_service() -> TaskService:
        return TaskService(ServiceProvider.get_supabase_client())

    @staticmethod
    def get_user_service() -> UserService:
        return UserService(ServiceProvider.get_supabase_client())
