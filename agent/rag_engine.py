"""
Medical RAG Engine - Main Orchestrator

PROCESSING RULES (CANNOT BE OVERRIDDEN):
1. Database lookup ALWAYS happens FIRST
2. Wikipedia ONLY if medication NOT in DB AND user asks for explanation
3. Images ONLY from local folder
4. NEVER hallucinate medications
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging

from .gemini_client import GeminiClient
from .query_classifier import QueryClassifier, QueryType, QueryIntent, ClassifiedQuery
from .wikipedia_crawler import WikipediaCrawler
from .image_validator import ImageValidator

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    success: bool
    query_type: str
    extracted_keyword: str
    medications: List[Dict]
    wiki_info: Optional[str]
    message: str
    image_paths: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class MedicalRAGEngine:
    """Main RAG Engine - connects all components"""
    
    def __init__(
        self,
        gemini_client: GeminiClient = None,
        query_classifier: QueryClassifier = None,
        wiki_crawler: WikipediaCrawler = None,
        image_validator: ImageValidator = None
    ):
        self.gemini = gemini_client or GeminiClient()
        self.classifier = query_classifier or QueryClassifier(self.gemini)
        self.wiki = wiki_crawler or WikipediaCrawler()
        self.image_validator = image_validator or ImageValidator()
    
    def process_query_sync(self, query: str, include_wiki: bool = False) -> RAGResponse:
        """Synchronous query processing pipeline"""
        classification = self.classifier.classify_sync(query)
        logger.info(f"Classified: {classification.to_dict()}")
        
        if not self.classifier.validate_medical_term(classification.extracted_keyword):
            return RAGResponse(
                success=False,
                query_type=classification.query_type.value,
                extracted_keyword=classification.extracted_keyword,
                medications=[],
                wiki_info=None,
                message="Invalid or unsafe query detected.",
                image_paths=[]
            )
        
        if classification.query_type == QueryType.MEDICATION:
            return self._handle_medication_sync(classification, include_wiki)
        elif classification.query_type in [QueryType.DISEASE, QueryType.SYMPTOM]:
            return self._handle_disease_sync(classification, include_wiki)
        else:
            return self._handle_general_sync(classification, include_wiki)
    
    def _handle_medication_sync(self, classification: ClassifiedQuery, include_wiki: bool) -> RAGResponse:
        """Handle medication queries"""
        from services.medicine_rag import search_medicines, get_medicine_by_name
        
        medications = search_medicines(classification.normalized_keyword, limit=5)
        
        if not medications:
            exact = get_medicine_by_name(classification.extracted_keyword)
            if exact:
                medications = [exact]
        
        if medications:
            image_paths = []
            for med in medications:
                if med.get('image'):
                    img_result = self.image_validator.validate_path(med['image'])
                    if img_result.is_valid:
                        med['validated_image'] = img_result.path
                        image_paths.append(img_result.path)
                    else:
                        med['validated_image'] = None
            
            wiki_info = None
            if include_wiki and classification.requires_wiki:
                wiki_info = self._fetch_wiki_safely(
                    classification.extracted_keyword, "medication"
                )
            
            return RAGResponse(
                success=True,
                query_type=classification.query_type.value,
                extracted_keyword=classification.extracted_keyword,
                medications=medications,
                wiki_info=wiki_info,
                message=f"Found {len(medications)} medication(s)",
                image_paths=image_paths
            )
        
        return RAGResponse(
            success=False,
            query_type=classification.query_type.value,
            extracted_keyword=classification.extracted_keyword,
            medications=[],
            wiki_info=None,
            message=f"Medication '{classification.extracted_keyword}' not found in database.",
            image_paths=[]
        )
    
    def _handle_disease_sync(self, classification: ClassifiedQuery, include_wiki: bool) -> RAGResponse:
        """Handle disease/symptom queries"""
        from services.medicine_rag import search_medicines, search_medicines_for_condition
        
        ingredients = self.gemini.map_disease_to_medications_sync(classification.extracted_keyword)
        logger.info(f"Mapped ingredients: {ingredients}")
        
        all_medications = []
        seen_ids = set()
        
        for ingredient in ingredients:
            meds = search_medicines(ingredient, limit=3)
            if not meds:
                meds = search_medicines_for_condition(ingredient, limit=3)
            
            for med in meds:
                med_id = med.get('id') or med.get('name')
                if med_id not in seen_ids:
                    seen_ids.add(med_id)
                    if med.get('image'):
                        img_result = self.image_validator.validate_path(med['image'])
                        med['validated_image'] = img_result.path if img_result.is_valid else None
                    med['matched_ingredient'] = ingredient
                    all_medications.append(med)
        
        image_paths = [m.get('validated_image') for m in all_medications if m.get('validated_image')]
        
        wiki_info = None
        if include_wiki or classification.requires_wiki:
            wiki_info = self._fetch_wiki_safely(
                classification.extracted_keyword, "disease"
            )
        
        if all_medications:
            return RAGResponse(
                success=True,
                query_type=classification.query_type.value,
                extracted_keyword=classification.extracted_keyword,
                medications=all_medications,
                wiki_info=wiki_info,
                message=f"Found {len(all_medications)} medication(s) for '{classification.extracted_keyword}'",
                image_paths=image_paths
            )
        
        return RAGResponse(
            success=wiki_info is not None,
            query_type=classification.query_type.value,
            extracted_keyword=classification.extracted_keyword,
            medications=[],
            wiki_info=wiki_info,
            message="No medications found. Please consult a healthcare provider.",
            image_paths=[]
        )
    
    def _handle_general_sync(self, classification: ClassifiedQuery, include_wiki: bool) -> RAGResponse:
        """Handle general/unclear queries"""
        from services.medicine_rag import search_medicines
        
        medications = search_medicines(classification.normalized_keyword, limit=5)
        
        if medications:
            return self._handle_medication_sync(classification, include_wiki)
        
        wiki_info = None
        if include_wiki:
            wiki_info = self._fetch_wiki_safely(
                classification.extracted_keyword, "general"
            )
        
        return RAGResponse(
            success=wiki_info is not None,
            query_type=classification.query_type.value,
            extracted_keyword=classification.extracted_keyword,
            medications=[],
            wiki_info=wiki_info,
            message="Could not identify medication or condition. Please be more specific.",
            image_paths=[]
        )
    
    def _fetch_wiki_safely(self, keyword: str, query_type: str) -> Optional[str]:
        """Fetch Wikipedia TEXT ONLY - no images"""
        wiki_query = f"{keyword} {query_type} medical"
        logger.info(f"Wiki query: {wiki_query}")
        
        results = self.wiki.search(wiki_query, limit=1)
        if not results:
            return None
        
        title = results[0].get('title')
        content = self.wiki.fetch_article(title)
        
        if not content:
            return None
        
        if len(content) > 1500:
            content = content[:1500] + "..."
        
        return content


_rag_engine = None

def get_rag_engine() -> MedicalRAGEngine:
    """Get or create global RAG engine instance"""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = MedicalRAGEngine()
    return _rag_engine


def smart_medical_query(query: str, include_wiki: bool = True) -> Dict:
    """Main entry point for smart medical queries"""
    engine = get_rag_engine()
    result = engine.process_query_sync(query, include_wiki)
    return result.to_dict()
