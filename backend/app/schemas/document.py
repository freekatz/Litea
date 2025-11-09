"""Document schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentSummaryResponse(BaseModel):
    summary: str
    highlights: List[str] = Field(default_factory=list)
    research_trends: List[str] = Field(default_factory=list)
    agent_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class DocumentResponse(BaseModel):
    id: int
    task_id: Optional[int]
    run_id: Optional[int]
    source_name: str
    external_id: str
    title: str
    authors: List[str]
    abstract: Optional[str]
    url: Optional[str]
    published_at: Optional[datetime]
    created_at: datetime  # 添加收录时间
    keywords: List[str]
    user_keywords: List[str]
    extra_metadata: Dict[str, Any]
    is_filtered_in: bool
    rank_score: Optional[float]
    zotero_key: Optional[str] = None
    summary: Optional[DocumentSummaryResponse] = None


class DocumentListQuery(BaseModel):
    task_id: Optional[int] = None
    source_name: Optional[str] = None
    keyword: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = 50
    offset: int = 0
