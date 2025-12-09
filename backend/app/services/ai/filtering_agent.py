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

# 批量筛选配置
COARSE_BATCH_SIZE = 30  # 粗筛每批处理的文献数
FINE_BATCH_SIZE = 8     # 精筛每批处理的文献数


class FilteringAgentService:
    """Run crew to filter documents with two-stage filtering: coarse + fine."""

    def __init__(self, crew_manager: CrewManager | None = None, max_retries: int = 3) -> None:
        self._crew_manager = crew_manager or CrewManager()
        self._max_retries = max_retries

    async def filter_documents(
        self,
        task_context: Dict[str, Any],
        documents: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Filter documents using two-stage AI filtering: coarse then fine."""
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
        
        logger.info(f"Starting two-stage filtering for {len(documents_to_filter)} documents (task: {task_context.get('task_name', 'unknown')})")
        
        # 第一阶段：粗筛 - 基于标题快速筛选，批量处理
        coarse_results = await self._coarse_filter(task_context, documents_to_filter, filter_config)
        
        # 获取粗筛通过的文档
        passed_doc_ids = {r["external_id"] for r in coarse_results if r.get("is_selected", False)}
        passed_docs = [d for d in documents_to_filter if d.get("external_id") in passed_doc_ids]
        
        logger.info(f"Coarse filtering: {len(passed_docs)}/{len(documents_to_filter)} documents passed")
        
        if not passed_docs:
            logger.warning("No documents passed coarse filtering")
            return coarse_results
        
        # 第二阶段：精筛 - 详细评估，批量处理
        fine_results = await self._fine_filter(task_context, passed_docs, filter_config)
        
        # 合并结果：粗筛未通过的 + 精筛结果
        final_results = []
        fine_result_map = {r["external_id"]: r for r in fine_results}
        
        for doc in documents_to_filter:
            doc_id = doc.get("external_id")
            if doc_id in fine_result_map:
                final_results.append(fine_result_map[doc_id])
            else:
                # 粗筛未通过的文档
                coarse_result = next((r for r in coarse_results if r["external_id"] == doc_id), None)
                if coarse_result:
                    final_results.append(coarse_result)
                else:
                    final_results.append(self._create_single_fallback_result(doc))
        
        selected_count = sum(1 for r in final_results if r.get("is_selected", False))
        logger.info(f"Two-stage filtering complete: {selected_count}/{len(documents_to_filter)} documents selected")
        
        return final_results

    async def _coarse_filter(
        self,
        task_context: Dict[str, Any],
        documents: List[Dict[str, Any]],
        filter_config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """第一阶段：粗筛 - 基于标题快速筛选大批量文献"""
        all_results = []
        
        # 分批处理
        for batch_start in range(0, len(documents), COARSE_BATCH_SIZE):
            batch_docs = documents[batch_start:batch_start + COARSE_BATCH_SIZE]
            batch_num = batch_start // COARSE_BATCH_SIZE + 1
            total_batches = (len(documents) + COARSE_BATCH_SIZE - 1) // COARSE_BATCH_SIZE
            
            logger.info(f"Coarse filter batch {batch_num}/{total_batches}: {len(batch_docs)} documents")
            
            for attempt in range(self._max_retries):
                try:
                    crew = self._crew_manager.build_coarse_filtering_crew(task_context, batch_docs)
                    
                    if hasattr(crew, "kickoff_async"):
                        result = await crew.kickoff_async()
                    else:
                        result = await asyncio.to_thread(crew.kickoff)
                    
                    raw_output = getattr(result, "output", None) or str(result)
                    logger.debug(f"Coarse filter raw output: {raw_output[:500]}...")
                    
                    batch_results = self._parse_batch_results(raw_output, batch_docs, filter_config, is_coarse=True)
                    
                    if batch_results:
                        all_results.extend(batch_results)
                        logger.info(f"Coarse batch {batch_num}: {sum(1 for r in batch_results if r.get('is_selected'))} passed")
                        break
                    else:
                        logger.warning(f"Coarse batch {batch_num} attempt {attempt + 1}: no valid results")
                        
                except Exception as e:
                    logger.error(f"Coarse batch {batch_num} attempt {attempt + 1} error: {e}")
                    if attempt < self._max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        # 失败时默认通过粗筛
                        for doc in batch_docs:
                            all_results.append({
                                "external_id": doc.get("external_id", ""),
                                "is_selected": True,  # 粗筛失败时默认通过
                                "score": 0.5,
                                "summary": "",
                                "highlights": [],
                            })
        
        return all_results

    async def _fine_filter(
        self,
        task_context: Dict[str, Any],
        documents: List[Dict[str, Any]],
        filter_config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """第二阶段：精筛 - 详细评估文献，批量处理"""
        all_results = []
        
        # 分批处理
        for batch_start in range(0, len(documents), FINE_BATCH_SIZE):
            batch_docs = documents[batch_start:batch_start + FINE_BATCH_SIZE]
            batch_num = batch_start // FINE_BATCH_SIZE + 1
            total_batches = (len(documents) + FINE_BATCH_SIZE - 1) // FINE_BATCH_SIZE
            
            logger.info(f"Fine filter batch {batch_num}/{total_batches}: {len(batch_docs)} documents")
            
            for attempt in range(self._max_retries):
                try:
                    crew = self._crew_manager.build_fine_filtering_crew(task_context, batch_docs)
                    
                    if hasattr(crew, "kickoff_async"):
                        result = await crew.kickoff_async()
                    else:
                        result = await asyncio.to_thread(crew.kickoff)
                    
                    raw_output = getattr(result, "output", None) or str(result)
                    logger.debug(f"Fine filter raw output: {raw_output[:500]}...")
                    
                    batch_results = self._parse_batch_results(raw_output, batch_docs, filter_config, is_coarse=False)
                    
                    if batch_results:
                        all_results.extend(batch_results)
                        logger.info(f"Fine batch {batch_num}: {sum(1 for r in batch_results if r.get('is_selected'))} selected")
                        break
                    else:
                        logger.warning(f"Fine batch {batch_num} attempt {attempt + 1}: no valid results")
                        
                except Exception as e:
                    logger.error(f"Fine batch {batch_num} attempt {attempt + 1} error: {e}")
                    if attempt < self._max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                    else:
                        # 失败时使用fallback
                        for doc in batch_docs:
                            all_results.append(self._create_single_fallback_result(doc))
        
        return all_results

    def _parse_batch_results(
        self,
        raw_output: str,
        original_docs: List[Dict[str, Any]],
        filter_config: Dict[str, Any],
        is_coarse: bool = False,
    ) -> List[Dict[str, Any]]:
        """解析批量筛选结果"""
        # 提取 JSON
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
            # 尝试找 JSON 数组
            start_idx = raw_output.find("[")
            end_idx = raw_output.rfind("]")
            if start_idx != -1 and end_idx != -1:
                try:
                    data = json.loads(raw_output[start_idx:end_idx + 1])
                except json.JSONDecodeError:
                    logger.error("Failed to extract JSON from batch output")
                    return []
            else:
                return []
        
        if not isinstance(data, list):
            logger.warning(f"Expected list, got {type(data)}")
            return []
        
        min_score = float(filter_config.get("min_relevance_score", DEFAULT_MIN_SCORE))
        # 粗筛使用更低的阈值
        if is_coarse:
            min_score = max(0.2, min_score - 0.2)
        
        normalized = []
        doc_map = {doc.get("external_id"): doc for doc in original_docs}
        
        for item in data:
            if not isinstance(item, dict):
                continue
            
            external_id = str(item.get("external_id", ""))
            if not external_id or external_id not in doc_map:
                continue
            
            score = max(0.0, min(1.0, float(item.get("score", 0.5))))
            is_selected = bool(item.get("is_selected", True))
            
            # 应用阈值
            if is_selected and score < min_score:
                logger.debug(f"Document {external_id} filtered by threshold: {score:.3f} < {min_score}")
                is_selected = False
            
            normalized.append({
                "external_id": external_id,
                "is_selected": is_selected,
                "score": score,
                "summary": str(item.get("summary", ""))[:500],
                "highlights": [str(h) for h in item.get("highlights", [])[:5]],
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
