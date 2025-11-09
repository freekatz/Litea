"""Application entry point."""

from __future__ import annotations

import logging

from aiohttp import web
import aiohttp_cors
from sqlalchemy import inspect

from app.api.routes import setup_routes
from app.config import get_settings
from app.db.session import async_session, get_engine
from app.db.base import Base
from app.logging_config import setup_logging
from app.services.scheduler import TaskScheduler

logger = logging.getLogger(__name__)


async def ensure_database() -> None:
    """Ensure database tables exist, create if missing."""
    engine = get_engine()
    
    async with engine.connect() as conn:
        # Check if tables exist
        def check_tables(connection):
            inspector = inspect(connection)
            existing_tables = set(inspector.get_table_names())
            expected_tables = set(Base.metadata.tables.keys())
            return existing_tables, expected_tables
        
        existing_tables, expected_tables = await conn.run_sync(check_tables)
        missing_tables = expected_tables - existing_tables
        
        if missing_tables:
            logger.warning(f"Missing tables detected: {missing_tables}")
            logger.info("Creating missing database tables...")
            
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info(f"Created {len(missing_tables)} missing tables")


async def create_app() -> web.Application:
    settings = get_settings()
    setup_logging(settings.log_level)
    
    # Ensure database is ready
    await ensure_database()
    
    # Import auth middleware
    from app.api.routes.auth import auth_middleware
    
    app = web.Application(middlewares=[auth_middleware])
    
    # Configure CORS
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })
    
    await setup_routes(app)
    
    # Add CORS to all routes
    for route in list(app.router.routes()):
        if not isinstance(route.resource, web.StaticResource):
            cors.add(route)
    
    # Initialize and start task scheduler
    scheduler = TaskScheduler(async_session)
    app['scheduler'] = scheduler
    
    async def start_scheduler(app):
        scheduler.start()
        logger.info("Task scheduler started")
        
        # Load all active tasks into scheduler
        from app.db.models import Task
        from sqlalchemy import select
        
        async with async_session() as session:
            result = await session.execute(
                select(Task).where(Task.status == 'active')
            )
            active_tasks = result.scalars().all()
            
            for task in active_tasks:
                try:
                    await scheduler.schedule_task(task)
                    # Update next_run_at
                    task.next_run_at = scheduler.get_next_run_time(task)
                    await session.commit()
                    logger.info(f"Scheduled active task {task.id} ({task.name})")
                except Exception as e:
                    logger.error(f"Failed to schedule task {task.id}: {e}")
    
    async def stop_scheduler(app):
        scheduler.shutdown()
        logger.info("Task scheduler stopped")
    
    app.on_startup.append(start_scheduler)
    app.on_cleanup.append(stop_scheduler)
    
    return app


def main() -> None:
    web.run_app(create_app(), port=6060)


if __name__ == "__main__":
    main()
