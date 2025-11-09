"""Email notification channel with template support."""

from __future__ import annotations

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List

import aiosmtplib
from loguru import logger

from app.config import get_settings
from app.services.notifications.base import NotificationChannel


class EmailNotificationChannel(NotificationChannel):
    name = "email"

    def __init__(self) -> None:
        self._settings = get_settings().email

    async def send(self, payload: Dict[str, Any]) -> None:
        recipients: List[str] = payload.get("recipients", [])
        if not recipients:
            logger.warning("Email send skipped: no recipients")
            return
            
        subject = payload.get("subject") or self._settings.template.subject_template
        html_body = payload.get("html") or payload.get("body", "")
        
        if not html_body:
            logger.warning("Email send skipped: no content")
            return
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self._settings.sender
        msg["To"] = ", ".join(recipients)
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        
        try:
            async with aiosmtplib.SMTP(
                hostname=self._settings.smtp_host,
                port=self._settings.smtp_port,
                use_tls=self._settings.use_tls,
                timeout=30
            ) as smtp:
                if self._settings.username and self._settings.password:
                    await smtp.login(self._settings.username, self._settings.password)
                await smtp.send_message(msg)
                logger.info(f"Email sent to {len(recipients)} recipients")
        except Exception as exc:
            logger.error(f"Failed to send email: {exc}")
            raise
