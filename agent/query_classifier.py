"""
Query Classifier - Intelligent medical query classification
"""
import re
from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum


class QueryType(Enum):
    MEDICATION = "medication"
    DISEASE = "disease"
    SYMPTOM = "symptom"
    GENERAL = "general"


class QueryIntent(Enum):
    LOOKUP = "lookup"
    EXPLANATION = "explanation"
    TREATMENT = "treatment"
    SIDE_EFFECTS = "side_effects"


@dataclass
class ClassifiedQuery:
    original_query: str
    extracted_keyword: str
    query_type: QueryType
    intent: QueryIntent
    confidence: float
    normalized_keyword: str
    requires_wiki: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_query": self.original_query,
            "extracted_keyword": self.extracted_keyword,
            "query_type": self.query_type.value,
            "intent": self.intent.value,
            "confidence": self.confidence,
            "normalized_keyword": self.normalized_keyword,
            "requires_wiki": self.requires_wiki
        }


class QueryClassifier:
    def __init__(self, gemini_client):
        self.gemini = gemini_client
    
    async def classify(self, query: str) -> ClassifiedQuery:
        """Main classification method using Gemini"""
        extraction = await self.gemini.extract_medical_keyword(query)
        
        keyword = extraction.get("extracted_keyword", "")
        query_type_str = extraction.get("query_type", "general")
        intent_str = extraction.get("intent", "lookup")
        confidence = extraction.get("confidence", 0.5)
        
        normalized = self.normalize_medication_name(keyword)
        query_type = self._map_query_type(query_type_str)
        intent = self._map_intent(intent_str)
        requires_wiki = self._should_fetch_wiki(query_type, intent, query)
        
        return ClassifiedQuery(
            original_query=query,
            extracted_keyword=keyword,
            query_type=query_type,
            intent=intent,
            confidence=confidence,
            normalized_keyword=normalized,
            requires_wiki=requires_wiki
        )
    
    def classify_sync(self, query: str) -> ClassifiedQuery:
        """Synchronous classification"""
        extraction = self.gemini.extract_medical_keyword_sync(query)
        
        keyword = extraction.get("extracted_keyword", "")
        query_type_str = extraction.get("query_type", "general")
        intent_str = extraction.get("intent", "lookup")
        confidence = extraction.get("confidence", 0.5)
        
        normalized = self.normalize_medication_name(keyword)
        query_type = self._map_query_type(query_type_str)
        intent = self._map_intent(intent_str)
        requires_wiki = self._should_fetch_wiki(query_type, intent, query)
        
        return ClassifiedQuery(
            original_query=query,
            extracted_keyword=keyword,
            query_type=query_type,
            intent=intent,
            confidence=confidence,
            normalized_keyword=normalized,
            requires_wiki=requires_wiki
        )
    
    def normalize_medication_name(self, name: str) -> str:
        """Normalize medication name for database lookup"""
        if not name:
            return ""
        
        normalized = name.lower().strip()
        normalized = re.sub(r'\d+\s*(mg|ml|mcg|g|iu|%)', '', normalized)
        
        for word in ['tablet', 'tablets', 'capsule', 'capsules', 'syrup', 
                     'injection', 'cream', 'ointment', 'drops', 'gel']:
            normalized = normalized.replace(word, '')
        
        normalized = re.sub(r'[^\w\s-]', '', normalized)
        return ' '.join(normalized.split()).strip()
    
    def _map_query_type(self, type_str: str) -> QueryType:
        mapping = {
            "medication": QueryType.MEDICATION,
            "disease": QueryType.DISEASE,
            "symptom": QueryType.SYMPTOM,
        }
        return mapping.get(type_str.lower(), QueryType.GENERAL)
    
    def _map_intent(self, intent_str: str) -> QueryIntent:
        mapping = {
            "lookup": QueryIntent.LOOKUP,
            "explanation": QueryIntent.EXPLANATION,
            "treatment": QueryIntent.TREATMENT,
            "side_effects": QueryIntent.SIDE_EFFECTS,
        }
        return mapping.get(intent_str.lower(), QueryIntent.LOOKUP)
    
    def _should_fetch_wiki(self, query_type: QueryType, intent: QueryIntent, query: str) -> bool:
        """Determine if Wikipedia fetch is needed"""
        if query_type in [QueryType.DISEASE, QueryType.SYMPTOM]:
            if intent in [QueryIntent.EXPLANATION, QueryIntent.SIDE_EFFECTS]:
                return True
        
        keywords = ['what is', 'explain', 'tell me about', 'symptoms of', 'side effects']
        return any(kw in query.lower() for kw in keywords)
    
    def validate_medical_term(self, term: str) -> bool:
        """Validate term is safe (not injection attack)"""
        blocked = [r'http[s]?://', r'<.*?>', r'[{}]', r'SELECT|INSERT|DELETE']
        for pattern in blocked:
            if re.search(pattern, term, re.IGNORECASE):
                return False
        return 2 < len(term) < 100
