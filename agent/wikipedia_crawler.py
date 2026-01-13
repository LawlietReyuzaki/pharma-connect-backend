"""
Wikipedia Crawler - TEXT ONLY (NO IMAGES EVER)
"""
import re
import requests
from typing import Optional, Dict, List


class WikipediaCrawler:
    """
    STRICT RULES:
    1. TEXT ONLY - No images, tables, infoboxes, media
    2. Fetch ONLY: indications, usage, side effects
    3. NEVER fetch images
    4. Sanitize all queries
    """
    
    SEARCH_URL = "https://en.wikipedia.org/w/api.php"
    
    BLOCKED_TERMS = [
        'image', 'images', 'picture', 'pictures', 'photo', 'photos',
        'anatomy', 'diagram', 'structure', 'illustration',
        'human body', 'body part', 'sexual', 'nude'
    ]
    
    def sanitize_query(self, query: str) -> Optional[str]:
        """Sanitize query - BLOCK forbidden terms"""
        if not query or len(query) < 3:
            return None
        
        query_lower = query.lower()
        
        for term in self.BLOCKED_TERMS:
            if term in query_lower:
                print(f"BLOCKED query term: {term}")
                return None
        
        return query
    
    def search(self, query: str, limit: int = 3) -> List[Dict]:
        """Search Wikipedia - returns TEXT info only (sync version)"""
        sanitized = self.sanitize_query(query)
        if not sanitized:
            return []
        
        params = {
            "action": "query",
            "list": "search",
            "srsearch": sanitized,
            "srlimit": limit,
            "format": "json"
        }
        
        try:
            response = requests.get(self.SEARCH_URL, params=params, timeout=10)
            if response.status_code != 200:
                return []
            data = response.json()
            return [
                {"title": item.get("title", ""), "pageid": item.get("pageid")}
                for item in data.get("query", {}).get("search", [])
            ]
        except Exception as e:
            print(f"Wikipedia search error: {e}")
            return []
    
    def fetch_article(self, title: str) -> Optional[str]:
        """Fetch article as PLAIN TEXT only"""
        if not title:
            return None
        
        params = {
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "explaintext": True,
            "format": "json"
        }
        
        try:
            response = requests.get(self.SEARCH_URL, params=params, timeout=10)
            if response.status_code != 200:
                return None
            
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            
            for page_id, page_data in pages.items():
                if page_id == "-1":
                    return None
                extract = page_data.get("extract", "")
                return self._clean_content(extract)
            return None
        except Exception as e:
            print(f"Wikipedia fetch error: {e}")
            return None
    
    def _clean_content(self, text: str) -> str:
        """Remove any URLs or image references from text"""
        if not text:
            return ""
        
        text = re.sub(r'https?://[^\s]+', '', text)
        text = re.sub(r'\S+\.(jpg|jpeg|png|gif|svg|webp)\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[\d+\]', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
