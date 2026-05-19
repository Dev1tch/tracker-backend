from app.core.config import settings
from app.core.supabase_client import SupabaseClient
from app.services.board_service import BoardService
from app.services.category_service import CategoryService
from app.services.email import BrevoEmailSender, EmailSender
from app.services.habit_service import HabitService
from app.services.log_service import LogService
from app.services.media_service import MediaService
from app.services.notes_service import NotesService
from app.services.task_service import TaskService
from app.services.user_notification_service import UserNotificationService
from app.services.user_service import UserService


class ServiceProvider:
    """Central factory for creating service instances."""

    _supabase_client = SupabaseClient()
    _email_sender: EmailSender = BrevoEmailSender(
        api_key=settings.BREVO_EMAIL_SENDER_API_KEY
    )

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
    def get_notes_service() -> NotesService:
        return NotesService(ServiceProvider.get_supabase_client())

    @staticmethod
    def get_board_service() -> BoardService:
        return BoardService(ServiceProvider.get_supabase_client())

    @staticmethod
    def get_media_service() -> MediaService:
        return MediaService(ServiceProvider.get_supabase_client())

    @staticmethod
    def get_user_service() -> UserService:
        return UserService(ServiceProvider.get_supabase_client())

    @staticmethod
    def get_email_sender() -> EmailSender:
        return ServiceProvider._email_sender

    @staticmethod
    def get_user_notification_service() -> UserNotificationService:
        return UserNotificationService(
            email_sender=ServiceProvider.get_email_sender(),
            sender_name=settings.EMAIL_SENDER_NAME,
            sender_email=settings.EMAIL_SENDER_EMAIL,
            admin_notification_email=settings.ADMIN_NOTIFICATION_EMAIL,
        )
