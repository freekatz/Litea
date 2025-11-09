"""Summarization agent service."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List

from loguru import logger

from app.services.ai.crew_manager import CrewManager


class SummarizationAgentService:
    """Generate overall summary for a task run with customizable templates."""

    def __init__(self, crew_manager: CrewManager | None = None, max_retries: int = 3) -> None:
        self._crew_manager = crew_manager or CrewManager()
        self._max_retries = max_retries

    async def summarize(
        self,
        task_context: Dict[str, Any],
        documents: List[Dict[str, Any]],
        summary_template: str | None = None,
    ) -> Dict[str, Any]:
        """Generate summary with retry mechanism and custom template support."""
        if not documents:
            logger.warning("No documents to summarize")
            return self._create_empty_summary()
        
        logger.info(f"Summarizing {len(documents)} documents for task: {task_context.get('task_name', 'unknown')}")
        
        # Add template to context if provided
        if summary_template:
            task_context = {**task_context, "summary_template": summary_template}
        
        for attempt in range(self._max_retries):
            try:
                crew = self._crew_manager.build_summary_crew(task_context, documents)
                
                # Execute crew
                if hasattr(crew, "kickoff_async"):
                    result = await crew.kickoff_async()
                else:  # pragma: no cover
                    result = await asyncio.to_thread(crew.kickoff)
                
                # Parse output
                raw_output = getattr(result, "output", None) or str(result)
                logger.debug(f"Raw summary output: {raw_output[:500]}...")
                
                summary = self._parse_and_validate(raw_output, documents)
                
                if summary and summary.get("trend_summary"):
                    logger.info("Successfully generated summary")
                    return summary
                else:
                    logger.warning(f"Invalid summary on attempt {attempt + 1}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error on attempt {attempt + 1}: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                    
            except Exception as e:
                logger.error(f"Summarization error on attempt {attempt + 1}: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    logger.warning("All retry attempts failed, returning fallback summary")
                    return self._create_fallback_summary(documents)
        
        # If we get here, all retries failed
        logger.error("Failed to generate summary after all retries")
        return self._create_fallback_summary(documents)
    
    def _parse_and_validate(self, raw_output: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse and validate summary output."""
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
                    return self._create_empty_summary()
            else:
                return self._create_empty_summary()
        
        if not isinstance(data, dict):
            logger.warning(f"Expected dict, got {type(data)}")
            return self._create_empty_summary()
        
        # Normalize and validate structure
        return {
            "trend_summary": str(data.get("trend_summary", ""))[:2000],  # Limit length
            "rankings": self._normalize_rankings(data.get("rankings", []), documents),
            "sections": self._normalize_sections(data.get("sections", [])),
            "key_insights": data.get("key_insights", [])[:10],  # Max 10 insights
            "research_directions": data.get("research_directions", [])[:5],  # Max 5 directions
        }
    
    def _normalize_rankings(self, rankings: List[Any], documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize rankings to ensure valid structure."""
        if not isinstance(rankings, list):
            return []
        
        normalized = []
        for item in rankings[:10]:  # Top 10 max
            if not isinstance(item, dict):
                continue
            
            normalized.append({
                "title": str(item.get("title", ""))[:200],
                "score": max(0.0, min(1.0, float(item.get("score", 0.0)))),
                "reason": str(item.get("reason", ""))[:300],
                "external_id": str(item.get("external_id", "")),
            })
        
        return normalized
    
    def _normalize_sections(self, sections: List[Any]) -> List[Dict[str, Any]]:
        """Normalize sections to ensure valid structure."""
        if not isinstance(sections, list):
            return []
        
        normalized = []
        for item in sections[:8]:  # Max 8 sections
            if not isinstance(item, dict):
                continue
            
            papers = item.get("papers", [])
            if not isinstance(papers, list):
                papers = []
            
            normalized.append({
                "category": str(item.get("category", "其他"))[:100],
                "papers": [str(p)[:200] for p in papers[:10]],  # Max 10 papers per section
                "description": str(item.get("description", ""))[:300],
            })
        
        return normalized
    
    def _create_empty_summary(self) -> Dict[str, Any]:
        """Create empty summary structure."""
        return {
            "trend_summary": "",
            "rankings": [],
            "sections": [],
            "key_insights": [],
            "research_directions": [],
        }
    
    def _create_fallback_summary(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create basic fallback summary when AI fails."""
        doc_count = len(documents)
        avg_score = sum(doc.get("score", 0.5) for doc in documents) / doc_count if doc_count > 0 else 0
        
        # Simple rankings by score
        sorted_docs = sorted(documents, key=lambda d: d.get("score", 0), reverse=True)
        rankings = [
            {
                "title": doc.get("title", "无标题"),
                "score": doc.get("score", 0.5),
                "reason": "基于相关性评分自动排序",
                "external_id": doc.get("external_id", ""),
            }
            for doc in sorted_docs[:10]
        ]
        
        return {
            "trend_summary": f"本次检索共找到 {doc_count} 篇相关文献，平均相关性评分为 {avg_score:.2f}。由于AI总结服务暂时不可用，以下为基础统计信息。",
            "rankings": rankings,
            "sections": [
                {
                    "category": "全部文献",
                    "papers": [doc.get("title", "无标题") for doc in sorted_docs[:20]],
                    "description": "按相关性排序的文献列表",
                }
            ],
            "key_insights": [
                f"共检索到 {doc_count} 篇文献",
                f"平均相关性评分: {avg_score:.2f}",
            ],
            "research_directions": [],
        }
