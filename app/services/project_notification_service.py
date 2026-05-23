import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

from app.services.email import EmailAddress, EmailMessage, EmailSendError, EmailSender

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "email-templates"
_PROJECT_INVITE_TEMPLATE_PATH = _TEMPLATES_DIR / "project-invite.html"


@lru_cache(maxsize=None)
def _load_template(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class ProjectNotificationService:
    def __init__(
        self,
        email_sender: EmailSender,
        sender_name: str,
        sender_email: str,
        app_url: str,
    ) -> None:
        self._email_sender = email_sender
        self._from = EmailAddress(email=sender_email, name=sender_name)
        self._app_url = app_url.rstrip("/")

    def send_project_invite_email(
        self,
        recipient_email: str,
        project_name: str,
        inviter_name: Optional[str] = None,
    ) -> None:
        display_inviter = (inviter_name or "A teammate").strip() or "A teammate"
        project_title = project_name.strip() or "a project"
        project_url = f"{self._app_url}/?tab=tasks"

        html_content = (
            _load_template(_PROJECT_INVITE_TEMPLATE_PATH)
            .replace("{{projectName}}", project_title)
            .replace("{{inviterName}}", display_inviter)
            .replace("{{projectUrl}}", project_url)
        )
        text_content = (
            f"{display_inviter} invited you to join {project_title} on Life Tracker.\n\n"
            f"Open the project: {project_url}\n\n"
            "If you did not expect this invitation, you can ignore this email."
        )

        message = EmailMessage(
            sender=self._from,
            to=[EmailAddress(email=recipient_email)],
            subject=f"You're invited to {project_title}",
            html_content=html_content,
            text_content=text_content,
        )

        try:
            self._email_sender.send(message)
        except EmailSendError:
            logger.exception(
                "Failed to send project invite email to %s", recipient_email
            )
