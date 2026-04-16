from __future__ import annotations

from typing import Any, Dict, List, Optional

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from app.services.email.email_sender import (
    EmailAddress,
    EmailMessage,
    EmailSendError,
    EmailSendResult,
    EmailSender,
)


class BrevoEmailSender(EmailSender):
    """Brevo (Sendinblue) transactional email sender.

    Standalone implementation. The only constructor argument is the API key;
    no application-wide configuration, database, or framework is touched.
    """

    PROVIDER_NAME = "brevo"

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("BrevoEmailSender requires a non-empty api_key.")

        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = api_key

        self._api_client = sib_api_v3_sdk.ApiClient(configuration)
        self._api = sib_api_v3_sdk.TransactionalEmailsApi(self._api_client)

    def send(self, message: EmailMessage) -> EmailSendResult:
        payload = sib_api_v3_sdk.SendSmtpEmail(
            sender=self._format_address(message.sender),
            to=self._format_address_list(message.to),
            cc=self._format_address_list(message.cc) or None,
            bcc=self._format_address_list(message.bcc) or None,
            reply_to=self._format_address(message.reply_to) if message.reply_to else None,
            subject=message.subject,
            html_content=message.html_content,
            text_content=message.text_content,
        )

        try:
            response = self._api.send_transac_email(payload)
        except ApiException as exc:
            raise EmailSendError(
                f"Brevo rejected the email (status={exc.status}): {exc.reason}"
            ) from exc

        return EmailSendResult(
            message_id=getattr(response, "message_id", None),
            provider=self.PROVIDER_NAME,
            raw=response,
        )

    @staticmethod
    def _format_address(address: EmailAddress) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"email": address.email}
        if address.name:
            payload["name"] = address.name
        return payload

    @classmethod
    def _format_address_list(
        cls, addresses: Optional[List[EmailAddress]]
    ) -> List[Dict[str, Any]]:
        if not addresses:
            return []
        return [cls._format_address(addr) for addr in addresses]
