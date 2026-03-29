"""
Safe Wikipedia Utilities - TEXT ONLY
NO image crawling, NO infobox data, NO tables.
Only fetches clean text summaries for medical context.
"""

import requests
import logging
import re
from urllib.parse import quote
from typing import Optional, Dict

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "RedDotPharmacyBot/2.0 (Medical Chatbot - Text Only)"

logger = logging.getLogger(__name__)


def wiki_search_top_title(query: str) -> Optional[str]:
    """Search Wikipedia for best matching page title."""
    try:
        query = _sanitize_query(query)
        
        if not query or len(query) < 3:
            logger.warning("Query too short or invalid after sanitization")
            return None
        
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": 1,
            "format": "json",
            "srprop": "snippet"
        }
        
        response = requests.get(
            WIKIPEDIA_API,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        search_results = data.get("query", {}).get("search", [])
        if search_results:
            title = search_results[0].get("title")
            logger.info(f"Wikipedia search: '{query}' -> '{title}'")
            return title
        
        logger.info(f"No Wikipedia results for: {query}")
        return None
        
    except Exception as e:
        logger.error(f"Wikipedia search error: {e}")
        return None


def fetch_wiki_text_summary(title: str, max_sentences: int = 5) -> Optional[Dict]:
    """Fetch ONLY the text summary of a Wikipedia page. NO images."""
    try:
        params = {
            "action": "query",
            "titles": title,
            "prop": "extracts|info",
            "exintro": True,
            "explaintext": True,
            "exsentences": max_sentences,
            "inprop": "url",
            "format": "json"
        }
        
        response = requests.get(
            WIKIPEDIA_API,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        pages = data.get("query", {}).get("pages", {})
        
        for page_id, page_data in pages.items():
            if page_id == "-1":
                logger.warning(f"Wikipedia page not found: {title}")
                return None
            
            summary_text = page_data.get("extract", "").strip()
            
            if not summary_text or len(summary_text) < 50:
                logger.warning(f"Summary too short for: {title}")
                return None
            
            summary_text = _clean_text(summary_text)
            
            result = {
                "title": page_data.get("title", title),
                "summary": summary_text,
                "page_url": page_data.get("fullurl", f"https://en.wikipedia.org/wiki/{quote(title)}"),
                "word_count": len(summary_text.split())
            }
            
            logger.info(f"Fetched Wikipedia text: {result['title']} ({result['word_count']} words)")
            return result
        
        return None
        
    except Exception as e:
        logger.error(f"Wikipedia summary fetch error: {e}")
        return None


def fetch_wiki_summary(title: str) -> Optional[Dict]:
    """Alias for fetch_wiki_text_summary for backward compatibility."""
    return fetch_wiki_text_summary(title)


def _sanitize_query(query: str) -> str:
    """Sanitize query for Wikipedia search.
    Limits to 60 chars / 6 words to prevent sending full sentences as queries."""
    query = re.sub(r'[^\w\s-]', '', query)
    query = ' '.join(query.split())
    # Hard limit: first 6 words only (prevents wiki summary bleed-through)
    words = query.split()
    query = ' '.join(words[:6])
    query = query[:60]

    blocked_keywords = ['porn', 'xxx', 'explicit', 'nude']
    if any(kw in query.lower() for kw in blocked_keywords):
        logger.warning(f"Blocked inappropriate query: {query}")
        return ""

    return query.strip()


def _clean_text(text: str) -> str:
    """Clean Wikipedia text for better readability."""
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\[citation needed\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s*\([^)]*pronunciation[^)]*\)', '', text, flags=re.IGNORECASE)
    return text.strip()


def fetch_wiki_images(*args, **kwargs):
    """DISABLED: Image fetching is not allowed."""
    logger.warning("fetch_wiki_images() is disabled - images must come from database only")
    return []


def get_commons_metadata(*args, **kwargs):
    """DISABLED: Commons metadata fetching is not allowed."""
    logger.warning("get_commons_metadata() is disabled")
    return None


def get_image_direct_url(*args, **kwargs):
    """DISABLED: Direct image URL fetching is not allowed."""
    logger.warning("get_image_direct_url() is disabled")
    return None


def collect_wikipedia_resources(*args, **kwargs):
    """DISABLED: Resource collection with images is not allowed."""
    logger.warning("collect_wikipedia_resources() is disabled - use text-only functions")
    return {
        "title": None,
        "page_url": None,
        "summary": None,
        "images": [],
        "success": False
    }
