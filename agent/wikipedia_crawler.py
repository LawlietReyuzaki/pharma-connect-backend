"""
Wikipedia Crawler - TEXT ONLY (NO IMAGES EVER)
Medical/Disease-Specific Wikipedia Search Agent

SYSTEM PROMPT FOR WIKIPEDIA SEARCH:
- When searching for diseases, ALWAYS append "disease" or "medical condition" to ensure 
  the Wikipedia API returns the MEDICAL article, not unrelated pages
- Example: "typhoid" → "typhoid fever disease" (NOT "Typhoid Mary")
- Example: "malaria" → "malaria disease infection"
- Example: "diabetes" → "diabetes mellitus medical"
- For medications, append "medication" or "drug" to ensure pharmaceutical results
- NEVER return biographical, historical, or non-medical Wikipedia pages
"""
import re
import requests
from typing import Optional, Dict, List


class WikipediaCrawler:
    """
    STRICT RULES:
    1. TEXT ONLY - No images, tables, infoboxes, media
    2. Fetch ONLY: medical conditions, medications, symptoms, treatments
    3. NEVER fetch images
    4. Sanitize all queries
    5. ALWAYS make queries disease/medicine-specific
    """
    
    SEARCH_URL = "https://en.wikipedia.org/w/api.php"
    
    BLOCKED_TERMS = [
        'image', 'images', 'picture', 'pictures', 'photo', 'photos',
        'anatomy', 'diagram', 'structure', 'illustration',
        'human body', 'body part', 'sexual', 'nude'
    ]
    
    MEDICAL_SUFFIXES = {
        'disease': ['disease', 'medical condition', 'infection', 'disorder'],
        'medication': ['medication', 'drug', 'pharmaceutical', 'medicine'],
        'symptom': ['symptom', 'medical symptom', 'clinical sign'],
    }
    
    KNOWN_DISEASES = [
        'typhoid', 'malaria', 'dengue', 'cholera', 'tuberculosis', 'pneumonia',
        'diabetes', 'hypertension', 'asthma', 'hepatitis', 'syphilis', 'gonorrhea',
        'covid', 'influenza', 'measles', 'chickenpox', 'polio', 'tetanus',
        'arthritis', 'epilepsy', 'migraine', 'bronchitis', 'gastritis'
    ]
    
    def make_medical_query(self, keyword: str, query_type: str = "disease") -> str:
        """
        Convert a keyword into a medical-specific Wikipedia search query.
        
        Examples:
        - "typhoid" + "disease" → "typhoid fever disease"
        - "paracetamol" + "medication" → "paracetamol medication drug"
        - "fever" + "symptom" → "fever medical symptom"
        """
        keyword = keyword.lower().strip()
        
        if query_type == "disease" or keyword in self.KNOWN_DISEASES:
            if 'fever' not in keyword and keyword in ['typhoid', 'dengue', 'yellow']:
                keyword = f"{keyword} fever"
            return f"{keyword} disease medical condition"
        
        elif query_type == "medication":
            return f"{keyword} medication drug pharmaceutical"
        
        elif query_type == "symptom":
            return f"{keyword} symptom medical"
        
        else:
            return f"{keyword} medical health"
    
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
    
    def search(self, query: str, limit: int = 3, query_type: str = "disease") -> List[Dict]:
        """
        Search Wikipedia - returns TEXT info only (sync version)
        
        Makes the query MEDICAL-SPECIFIC to avoid non-medical results.
        Example: "typhoid" searches for "typhoid fever disease" to get the disease article,
        NOT "Typhoid Mary" or other unrelated pages.
        """
        sanitized = self.sanitize_query(query)
        if not sanitized:
            return []
        
        medical_query = self.make_medical_query(sanitized, query_type)
        
        params = {
            "action": "query",
            "list": "search",
            "srsearch": medical_query,
            "srlimit": limit,
            "format": "json"
        }
        
        try:
            response = requests.get(self.SEARCH_URL, params=params, timeout=10)
            if response.status_code != 200:
                return []
            data = response.json()
            
            results = []
            for item in data.get("query", {}).get("search", []):
                title = item.get("title", "")
                if self._is_medical_result(title):
                    results.append({"title": title, "pageid": item.get("pageid")})
            
            return results if results else [
                {"title": item.get("title", ""), "pageid": item.get("pageid")}
                for item in data.get("query", {}).get("search", [])[:1]
            ]
        except Exception as e:
            print(f"Wikipedia search error: {e}")
            return []
    
    def _is_medical_result(self, title: str) -> bool:
        """Check if Wikipedia result is likely a medical article"""
        title_lower = title.lower()
        
        non_medical_patterns = [
            'mary', 'john', 'person', 'singer', 'actor', 'film', 'movie',
            'novel', 'book', 'album', 'song', 'band', 'tv series', 'episode'
        ]
        
        if any(pattern in title_lower for pattern in non_medical_patterns):
            return False
        
        medical_indicators = [
            'disease', 'disorder', 'syndrome', 'infection', 'fever',
            'medication', 'drug', 'symptom', 'treatment', 'therapy',
            'itis', 'osis', 'emia', 'pathy'
        ]
        
        if any(indicator in title_lower for indicator in medical_indicators):
            return True
        
        return True
    
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
