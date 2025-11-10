"""Filtering agent service."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List

from loguru import logger

from app.config import get_settings
from app.services.ai.crew_manager import CrewManager

_SETTINGS = get_settings()
_FILTER_DEFAULTS = (_SETTINGS.static.filter_defaults if _SETTINGS.static else {})
DEFAULT_MIN_SCORE = float(_FILTER_DEFAULTS.get("min_relevance_score", 0.4))
DEFAULT_MAX_DOCS_PER_SOURCE = int(_FILTER_DEFAULTS.get("max_documents_per_source", 50))


class FilteringAgentService:
    """Run crew to filter documents with retry mechanism."""

    def __init__(self, crew_manager: CrewManager | None = None, max_retries: int = 3) -> None:
        self._crew_manager = crew_manager or CrewManager()
        self._max_retries = max_retries

    async def filter_documents(
        self,
        task_context: Dict[str, Any],
        documents: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Filter documents using AI agent with retry mechanism - one agent per document."""
        if not documents:
            logger.warning("No documents to filter")
            return []
        
        # 获取筛选配置
        filter_config = task_context.get("filter_config") or {}
        
        # 检查是否启用AI筛选
        if not filter_config.get("enabled", True):
            logger.info("AI filtering is disabled, returning all documents")
            return self._create_fallback_results(documents)
        
        # 限制每个来源的文档数量
        max_docs = int(filter_config.get("max_documents_per_source", DEFAULT_MAX_DOCS_PER_SOURCE))
        documents_to_filter = documents[:max_docs] if len(documents) > max_docs else documents
        
        logger.info(f"Filtering {len(documents_to_filter)} documents (out of {len(documents)}) for task: {task_context.get('task_name', 'unknown')}")
        
        # 为每篇文档创建独立的筛选任务
        all_results = []
        for idx, doc in enumerate(documents_to_filter):
            logger.debug(f"Processing document {idx + 1}/{len(documents_to_filter)}: {doc.get('title', 'Unknown')[:50]}")
            
            for attempt in range(self._max_retries):
                try:
                    # 为单个文档构建crew
                    crew = self._crew_manager.build_single_doc_filtering_crew(task_context, doc)
                    
                    # Execute crew
                    if hasattr(crew, "kickoff_async"):
                        result = await crew.kickoff_async()
                    else:  # pragma: no cover - fallback for older crewai versions
                        result = await asyncio.to_thread(crew.kickoff)
                    
                    # Parse output
                    raw_output = getattr(result, "output", None) or str(result)
                    logger.debug(f"Raw crew output for doc {idx + 1}: {raw_output[:300]}...")
                    
                    # 解析单个文档的结果
                    doc_result = self._parse_single_doc_result(raw_output, doc, filter_config)
                    
                    if doc_result:
                        all_results.append(doc_result)
                        logger.info(f"Document {idx + 1}/{len(documents_to_filter)} - '{doc.get('title', 'Unknown')[:50]}': is_selected={doc_result.get('is_selected')}, score={doc_result.get('score'):.3f}")
                        break  # Success, move to next document
                    else:
                        logger.warning(f"No valid result for doc {idx + 1} on attempt {attempt + 1}, raw output: {raw_output[:200]}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error for doc {idx + 1} on attempt {attempt + 1}: {e}")
                    if attempt < self._max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                        
                except Exception as e:
                    logger.error(f"Filtering error for doc {idx + 1} on attempt {attempt + 1}: {e}")
                    if attempt < self._max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        # Last attempt failed, add fallback result
                        logger.warning(f"All retry attempts failed for doc {idx + 1}, using fallback")
                        all_results.append(self._create_single_fallback_result(doc))
                        break
            
            # If all retries failed and no fallback was added
            if len(all_results) < idx + 1:
                all_results.append(self._create_single_fallback_result(doc))
        
        logger.info(f"Successfully filtered {len(all_results)} documents")
        return all_results
    
    def _parse_and_normalize(self, raw_output: str, original_docs: List[Dict[str, Any]], filter_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse and normalize filtering results."""
        # Try to extract JSON from markdown code blocks
        if "```json" in raw_output:
            start = raw_output.find("```json") + 7
            end = raw_output.find("```", start)
            if end > start:
                raw_output = raw_output[start:end].strip()
        elif "```" in raw_output:
            start = raw_output.find("```") + 3
            end = raw_output.find("```", start)
            if end > start:
                raw_output = raw_output[start:end].strip()
        
        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError:
            # Try to find JSON array in the text
            start_idx = raw_output.find("[")
            end_idx = raw_output.rfind("]")
            if start_idx != -1 and end_idx != -1:
                try:
                    data = json.loads(raw_output[start_idx:end_idx + 1])
                except json.JSONDecodeError:
                    logger.error("Failed to extract JSON from output")
                    return []
            else:
                return []
        
        if not isinstance(data, list):
            logger.warning(f"Expected list, got {type(data)}")
            return []
        
        # 获取最低相关度阈值
        min_score = float(filter_config.get("min_relevance_score", DEFAULT_MIN_SCORE))
        
        normalized: List[Dict[str, Any]] = []
        doc_map = {doc.get("external_id"): doc for doc in original_docs}
        
        for item in data:
            if not isinstance(item, dict):
                continue
            
            external_id = str(item.get("external_id", ""))
            if not external_id or external_id not in doc_map:
                continue
            
            score = max(0.0, min(1.0, float(item.get("score", 0.5))))  # Clamp to [0, 1]
            is_selected = bool(item.get("is_selected", True))
            
            # 应用最低相关度阈值
            if is_selected and score < min_score:
                logger.debug(f"Document {external_id} filtered out by min_relevance_score: {score} < {min_score}")
                is_selected = False
            
            normalized.append({
                "external_id": external_id,
                "is_selected": is_selected,
                "score": score,
                "summary": str(item.get("summary", ""))[:500],  # Limit length
                "highlights": [str(h) for h in item.get("highlights", [])[:5]],  # Max 5 highlights
            })
        
        return normalized
    
    def _parse_single_doc_result(self, raw_output: str, original_doc: Dict[str, Any], filter_config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse result for a single document."""
        # Try to extract JSON from markdown code blocks
        if "```json" in raw_output:
            start = raw_output.find("```json") + 7
            end = raw_output.find("```", start)
            if end > start:
                raw_output = raw_output[start:end].strip()
        elif "```" in raw_output:
            start = raw_output.find("```") + 3
            end = raw_output.find("```", start)
            if end > start:
                raw_output = raw_output[start:end].strip()
        
        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError:
            # Try to find JSON object in the text
            start_idx = raw_output.find("{")
            end_idx = raw_output.rfind("}")
            if start_idx != -1 and end_idx != -1:
                try:
                    data = json.loads(raw_output[start_idx:end_idx + 1])
                except json.JSONDecodeError:
                    logger.error("Failed to extract JSON from output")
                    return {}
            else:
                return {}
        
        if not isinstance(data, dict):
            logger.warning(f"Expected dict, got {type(data)}")
            return {}
        
        # 获取最低相关度阈值
        min_score = float(filter_config.get("min_relevance_score", DEFAULT_MIN_SCORE))
        
        external_id = str(original_doc.get("external_id", ""))
        score = max(0.0, min(1.0, float(data.get("score", 0.5))))  # Clamp to [0, 1]
        is_selected_raw = bool(data.get("is_selected", True))
        
        logger.info(f"Parsing result for {external_id}: raw is_selected={is_selected_raw}, score={score:.3f}, min_score={min_score}")
        
        # 应用最低相关度阈值
        is_selected = is_selected_raw
        if is_selected and score < min_score:
            logger.warning(f"Document {external_id} filtered out by min_relevance_score: {score:.3f} < {min_score}")
            is_selected = False
        
        return {
            "external_id": external_id,
            "is_selected": is_selected,
            "score": score,
            "summary": str(data.get("summary", ""))[:500],  # Limit length
            "highlights": [str(h) for h in data.get("highlights", [])[:5]],  # Max 5 highlights
        }
    
    def _create_single_fallback_result(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback result for a single document when filtering fails."""
        return {
            "external_id": document.get("external_id", ""),
            "is_selected": True,  # Accept by default
            "score": 0.5,
            "summary": document.get("abstract", "")[:200] if document.get("abstract") else "无摘要",
            "highlights": [],
        }
    
    def _create_fallback_results(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create fallback results when filtering fails."""
        return [
            {
                "external_id": doc.get("external_id", ""),
                "is_selected": True,  # Accept all by default
                "score": 0.5,
                "summary": doc.get("abstract", "")[:200] if doc.get("abstract") else "无摘要",
                "highlights": [],
            }
            for doc in documents
        ]
