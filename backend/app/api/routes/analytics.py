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
    app.router.add_get("/api/analytics/sources", get_global_sources)
    app.router.add_get("/api/analytics/scores", get_global_scores)
    app.router.add_get("/api/analytics/tasks/{task_id}/trends", get_task_trends)
    app.router.add_get("/api/analytics/tasks/{task_id}/keywords", get_keyword_distribution)
    app.router.add_get("/api/analytics/tasks/{task_id}/sources", get_source_distribution)


async def get_overview_stats(request: web.Request) -> web.Response:
    """Get overview statistics for the dashboard."""
    time_range = request.query.get("range", "30d")
    task_id = request.query.get("task_id")
    
    # Parse time range
    days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365, "all": 36500}
    days = days_map.get(time_range, 30)
    start_date = datetime.utcnow() - timedelta(days=days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    async with async_session() as session:
        # 构建基础查询条件 - 默认只统计被筛选为相关的文档
        base_filter = [Document.is_filtered_in == True]
        if task_id:
            base_filter.append(Document.task_id == int(task_id))
        
        # Total documents
        total_query = select(func.count(Document.id)).where(*base_filter)
        total_docs_result = await session.execute(total_query)
        total_docs = total_docs_result.scalar() or 0
        
        # Active tasks
        active_tasks_result = await session.execute(
            select(func.count(Task.id)).where(Task.status == "active")
        )
        active_tasks = active_tasks_result.scalar() or 0
        
        # Documents this week
        week_query = select(func.count(Document.id)).where(
            Document.created_at >= week_ago,
            *base_filter
        )
        week_docs_result = await session.execute(week_query)
        week_docs = week_docs_result.scalar() or 0
        
        # Previous week for growth rate
        two_weeks_ago = datetime.utcnow() - timedelta(days=14)
        prev_week_query = select(func.count(Document.id)).where(
            Document.created_at >= two_weeks_ago,
            Document.created_at < week_ago,
            *base_filter
        )
        prev_week_result = await session.execute(prev_week_query)
        prev_week_docs = prev_week_result.scalar() or 1  # Avoid division by zero
        
        # Calculate growth rate
        growth_rate = ((week_docs - prev_week_docs) / prev_week_docs * 100) if prev_week_docs > 0 else 0
        
        # Average citations (using rank_score as proxy if citation_count not available)
        avg_query = select(func.avg(Document.rank_score)).where(
            Document.rank_score.isnot(None),
            *base_filter
        )
        avg_score_result = await session.execute(avg_query)
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
    task_id = request.query.get("task_id")
    start_date = datetime.utcnow() - timedelta(days=days)
    
    async with async_session() as session:
        # 构建查询 - 默认只统计被筛选为相关的文档
        conditions = [Document.created_at >= start_date, Document.is_filtered_in == True]
        if task_id:
            conditions.append(Document.task_id == int(task_id))
        
        query = select(
            func.date(Document.created_at).label("date"),
            func.count(Document.id).label("count")
        ).where(
            *conditions
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


async def get_global_sources(request: web.Request) -> web.Response:
    """Get global document count by source."""
    task_id = request.query.get("task_id")
    
    async with async_session() as session:
        # 默认只统计被筛选为相关的文档
        base_conditions = [Document.is_filtered_in == True]
        if task_id:
            base_conditions.append(Document.task_id == int(task_id))
        
        stmt = (
            select(Document.source_name, func.count().label("count"))
            .where(*base_conditions)
            .group_by(Document.source_name)
            .order_by(func.count().desc())
        )
        
        result = await session.execute(stmt)
        sources = result.all()
        
        return web.json_response({
            "data": {
                "sources": [
                    {"source": row.source_name, "count": row.count}
                    for row in sources
                ]
            }
        })


async def get_global_scores(request: web.Request) -> web.Response:
    """Get global relevance score distribution."""
    task_id = request.query.get("task_id")
    
    async with async_session() as session:
        # 默认只统计被筛选为相关的文档
        base_conditions = [Document.rank_score.isnot(None), Document.is_filtered_in == True]
        if task_id:
            base_conditions.append(Document.task_id == int(task_id))
        
        base_query = select(Document.rank_score).where(*base_conditions)
        
        result = await session.execute(base_query)
        scores = [row[0] for row in result.all()]
        
        # 分布统计
        ranges = [
            {"range": "90-100%", "min": 0.9, "max": 1.01, "count": 0},
            {"range": "80-90%", "min": 0.8, "max": 0.9, "count": 0},
            {"range": "70-80%", "min": 0.7, "max": 0.8, "count": 0},
            {"range": "60-70%", "min": 0.6, "max": 0.7, "count": 0},
            {"range": "<60%", "min": 0, "max": 0.6, "count": 0}
        ]
        
        for score in scores:
            for r in ranges:
                if r["min"] <= score < r["max"]:
                    r["count"] += 1
                    break
        
        # 计算平均分
        avg_score = sum(scores) / len(scores) if scores else 0
        
        return web.json_response({
            "data": {
                "avg_score": round(avg_score * 100, 1),
                "distribution": [
                    {"range": r["range"], "count": r["count"]}
                    for r in ranges if r["count"] > 0
                ]
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
