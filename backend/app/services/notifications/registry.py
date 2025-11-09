"""Notification registry."""

from __future__ import annotations

from typing import Dict, Type

from app.services.notifications.email_channel import EmailNotificationChannel


class NotificationRegistry:
    """Store available notification channels."""

    _channels: Dict[str, Type] = {EmailNotificationChannel.name: EmailNotificationChannel}

    def __init__(self) -> None:
        self._instances: Dict[str, object] = {}

    def get(self, name: str):
        if name not in self._channels:
            raise KeyError(f"Notification channel '{name}' is not registered")
        if name not in self._instances:
            self._instances[name] = self._channels[name]()
        return self._instances[name]

    def list_channels(self) -> Dict[str, object]:
        for key in self._channels:
            self.get(key)
        return dict(self._instances)
