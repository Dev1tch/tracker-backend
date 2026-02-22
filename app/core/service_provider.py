from app.services.category_service import CategoryService
from app.services.habit_service import HabitService
from app.services.log_service import LogService

class ServiceProvider:
    """Central factory for creating service instances."""
    @staticmethod
    def get_category_service() -> CategoryService:
        return CategoryService()

    @staticmethod
    def get_habit_service() -> HabitService:
        return HabitService()

    @staticmethod
    def get_log_service() -> LogService:
        return LogService()
