"""Configuration routes for frontend."""

from __future__ import annotations

from aiohttp import web

from app.config import get_settings


def setup_config_routes(app: web.Application) -> None:
    app.router.add_get("/api/config", get_config)


async def get_config(request: web.Request) -> web.Response:
    settings = get_settings()
    payload = {
        "environment": settings.environment,
        "log_level": settings.log_level,
        "ai": {
            "default_provider": settings.ai.default_provider,
            "providers": {
                name: {
                    "model": provider.model,
                    "base_url": provider.base_url,
                    "name": provider.name,
                    "extra": provider.extra,
                }
                for name, provider in settings.ai.providers.items()
            },
            "keyword_model": settings.ai.keyword_model,
            "filter_model": settings.ai.filter_model,
            "summary_model": settings.ai.summary_model,
        },
        "email": settings.email.model_dump(),
        "scheduler": settings.scheduler.model_dump(),
        "zotero": {
            "library_type": settings.zotero.library_type,
        },
    }
    return web.json_response(payload)
