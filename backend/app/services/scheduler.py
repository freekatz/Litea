"""
Dynamic task scheduler with per-task scheduling.

Each task is scheduled individually at its specific hour:minute time.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from app.db.models import Task, TaskRun
from app.services.tasks.task_runner import TaskRunner

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Dynamic task scheduler with per-task scheduling."""

    def __init__(self, db_session_factory):
        """
        Initialize scheduler.
        
        Args:
            db_session_factory: Factory function that returns an async database session
        """
        self.db_session_factory = db_session_factory
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone('Asia/Shanghai'))
        self.running_tasks = set()  # Track currently running tasks to avoid duplicates
        
    def start(self):
        """Start the scheduler."""
        self.scheduler.start()
        logger.info("Task scheduler started")
        
    def shutdown(self):
        """Shutdown the scheduler."""
        self.scheduler.shutdown()
        logger.info("Task scheduler shut down")
    
    async def schedule_task(self, task: Task):
        """
        Schedule a task to run at its specified time.
        
        Args:
            task: Task to schedule
        """
        job_id = f'task_{task.id}'
        
        # Remove existing job if any
        try:
            self.scheduler.remove_job(job_id)
        except:
            pass
        
        # Add new job
        self.scheduler.add_job(
            self._execute_task,
            trigger=CronTrigger(
                hour=task.run_at_hour,
                minute=task.run_at_minute,
                timezone=task.run_timezone or 'Asia/Shanghai'
            ),
            id=job_id,
            args=[task.id],
            replace_existing=True
        )
        
        logger.info(f"Scheduled task {task.id} ({task.name}) at {task.run_at_hour:02d}:{task.run_at_minute:02d}")
    
    async def remove_task(self, task_id: int):
        """
        Remove a task from the schedule.
        
        Args:
            task_id: ID of task to remove
        """
        job_id = f'task_{task_id}'
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed task {task_id} from schedule")
        except Exception as e:
            logger.warning(f"Failed to remove task {task_id}: {e}")
    
    async def reschedule_task(self, task: Task):
        """
        Reschedule a task (remove and re-add).
        
        Args:
            task: Task to reschedule
        """
        await self.remove_task(task.id)
        await self.schedule_task(task)
    
    def get_next_run_time(self, task: Task) -> Optional[datetime]:
        """
        Get the next scheduled run time for a task.
        Always returns tomorrow's scheduled time to ensure daily execution pattern.
        
        Args:
            task: Task to check
            
        Returns:
            Next run time (always tomorrow at scheduled time)
        """
        # Always calculate for tomorrow to ensure consistent daily pattern
        tz = pytz.timezone(task.run_timezone or 'Asia/Shanghai')
        now = datetime.now(tz)
        
        # Create time for tomorrow
        next_run = now.replace(
            hour=task.run_at_hour,
            minute=task.run_at_minute,
            second=0,
            microsecond=0
        ) + timedelta(days=1)  # Always schedule for tomorrow
        
        return next_run
    
    async def _execute_task(self, task_id: int):
        """
        Execute a scheduled task.
        
        Args:
            task_id: ID of task to execute
        """
        # Skip if already running
        if task_id in self.running_tasks:
            logger.info(f"Task {task_id} is already running, skipping")
            return
        
        self.running_tasks.add(task_id)
        
        try:
            async with self.db_session_factory() as session:
                # Fetch task
                result = await session.execute(
                    select(Task).where(Task.id == task_id)
                )
                task = result.scalar_one_or_none()
                
                if not task:
                    logger.error(f"Task {task_id} not found")
                    return
                
                if task.status != 'active':
                    logger.info(f"Task {task_id} is not active, skipping execution")
                    return
                
                logger.info(f"Starting scheduled execution of task {task_id} ({task.name})")
                
                # Create TaskRun record
                tz = pytz.timezone(task.run_timezone or 'Asia/Shanghai')
                now = datetime.now(tz)
                
                task_run = TaskRun(
                    task_id=task.id,
                    status='running',
                    started_at=now,
                    retrieved_count=0,
                    filtered_count=0
                )
                session.add(task_run)
                await session.commit()
                await session.refresh(task_run)
                
                # Update task's last_run_at and next_run_at
                task.last_run_at = now
                task.next_run_at = self.get_next_run_time(task)
                await session.commit()
                
                # Execute task
                runner = TaskRunner()
                await runner.run_with_existing_run(session, task, task_run)
                
                logger.info(f"Completed scheduled execution of task {task_id}")
                
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}", exc_info=True)
        finally:
            self.running_tasks.discard(task_id)
