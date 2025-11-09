"""Analytics and statistics routes."""

from __future__ import annotations

from datetime import datetime, timedelta

from aiohttp import web
from sqlalchemy import func, select

from app.db import async_session
from app.db.models import Document, Task
from app.db.repositories import DocumentRepository, TaskRepository


def setup_analytics_routes(app: web.Application) -> None:
    app.router.add_get("/api/analytics/overview", get_overview_stats)
    app.router.add_get("/api/analytics/trends", get_global_trends)
    app.router.add_get("/api/analytics/tasks/{task_id}/trends", get_task_trends)
    app.router.add_get("/api/analytics/tasks/{task_id}/keywords", get_keyword_distribution)
    app.router.add_get("/api/analytics/tasks/{task_id}/sources", get_source_distribution)


async def get_overview_stats(request: web.Request) -> web.Response:
    """Get overview statistics for the dashboard."""
    time_range = request.query.get("range", "30d")
    
    # Parse time range
    days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365, "all": 36500}
    days = days_map.get(time_range, 30)
    start_date = datetime.utcnow() - timedelta(days=days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    async with async_session() as session:
        # Total documents
        total_docs_result = await session.execute(
            select(func.count(Document.id))
        )
        total_docs = total_docs_result.scalar() or 0
        
        # Active tasks
        active_tasks_result = await session.execute(
            select(func.count(Task.id)).where(Task.status == "active")
        )
        active_tasks = active_tasks_result.scalar() or 0
        
        # Documents this week
        week_docs_result = await session.execute(
            select(func.count(Document.id)).where(Document.created_at >= week_ago)
        )
        week_docs = week_docs_result.scalar() or 0
        
        # Previous week for growth rate
        two_weeks_ago = datetime.utcnow() - timedelta(days=14)
        prev_week_result = await session.execute(
            select(func.count(Document.id)).where(
                Document.created_at >= two_weeks_ago,
                Document.created_at < week_ago
            )
        )
        prev_week_docs = prev_week_result.scalar() or 1  # Avoid division by zero
        
        # Calculate growth rate
        growth_rate = ((week_docs - prev_week_docs) / prev_week_docs * 100) if prev_week_docs > 0 else 0
        
        # Average citations (using rank_score as proxy if citation_count not available)
        avg_score_result = await session.execute(
            select(func.avg(Document.rank_score)).where(Document.rank_score.isnot(None))
        )
        avg_score = avg_score_result.scalar() or 0
        
        # Total tasks
        total_tasks_result = await session.execute(
            select(func.count(Task.id))
        )
        total_tasks = total_tasks_result.scalar() or 0
        
        return web.json_response({
            "data": {
                "total_documents": total_docs,
                "active_tasks": active_tasks,
                "total_tasks": total_tasks,
                "documents_this_week": week_docs,
                "week_growth_rate": round(growth_rate, 1),
                "avg_citations": round(avg_score * 100, 1),  # Scale to 0-100
                "time_range": time_range,
            }
        })


async def get_global_trends(request: web.Request) -> web.Response:
    """Get global document trends over time."""
    days = int(request.query.get("days", 30))
    start_date = datetime.utcnow() - timedelta(days=days)
    
    async with async_session() as session:
        repo = DocumentRepository(session)
        # Reuse the trends method but without task filter
        query = select(
            func.date(Document.created_at).label("date"),
            func.count(Document.id).label("count")
        ).where(
            Document.created_at >= start_date
        ).group_by(
            func.date(Document.created_at)
        ).order_by(
            func.date(Document.created_at)
        )
        
        result = await session.execute(query)
        trends = result.mappings().all()
        
        return web.json_response({
            "data": {
                "period_days": days,
                "trends": [
                    {"date": str(item["date"]), "count": item["count"]}
                    for item in trends
                ],
            }
        })


async def get_task_trends(request: web.Request) -> web.Response:
    """Get document count trends over time for a task."""
    task_id = int(request.match_info["task_id"])
    days = int(request.query.get("days", 30))

    async with async_session() as session:
        repo = DocumentRepository(session)
        start_date = datetime.utcnow() - timedelta(days=days)
        trends = await repo.get_document_trends(task_id, start_date)

        return web.json_response(
            {
                "data": {
                    "task_id": task_id,
                    "period_days": days,
                    "trends": [
                        {"date": item["date"].isoformat() if isinstance(item["date"], datetime) else item["date"], "count": item["count"]}
                        for item in trends
                    ],
                }
            }
        )


async def get_keyword_distribution(request: web.Request) -> web.Response:
    """Get keyword frequency distribution for a task."""
    task_id = int(request.match_info["task_id"])
    limit = int(request.query.get("limit", 50))

    async with async_session() as session:
        repo = DocumentRepository(session)
        distribution = await repo.get_keyword_distribution(task_id, limit=limit)

        return web.json_response(
            {
                "data": {
                    "task_id": task_id,
                    "keywords": [{"keyword": item["keyword"], "count": item["count"]} for item in distribution],
                }
            }
        )


async def get_source_distribution(request: web.Request) -> web.Response:
    """Get document count by source for a task."""
    task_id = int(request.match_info["task_id"])

    async with async_session() as session:
        repo = DocumentRepository(session)
        distribution = await repo.get_source_distribution(task_id)

        return web.json_response(
            {
                "data": {
                    "task_id": task_id,
                    "sources": [{"source_name": item["source_name"], "count": item["count"]} for item in distribution],
                }
            }
        )
