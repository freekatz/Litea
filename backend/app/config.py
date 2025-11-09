"""Application configuration models."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    url: str = Field(default="sqlite+aiosqlite:///./litea.db")
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10


class AIProviderConfig(BaseModel):
    name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    extra: Dict[str, str] = Field(default_factory=dict)


class AISettings(BaseModel):
    default_provider: str = "openai"
    providers: Dict[str, AIProviderConfig] = Field(default_factory=dict)
    keyword_model: Optional[str] = None
    filter_model: Optional[str] = None
    summary_model: Optional[str] = None


class EmailTemplateConfig(BaseModel):
    subject_template: str = "{{ task_name }} 文献推送"
    body_header: str = "您好，以下是今日的文献推送："
    body_footer: str = "感谢使用 Litea！"
    show_source_sections: bool = True
    show_rankings: bool = True
    display_mode: str = Field(default="grouped", description="grouped or ranked")


class EmailSettings(BaseModel):
    smtp_host: str = "localhost"
    smtp_port: int = 587
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True
    sender: str = "litea@example.com"
    template: EmailTemplateConfig = Field(default_factory=EmailTemplateConfig)


class SchedulerSettings(BaseModel):
    timezone: str = "Asia/Shanghai"
    jobstore_url: Optional[str] = None


class ZoteroSettings(BaseModel):
    api_key: str = ""
    library_id: str = ""
    library_type: str = "user"
    requests_per_minute: int = 60


class RetrievalSourceConfig(BaseModel):
    name: str
    enabled: bool = True
    parameters: Dict[str, str] = Field(default_factory=dict)


class RetrievalSettings(BaseModel):
    sources: List[RetrievalSourceConfig] = Field(default_factory=lambda: [RetrievalSourceConfig(name="arxiv")])


class AuthSettings(BaseModel):
    """Authentication settings."""
    admin_password: str = Field(default="admin123")
    jwt_secret: str = Field(default="your-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 30


class LiteaSettings(BaseSettings):
    """Top-level application settings."""

    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    ai: AISettings = Field(default_factory=AISettings)
    email: EmailSettings = Field(default_factory=EmailSettings)
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings)
    zotero: ZoteroSettings = Field(default_factory=ZoteroSettings)
    retrieval: RetrievalSettings = Field(default_factory=RetrievalSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )


@lru_cache
def get_settings() -> LiteaSettings:
    """Load settings once."""

    return LiteaSettings(_env_file=Path(__file__).resolve().parent.parent / ".env")
