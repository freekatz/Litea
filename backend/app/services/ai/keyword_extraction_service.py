"""Keyword extraction logic via AI."""

from __future__ import annotations

import json
from typing import List

from app.config import get_settings
from app.services.ai.provider_registry import ProviderRegistry


class KeywordExtractionService:
    """Use AI model to suggest keywords."""

    def __init__(self, provider_registry: ProviderRegistry | None = None) -> None:
        self._registry = provider_registry or ProviderRegistry()

    async def extract_keywords(self, prompt: str, max_keywords: int = 10) -> List[str]:
        settings = get_settings()
        provider = self._registry.get(settings.ai.default_provider)
        payload = {
            "model": settings.ai.keyword_model or provider.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a scientific literature search assistant. Extract relevant English keywords for academic paper search from user's research description. Output MUST be a JSON array with English keywords only. Example: {\"keywords\": [\"deep learning\", \"computer vision\", \"neural networks\"]}",
                },
                {
                    "role": "user", 
                    "content": f"Research topic: {prompt}\n\nExtract 5-10 English keywords for searching academic databases like arXiv, PubMed, etc. Keywords should be:\n1. In English only\n2. Commonly used in academic literature\n3. Specific to the research domain\n4. Suitable for search queries"
                },
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.4,
            "top_p": 0.9,
        }
        response = await provider.request(payload)
        raw = response.get("choices", [{}])[0].get("message", {}).get("content", "[]")
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and "keywords" in data:
                keywords = data.get("keywords", [])
            elif isinstance(data, list):
                keywords = data
            else:
                keywords = []
        except json.JSONDecodeError:
            keywords = []
        
        # Clean and deduplicate keywords (case-insensitive)
        # Also validate that keywords are in English (basic check: contains only ASCII letters, numbers, spaces, hyphens)
        result = []
        seen = set()
        for k in keywords:
            keyword = str(k).strip()
            keyword_lower = keyword.lower()
            
            # Basic validation: keyword should be primarily ASCII (English)
            if keyword and keyword_lower not in seen:
                # Check if keyword is mostly ASCII characters
                ascii_chars = sum(1 for c in keyword if ord(c) < 128)
                if ascii_chars / len(keyword) > 0.8:  # At least 80% ASCII characters
                    seen.add(keyword_lower)
                    result.append(keyword)
                    if len(result) >= max_keywords:
                        break
        
        return result
