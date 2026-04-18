import logging
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Optional

from app.services.email import (
    EmailAddress,
    EmailMessage,
    EmailSendError,
    EmailSender,
)

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "email-templates"
_WELCOME_TEMPLATE_PATH = _TEMPLATES_DIR / "welcome-email.html"
_SIGNUP_NOTIFICATION_TEMPLATE_PATH = _TEMPLATES_DIR / "signup-notification.html"


@lru_cache(maxsize=None)
def _load_template(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class UserNotificationService:
    """Application-level notifications tied to user lifecycle events.

    Depends only on the abstract EmailSender; the concrete provider is
    injected by the ServiceProvider.
    """

    def __init__(
        self,
        email_sender: EmailSender,
        sender_name: str,
        sender_email: str,
        admin_notification_email: Optional[str] = None,
    ) -> None:
        self._email_sender = email_sender
        self._from = EmailAddress(email=sender_email, name=sender_name)
        self._admin_notification_email = admin_notification_email

    def send_welcome_email(
        self,
        recipient_email: str,
        first_name: Optional[str] = None,
    ) -> None:
        """Send the welcome email. Failures are logged, not raised."""
        display_name = (first_name or "there").strip() or "there"

        html_content = _load_template(_WELCOME_TEMPLATE_PATH).replace(
            "{{firstName}}", display_name
        )
        text_content = (
            f"Welcome to Life Tracker, {display_name}.\n\n"
            "Your account is live. Habits, tasks, and calendar now sit inside "
            "the same focused space.\n\n"
            "Open Life Tracker: https://tracker-six-gules.vercel.app\n\n"
            "If you did not create this account, please ignore this email."
        )

        message = EmailMessage(
            sender=self._from,
            to=[EmailAddress(email=recipient_email)],
            subject="Welcome to Life Tracker",
            html_content=html_content,
            text_content=text_content,
        )

        try:
            self._email_sender.send(message)
        except EmailSendError:
            logger.exception(
                "Failed to send welcome email to %s", recipient_email
            )

    def send_signup_notification(
        self,
        user_email: str,
        first_name: Optional[str] = None,
    ) -> None:
        """Notify the admin address that a new user has signed up."""
        if not self._admin_notification_email:
            return

        display_name = (first_name or "Unknown").strip() or "Unknown"
        signup_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        html_content = (
            _load_template(_SIGNUP_NOTIFICATION_TEMPLATE_PATH)
            .replace("{{firstName}}", display_name)
            .replace("{{userEmail}}", user_email)
            .replace("{{signupTime}}", signup_time)
        )
        text_content = (
            "New signup on Life Tracker.\n\n"
            f"Name: {display_name}\n"
            f"Email: {user_email}\n"
            f"Signed up: {signup_time}\n\n"
            "Open Life Tracker: https://tracker-six-gules.vercel.app"
        )

        message = EmailMessage(
            sender=self._from,
            to=[EmailAddress(email=self._admin_notification_email)],
            subject=f"New Life Tracker signup: {display_name}",
            html_content=html_content,
            text_content=text_content,
        )

        try:
            self._email_sender.send(message)
        except EmailSendError:
            logger.exception(
                "Failed to send signup notification for %s", user_email
            )
