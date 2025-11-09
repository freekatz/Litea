"""Task repository."""

from __future__ import annotations

from typing import Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models


class TaskRepository:
    """Data access helpers for tasks."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_tasks(self, include_archived: bool = False) -> List[models.Task]:
        """
        List tasks, optionally including archived ones.
        
        Args:
            include_archived: If False (default), excludes archived tasks
        """
        stmt = (
            select(models.Task)
            .options(
                selectinload(models.Task.keywords),
                selectinload(models.Task.sources).selectinload(models.TaskSource.source),
            )
        )
        
        if not include_archived:
            stmt = stmt.where(models.Task.is_archived == False)
        
        stmt = stmt.order_by(models.Task.created_at.desc())
        
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
    
    async def list_archived_tasks(self) -> List[models.Task]:
        """List only archived tasks."""
        stmt = (
            select(models.Task)
            .where(models.Task.is_archived == True)
            .options(
                selectinload(models.Task.keywords),
                selectinload(models.Task.sources).selectinload(models.TaskSource.source),
            )
            .order_by(models.Task.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_task(self, task_id: int) -> Optional[models.Task]:
        stmt = (
            select(models.Task)
            .where(models.Task.id == task_id)
            .options(
                selectinload(models.Task.keywords),
                selectinload(models.Task.sources).selectinload(models.TaskSource.source),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_task(
        self,
        task: models.Task,
        keywords: Iterable[models.TaskKeyword],
        sources: Iterable[models.TaskSource],
    ) -> models.Task:
        task.keywords.extend(keywords)
        task.sources.extend(sources)
        self._session.add(task)
        await self._session.flush()
        return task

    async def update_task(self, task: models.Task) -> models.Task:
        await self._session.flush()
        return task

    async def delete_task(self, task: models.Task) -> None:
        await self._session.delete(task)
    
    async def delete_task_with_documents(self, task_id: int) -> int:
        """
        Delete a task and all its associated documents.
        Returns the count of deleted documents.
        """
        from sqlalchemy import delete
        
        # First, delete all document summaries for documents belonging to this task
        await self._session.execute(
            delete(models.DocumentSummary).where(
                models.DocumentSummary.document_id.in_(
                    select(models.Document.id).where(models.Document.task_id == task_id)
                )
            )
        )
        
        # Delete all documents for this task
        doc_result = await self._session.execute(
            delete(models.Document).where(models.Document.task_id == task_id)
        )
        deleted_docs_count = doc_result.rowcount
        
        # Delete the task itself (this will cascade delete runs, keywords, sources via DB cascade)
        task = await self.get_task(task_id)
        if task:
            await self._session.delete(task)
        
        return deleted_docs_count

    async def add_run(self, run: models.TaskRun) -> models.TaskRun:
        self._session.add(run)
        await self._session.flush()
        return run

    async def list_runs(self, task_id: int, limit: int = 20) -> List[models.TaskRun]:
        result = await self._session.execute(
            select(models.TaskRun)
            .where(models.TaskRun.task_id == task_id)
            .order_by(models.TaskRun.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
