"""
Wikipedia Medical Information Agent
Intelligent agent for fetching ONLY relevant medical text from Wikipedia.
NO images, NO irrelevant content, STRICT medical context filtering.
"""

import logging
import re
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MedicalTopicType(Enum):
    """Types of medical topics"""
    MEDICATION = "medication"
    DISEASE = "disease"
    SYMPTOM = "symptom"
    CONDITION = "condition"
    TREATMENT = "treatment"
    ANATOMY = "anatomy"  # Usually NOT needed
    UNKNOWN = "unknown"


@dataclass
class WikiMedicalQuery:
    """Structured Wikipedia query"""
    original_query: str
    topic_type: MedicalTopicType
    search_term: str
    should_fetch: bool
    reason: str


class WikipediaMedicalAgent:
    """
    Intelligent agent for Wikipedia medical information retrieval.
    
    Key Features:
    - Query validation and sanitization
    - Medical relevance filtering
    - TEXT ONLY retrieval (NO images)
    - Quality scoring
    - Safety checks
    """
    
    # Medical terms that indicate medication
    MEDICATION_INDICATORS = [
        'tablet', 'capsule', 'syrup', 'injection', 'drug', 'medicine',
        'pharmaceutical', 'mg', 'ml', 'dose', 'prescription', 'antibiotic',
        'painkiller', 'analgesic', 'antipyretic', 'treatment'
    ]
    
    # Disease/condition indicators
    DISEASE_INDICATORS = [
        'disease', 'syndrome', 'disorder', 'condition', 'infection',
        'inflammation', 'deficiency', 'symptoms', 'diagnosis', 'treatment'
    ]
    
    # Terms to avoid fetching (not useful medically)
    AVOID_TERMS = [
        'how to', 'best', 'top 10', 'review', 'comparison',
        'buy', 'price', 'near me', 'home remedy', 'natural cure'
    ]
    
    # Irrelevant Wikipedia categories to block
    BLOCKED_CATEGORIES = [
        'people', 'biography', 'places', 'geography', 'history',
        'culture', 'entertainment', 'sports', 'politics'
    ]
    
    def __init__(self):
        self.cache = {}  # Simple in-memory cache
        self.fetch_count = 0
        self.cache_hits = 0
    
    def analyze_query(self, query: str) -> WikiMedicalQuery:
        """
        Analyze user query and determine if/how to fetch from Wikipedia.
        
        Returns structured query with validation.
        """
        query = query.strip().lower()
        
        # Check if query should be avoided
        if any(term in query for term in self.AVOID_TERMS):
            return WikiMedicalQuery(
                original_query=query,
                topic_type=MedicalTopicType.UNKNOWN,
                search_term="",
                should_fetch=False,
                reason="Query contains non-medical shopping/comparison terms"
            )
        
        # Detect topic type
        topic_type = self._detect_topic_type(query)
        
        # Generate search term
        search_term = self._generate_search_term(query, topic_type)
        
        # Validate medical relevance
        if not self._is_medically_relevant(search_term):
            return WikiMedicalQuery(
                original_query=query,
                topic_type=topic_type,
                search_term=search_term,
                should_fetch=False,
                reason="Query lacks medical relevance"
            )
        
        # Block anatomy queries (usually need images which we don't provide)
        if topic_type == MedicalTopicType.ANATOMY:
            return WikiMedicalQuery(
                original_query=query,
                topic_type=topic_type,
                search_term=search_term,
                should_fetch=False,
                reason="Anatomy topics require visual aids not available"
            )
        
        return WikiMedicalQuery(
            original_query=query,
            topic_type=topic_type,
            search_term=search_term,
            should_fetch=True,
            reason="Valid medical query"
        )
    
    def fetch_medical_info(self, query: str) -> Optional[Dict]:
        """
        Main method: Fetch medical information from Wikipedia.
        
        Returns:
            {
                'title': str,
                'summary': str,
                'page_url': str,
                'topic_type': str,
                'quality_score': float,
                'is_reliable': bool,
                'cached': bool
            }
        """
        # Analyze query first
        analyzed = self.analyze_query(query)
        
        if not analyzed.should_fetch:
            logger.info(f"Wikipedia fetch blocked: {analyzed.reason}")
            return None
        
        # Check cache
        cache_key = analyzed.search_term.lower()
        if cache_key in self.cache:
            self.cache_hits += 1
            logger.info(f"Cache hit for: {analyzed.search_term}")
            cached_result = self.cache[cache_key].copy()
            cached_result['cached'] = True
            return cached_result
        
        # Fetch from Wikipedia
        try:
            from services.wikipedia_utils import (
                wiki_search_top_title,
                fetch_wiki_text_summary
            )
            
            # Search for page
            title = wiki_search_top_title(analyzed.search_term)
            
            if not title:
                logger.info(f"No Wikipedia page found for: {analyzed.search_term}")
                return None
            
            # Validate page relevance
            if not self._is_valid_medical_page(title):
                logger.warning(f"Page '{title}' failed medical relevance check")
                return None
            
            # Fetch text summary
            wiki_data = fetch_wiki_text_summary(title, max_sentences=6)
            
            if not wiki_data:
                return None
            
            # Score quality
            quality_score = self._score_content_quality(wiki_data['summary'])
            
            if quality_score < 0.4:
                logger.warning(f"Low quality content for: {title} (score: {quality_score})")
                return None
            
            # Build result
            result = {
                'title': wiki_data['title'],
                'summary': wiki_data['summary'],
                'page_url': wiki_data['page_url'],
                'topic_type': analyzed.topic_type.value,
                'quality_score': quality_score,
                'is_reliable': quality_score > 0.6,
                'cached': False,
                'word_count': wiki_data.get('word_count', 0)
            }
            
            # Cache result
            self.cache[cache_key] = result.copy()
            self.fetch_count += 1
            
            logger.info(f"Fetched Wikipedia: {title} (quality: {quality_score:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Wikipedia fetch error: {e}")
            return None
    
    def build_medical_context(self, wiki_data: Optional[Dict]) -> str:
        """
        Build AI context string from Wikipedia data with medical safety.
        """
        if not wiki_data:
            return ""
        
        # Add quality indicators
        reliability_note = "reliable medical source" if wiki_data['is_reliable'] else "general reference"
        
        context = f"""
[Wikipedia Medical Reference - {reliability_note.upper()}]

Topic: {wiki_data['title']}
Category: {wiki_data['topic_type'].title()}
Quality Score: {wiki_data['quality_score']:.2f}/1.0

Summary:
{wiki_data['summary']}

Source: {wiki_data['page_url']}

---
⚠️ CRITICAL MEDICAL DISCLAIMER:
This Wikipedia information is for EDUCATIONAL PURPOSES ONLY.
It is NOT a substitute for professional medical advice, diagnosis, or treatment.
ALWAYS consult a qualified healthcare provider for medical decisions.

Patient should visit Red Dot Pharmacy or consult a licensed physician.
---
"""
        return context.strip()
    
    def _detect_topic_type(self, query: str) -> MedicalTopicType:
        """Detect the type of medical topic"""
        query_lower = query.lower()
        
        # Check for medication indicators
        if any(term in query_lower for term in self.MEDICATION_INDICATORS):
            return MedicalTopicType.MEDICATION
        
        # Check for disease indicators
        if any(term in query_lower for term in self.DISEASE_INDICATORS):
            return MedicalTopicType.DISEASE
        
        # Check for symptom patterns
        symptom_patterns = [
            r'\b(pain|ache|fever|cough|nausea)\b',
            r'\bi have\b',
            r'\bfeeling\b',
            r'\bsuffering from\b'
        ]
        if any(re.search(pattern, query_lower) for pattern in symptom_patterns):
            return MedicalTopicType.SYMPTOM
        
        # Check for anatomy terms
        anatomy_terms = ['heart', 'liver', 'kidney', 'brain', 'lung', 'bone', 'muscle']
        if any(term in query_lower for term in anatomy_terms) and 'disease' not in query_lower:
            return MedicalTopicType.ANATOMY
        
        return MedicalTopicType.UNKNOWN
    
    def _generate_search_term(self, query: str, topic_type: MedicalTopicType) -> str:
        """Generate optimized Wikipedia search term"""
        # Remove question words
        cleaned = re.sub(
            r'\b(what|how|why|when|where|who|tell|me|about|is|are|the|a|an)\b',
            '',
            query,
            flags=re.IGNORECASE
        )
        
        # Clean whitespace
        cleaned = ' '.join(cleaned.split())
        
        # Add context based on topic type
        if topic_type == MedicalTopicType.MEDICATION:
            if 'medication' not in cleaned and 'drug' not in cleaned:
                cleaned += " medication"
        elif topic_type == MedicalTopicType.DISEASE:
            if 'disease' not in cleaned and 'condition' not in cleaned:
                cleaned += " disease"
        
        return cleaned.strip()[:100]  # Limit length
    
    def _is_medically_relevant(self, search_term: str) -> bool:
        """Check if search term is medically relevant"""
        if not search_term or len(search_term) < 3:
            return False
        
        # Must contain some medical term
        medical_terms = (
            self.MEDICATION_INDICATORS + 
            self.DISEASE_INDICATORS + 
            ['medical', 'health', 'clinical', 'patient', 'therapy']
        )
        
        search_lower = search_term.lower()
        return any(term in search_lower for term in medical_terms)
    
    def _is_valid_medical_page(self, title: str) -> bool:
        """Validate if Wikipedia page title is medical"""
        title_lower = title.lower()
        
        # Block non-medical categories
        blocked_terms = [
            'list of', 'category:', 'disambiguation',
            'film', 'movie', 'album', 'song', 'book',
            'company', 'organization', 'university',
            'footballer', 'actor', 'politician'
        ]
        
        if any(term in title_lower for term in blocked_terms):
            return False
        
        return True
    
    def _score_content_quality(self, text: str) -> float:
        """
        Score content quality (0.0 to 1.0)
        Higher score = more reliable medical content
        """
        if not text:
            return 0.0
        
        score = 0.0
        text_lower = text.lower()
        
        # Positive indicators
        medical_terms = [
            'treatment', 'symptoms', 'diagnosis', 'medication',
            'therapy', 'disease', 'condition', 'medical', 'clinical'
        ]
        term_count = sum(1 for term in medical_terms if term in text_lower)
        score += min(term_count * 0.1, 0.4)
        
        # Length check (too short = low quality)
        word_count = len(text.split())
        if word_count > 50:
            score += 0.2
        if word_count > 100:
            score += 0.2
        
        # Citation indicators (Wikipedia quality)
        if any(marker in text for marker in ['[', 'citation', 'ref']):
            score += 0.1
        
        # Negative indicators
        spam_terms = ['buy', 'shop', 'discount', 'sale', 'cheap']
        if any(term in text_lower for term in spam_terms):
            score -= 0.3
        
        return max(0.0, min(1.0, score))
    
    def get_stats(self) -> Dict:
        """Get agent statistics"""
        cache_hit_rate = (
            (self.cache_hits / (self.fetch_count + self.cache_hits)) * 100
            if (self.fetch_count + self.cache_hits) > 0
            else 0
        )
        
        return {
            'total_fetches': self.fetch_count,
            'cache_hits': self.cache_hits,
            'cache_hit_rate': f"{cache_hit_rate:.1f}%",
            'cached_pages': len(self.cache)
        }


# Global agent instance
_wiki_agent = None

def get_wiki_agent() -> WikipediaMedicalAgent:
    """Get or create global Wikipedia agent"""
    global _wiki_agent
    if _wiki_agent is None:
        _wiki_agent = WikipediaMedicalAgent()
    return _wiki_agent


# Convenience functions
def fetch_medical_wikipedia(query: str) -> Optional[Dict]:
    """
    Main entry point for fetching medical info from Wikipedia.
    Use this instead of directly calling wikipedia_utils functions.
    """
    agent = get_wiki_agent()
    return agent.fetch_medical_info(query)


def build_wiki_medical_context(query: str) -> str:
    """
    Fetch Wikipedia info and build AI context string in one call.
    """
    agent = get_wiki_agent()
    wiki_data = agent.fetch_medical_info(query)
    
    if wiki_data:
        return agent.build_medical_context(wiki_data)
    
    return ""


def validate_query_for_wikipedia(query: str) -> bool:
    """
    Quick validation: Should this query use Wikipedia?
    Use before attempting fetch to save API calls.
    """
    agent = get_wiki_agent()
    analyzed = agent.analyze_query(query)
    return analyzed.should_fetch
