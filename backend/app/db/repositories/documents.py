"""Document repository."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

from sqlalchemy import Select, and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import models


class DocumentRepository:
    """Data access for documents."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_documents(self, docs: Iterable[models.Document]) -> List[models.Document]:
        doc_list = list(docs)
        for doc in doc_list:
            self._session.add(doc)
        await self._session.flush()
        return doc_list

    async def get_document(self, doc_id: int) -> Optional[models.Document]:
        result = await self._session.execute(
            select(models.Document).where(models.Document.id == doc_id).options(selectinload(models.Document.summary))
        )
        return result.scalar_one_or_none()

    async def get_documents_by_ids(self, doc_ids: List[int]) -> List[models.Document]:
        result = await self._session.execute(
            select(models.Document).where(models.Document.id.in_(doc_ids)).options(selectinload(models.Document.summary))
        )
        return list(result.scalars().all())

    async def get_by_external(self, external_id: str, source_name: str) -> Optional[models.Document]:
        result = await self._session.execute(
            select(models.Document).where(
                models.Document.external_id == external_id,
                models.Document.source_name == source_name,
            )
        )
        return result.scalar_one_or_none()

    async def list_documents(
        self,
        filters: Dict[str, Any],
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[models.Document], int]:
        """List documents with filters and pagination."""
        stmt: Select[tuple[models.Document]] = select(models.Document).options(selectinload(models.Document.summary))

        conditions = []
        
        # 默认只显示被筛选为相关的文档（is_filtered_in=True）
        # 除非明确指定要显示所有文档
        if filters.get("show_all") is not True:
            conditions.append(models.Document.is_filtered_in == True)
        
        if "task_id" in filters:
            conditions.append(models.Document.task_id == filters["task_id"])
        if "source_name" in filters:
            conditions.append(models.Document.source_name == filters["source_name"])
        if "keyword" in filters:
            # Search in user_keywords array
            conditions.append(func.json_contains(models.Document.user_keywords, f'"{filters["keyword"]}"'))
        if "start_date" in filters:
            conditions.append(models.Document.published_at >= filters["start_date"])
        if "end_date" in filters:
            conditions.append(models.Document.published_at <= filters["end_date"])

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Count total
        count_stmt = select(func.count()).select_from(models.Document)
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar() or 0

        # Fetch page
        stmt = stmt.order_by(desc(models.Document.published_at)).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        documents = list(result.scalars().all())

        return documents, total

    async def list_for_task(
        self,
        task_id: int,
        source_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[models.Document], int]:
        """List documents for a task with pagination and total count."""
        stmt: Select[tuple[models.Document]] = (
            select(models.Document)
            .where(
                models.Document.task_id == task_id,
                models.Document.is_filtered_in == True  # 只返回被筛选为相关的文档
            )
            .options(selectinload(models.Document.summary))
        )
        
        # Count query - 也只统计被筛选为相关的文档
        count_stmt = select(func.count()).select_from(models.Document).where(
            models.Document.task_id == task_id,
            models.Document.is_filtered_in == True
        )
        
        if source_name:
            stmt = stmt.where(models.Document.source_name == source_name)
            count_stmt = count_stmt.where(models.Document.source_name == source_name)
        
        # Get total count
        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar() or 0
        
        # Get documents
        stmt = stmt.order_by(desc(models.Document.published_at)).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        documents = list(result.scalars().all())
        
        return documents, total

    async def attach_summary(self, summary: models.DocumentSummary) -> models.DocumentSummary:
        self._session.add(summary)
        await self._session.flush()
        return summary

    async def get_summaries(self, doc_id: int) -> List[models.DocumentSummary]:
        result = await self._session.execute(
            select(models.DocumentSummary)
            .where(models.DocumentSummary.document_id == doc_id)
            .order_by(desc(models.DocumentSummary.created_at))
        )
        return list(result.scalars().all())

    async def get_document_trends(self, task_id: int, start_date: datetime) -> List[Dict[str, Any]]:
        """Get document count trends grouped by date."""
        stmt = (
            select(func.date(models.Document.created_at).label("date"), func.count().label("count"))
            .where(models.Document.task_id == task_id, models.Document.created_at >= start_date)
            .group_by(func.date(models.Document.created_at))
            .order_by("date")
        )
        result = await self._session.execute(stmt)
        return [{"date": row.date, "count": row.count} for row in result]

    async def get_keyword_distribution(self, task_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get keyword frequency distribution."""
        # For SQLite with JSON, we need a workaround
        # Fetch documents and aggregate in Python
        stmt = select(models.Document.user_keywords).where(models.Document.task_id == task_id)
        result = await self._session.execute(stmt)
        keyword_counter: Dict[str, int] = {}
        for (keywords,) in result:
            if keywords:
                for kw in keywords:
                    keyword_counter[kw] = keyword_counter.get(kw, 0) + 1

        sorted_keywords = sorted(keyword_counter.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{"keyword": kw, "count": count} for kw, count in sorted_keywords]

    async def get_source_distribution(self, task_id: int) -> List[Dict[str, Any]]:
        """Get document count by source."""
        stmt = (
            select(models.Document.source_name, func.count().label("count"))
            .where(models.Document.task_id == task_id)
            .group_by(models.Document.source_name)
            .order_by(desc("count"))
        )
        result = await self._session.execute(stmt)
        return [{"source_name": row.source_name, "count": row.count} for row in result]

    async def delete_documents_by_ids(self, doc_ids: List[int]) -> int:
        """Delete documents by IDs and return count of deleted documents."""
        from sqlalchemy import delete
        
        # Delete related summaries first
        await self._session.execute(
            delete(models.DocumentSummary).where(
                models.DocumentSummary.document_id.in_(doc_ids)
            )
        )
        
        # Delete documents
        result = await self._session.execute(
            delete(models.Document).where(
                models.Document.id.in_(doc_ids)
            )
        )
        return result.rowcount
