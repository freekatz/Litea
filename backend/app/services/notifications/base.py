"""Notification channel base interface."""

from __future__ import annotations

from typing import Any, Dict, Protocol


class NotificationChannel(Protocol):
    name: str

    async def send(self, payload: Dict[str, Any]) -> None:
        ...
