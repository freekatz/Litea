"""Database models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class RetrievalSource(Base):
    __tablename__ = "retrieval_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text())
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    task_sources: Mapped[List["TaskSource"]] = relationship(back_populates="source")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    prompt: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active")
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    run_at_hour: Mapped[Optional[int]] = mapped_column(Integer)
    run_at_minute: Mapped[int] = mapped_column(Integer, default=0)
    run_timezone: Mapped[str] = mapped_column(String(60), default="Asia/Shanghai")
    notification_config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # AI配置
    ai_config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # 文献筛选配置
    filter_config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # 文献总结配置
    summary_config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    keywords: Mapped[List["TaskKeyword"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    sources: Mapped[List["TaskSource"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    runs: Mapped[List["TaskRun"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    documents: Mapped[List["Document"]] = relationship(back_populates="task")


class TaskKeyword(Base):
    __tablename__ = "task_keywords"
    __table_args__ = (UniqueConstraint("task_id", "keyword", name="uq_task_keyword"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    is_user_defined: Mapped[bool] = mapped_column(Boolean, default=False)

    task: Mapped[Task] = relationship(back_populates="keywords")


class TaskSource(Base):
    __tablename__ = "task_sources"
    __table_args__ = (UniqueConstraint("task_id", "source_id", name="uq_task_sources"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("retrieval_sources.id", ondelete="CASCADE"), nullable=False)
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    task: Mapped[Task] = relationship(back_populates="sources")
    source: Mapped[RetrievalSource] = relationship(back_populates="task_sources")


class TaskRun(Base):
    __tablename__ = "task_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), default="running")
    retrieved_count: Mapped[int] = mapped_column(Integer, default=0)
    filtered_count: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[Optional[str]] = mapped_column(Text())
    run_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    task: Mapped[Task] = relationship(back_populates="runs")
    documents: Mapped[List["Document"]] = relationship(back_populates="run")


class Document(Base):
    __tablename__ = "documents"
    # 修改唯一约束：同一任务内相同来源的文献唯一，不同任务可以有相同的文献
    __table_args__ = (UniqueConstraint("task_id", "external_id", "source_name", name="uq_task_document_source"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("task_runs.id", ondelete="SET NULL"))
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    authors: Mapped[List[str]] = mapped_column(JSON, default=list)
    abstract: Mapped[Optional[str]] = mapped_column(Text())
    url: Mapped[Optional[str]] = mapped_column(String(500))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    keywords: Mapped[List[str]] = mapped_column(JSON, default=list)
    user_keywords: Mapped[List[str]] = mapped_column(JSON, default=list)
    extra_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    is_filtered_in: Mapped[bool] = mapped_column(Boolean, default=False)
    rank_score: Mapped[Optional[float]] = mapped_column(Float)
    zotero_key: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    task: Mapped[Optional[Task]] = relationship(back_populates="documents")
    run: Mapped[Optional[TaskRun]] = relationship(back_populates="documents")
    summary: Mapped[Optional["DocumentSummary"]] = relationship(back_populates="document", uselist=False, cascade="all, delete-orphan")


class DocumentSummary(Base):
    __tablename__ = "document_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), unique=True)
    summary: Mapped[str] = mapped_column(Text(), nullable=False)
    highlights: Mapped[List[str]] = mapped_column(JSON, default=list)
    research_trends: Mapped[List[str]] = mapped_column(JSON, default=list)
    agent_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    document: Mapped[Document] = relationship(back_populates="summary")


class HistoricalMetric(Base):
    __tablename__ = "historical_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    metric_type: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    task: Mapped[Task] = relationship()
