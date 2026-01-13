"""
Smart RAG Orchestrator
Coordinates database retrieval, Wikipedia crawling, and image fetching
with intelligent query classification and filtering.
"""

import logging
from typing import Dict, List, Optional
from query_classifier import QueryClassifier, should_fetch_medication_image, validate_image_relevance

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
        
        Returns:
            {
                'medications': List[Dict],
                'wiki_context': Optional[str],
                'images': List[Dict],
                'context_type': str,
                'should_show_images': bool
            }
        """
        result = {
            'medications': [],
            'wiki_context': None,
            'images': [],
            'context_type': 'none',
            'should_show_images': False
        }
        
        # Step 1: Classify the query
        classification = self.classifier.classify(user_query)
        logger.info(f"Query type: {classification['type']}, Confidence: {classification['confidence']}")
        
        # Step 2: Database search (ALWAYS FIRST)
        if classification['should_search_db']:
            db_query = self.classifier.generate_db_query(classification)
            result['medications'] = self._search_database(db_query)
            
            if result['medications']:
                result['context_type'] = 'database'
                logger.info(f"Found {len(result['medications'])} medications in database")
        
        # Step 3: Image retrieval (ONLY for medications from DB)
        if classification['should_fetch_images'] and result['medications']:
            result['images'] = self._fetch_medication_images(result['medications'])
            result['should_show_images'] = len(result['images']) > 0
        
        # Step 4: Wikipedia fallback (TEXT ONLY, NO IMAGES)
        if classification['should_crawl_wiki'] and not result['medications']:
            wiki_subject = self.classifier.generate_wiki_subject(classification, user_query)
            
            if wiki_subject:
                result['wiki_context'] = self._fetch_wiki_text_only(wiki_subject)
                if result['wiki_context']:
                    result['context_type'] = 'wikipedia_text'
                    logger.info(f"Retrieved Wikipedia text for: {wiki_subject}")
        
        return result
    
    def _search_database(self, query: str) -> List[Dict]:
        """
        Search internal medicine database with fallback strategies.
        """
        try:
            from services.medicine_rag import (
                search_medicines,
                search_medicines_for_condition,
                get_medicine_by_name
            )
            
            if not query or len(query.strip()) < 2:
                return []
            
            # Strategy 1: Direct name search
            results = search_medicines(query, limit=5)
            
            if results:
                logger.info(f"Direct search found {len(results)} results")
                return results
            
            # Strategy 2: Exact name match
            exact_match = get_medicine_by_name(query)
            if exact_match:
                logger.info("Exact name match found")
                return [exact_match]
            
            # Strategy 3: Condition/symptom search
            results = search_medicines_for_condition(query, limit=5)
            
            if results:
                logger.info(f"Condition search found {len(results)} results")
            
            return results
            
        except Exception as e:
            logger.error(f"Database search error: {e}")
            return []
    
    def _fetch_medication_images(self, medications: List[Dict]) -> List[Dict]:
        """
        Fetch ONLY validated medication images from local storage.
        NO external crawling, NO Wikipedia images.
        """
        validated_images = []
        
        for med in medications:
            med_name = med.get('name', '')
            
            # Validate image should be fetched
            if not should_fetch_medication_image(med_name, med):
                continue
            
            image_path = med.get('image', '').strip()
            
            # Additional validation
            if not validate_image_relevance(image_path, med_name):
                logger.warning(f"Image validation failed for {med_name}: {image_path}")
                continue
            
            # Construct proper URL
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
        """
        Fetch Wikipedia text summary ONLY using intelligent agent.
        NO images, NO tables, NO infoboxes.
        """
        try:
            from services.wikipedia_medical_agent import get_wiki_agent
            
            # Use Wikipedia Medical Agent
            agent = get_wiki_agent()
            wiki_data = agent.fetch_medical_info(subject)
            
            if not wiki_data:
                logger.info(f"No medical Wikipedia info for: {subject}")
                return None
            
            # Build medical context with safety disclaimers
            context = agent.build_medical_context(wiki_data)
            
            logger.info(f"Wikipedia agent: {wiki_data['title']} "
                       f"(quality: {wiki_data['quality_score']:.2f})")
            
            return context
            
        except Exception as e:
            logger.error(f"Wikipedia agent error: {e}")
            return None
    
    def build_ai_context(self, retrieval_result: Dict) -> str:
        """
        Build context string for AI prompt based on retrieval results.
        """
        context_parts = []
        
        # Add medication data
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
                
                # Add image URL if available
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
        
        # Add Wikipedia text if available
        if retrieval_result['wiki_context']:
            context_parts.append("\n" + retrieval_result['wiki_context'])
        
        return "\n".join(context_parts) if context_parts else ""


# Global instance
_orchestrator = None

def get_orchestrator() -> SmartRAGOrchestrator:
    """Get or create global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SmartRAGOrchestrator()
    return _orchestrator


def smart_retrieve(user_query: str, language: str = "en") -> Dict:
    """
    Main entry point for smart retrieval.
    Use this instead of directly calling medicine_rag or wikipedia_utils.
    """
    orchestrator = get_orchestrator()
    return orchestrator.retrieve(user_query, language)
