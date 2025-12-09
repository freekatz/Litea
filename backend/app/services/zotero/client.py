"""Wrapper around PyZotero with safety checks."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from loguru import logger

from pyzotero import zotero

from app.config import get_settings


class ZoteroClient:
    """Handle Zotero persistence while avoiding destructive actions."""

    def __init__(self) -> None:
        settings = get_settings().zotero
        if not settings.api_key or not settings.library_id or zotero is None:
            self._client = None
            logger.warning("Zotero client disabled: missing configuration or pyzotero not installed")
        else:
            # Validate library_id is numeric for user libraries
            if settings.library_type == "user":
                try:
                    # library_id must be a valid integer for user libraries
                    int(settings.library_id)
                except ValueError:
                    self._client = None
                    logger.error(
                        "Zotero client disabled: library_id must be numeric for user libraries. "
                        "Current value: '{}'. Please set ZOTERO__LIBRARY_ID to your numeric user ID "
                        "from https://www.zotero.org/settings/keys",
                        settings.library_id
                    )
                    return
            
            self._client = zotero.Zotero(settings.library_id, settings.library_type, settings.api_key)
            logger.info("Zotero client initialized for library {}", settings.library_id)

    async def get_or_create_collection(self, collection_name: str) -> Optional[str]:
        """Get existing collection key or create new one."""
        if not self._client or not collection_name:
            return None
        try:
            # Get all collections
            collections = self._client.collections()
            
            # Check if collection already exists
            for coll in collections:
                if coll["data"]["name"] == collection_name:
                    logger.info("Found existing Zotero collection '{}' with key: {}", collection_name, coll["key"])
                    return coll["key"]
            
            # Collection doesn't exist, create new one
            logger.info("Creating new Zotero collection '{}'", collection_name)
            
            # create_collections expects a list of dictionaries with 'name' and optionally 'parentCollection'
            new_coll_template = [{"name": collection_name}]
            response = self._client.create_collections(new_coll_template)
            
            # Response format: {'successful': {'0': {'key': 'ABC123', 'version': 1, 'data': {...}}}, 'failed': {}}
            if isinstance(response, dict) and "successful" in response and response["successful"]:
                # Get the first (and only) successful item
                first_key = list(response["successful"].keys())[0]
                collection_key = response["successful"][first_key]["key"]
                logger.info("Successfully created Zotero collection '{}' with key: {}", collection_name, collection_key)
                return collection_key
            else:
                logger.error("Failed to create Zotero collection '{}': unexpected response format: {}", collection_name, response)
                return None
                
        except Exception as exc:
            logger.error("Failed to get/create Zotero collection '{}': {}", collection_name, exc)
            logger.exception("Full exception details:")
            return None

    async def retrieve_webpage_metadata(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Use Zotero Web Translation API to extract metadata from webpage.
        
        Returns structured metadata including:
        - title, abstract, authors, publication date
        - DOI, ISSN, journal name
        - PDF links, citation info
        """
        if not self._client:
            logger.warning("Zotero metadata extraction skipped: client not initialized")
            return None
        
        try:
            # PyZotero's retrieve_webpage uses Zotero's web translation server
            # to parse metadata from arXiv, DOI, PubMed, etc.
            result = self._client.retrieve_webpage(url)
            
            if not result or not isinstance(result, list) or len(result) == 0:
                logger.warning("No metadata extracted from URL: {}", url)
                return None
            
            # Web translation API returns list of items, take first
            item_data = result[0]
            logger.info("Successfully extracted metadata from URL: {}", url)
            return item_data
            
        except Exception as exc:
            logger.error("Failed to extract metadata from URL {}: {}", url, exc)
            return None

    async def batch_export(self, documents: List[Any], collection_key: Optional[str] = None) -> List[str]:
        """Export documents to Zotero with comprehensive metadata and return list of Zotero keys."""
        if not self._client:
            logger.warning("Zotero export skipped: client not initialized")
            return []

        logger.info("Starting batch export of {} documents to Zotero", len(documents))
        items = []
        
        for idx, doc in enumerate(documents):
            try:
                # Extract document attributes safely
                def get_attr(obj, key, default=""):
                    if hasattr(obj, key):
                        val = getattr(obj, key, default)
                        return val if val is not None else default
                    elif isinstance(obj, dict):
                        val = obj.get(key, default)
                        return val if val is not None else default
                    return default
                
                title = get_attr(doc, "title", "")
                abstract = get_attr(doc, "abstract", "")
                url = get_attr(doc, "url", "")
                keywords = get_attr(doc, "keywords", []) or []
                authors = get_attr(doc, "authors", []) or []
                published_at = get_attr(doc, "published_at", "")
                source_name = get_attr(doc, "source_name", "")
                external_id = get_attr(doc, "external_id", "")
                
                # Extract additional metadata from extra_metadata field
                extra_metadata = get_attr(doc, "extra_metadata", {})
                if not isinstance(extra_metadata, dict):
                    extra_metadata = {}
                
                # Get various metadata fields with fallback to extra_metadata
                doi = get_attr(doc, "doi", "") or extra_metadata.get("doi", "")
                pdf_url = get_attr(doc, "pdf_url", "") or extra_metadata.get("pdf_url", "") or extra_metadata.get("pdf", "")
                language = get_attr(doc, "language", "") or extra_metadata.get("language", "")
                volume = get_attr(doc, "volume", "") or extra_metadata.get("volume", "")
                issue = get_attr(doc, "issue", "") or extra_metadata.get("issue", "")
                pages = get_attr(doc, "pages", "") or extra_metadata.get("pages", "")
                issn = get_attr(doc, "issn", "") or extra_metadata.get("issn", "")
                publisher = get_attr(doc, "publisher", "") or extra_metadata.get("publisher", "")
                journal = get_attr(doc, "journal", "") or extra_metadata.get("journal", "") or extra_metadata.get("journal_ref", "")
                arxiv_id = get_attr(doc, "arxiv_id", "") or extra_metadata.get("arxiv_id", "")
                
                # Extract arXiv ID from external_id if source is arxiv
                if not arxiv_id and source_name == "arxiv" and external_id:
                    # external_id format: http://arxiv.org/abs/2301.12345v1
                    if "arxiv.org/abs/" in external_id:
                        arxiv_id = external_id.split("arxiv.org/abs/")[-1]
                
                # Extract categories/subjects from extra_metadata
                categories = extra_metadata.get("categories", []) or extra_metadata.get("primary_category", "")
                if isinstance(categories, str):
                    categories = [categories] if categories else []
                
                # Build Zotero item with all available fields
                item = {
                    "itemType": "journalArticle",
                    "title": title,
                    "abstractNote": abstract,
                    "url": url,
                }
                
                # Add tags from keywords and categories
                all_tags = []
                if keywords:
                    all_tags.extend([{"tag": kw} for kw in keywords])
                if categories:
                    all_tags.extend([{"tag": f"arXiv:{cat}"} for cat in categories])
                if all_tags:
                    item["tags"] = all_tags
                
                # Add creators (authors) with improved name parsing
                if authors:
                    creators = []
                    for author in authors:
                        # Handle different author formats
                        if isinstance(author, dict):
                            # If author is already structured
                            creators.append({
                                "creatorType": "author",
                                "firstName": author.get("firstName", ""),
                                "lastName": author.get("lastName", author.get("name", ""))
                            })
                        elif isinstance(author, str):
                            # Split name if it contains comma (Last, First format)
                            if ", " in author:
                                last, first = author.split(", ", 1)
                                creators.append({
                                    "creatorType": "author",
                                    "firstName": first.strip(),
                                    "lastName": last.strip()
                                })
                            # Split name if it contains space (First Last format)
                            elif " " in author:
                                parts = author.strip().rsplit(" ", 1)
                                if len(parts) == 2:
                                    creators.append({
                                        "creatorType": "author",
                                        "firstName": parts[0],
                                        "lastName": parts[1]
                                    })
                                else:
                                    # Single name
                                    creators.append({
                                        "creatorType": "author",
                                        "firstName": "",
                                        "lastName": author.strip()
                                    })
                            else:
                                # Single name without space
                                creators.append({
                                    "creatorType": "author",
                                    "firstName": "",
                                    "lastName": author
                                })
                    item["creators"] = creators
                
                # Add publication date (convert datetime to string if needed)
                if published_at:
                    if hasattr(published_at, "isoformat"):
                        item["date"] = published_at.isoformat()
                    else:
                        item["date"] = str(published_at)
                
                # Add DOI
                if doi:
                    item["DOI"] = doi
                
                # Add journal/publication name
                if journal:
                    item["publicationTitle"] = journal
                elif source_name:
                    # Fallback to source name with proper capitalization
                    item["publicationTitle"] = source_name.title()
                
                # Add volume, issue, pages
                if volume:
                    item["volume"] = str(volume)
                if issue:
                    item["issue"] = str(issue)
                if pages:
                    item["pages"] = str(pages)
                
                # Add ISSN
                if issn:
                    item["ISSN"] = issn
                
                # Add publisher
                if publisher:
                    item["publisher"] = publisher
                
                # Add language
                if language:
                    item["language"] = language
                
                # Add additional info to extra field
                extra_fields = []
                if arxiv_id:
                    extra_fields.append(f"arXiv: {arxiv_id}")
                if pdf_url:
                    extra_fields.append(f"PDF: {pdf_url}")
                # Add source identifier
                if external_id and not arxiv_id:
                    extra_fields.append(f"ID: {external_id}")
                if extra_fields:
                    item["extra"] = "\n".join(extra_fields)
                
                # Add to collection if specified
                if collection_key:
                    item["collections"] = [collection_key]
                
                items.append(item)
                logger.debug("Prepared Zotero item {} for '{}' with {} fields", idx + 1, title[:50], len(item))
                
            except Exception as exc:
                logger.error("Failed to prepare document {} for Zotero export: {}", idx + 1, exc)
                logger.exception("Document data that failed:")
                continue
        if not items:
            return []

        try:
            response = self._client.create_items(items)
            # Extract keys from response
            keys = []
            if isinstance(response, dict) and "successful" in response:
                for idx, item_data in response["successful"].items():
                    keys.append(item_data["key"])
            logger.info("Exported {} documents to Zotero with enhanced metadata", len(keys))
            return keys
        except Exception as exc:
            logger.error("Failed to export to Zotero: {}", exc)
            return []

    async def safe_persist(self, documents: Dict[str, List[Dict[str, Any]]]) -> None:
        """Legacy method: persist documents without collection assignment."""
        if not self._client:
            return

        items = []
        for docs in documents.values():
            for doc in docs:
                item = {
                    "itemType": "journalArticle",
                    "title": doc.get("title", ""),
                    "abstractNote": doc.get("summary", doc.get("abstract", "")),
                    "url": doc.get("url"),
                    "tags": [{"tag": kw} for kw in doc.get("keywords", [])],
                    "creators": [
                        {"creatorType": "author", "firstName": "", "lastName": author}
                        for author in doc.get("authors", [])
                    ],
                }
                items.append(item)

        if items:
            try:
                self._client.create_items(items)
                logger.info("Persisted {} items to Zotero", len(items))
            except Exception as exc:
                logger.warning("Failed to persist items to Zotero: {}", exc)
