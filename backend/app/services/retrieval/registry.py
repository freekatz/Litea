"""Registry to manage retrieval sources."""

from __future__ import annotations

from typing import Dict, Type

from loguru import logger

from app.config import get_settings
from app.services.retrieval.arxiv_source import ArxivRetrievalSource


class RetrievalRegistry:
    """Manages retrieval sources."""

    _source_classes: Dict[str, Type] = {
        "arxiv": ArxivRetrievalSource,
    }

    def __init__(self) -> None:
        self._instances: Dict[str, object] = {}
        self._load_from_config()

    def _load_from_config(self) -> None:
        settings = get_settings()
        for source_conf in settings.retrieval.sources:
            if not source_conf.enabled:
                continue
            if source_conf.name in self._source_classes:
                try:
                    self._instances[source_conf.name] = self._source_classes[source_conf.name]()
                except Exception as exc:  # pragma: no cover - log and continue
                    logger.error("Failed to init source {}: {}", source_conf.name, exc)
            else:
                logger.warning("Skipping unregistered source: {}", source_conf.name)

    def get(self, name: str):
        if name not in self._instances:
            raise KeyError(f"Retrieval source '{name}' is not available")
        return self._instances[name]

    def list_sources(self) -> Dict[str, object]:
        return dict(self._instances)
