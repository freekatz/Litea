"""Document query and management routes."""

from __future__ import annotations

from aiohttp import web

from app.db import async_session
from app.db.repositories import DocumentRepository
from app.schemas.document import DocumentResponse, DocumentSummaryResponse
from app.utils.pagination import normalize_pagination


def setup_document_routes(app: web.Application) -> None:
    app.router.add_get("/api/documents", list_documents)
    app.router.add_get("/api/documents/{doc_id}", get_document)
    app.router.add_get("/api/documents/{doc_id}/detail", get_document_detail)
    app.router.add_get("/api/tasks/{task_id}/documents", list_task_documents)
    app.router.add_post("/api/documents/export/zotero", export_to_zotero)
    app.router.add_post("/api/documents/batch/delete", batch_delete_documents)


async def list_documents(request: web.Request) -> web.Response:
    """List documents with comprehensive filters."""
    task_id = request.query.get("task_id")
    source = request.query.get("source")
    keyword = request.query.get("keyword")
    start_date = request.query.get("start_date")
    end_date = request.query.get("end_date")
    limit, offset = normalize_pagination(
        limit=int(request.query.get("limit", 50)) if request.query.get("limit") else None,
        offset=int(request.query.get("offset", 0)) if request.query.get("offset") else None,
    )

    async with async_session() as session:
        repo = DocumentRepository(session)
        filters = {}
        if task_id:
            filters["task_id"] = int(task_id)
        if source:
            filters["source_name"] = source
        if keyword:
            filters["keyword"] = keyword
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date

        documents, total = await repo.list_documents(filters, limit=limit, offset=offset)
        data = []
        for doc in documents:
            summary_schema = None
            if hasattr(doc, "summary") and doc.summary:
                summary_schema = DocumentSummaryResponse(
                    summary=doc.summary.summary,
                    highlights=doc.summary.highlights,
                    research_trends=doc.summary.research_trends,
                    agent_metadata=doc.summary.agent_metadata,
                    created_at=doc.summary.created_at,
                )
            data.append(
                DocumentResponse(
                    id=doc.id,
                    task_id=doc.task_id,
                    run_id=doc.run_id,
                    source_name=doc.source_name,
                    external_id=doc.external_id,
                    title=doc.title,
                    authors=doc.authors,
                    abstract=doc.abstract,
                    url=doc.url,
                    published_at=doc.published_at,
                    created_at=doc.created_at,
                    keywords=doc.keywords,
                    user_keywords=doc.user_keywords,
                    extra_metadata=doc.extra_metadata,
                    is_filtered_in=doc.is_filtered_in,
                    rank_score=doc.rank_score,
                    zotero_key=doc.zotero_key if hasattr(doc, "zotero_key") else None,
                    summary=summary_schema,
                ).model_dump(mode="json")
            )
        return web.json_response({
            "data": {"items": data, "total": total},
            "pagination": {"limit": limit, "offset": offset}
        })


async def get_document(request: web.Request) -> web.Response:
    """Get single document with full details."""
    doc_id = int(request.match_info["doc_id"])
    async with async_session() as session:
        repo = DocumentRepository(session)
        doc = await repo.get_document(doc_id)
        if not doc:
            return web.json_response({"error": "document not found"}, status=404)

        summary_schema = None
        if hasattr(doc, "summary") and doc.summary:
            summary_schema = DocumentSummaryResponse(
                summary=doc.summary.summary,
                highlights=doc.summary.highlights,
                research_trends=doc.summary.research_trends,
                agent_metadata=doc.summary.agent_metadata,
                created_at=doc.summary.created_at,
            )

        return web.json_response(
            {
                "data": DocumentResponse(
                    id=doc.id,
                    task_id=doc.task_id,
                    run_id=doc.run_id,
                    source_name=doc.source_name,
                    external_id=doc.external_id,
                    title=doc.title,
                    authors=doc.authors,
                    abstract=doc.abstract,
                    url=doc.url,
                    published_at=doc.published_at,
                    created_at=doc.created_at,
                    keywords=doc.keywords,
                    user_keywords=doc.user_keywords,
                    extra_metadata=doc.extra_metadata,
                    is_filtered_in=doc.is_filtered_in,
                    rank_score=doc.rank_score,
                    zotero_key=doc.zotero_key if hasattr(doc, "zotero_key") else None,
                    summary=summary_schema,
                ).model_dump(mode="json")
            }
        )


async def get_document_detail(request: web.Request) -> web.Response:
    """
    Get enriched document metadata from source URL using Zotero Web Translation API.
    
    This endpoint fetches detailed metadata for a document by:
    1. Looking up the document by ID in the database
    2. Using the document's URL to call the appropriate retrieval source's get_detail()
    3. Returning enhanced metadata with DOI, journal info, complete author details, etc.
    """
    doc_id = int(request.match_info["doc_id"])
    
    async with async_session() as session:
        repo = DocumentRepository(session)
        doc = await repo.get_document(doc_id)
        
        if not doc:
            return web.json_response({"error": "document not found"}, status=404)
        
        if not doc.url:
            return web.json_response({"error": "document has no URL"}, status=400)
        
        # Get the appropriate retrieval source
        from app.services.retrieval.registry import RetrievalRegistry
        
        try:
            registry = RetrievalRegistry()
            source = registry.get(doc.source_name)
        except KeyError:
            return web.json_response(
                {"error": f"retrieval source '{doc.source_name}' not available"},
                status=400
            )
        
        # Fetch detailed metadata from source
        try:
            metadata = await source.get_detail(doc.url)
            
            if not metadata:
                return web.json_response(
                    {"error": "failed to extract metadata from URL"},
                    status=500
                )
            
            return web.json_response({
                "data": {
                    "document_id": doc_id,
                    "url": doc.url,
                    "source_name": doc.source_name,
                    "metadata": metadata
                }
            })
            
        except Exception as exc:
            logger = request.app["logger"] if "logger" in request.app else None
            if logger:
                logger.error("Failed to get document detail for {}: {}", doc_id, exc)
            return web.json_response(
                {"error": f"failed to fetch metadata: {str(exc)}"},
                status=500
            )


async def list_task_documents(request: web.Request) -> web.Response:
    """List documents for a specific task."""
    task_id = int(request.match_info["task_id"])
    source = request.query.get("source")
    limit, offset = normalize_pagination(
        limit=int(request.query.get("limit", 50)) if request.query.get("limit") else None,
        offset=int(request.query.get("offset", 0)) if request.query.get("offset") else None,
    )
    async with async_session() as session:
        repo = DocumentRepository(session)
        documents, total = await repo.list_for_task(task_id, source_name=source, limit=limit, offset=offset)
        data = []
        for doc in documents:
            summary_schema = None
            if hasattr(doc, "summary") and doc.summary:
                summary_schema = DocumentSummaryResponse(
                    summary=doc.summary.summary,
                    highlights=doc.summary.highlights,
                    research_trends=doc.summary.research_trends,
                    agent_metadata=doc.summary.agent_metadata,
                    created_at=doc.summary.created_at,
                )
            data.append(
                DocumentResponse(
                    id=doc.id,
                    task_id=doc.task_id,
                    run_id=doc.run_id,
                    source_name=doc.source_name,
                    external_id=doc.external_id,
                    title=doc.title,
                    authors=doc.authors,
                    abstract=doc.abstract,
                    url=doc.url,
                    published_at=doc.published_at,
                    created_at=doc.created_at,
                    keywords=doc.keywords,
                    user_keywords=doc.user_keywords,
                    extra_metadata=doc.extra_metadata,
                    is_filtered_in=doc.is_filtered_in,
                    rank_score=doc.rank_score,
                    zotero_key=doc.zotero_key if hasattr(doc, "zotero_key") else None,
                    summary=summary_schema,
                ).model_dump(mode="json")
            )
        return web.json_response({
            "data": {"items": data, "total": total},
            "pagination": {"limit": limit, "offset": offset}
        })


async def export_to_zotero(request: web.Request) -> web.Response:
    """Export selected documents to Zotero collection."""
    payload = await request.json()
    doc_ids = payload.get("document_ids", [])
    collection_name = payload.get("collection_name")

    if not doc_ids:
        return web.json_response({"error": "document_ids required"}, status=400)

    async with async_session() as session:
        repo = DocumentRepository(session)
        documents = await repo.get_documents_by_ids(doc_ids)

        from app.services.zotero.client import ZoteroClient
        from loguru import logger

        zotero = ZoteroClient()
        results = []
        try:
            logger.info("Exporting {} documents to Zotero collection: '{}'", len(documents), collection_name)
            collection_key = await zotero.get_or_create_collection(collection_name) if collection_name else None
            logger.info("Collection key: {}", collection_key)
            
            results = await zotero.batch_export(documents, collection_key)
            logger.info("Export results: {} keys returned", len(results))
            
            # Update zotero_key in documents
            for doc, zotero_key in zip(documents, results):
                if zotero_key:
                    doc.zotero_key = zotero_key
            await session.commit()
        except Exception as exc:
            logger.error("Failed to export to Zotero: {}", exc)
            logger.exception("Full exception details:")
            return web.json_response({"error": str(exc)}, status=500)

        return web.json_response({"data": {"exported": len(results), "results": results}})


async def batch_delete_documents(request: web.Request) -> web.Response:
    """Batch delete documents by IDs."""
    payload = await request.json()
    doc_ids = payload.get("document_ids", [])

    if not doc_ids:
        return web.json_response({"error": "document_ids required"}, status=400)

    async with async_session() as session:
        repo = DocumentRepository(session)
        try:
            deleted_count = await repo.delete_documents_by_ids(doc_ids)
            await session.commit()
            return web.json_response({
                "success": True,
                "deleted": deleted_count,
                "message": f"Deleted {deleted_count} documents"
            })
        except Exception as exc:
            await session.rollback()
            return web.json_response({"error": str(exc)}, status=500)
