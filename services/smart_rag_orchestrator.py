"""
Smart RAG Orchestrator
Coordinates database retrieval, Wikipedia crawling, and image fetching
with intelligent query classification and filtering.
"""

import logging
from typing import Dict, List, Optional
from services.query_classifier import QueryClassifier, should_fetch_medication_image, validate_image_relevance

logger = logging.getLogger(__name__)


class SmartRAGOrchestrator:
    """
    Intelligent orchestration layer for medical information retrieval.
    Enforces database-first approach and prevents irrelevant content.
    """
    
    def __init__(self):
        self.classifier = QueryClassifier()
    
    def retrieve(self, user_query: str, language: str = "en") -> Dict:
        """
        Main retrieval method with intelligent routing.
        """
        result = {
            'medications': [],
            'wiki_context': None,
            'images': [],
            'context_type': 'none',
            'should_show_images': False
        }
        
        classification = self.classifier.classify(user_query)
        logger.info(f"Query type: {classification['type']}, Confidence: {classification['confidence']}")
        
        if classification['should_search_db']:
            db_query = self.classifier.generate_db_query(classification)
            if db_query:
                result['medications'] = self._search_database(db_query)
            
            if not result['medications']:
                result['medications'] = self._search_database(user_query)
            
            if result['medications']:
                result['context_type'] = 'database'
                logger.info(f"Found {len(result['medications'])} medications in database")
        
        if classification['should_fetch_images'] and result['medications']:
            result['images'] = self._fetch_medication_images(result['medications'])
            result['should_show_images'] = len(result['images']) > 0
        
        if classification['should_crawl_wiki'] and not result['medications']:
            wiki_subject = self.classifier.generate_wiki_subject(classification, user_query)
            
            if wiki_subject:
                result['wiki_context'] = self._fetch_wiki_text_only(wiki_subject)
                if result['wiki_context']:
                    result['context_type'] = 'wikipedia_text'
                    logger.info(f"Retrieved Wikipedia text for: {wiki_subject}")
        
        return result
    
    def _search_database(self, query: str) -> List[Dict]:
        """Search internal medicine database with fallback strategies."""
        try:
            from services.medicine_rag import (
                search_medicines,
                search_medicines_for_condition,
                get_medicine_by_name
            )
            
            if not query or len(query.strip()) < 2:
                return []
            
            results = search_medicines(query, limit=5)
            
            if results:
                logger.info(f"Direct search found {len(results)} results")
                return results
            
            exact_match = get_medicine_by_name(query)
            if exact_match:
                logger.info("Exact name match found")
                return [exact_match]
            
            results = search_medicines_for_condition(query, limit=5)
            
            if results:
                logger.info(f"Condition search found {len(results)} results")
            
            return results
            
        except Exception as e:
            logger.error(f"Database search error: {e}")
            return []
    
    def _fetch_medication_images(self, medications: List[Dict]) -> List[Dict]:
        """Fetch ONLY validated medication images from local storage."""
        validated_images = []
        
        for med in medications:
            med_name = med.get('name', '')
            
            if not should_fetch_medication_image(med_name, med):
                continue
            
            image_path = med.get('image', '').strip()
            
            if not validate_image_relevance(image_path, med_name):
                logger.warning(f"Image validation failed for {med_name}: {image_path}")
                continue
            
            if image_path and not image_path.startswith('/'):
                image_url = f"/static/uploads/medicines/{image_path}"
            else:
                image_url = image_path if image_path else '/static/images/default-medicine.png'
            
            validated_images.append({
                'medication_id': med.get('id'),
                'medication_name': med_name,
                'url': image_url,
                'local_path': image_path,
                'source': 'database'
            })
            
            logger.info(f"Validated image for {med_name}: {image_url}")
        
        return validated_images
    
    def _fetch_wiki_text_only(self, subject: str) -> Optional[str]:
        """Fetch Wikipedia text summary ONLY. NO images."""
        try:
            from services.wikipedia_utils_safe import wiki_search_top_title, fetch_wiki_text_summary
            
            title = wiki_search_top_title(subject)
            
            if not title:
                logger.info(f"No Wikipedia page found for: {subject}")
                return None
            
            summary_data = fetch_wiki_text_summary(title)
            
            if not summary_data or not summary_data.get('summary'):
                return None
            
            context = f"""
[Wikipedia Reference - Text Only]
Topic: {summary_data['title']}
Summary: {summary_data['summary'][:500]}
Source: {summary_data['page_url']}

Note: This is general information. Always consult a healthcare professional.
"""
            return context.strip()
            
        except Exception as e:
            logger.error(f"Wikipedia text fetch error: {e}")
            return None
    
    def build_ai_context(self, retrieval_result: Dict) -> str:
        """Build context string for AI prompt based on retrieval results."""
        context_parts = []
        
        if retrieval_result['medications']:
            context_parts.append("[MEDICINE DATA FROM RED DOT PHARMACY DATABASE]")
            
            for med in retrieval_result['medications']:
                context_parts.append(f"\n--- Medicine: {med['name']} ---")
                context_parts.append(f"Price: Rs. {med['price']}")
                
                if med.get('manufacturer'):
                    context_parts.append(f"Manufacturer: {med['manufacturer']}")
                
                if med.get('ingredients'):
                    context_parts.append(f"Active Ingredients: {med['ingredients']}")
                
                if med.get('form'):
                    context_parts.append(f"Form: {med['form']}")
                
                if med.get('description'):
                    desc = med['description'][:300]
                    context_parts.append(f"Description: {desc}")
                
                if retrieval_result['should_show_images']:
                    matching_image = next(
                        (img for img in retrieval_result['images'] 
                         if img['medication_id'] == med.get('id')),
                        None
                    )
                    if matching_image:
                        context_parts.append(f"Image: {matching_image['url']}")
            
            context_parts.append("\n[END OF MEDICINE DATA]")
            context_parts.append("IMPORTANT: Use ONLY this medicine data. Do NOT invent other medicines.")
        
        if retrieval_result['wiki_context']:
            context_parts.append("\n" + retrieval_result['wiki_context'])
        
        return "\n".join(context_parts) if context_parts else ""


_orchestrator = None

def get_orchestrator() -> SmartRAGOrchestrator:
    """Get or create global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SmartRAGOrchestrator()
    return _orchestrator


def smart_retrieve(user_query: str, language: str = "en") -> Dict:
    """Main entry point for smart retrieval."""
    orchestrator = get_orchestrator()
    return orchestrator.retrieve(user_query, language)
