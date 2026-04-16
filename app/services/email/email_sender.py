from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


class EmailSendError(Exception):
    """Raised when an email fails to be delivered by the underlying provider."""


@dataclass(frozen=True)
class EmailAddress:
    email: str
    name: Optional[str] = None


@dataclass
class EmailMessage:
    sender: EmailAddress
    to: List[EmailAddress]
    subject: str
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    cc: List[EmailAddress] = field(default_factory=list)
    bcc: List[EmailAddress] = field(default_factory=list)
    reply_to: Optional[EmailAddress] = None

    def __post_init__(self) -> None:
        if not self.to:
            raise ValueError("EmailMessage requires at least one 'to' recipient.")
        if not self.html_content and not self.text_content:
            raise ValueError("EmailMessage requires either html_content or text_content.")
        if not self.subject:
            raise ValueError("EmailMessage requires a subject.")


@dataclass
class EmailSendResult:
    message_id: Optional[str]
    provider: str
    raw: object = None


class EmailSender(ABC):
    """Abstract strategy for delivering transactional email.

    Implementations must be self-contained and free of application-level
    dependencies so the interface can be swapped for any provider.
    """

    @abstractmethod
    def send(self, message: EmailMessage) -> EmailSendResult:
        raise NotImplementedError
