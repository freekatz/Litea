"""Execute retrieval and AI pipeline for a task."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models
from app.db.repositories import DocumentRepository, TaskRepository
from app.services.ai.filtering_agent import FilteringAgentService
from app.services.ai.keyword_extraction_service import KeywordExtractionService
from app.services.retrieval.registry import RetrievalRegistry
from app.services.mcp import mcp_server, EmailTool, FeishuTool


class TaskRunner:
    """Coordinates retrieval, filtering, persistence and notifications."""

    def __init__(
        self,
        retrieval_registry: RetrievalRegistry | None = None,
        keyword_service: KeywordExtractionService | None = None,
        filtering_service: FilteringAgentService | None = None,
    ) -> None:
        self._retrieval = retrieval_registry or RetrievalRegistry()
        self._keywords = keyword_service or KeywordExtractionService()
        self._filtering = filtering_service or FilteringAgentService()

        # Initialize MCP tools
        self._init_mcp_tools()

    async def run(self, session: AsyncSession, task: models.Task) -> models.TaskRun:
        """Create a new run and execute the task."""
        task_repo = TaskRepository(session)
        run = models.TaskRun(task_id=task.id)
        await task_repo.add_run(run)
        await session.flush()
        await self.run_with_existing_run(session, task, run)
        return run

    async def run_with_existing_run(self, session: AsyncSession, task: models.Task, run: models.TaskRun) -> None:
        """Execute the task with an existing run record."""
        doc_repo = DocumentRepository(session)
        logger.info("Started task '{}' run {}", task.name, run.id)
        try:
            keywords = await self._get_keywords(task)
            run.run_metadata["keywords"] = keywords
            
            # Retrieve documents (continue even if some sources fail)
            retrieved_docs = await self._retrieve_documents(task, keywords)
            run.retrieved_count = sum(len(items) for items in retrieved_docs.values())
            
            if run.retrieved_count == 0:
                logger.warning("No documents retrieved for task {}", task.id)
                run.status = "completed"
                run.run_metadata["warning"] = "No documents retrieved from any source"
                run.finished_at = datetime.utcnow()
                await session.flush()
                return
            
            # Filter documents
            filtered_docs = await self._filter_documents(task, keywords, retrieved_docs)
            run.filtered_count = sum(len(items) for items in filtered_docs.values())
            
            # Persist documents - 保存所有文档
            await self._persist_documents(session, doc_repo, run, filtered_docs)
            
            # 只使用被选中的文档进行摘要生成和通知
            selected_docs = {}
            for source_name, docs in filtered_docs.items():
                selected = [doc for doc in docs if doc.get("is_selected", False)]
                if selected:
                    selected_docs[source_name] = selected
                logger.info(f"Source '{source_name}': {len(selected)}/{len(docs)} documents selected (is_selected=True)")
            
            selected_count = sum(len(items) for items in selected_docs.values())
            logger.info(f"Task {task.id}: {selected_count} documents selected out of {run.filtered_count} total for notifications")
            
            run.summary = f"{selected_count} documents selected out of {run.filtered_count}"

            # Send notifications (non-critical operation) - 只通知被选中的文档
            try:
                await self._send_notifications(task, selected_docs)
            except Exception as exc:
                logger.error("Failed to send notifications for task {}: {}", task.id, exc)
                run.run_metadata["notification_error"] = str(exc)
            
            # Note: Zotero export is now handled manually from the frontend
            
            run.status = "completed"
        except Exception as exc:  # pragma: no cover
            logger.exception("Task {} failed: {}", task.id, exc)
            run.status = "failed"
            run.run_metadata["error"] = str(exc)
        finally:
            run.finished_at = datetime.utcnow()
            await session.flush()

    async def _get_keywords(self, task: models.Task) -> List[str]:
        """获取任务关键词（用户定义的关键词）"""
        user_keywords = [kw.keyword for kw in task.keywords if kw.is_user_defined]
        # 目前只使用用户定义的关键词，不自动提取
        return user_keywords

    async def _retrieve_documents(
        self,
        task: models.Task,
        keywords: List[str],
    ) -> Dict[str, List[Dict[str, Any]]]:
        documents: Dict[str, List[Dict[str, Any]]] = {}
        for task_source in task.sources:
            source_name = task_source.source.name
            try:
                source = self._retrieval.get(source_name)
                docs = await source.search(task.prompt, keywords, task_source.parameters)
                documents[source_name] = docs
                logger.info("Retrieved {} documents from {}", len(docs), source_name)
            except Exception as exc:
                logger.error("Failed to retrieve from {}: {}", source_name, exc)
                # Continue with other sources even if one fails
                documents[source_name] = []
        return documents

    async def _filter_documents(
        self,
        task: models.Task,
        keywords: List[str],
        documents: Dict[str, List[Dict[str, Any]]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """筛选文档，但保留所有文档（包括未选中的），以便完整记录"""
        all_filtered: Dict[str, List[Dict[str, Any]]] = {}
        
        for source_name, docs in documents.items():
            context = {
                "prompt": task.prompt,
                "keywords": keywords,
                "source": source_name,
                "filter_config": task.filter_config,
                "ai_config": task.ai_config,
            }
            
            # 调用AI筛选服务
            filter_results = await self._filtering.filter_documents(context, docs)
            
            logger.info(f"Filter results for {source_name}: {len(filter_results)} results returned for {len(docs)} documents")
            
            # 合并原始文档和筛选结果
            enhanced_docs = []
            matched_count = 0
            for doc in docs:
                match = next((item for item in filter_results if item.get("external_id") == doc.get("external_id")), None)
                if match:
                    # 合并筛选结果到原文档
                    doc = {**doc, **match}
                    matched_count += 1
                else:
                    # 如果没有匹配结果，标记为未选中
                    logger.warning(f"No filter result for document: {doc.get('external_id')} - {doc.get('title', 'Unknown')[:50]}")
                    doc["is_selected"] = False
                    doc["score"] = 0.0
                    doc["summary"] = doc.get("abstract", "")[:200] if doc.get("abstract") else "无摘要"
                    doc["highlights"] = []
                
                doc.setdefault("user_keywords", keywords)
                enhanced_docs.append(doc)
            
            all_filtered[source_name] = enhanced_docs
            
            # 记录筛选统计
            selected_count = sum(1 for d in enhanced_docs if d.get("is_selected", False))
            logger.info(f"Filtered {source_name}: {selected_count}/{len(enhanced_docs)} documents selected (matched: {matched_count})")
        
        return all_filtered

    async def _persist_documents(
        self,
        session: AsyncSession,
        doc_repo: DocumentRepository,
        run: models.TaskRun,
        filtered_docs: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """持久化所有文档（不管是否被选中），以便完整记录筛选过程"""
        updated_count = 0
        created_count = 0
        selected_count = 0
        
        for source_name, docs in filtered_docs.items():
            for doc in docs:
                is_selected = doc.get("is_selected", False)
                if is_selected:
                    selected_count += 1
                
                existing = await doc_repo.get_by_external(doc["external_id"], source_name)
                if existing:
                    # Update existing document fields
                    existing.is_filtered_in = is_selected  # 根据is_selected设置
                    existing.rank_score = doc.get("score", 0.0)
                    existing.user_keywords = doc.get("user_keywords", existing.user_keywords)
                    # Also update run_id to link to current run
                    existing.run_id = run.id
                    updated_count += 1
                    
                    # Update or create summary if provided
                    if doc.get("summary"):
                        # Query existing summaries to avoid lazy loading
                        existing_summaries = await doc_repo.get_summaries(existing.id)
                        if existing_summaries:
                            # Update the most recent summary
                            existing_summaries[0].summary = doc.get("summary", "")
                            existing_summaries[0].highlights = doc.get("highlights", [])
                        else:
                            # Create new summary
                            summary = models.DocumentSummary(
                                document=existing,
                                summary=doc.get("summary", ""),
                                highlights=doc.get("highlights", []),
                                agent_metadata={"source": "filtering_agent"},
                            )
                            await doc_repo.attach_summary(summary)
                    continue
                
                # Create new document - 保存所有文档，不管is_selected状态
                model = models.Document(
                    task_id=run.task_id,
                    run_id=run.id,
                    source_name=source_name,
                    external_id=doc["external_id"],
                    title=doc.get("title", ""),
                    abstract=doc.get("abstract"),
                    authors=doc.get("authors", []),
                    url=doc.get("url"),
                    published_at=doc.get("published_at"),
                    keywords=doc.get("keywords", []),
                    user_keywords=doc.get("user_keywords", []),
                    extra_metadata=doc.get("extra", {}),
                    is_filtered_in=is_selected,  # 根据is_selected设置
                    rank_score=doc.get("score", 0.0),
                )
                await doc_repo.add_documents([model])
                created_count += 1
                
                if doc.get("summary"):
                    summary = models.DocumentSummary(
                        document=model,
                        summary=doc.get("summary", ""),
                        highlights=doc.get("highlights", []),
                        agent_metadata={"source": "filtering_agent"},
                    )
                    await doc_repo.attach_summary(summary)
        
        await session.flush()
        logger.info("Persisted documents: {} created, {} updated, {} selected as relevant", 
                   created_count, updated_count, selected_count)

    async def _send_notifications(
        self,
        task: models.Task,
        filtered_docs: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Send notifications using MCP tools."""
        # Get notification config
        notification_config = task.notification_config or {}
        
        # Skip if notifications are disabled
        if not notification_config.get("enabled", False):
            logger.info(f"Task {task.id} '{task.name}': Notifications disabled")
            return
        
        enabled_channels = notification_config.get("channels", [])
        if not enabled_channels:
            logger.info(f"Task {task.id} '{task.name}': No notification channels configured")
            return
        
        # Prepare documents list for notifications
        all_docs = []
        for source_name, docs in filtered_docs.items():
            for doc in docs:
                doc_data = doc.copy()
                doc_data["source"] = source_name
                all_docs.append(doc_data)
        
        logger.info(f"Task {task.id}: Preparing to send notifications with {len(all_docs)} documents to channels: {enabled_channels}")
        
        # Check if we have documents to send
        if not all_docs:
            logger.warning(f"Task {task.id}: No documents to notify")
            return
        
        # Sort by relevance score
        all_docs.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # Send to each enabled channel
        for channel in enabled_channels:
            try:
                if channel == "email":
                    await self._send_email_notification(
                        task, all_docs, notification_config
                    )
                elif channel == "feishu":
                    await self._send_feishu_notification(
                        task, all_docs, notification_config
                    )
                else:
                    logger.warning(f"Unknown notification channel: {channel}")
            except Exception as e:
                logger.error(f"Failed to send {channel} notification: {str(e)}")
                logger.exception(f"Full exception for {channel}:")
    
    async def _send_email_notification(
        self,
        task: models.Task,
        documents: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> None:
        """Send email notification via MCP."""
        recipients = config.get("email_recipients", [])
        if not recipients:
            logger.warning(f"Task {task.id}: No email recipients configured")
            return
        
        logger.info(f"Task {task.id}: Sending email to {len(recipients)} recipients with {len(documents)} documents")
        
        # Get email tool from MCP server
        email_tool = mcp_server.get_tool("send_email")
        if not email_tool:
            logger.error("Email MCP tool not found")
            return
        
        # Format email subject
        subject_template = config.get("email_subject_template") or "{} 文献推送"
        subject = subject_template.format(task.name) if "{}" in subject_template else subject_template
        
        # Format email body using the tool's formatter
        body = email_tool.format_documents_html(
            documents=documents[:20],  # Limit to top 20
            task_name=task.name
        )
        
        logger.debug(f"Email subject: {subject}")
        logger.debug(f"Email body length: {len(body)} characters")
        
        # Send to each recipient
        for recipient in recipients:
            try:
                logger.info(f"Sending email to: {recipient}")
                result = await mcp_server.execute_tool(
                    "send_email",
                    to_email=recipient,
                    subject=subject,
                    body=body,
                    task_name=task.name
                )
                
                if result.success:
                    logger.info(f"Email sent successfully to {recipient} for task {task.id}")
                else:
                    logger.error(f"Failed to send email to {recipient}: {result.error}")
            except Exception as e:
                logger.error(f"Error sending email to {recipient}: {str(e)}")
                logger.exception(f"Full exception:")
    
    async def _send_feishu_notification(
        self,
        task: models.Task,
        documents: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> None:
        """Send Feishu notification via MCP."""
        webhook_url = config.get("feishu_webhook_url")
        if not webhook_url:
            logger.warning(f"Task {task.id}: No Feishu webhook URL configured")
            return
        
        logger.info(f"Task {task.id}: Sending Feishu notification with {len(documents)} documents")
        
        # Get Feishu tool from MCP server
        feishu_tool = mcp_server.get_tool("send_feishu")
        if not feishu_tool:
            logger.error("Feishu MCP tool not found")
            return
        
        try:
            logger.info(f"Executing Feishu webhook: {webhook_url[:50]}...")
            result = await mcp_server.execute_tool(
                "send_feishu",
                webhook_url=webhook_url,
                task_name=task.name,
                documents_count=len(documents),
                documents=documents[:10]  # Send top 10 documents
            )
            
            if result.success:
                logger.info(f"Feishu notification sent successfully for task {task.id}")
            else:
                logger.error(f"Failed to send Feishu notification: {result.error}")
        except Exception as e:
            logger.error(f"Error sending Feishu notification: {str(e)}")
            logger.exception(f"Full exception:")

    def _init_mcp_tools(self) -> None:
        """Initialize and register MCP tools."""
        # Register email tool
        email_tool = EmailTool()
        mcp_server.register_tool(email_tool)
        
        # Register Feishu tool
        feishu_tool = FeishuTool()
        mcp_server.register_tool(feishu_tool)
        
        logger.info("MCP tools initialized and registered")
