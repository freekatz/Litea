"""Task related schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class KeywordSchema(BaseModel):
    keyword: str
    is_user_defined: bool = False


class SourceConfigSchema(BaseModel):
    source_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class NotificationChannelConfig(BaseModel):
    """Notification channel configuration."""
    enabled: bool = Field(default=False, description="是否启用通知")
    channels: List[str] = Field(default_factory=list, description="启用的通知渠道: email, feishu")
    
    # Email configuration
    email_recipients: List[str] = Field(default_factory=list, description="邮件接收人列表")
    email_subject_template: Optional[str] = Field(None, description="邮件主题模板")
    
    # Feishu configuration
    feishu_webhook_url: Optional[str] = Field(None, description="飞书群机器人Webhook URL")
    
    # Notification options
    schedule: Optional[str] = Field(None, description="通知计划（暂未使用）")
    options: Dict[str, Any] = Field(default_factory=dict, description="其他选项")



class AIModelConfig(BaseModel):
    """AI模型配置"""
    provider: str = Field(default="deepseek", description="AI提供商: openai, deepseek, doubao, qwen等")
    model: str = Field(default="deepseek-chat", description="模型名称")
    api_key: Optional[str] = Field(None, description="API密钥（可选，使用全局配置）")
    base_url: Optional[str] = Field(None, description="API基础URL（可选）")
    temperature: float = Field(default=0.7, ge=0, le=2, description="温度参数")
    max_tokens: Optional[int] = Field(None, description="最大token数")


class FilterConfig(BaseModel):
    """文献筛选配置"""
    enabled: bool = Field(default=True, description="是否启用AI筛选")
    filter_prompt: Optional[str] = Field(None, description="筛选提示词（可选，使用默认）")
    min_relevance_score: float = Field(default=0.4, ge=0, le=1, description="最低相关度阈值")
    max_documents_per_source: int = Field(default=50, ge=1, le=200, description="每个来源最多筛选文献数")
    use_abstract_only: bool = Field(default=True, description="仅使用摘要进行筛选")


class SummaryConfig(BaseModel):
    """文献总结配置"""
    enabled: bool = Field(default=True, description="是否启用AI总结")
    summary_prompt: Optional[str] = Field(None, description="总结提示词（可选，使用默认）")
    generate_individual_summary: bool = Field(default=True, description="为每篇文献生成独立总结")
    generate_overall_summary: bool = Field(default=True, description="生成整体总结")
    display_mode: str = Field(default="grouped", description="展示模式: grouped(按来源分组) 或 ranked(按排名)")
    items_per_source: int = Field(default=5, ge=1, le=50, description="每个来源展示的文献数（分组模式）")
    top_n_ranked: int = Field(default=10, ge=1, le=100, description="展示的top文献数（排名模式）")
    include_trends: bool = Field(default=True, description="包含研究趋势分析")


class TaskBase(BaseModel):
    name: str
    prompt: str
    keywords: List[KeywordSchema] = Field(default_factory=list)
    sources: List[SourceConfigSchema] = Field(default_factory=list)
    notification: NotificationChannelConfig = Field(default_factory=NotificationChannelConfig)
    run_at_hour: Optional[int] = Field(None, ge=0, le=23)
    run_at_minute: int = Field(0, ge=0, le=59)
    run_timezone: Optional[str] = None
    
    # 新增配置项
    ai_config: AIModelConfig = Field(default_factory=AIModelConfig)
    filter_config: FilterConfig = Field(default_factory=FilterConfig)
    summary_config: SummaryConfig = Field(default_factory=SummaryConfig)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(TaskBase):
    id: int
    status: Optional[str] = None


class TaskResponse(TaskBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None


class TaskRunResponse(BaseModel):
    id: int
    task_id: int
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    retrieved_count: int
    filtered_count: int
    summary: Optional[str]
