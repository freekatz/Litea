"""Route registration helpers."""

from aiohttp import web

from .analytics import setup_analytics_routes
from .auth import setup_routes as setup_auth_routes
from .config import setup_config_routes
from .documents import setup_document_routes
from .sources import setup_source_routes
from .tasks import setup_task_routes


async def setup_routes(app: web.Application) -> None:
    setup_auth_routes(app)
    setup_task_routes(app)
    setup_source_routes(app)
    setup_document_routes(app)
    setup_config_routes(app)
    setup_analytics_routes(app)
