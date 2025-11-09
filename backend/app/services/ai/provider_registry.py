"""AI provider registry supporting multiple vendors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

import httpx

from app.config import AIProviderConfig, get_settings


@dataclass
class ProviderClient:
    name: str
    model: str | None
    base_url: str | None
    api_key: str | None
    extra: Dict[str, Any]

    async def request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send a generic JSON request to the provider."""

        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        
        # Build full URL - if base_url already ends with /v1, use /chat/completions
        # otherwise use /v1/chat/completions
        endpoint = "/chat/completions" if self.base_url and self.base_url.rstrip("/").endswith("/v1") else "/v1/chat/completions"
        
        async with httpx.AsyncClient(base_url=self.base_url or "", timeout=60) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()


class ProviderRegistry:
    """Registry for AI providers."""

    def __init__(self) -> None:
        self._clients: Dict[str, ProviderClient] = {}
        self._load_from_config()

    def _load_from_config(self) -> None:
        settings = get_settings()
        for key, provider in settings.ai.providers.items():
            self._clients[key] = self._build_client(provider)

    def _build_client(self, provider: AIProviderConfig) -> ProviderClient:
        return ProviderClient(
            name=provider.name,
            model=provider.model,
            base_url=provider.base_url,
            api_key=provider.api_key,
            extra=provider.extra,
        )

    def get(self, provider_name: str | None = None) -> ProviderClient:
        settings = get_settings()
        name = provider_name or settings.ai.default_provider
        if name not in self._clients:
            raise KeyError(f"AI provider '{name}' is not configured")
        return self._clients[name]

    def reload(self) -> None:
        self._clients.clear()
        self._load_from_config()
