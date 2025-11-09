"""ArXiv retrieval source with HTTP fallback."""

from __future__ import annotations

import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

try:
    from pypaperbot.arxiv import Arxiv  # type: ignore[import]
except ImportError:  # pragma: no cover
    Arxiv = None  # type: ignore

from app.services.zotero.client import ZoteroClient


class ArxivRetrievalSource:
    """ArXiv source with PyPaperBot support and HTTP API fallback."""

    name = "arxiv"

    def __init__(self) -> None:
        self._client = Arxiv() if Arxiv is not None else None
        self._zotero_client = ZoteroClient()

    async def search(self, prompt: str, keywords: List[str], parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        query = parameters.get("query") or " OR ".join(keywords) or prompt
        max_results = int(parameters.get("max_results", 50))
        logger.info("Searching arXiv with query='{}', max_results={}", query, max_results)

        if self._client is not None:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self._client.search(
                    query,
                    max_results=max_results,
                    sort_by=parameters.get("sort_by", "submittedDate"),
                    sort_order=parameters.get("sort_order", "descending"),
                ),
            )
        else:
            logger.warning("PyPaperBot unavailable, using arXiv HTTP API")
            results = await self._search_via_http(
                query=query,
                max_results=max_results,
                sort_by=parameters.get("sort_by", "submittedDate"),
                sort_order=parameters.get("sort_order", "descending"),
            )

        documents: List[Dict[str, Any]] = []
        for item in results:
            published_at: Optional[datetime] = None
            raw_published = item.get("published")
            if raw_published:
                try:
                    published_at = datetime.fromisoformat(str(raw_published).replace("Z", "+00:00"))
                except ValueError:
                    published_at = None
            documents.append(
                {
                    "external_id": item.get("id", ""),
                    "title": item.get("title", ""),
                    "abstract": item.get("summary", ""),
                    "authors": item.get("authors", []),
                    "url": item.get("link", ""),
                    "published_at": published_at,
                    "source": self.name,
                    "extra": {k: v for k, v in item.items() if k not in {"id", "title", "summary", "authors", "link", "published"}},
                }
            )
        return documents

    async def _search_via_http(
        self,
        query: str,
        max_results: int = 50,
        sort_by: str = "submittedDate",
        sort_order: str = "descending",
        max_retries: int = 3,
    ) -> List[Dict[str, Any]]:
        """Fallback to arXiv HTTP API with retry mechanism."""
        url = "https://export.arxiv.org/api/query"
        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }
        
        last_error = None
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    return self._parse_atom_feed(response.text)
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_error = e
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(
                    "ArXiv API connection failed on attempt {} ({}). Retrying in {}s...",
                    attempt + 1,
                    type(e).__name__,
                    wait_time
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
            except httpx.HTTPStatusError as e:
                logger.error("ArXiv API returned error status {}: {}", e.response.status_code, e)
                last_error = e
                if e.response.status_code >= 500:  # Server error, retry
                    wait_time = 2 ** attempt
                    logger.warning("Server error, retrying in {}s...", wait_time)
                    if attempt < max_retries - 1:
                        await asyncio.sleep(wait_time)
                else:  # Client error, don't retry
                    break
            except Exception as e:
                logger.error("Unexpected error during arXiv search: {}", e)
                last_error = e
                break
        
        # All retries failed
        logger.error("Failed to retrieve from arXiv after {} attempts", max_retries)
        if last_error:
            raise last_error
        return []

    async def get_detail(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed metadata from arXiv URL using Zotero Web Translation API.
        
        Args:
            url: arXiv abstract page URL (e.g., https://arxiv.org/abs/2301.12345)
            
        Returns:
            Enhanced metadata dictionary with fields like:
            - DOI, journal, volume, issue
            - Complete author info (first/last names)
            - Publication date, access date
            - PDF links, citation info
            - Item type, language
        """
        logger.info("Fetching detailed metadata for arXiv URL: {}", url)
        
        # Use Zotero's web translation to extract metadata
        metadata = await self._zotero_client.retrieve_webpage_metadata(url)
        
        if not metadata:
            logger.warning("Failed to extract metadata from URL: {}", url)
            return None
        
        # Zotero returns structured data in Zotero item format
        # Example fields: title, abstractNote, creators, date, DOI, url, etc.
        logger.info("Successfully fetched detailed metadata with {} fields", len(metadata))
        return metadata

    def _parse_atom_feed(self, payload: str) -> List[Dict[str, Any]]:
        """Parse arXiv Atom feed."""
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(payload)
        documents: List[Dict[str, Any]] = []
        for entry in root.findall("atom:entry", ns):
            doc_id = entry.findtext("atom:id", default="", namespaces=ns)
            title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
            summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip()
            published = entry.findtext("atom:published", default="", namespaces=ns)
            links = entry.findall("atom:link", ns)
            link = ""
            for lnk in links:
                if lnk.attrib.get("rel") == "alternate":
                    link = lnk.attrib.get("href", "")
                    break
            authors = [author.findtext("atom:name", default="", namespaces=ns) for author in entry.findall("atom:author", ns)]
            documents.append(
                {
                    "id": doc_id,
                    "title": title,
                    "summary": summary,
                    "published": published,
                    "link": link,
                    "authors": [name for name in authors if name],
                }
            )
        return documents
