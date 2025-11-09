"""Retrieval source routes."""

from __future__ import annotations

from aiohttp import web

from app.services.retrieval.registry import RetrievalRegistry


def setup_source_routes(app: web.Application) -> None:
    app.router.add_get("/api/sources", list_sources)


async def list_sources(request: web.Request) -> web.Response:
    registry = RetrievalRegistry()
    sources = [
        {
            "name": name,
            "description": getattr(instance, "description", ""),
        }
        for name, instance in registry.list_sources().items()
    ]
    return web.json_response({"data": sources})
