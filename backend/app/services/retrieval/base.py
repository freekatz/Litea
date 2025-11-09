"""Base classes for retrieval sources."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol


class RetrievalSource(Protocol):
    name: str

    async def search(self, prompt: str, keywords: List[str], parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for documents based on query and keywords."""
        ...

    async def get_detail(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed metadata for a document from its URL.
        
        Uses Zotero Web Translation API to extract structured metadata
        including title, abstract, authors, publication info, DOI, etc.
        
        Args:
            url: Document URL (e.g., arXiv abstract page, DOI link)
            
        Returns:
            Dictionary with detailed metadata or None if extraction fails
        """
        ...
