"""Task management routes."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Dict

import pytz
from aiohttp import web
from loguru import logger
from pydantic import ValidationError

from app.db import async_session, models
from app.db.models import TaskRun
from app.db.repositories import TaskRepository
from app.schemas.task import TaskCreate, TaskResponse, TaskRunResponse, TaskUpdate
from app.services.ai.keyword_extraction_service import KeywordExtractionService
from app.services.tasks.task_runner import TaskRunner
from sqlalchemy import select


def _serialize_task(task: models.Task) -> Dict[str, Any]:
    return TaskResponse(
        id=task.id,
        name=task.name,
        prompt=task.prompt,
        run_at_hour=task.run_at_hour,
        run_at_minute=task.run_at_minute,
        run_timezone=task.run_timezone,
        keywords=[{"keyword": kw.keyword, "is_user_defined": kw.is_user_defined} for kw in task.keywords],
        sources=[{"source_name": ts.source.name, "parameters": ts.parameters} for ts in task.sources],
        notification=task.notification_config,
        ai_config=task.ai_config,
        filter_config=task.filter_config,
        summary_config=task.summary_config,
        status=task.status,
        created_at=task.created_at,
        updated_at=task.updated_at,
        last_run_at=task.last_run_at,
        next_run_at=task.next_run_at,
    ).model_dump(mode="json")


async def list_tasks(request: web.Request) -> web.Response:
    """List active (non-archived) tasks."""
    async with async_session() as session:
        repo = TaskRepository(session)
        tasks = await repo.list_tasks(include_archived=False)
        data = [_serialize_task(task) for task in tasks]
        return web.json_response({"data": data})


async def list_archived_tasks(request: web.Request) -> web.Response:
    """List archived tasks."""
    async with async_session() as session:
        repo = TaskRepository(session)
        tasks = await repo.list_archived_tasks()
        data = [_serialize_task(task) for task in tasks]
        return web.json_response({"data": data})


async def create_task(request: web.Request) -> web.Response:
    payload = await request.json()
    try:
        schema = TaskCreate(**payload)
    except ValidationError as exc:
        return web.json_response({"error": exc.errors()}, status=400)
    async with async_session() as session:
        repo = TaskRepository(session)
        task = models.Task(
            name=schema.name,
            prompt=schema.prompt,
            run_at_hour=schema.run_at_hour,
            run_at_minute=schema.run_at_minute,
            run_timezone=schema.run_timezone or "Asia/Shanghai",
            notification_config=schema.notification.model_dump(),
            ai_config=schema.ai_config.model_dump(),
            filter_config=schema.filter_config.model_dump(),
            summary_config=schema.summary_config.model_dump(),
            status="inactive"  # New tasks default to inactive
        )
        
        # Deduplicate keywords (case-insensitive)
        seen_keywords = set()
        keywords = []
        for item in schema.keywords:
            keyword_lower = item.keyword.lower()
            if keyword_lower not in seen_keywords:
                seen_keywords.add(keyword_lower)
                keywords.append(models.TaskKeyword(keyword=item.keyword, is_user_defined=item.is_user_defined))
        
        sources = []
        for src in schema.sources:
            result = await session.execute(select(models.RetrievalSource).where(models.RetrievalSource.name == src.source_name))
            source_model = result.scalar_one_or_none()
            if not source_model:
                source_model = models.RetrievalSource(name=src.source_name)
                session.add(source_model)
                await session.flush()
                await session.refresh(source_model)  # Ensure ID is populated
            sources.append(models.TaskSource(parameters=src.parameters, source_id=source_model.id, source=source_model))
        task = await repo.create_task(task, keywords, sources)
        await session.commit()
        # Reload task with relationships
        task = await repo.get_task(task.id)
        return web.json_response({"data": _serialize_task(task)}, status=201)


async def get_task(request: web.Request) -> web.Response:
    task_id = int(request.match_info["task_id"])
    async with async_session() as session:
        repo = TaskRepository(session)
        task = await repo.get_task(task_id)
        if not task:
            return web.json_response({"error": "task not found"}, status=404)
        return web.json_response({"data": _serialize_task(task)})


async def update_task(request: web.Request) -> web.Response:
    task_id = int(request.match_info["task_id"])
    payload = await request.json()
    payload["id"] = task_id
    try:
        schema = TaskUpdate(**payload)
    except ValidationError as exc:
        return web.json_response({"error": exc.errors()}, status=400)
    async with async_session() as session:
        repo = TaskRepository(session)
        task = await repo.get_task(task_id)
        if not task:
            return web.json_response({"error": "task not found"}, status=404)
        task.name = schema.name
        task.prompt = schema.prompt
        task.run_at_hour = schema.run_at_hour
        task.run_at_minute = schema.run_at_minute
        task.run_timezone = schema.run_timezone or task.run_timezone
        task.notification_config = schema.notification.model_dump()
        task.ai_config = schema.ai_config.model_dump()
        task.filter_config = schema.filter_config.model_dump()
        task.summary_config = schema.summary_config.model_dump()
        task.status = schema.status or task.status
        
        # Update keywords with deduplication
        task.keywords.clear()
        await session.flush()  # Flush delete operations first to avoid unique constraint conflicts
        seen_keywords = set()
        for kw in schema.keywords:
            # Deduplicate keywords (case-insensitive)
            keyword_lower = kw.keyword.lower()
            if keyword_lower not in seen_keywords:
                seen_keywords.add(keyword_lower)
                task.keywords.append(models.TaskKeyword(keyword=kw.keyword, is_user_defined=kw.is_user_defined))
        
        # Update sources
        task.sources.clear()
        await session.flush()  # Flush delete operations first
        for src in schema.sources:
            result = await session.execute(select(models.RetrievalSource).where(models.RetrievalSource.name == src.source_name))
            db_source = result.scalar_one_or_none()
            if not db_source:
                db_source = models.RetrievalSource(name=src.source_name)
                session.add(db_source)
                await session.flush()
                await session.refresh(db_source)  # Ensure ID is populated
            task.sources.append(models.TaskSource(parameters=src.parameters, source_id=db_source.id, source=db_source))
        await repo.update_task(task)
        await session.commit()
        return web.json_response({"data": _serialize_task(task)})


async def delete_task(request: web.Request) -> web.Response:
    """
    Permanently delete a task and all its associated data.
    - Deletes the task and all related documents
    - Stops the task if it's active
    - Cannot be undone
    """
    task_id = int(request.match_info["task_id"])
    scheduler = request.app.get('scheduler')
    
    async with async_session() as session:
        repo = TaskRepository(session)
        task = await repo.get_task(task_id)
        if not task:
            return web.json_response(status=204)
        
        # Stop task if active
        if task.status == "active":
            task.status = "inactive"
            task.next_run_at = None
            
            # Remove from scheduler
            if scheduler:
                await scheduler.remove_task(task_id)
        
        # Delete the task and all its documents
        deleted_docs_count = await repo.delete_task_with_documents(task_id)
        await session.commit()
        
        logger.info(f"Deleted task {task_id} ({task.name}) and {deleted_docs_count} associated documents")
        
        return web.json_response(status=204)


async def archive_task(request: web.Request) -> web.Response:
    """
    Archive a task without deleting it.
    - Sets is_archived = True
    - Stops the task if it's active
    - Preserves all task data and documents
    - Archived tasks won't appear in normal task list
    """
    task_id = int(request.match_info["task_id"])
    scheduler = request.app.get('scheduler')
    
    async with async_session() as session:
        repo = TaskRepository(session)
        task = await repo.get_task(task_id)
        if not task:
            return web.json_response({"error": "Task not found"}, status=404)
        
        # Stop task if active
        if task.status == "active":
            task.status = "inactive"
            task.next_run_at = None
            
            # Remove from scheduler
            if scheduler:
                await scheduler.remove_task(task_id)
        
        # Archive the task
        task.is_archived = True
        await session.commit()
        
        logger.info(f"Archived task {task_id} ({task.name})")
        
        return web.json_response({"data": _serialize_task(task)})


async def run_task(request: web.Request) -> web.Response:
    """Start a task execution in the background."""
    task_id = int(request.match_info["task_id"])
    async with async_session() as session:
        repo = TaskRepository(session)
        task = await repo.get_task(task_id)
        if not task:
            return web.json_response({"error": "task not found"}, status=404)
        
        # Create a task run record immediately with 'running' status
        run = models.TaskRun(task_id=task.id, status="running")
        await repo.add_run(run)
        await session.commit()
        
        # Start the task execution in the background
        request.app.loop.create_task(_run_task_background(task_id, run.id))
        
        # Return immediately with the run info
        run_schema = TaskRunResponse(
            id=run.id,
            task_id=run.task_id,
            status=run.status,
            started_at=run.started_at,
            finished_at=run.finished_at,
            retrieved_count=run.retrieved_count,
            filtered_count=run.filtered_count,
            summary=run.summary,
        )
        return web.json_response({"data": run_schema.model_dump(mode="json")}, status=202)


async def _run_task_background(task_id: int, run_id: int) -> None:
    """Execute task in the background and update the run record."""
    try:
        async with async_session() as session:
            repo = TaskRepository(session)
            task = await repo.get_task(task_id)
            if not task:
                logger.error(f"Task {task_id} not found for background execution")
                return
            
            # Get the run record
            runs = await repo.list_runs(task_id, limit=1)
            run = next((r for r in runs if r.id == run_id), None)
            if not run:
                logger.error(f"Run {run_id} not found for task {task_id}")
                return
            
            # Execute the task
            runner = TaskRunner()
            await runner.run_with_existing_run(session, task, run)
            await session.commit()
            
            logger.info(f"Task {task_id} run {run_id} completed with status: {run.status}")
    except Exception as e:
        logger.exception(f"Background task execution failed for task {task_id} run {run_id}: {e}")
        # Try to update run status to failed
        try:
            async with async_session() as session:
                repo = TaskRepository(session)
                runs = await repo.list_runs(task_id, limit=1)
                run = next((r for r in runs if r.id == run_id), None)
                if run:
                    run.status = "failed"
                    run.finished_at = datetime.utcnow()
                    run.run_metadata["error"] = str(e)
                    await session.commit()
        except Exception as update_error:
            logger.exception(f"Failed to update run status: {update_error}")


async def list_runs(request: web.Request) -> web.Response:
    task_id = int(request.match_info["task_id"])
    async with async_session() as session:
        repo = TaskRepository(session)
        runs = await repo.list_runs(task_id)
        data = [
            TaskRunResponse(
                id=run.id,
                task_id=run.task_id,
                status=run.status,
                started_at=run.started_at,
                finished_at=run.finished_at,
                retrieved_count=run.retrieved_count,
                filtered_count=run.filtered_count,
                summary=run.summary,
            ).model_dump(mode="json")
            for run in runs
        ]
        return web.json_response({"data": data})


async def suggest_keywords(request: web.Request) -> web.Response:
    payload = await request.json()
    prompt = payload.get("prompt")
    if not prompt:
        return web.json_response({"error": "prompt is required"}, status=400)
    max_keywords = int(payload.get("max_keywords", 10))
    service = KeywordExtractionService()
    keywords = await service.extract_keywords(prompt, max_keywords=max_keywords)
    return web.json_response({"data": keywords})


# ==================== Task Status Control ====================

async def start_task(request: web.Request) -> web.Response:
    """
    Start a task (inactive -> active).
    - Changes status to 'active'
    - Schedules task in scheduler
    - Immediately triggers one execution
    - Calculates next_run_at
    """
    task_id = int(request.match_info["task_id"])
    scheduler = request.app.get('scheduler')
    
    async with async_session() as session:
        repo = TaskRepository(session)
        task = await repo.get_task(task_id)
        
        if not task:
            return web.json_response({"error": "Task not found"}, status=404)
        
        # Validate status transition
        if task.status == "active":
            return web.json_response({"error": "Task is already running"}, status=400)
        
        # Validate run_at_hour is set
        if task.run_at_hour is None:
            return web.json_response({"error": "run_at_hour must be set before starting task"}, status=400)
        
        # Update status to active
        task.status = "active"
        
        # Set last_run_at to now
        tz = pytz.timezone(task.run_timezone or 'Asia/Shanghai')
        now = datetime.now(tz)
        task.last_run_at = now
        
        await session.commit()
        await session.refresh(task)
        
        # Schedule task in scheduler (for daily recurring execution)
        if scheduler:
            await scheduler.schedule_task(task)
            # Set next_run_at to tomorrow at scheduled time
            task.next_run_at = scheduler.get_next_run_time(task)
            await session.commit()
            await session.refresh(task)
        
        # Trigger immediate execution in background
        logger.info(f"Starting task {task_id} - immediate execution + scheduled for tomorrow at {task.run_at_hour:02d}:{task.run_at_minute:02d}")
        
        # Create a new TaskRun
        task_run = TaskRun(
            task_id=task_id,
            status='running',
            started_at=now,
            retrieved_count=0,
            filtered_count=0
        )
        session.add(task_run)
        await session.commit()
        await session.refresh(task_run)
        
        # Execute in background
        asyncio.create_task(_run_task_background(task_id, task_run.id))
        
        return web.json_response({"data": _serialize_task(task)})


async def stop_task(request: web.Request) -> web.Response:
    """
    Stop a task (active -> inactive).
    - Changes status to 'inactive'
    - Removes task from scheduler
    - Clears next_run_at
    - Note: Cannot stop already running executions (they will complete)
    """
    task_id = int(request.match_info["task_id"])
    scheduler = request.app.get('scheduler')
    
    async with async_session() as session:
        repo = TaskRepository(session)
        task = await repo.get_task(task_id)
        
        if not task:
            return web.json_response({"error": "Task not found"}, status=404)
        
        # Validate status transition
        if task.status == "inactive":
            return web.json_response({"error": "Task is already inactive"}, status=400)
        
        # Update status to inactive
        task.status = "inactive"
        task.next_run_at = None
        
        await session.commit()
        await session.refresh(task)
        
        # Remove from scheduler
        if scheduler:
            await scheduler.remove_task(task_id)
        
        logger.info(f"Stopped task {task_id}")
        
        return web.json_response({"data": _serialize_task(task)})


async def restart_task(request: web.Request) -> web.Response:
    """
    Restart a task with updated configuration.
    - Updates task configuration
    - If task is active, reschedules it in scheduler
    - Starts the task (triggers immediate execution)
    """
    task_id = int(request.match_info["task_id"])
    payload = await request.json()
    scheduler = request.app.get('scheduler')
    
    async with async_session() as session:
        repo = TaskRepository(session)
        task = await repo.get_task(task_id)
        
        if not task:
            return web.json_response({"error": "Task not found"}, status=404)
        
        was_active = task.status == "active"
        
        # Update task configuration
        if "run_at_hour" in payload:
            task.run_at_hour = payload["run_at_hour"]
        
        if "run_at_minute" in payload:
            task.run_at_minute = payload["run_at_minute"]
        
        if "notification_config" in payload:
            task.notification_config = payload["notification_config"]
        
        # If task was active, restart it
        if was_active:
            task.status = "active"
            
            # Set last_run_at to now
            tz = pytz.timezone(task.run_timezone or 'Asia/Shanghai')
            now = datetime.now(tz)
            task.last_run_at = now
            
            await session.commit()
            await session.refresh(task)
            
            # Reschedule in scheduler
            if scheduler:
                await scheduler.reschedule_task(task)
                task.next_run_at = scheduler.get_next_run_time(task)
                await session.commit()
                await session.refresh(task)
            
            # Trigger immediate execution in background
            logger.info(f"Restarting task {task_id} with updated config and triggering immediate execution")
            
            # Create a new TaskRun
            task_run = TaskRun(
                task_id=task_id,
                status='running',
                started_at=now,
                retrieved_count=0,
                filtered_count=0
            )
            session.add(task_run)
            await session.commit()
            await session.refresh(task_run)
            
            # Execute in background
            asyncio.create_task(_run_task_background(task_id, task_run.id))
        else:
            # Just update config if not active
            await session.commit()
            await session.refresh(task)
        
        return web.json_response({"data": _serialize_task(task)})


def setup_task_routes(app: web.Application) -> None:
    app.router.add_get("/api/tasks", list_tasks)
    app.router.add_get("/api/tasks/archived", list_archived_tasks)
    app.router.add_post("/api/tasks", create_task)
    app.router.add_get("/api/tasks/{task_id}", get_task)
    app.router.add_put("/api/tasks/{task_id}", update_task)
    app.router.add_delete("/api/tasks/{task_id}", delete_task)  # Now permanently deletes
    app.router.add_post("/api/tasks/{task_id}/archive", archive_task)  # Archive without deleting
    app.router.add_post("/api/tasks/{task_id}/run", run_task)
    app.router.add_get("/api/tasks/{task_id}/runs", list_runs)
    app.router.add_post("/api/tasks/keywords/suggest", suggest_keywords)
    # Task status control (simplified to start/stop only)
    app.router.add_post("/api/tasks/{task_id}/start", start_task)
    app.router.add_post("/api/tasks/{task_id}/stop", stop_task)
    app.router.add_post("/api/tasks/{task_id}/restart", restart_task)

