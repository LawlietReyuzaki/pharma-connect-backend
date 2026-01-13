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
    """
    Search Wikipedia for best matching page title.
    Sanitizes query to prevent inappropriate searches.
    """
    try:
        # Sanitize query
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
            timeout=10
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
    """
    Fetch ONLY the text summary of a Wikipedia page.
    NO images, NO infobox, NO tables.
    
    Returns:
        {
            'title': str,
            'summary': str,
            'page_url': str,
            'word_count': int
        }
    """
    try:
        params = {
            "action": "query",
            "titles": title,
            "prop": "extracts|info",
            "exintro": True,           # Intro section only
            "explaintext": True,       # Plain text, no HTML
            "exsentences": max_sentences,
            "inprop": "url",
            "format": "json"
        }
        
        response = requests.get(
            WIKIPEDIA_API,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        pages = data.get("query", {}).get("pages", {})
        
        for page_id, page_data in pages.items():
            if page_id == "-1":
                logger.warning(f"Wikipedia page not found: {title}")
                return None
            
            summary_text = page_data.get("extract", "").strip()
            
            # Validate summary quality
            if not summary_text or len(summary_text) < 50:
                logger.warning(f"Summary too short for: {title}")
                return None
            
            # Clean summary text
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


def fetch_medication_info_text(medication_name: str) -> Optional[Dict]:
    """
    Fetch medication information from Wikipedia (TEXT ONLY).
    Specialized for pharmaceutical queries.
    """
    try:
        # Append "medication" or "drug" to improve search
        search_query = f"{medication_name} medication"
        
        title = wiki_search_top_title(search_query)
        
        if not title:
            # Fallback: try with "drug"
            search_query = f"{medication_name} drug"
            title = wiki_search_top_title(search_query)
        
        if not title:
            logger.info(f"No Wikipedia page for medication: {medication_name}")
            return None
        
        # Fetch text summary
        summary_data = fetch_wiki_text_summary(title, max_sentences=6)
        
        if not summary_data:
            return None
        
        # Add medical context flag
        summary_data['is_medication'] = _is_medication_page(summary_data['summary'])
        
        return summary_data
        
    except Exception as e:
        logger.error(f"Medication info fetch error: {e}")
        return None


def fetch_disease_info_text(disease_name: str) -> Optional[Dict]:
    """
    Fetch disease/condition information from Wikipedia (TEXT ONLY).
    NO anatomy images, NO disease images.
    """
    try:
        title = wiki_search_top_title(disease_name)
        
        if not title:
            logger.info(f"No Wikipedia page for disease: {disease_name}")
            return None
        
        summary_data = fetch_wiki_text_summary(title, max_sentences=5)
        
        if not summary_data:
            return None
        
        # Add medical context flag
        summary_data['is_disease'] = True
        
        return summary_data
        
    except Exception as e:
        logger.error(f"Disease info fetch error: {e}")
        return None


def build_medical_context_from_wiki(wiki_data: Optional[Dict]) -> str:
    """
    Build AI context string from Wikipedia text data.
    Ensures medical safety disclaimers are included.
    """
    if not wiki_data:
        return ""
    
    context = f"""
[Wikipedia Medical Reference - Educational Purpose Only]

Topic: {wiki_data['title']}

Summary:
{wiki_data['summary']}

Source: {wiki_data['page_url']}

---
⚠️ IMPORTANT: This Wikipedia information is for general education only.
It is NOT a substitute for professional medical advice, diagnosis, or treatment.
Always consult a qualified healthcare provider for medical decisions.
---
"""
    
    return context.strip()


def _sanitize_query(query: str) -> str:
    """
    Sanitize query to prevent inappropriate Wikipedia searches.
    """
    # Remove special characters
    query = re.sub(r'[^\w\s-]', '', query)
    
    # Remove excessive whitespace
    query = ' '.join(query.split())
    
    # Limit length
    query = query[:100]
    
    # Block explicit keywords (safety)
    blocked_keywords = ['porn', 'xxx', 'explicit', 'nude']
    query_lower = query.lower()
    
    if any(kw in query_lower for kw in blocked_keywords):
        logger.warning(f"Blocked inappropriate query: {query}")
        return ""
    
    return query.strip()


def _clean_text(text: str) -> str:
    """
    Clean Wikipedia text for better readability.
    """
    # Remove citation markers like [1], [citation needed]
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\[citation needed\]', '', text, flags=re.IGNORECASE)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove parenthetical pronunciations
    text = re.sub(r'\s*\([^)]*pronunciation[^)]*\)', '', text, flags=re.IGNORECASE)
    
    return text.strip()


def _is_medication_page(text: str) -> bool:
    """
    Heuristic to detect if Wikipedia page is about medication/drug.
    """
    medication_keywords = [
        'medication', 'drug', 'pharmaceutical', 'tablet', 'capsule',
        'treatment', 'prescribed', 'antibiotic', 'analgesic'
    ]
    
    text_lower = text.lower()
    matches = sum(1 for kw in medication_keywords if kw in text_lower)
    
    return matches >= 2


# === NO IMAGE FUNCTIONS ===
# These functions are intentionally removed/disabled

def fetch_wiki_images(*args, **kwargs):
    """
    DISABLED: Image fetching is not allowed.
    Always returns empty list.
    """
    logger.warning("fetch_wiki_images() is disabled - images must come from database only")
    return []


def get_commons_metadata(*args, **kwargs):
    """
    DISABLED: Commons metadata fetching is not allowed.
    """
    logger.warning("get_commons_metadata() is disabled")
    return None


def get_image_direct_url(*args, **kwargs):
    """
    DISABLED: Direct image URL fetching is not allowed.
    """
    logger.warning("get_image_direct_url() is disabled")
    return None


def collect_wikipedia_resources(*args, **kwargs):
    """
    DISABLED: Resource collection with images is not allowed.
    Use fetch_wiki_text_summary() instead.
    """
    logger.warning("collect_wikipedia_resources() is disabled - use text-only functions")
    return {
        "title": None,
        "page_url": None,
        "summary": None,
        "images": [],  # Always empty
        "success": False
    }
