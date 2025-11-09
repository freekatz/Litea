"""Scheduler service wrapping APScheduler."""

from __future__ import annotations

from datetime import datetime
from typing import Awaitable, Callable, Dict

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from app.config import get_settings


class SchedulerService:
    """Manage recurring task execution."""

    def __init__(self) -> None:
        config = get_settings().scheduler
        self._scheduler = AsyncIOScheduler(timezone=config.timezone)
        self._scheduler.start()
        logger.info("Scheduler started with timezone {}", config.timezone)

    def add_task(
        self,
        task_id: int,
        cron_expression: str,
        callback: Callable[[], Awaitable[None]],
    ) -> None:
        trigger = CronTrigger.from_crontab(cron_expression)
        self._scheduler.add_job(callback, trigger=trigger, id=str(task_id), name=f"task-{task_id}")
        logger.info("Scheduled task {} with cron {}", task_id, cron_expression)

    def run_daily_at(
        self,
        task_id: int,
        hour: int,
        callback: Callable[[], Awaitable[None]],
        timezone: str | None = None,
    ) -> None:
        tz = timezone or get_settings().scheduler.timezone
        trigger = CronTrigger(hour=hour, timezone=tz)
        self._scheduler.add_job(callback, trigger=trigger, id=str(task_id), name=f"task-{task_id}")
        logger.info("Scheduled task {} daily at {} {}", task_id, hour, tz)

    def cancel(self, task_id: int) -> None:
        job_id = str(task_id)
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)
            logger.info("Cancelled scheduled task {}", task_id)

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("Scheduler shutdown at {}", datetime.utcnow())
