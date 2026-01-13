"""
Query Classifier for Medical Chatbot
Intelligently classifies user queries to determine retrieval strategy.
"""

import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

MEDICATION_PATTERNS = [
    r'\b(\w+)\s*(?:\d+\s*(?:mg|ml|gm|g|mcg|iu))?\s*(?:tablets?|capsules?|syrup|injection|drops?|suspension|cream|ointment|gel|solution)?\b',
    r'\b(?:panadol|disprin|brufen|flagyl|augmentin|amoxil|paracetamol|ibuprofen|aspirin)\b',
]

DISEASE_KEYWORDS = [
    'fever', 'cold', 'flu', 'infection', 'pain', 'headache', 'stomach',
    'diabetes', 'blood pressure', 'hypertension', 'cholesterol', 'allergy',
    'cough', 'asthma', 'arthritis', 'depression', 'anxiety', 'insomnia',
    'diarrhea', 'constipation', 'nausea', 'vomiting', 'migraine',
    'بخار', 'درد', 'سردی', 'کھانسی', 'پیٹ', 'سر درد', 'الرجی'
]

SYMPTOM_KEYWORDS = [
    'symptoms', 'علامات', 'feeling', 'having', 'suffering',
    'hurts', 'aching', 'burning', 'itching', 'swelling',
    'tired', 'weak', 'dizzy', 'nauseous'
]

BLOCKED_IMAGE_KEYWORDS = [
    'anatomy', 'organ', 'body part', 'surgery', 'wound', 'injury',
    'disease image', 'symptom image', 'medical image', 'x-ray', 'scan',
    'blood', 'tissue', 'cell', 'tumor', 'lesion', 'rash'
]


class QueryClassifier:
    """Classifies medical queries for intelligent retrieval routing."""
    
    def classify(self, query: str) -> Dict:
        """
        Classify a user query.
        
        Returns:
            {
                'type': str,  # 'medication_specific', 'medication_search', 'disease_info', 'symptom_check', 'general'
                'confidence': float,
                'extracted_medication': Optional[str],
                'extracted_disease': Optional[str],
                'extracted_symptoms': List[str],
                'should_search_db': bool,
                'should_fetch_images': bool,
                'should_crawl_wiki': bool
            }
        """
        query_lower = query.lower().strip()
        
        result = {
            'type': 'general',
            'confidence': 0.5,
            'extracted_medication': None,
            'extracted_disease': None,
            'extracted_symptoms': [],
            'should_search_db': True,
            'should_fetch_images': False,
            'should_crawl_wiki': False
        }
        
        medication = self._extract_medication(query)
        if medication:
            result['extracted_medication'] = medication
            result['type'] = 'medication_specific'
            result['confidence'] = 0.9
            result['should_fetch_images'] = True
            result['should_crawl_wiki'] = False
            return result
        
        disease = self._extract_disease(query_lower)
        if disease:
            result['extracted_disease'] = disease
            result['type'] = 'disease_info'
            result['confidence'] = 0.8
            result['should_fetch_images'] = False
            result['should_crawl_wiki'] = True
            return result
        
        symptoms = self._extract_symptoms(query_lower)
        if symptoms:
            result['extracted_symptoms'] = symptoms
            result['type'] = 'symptom_check'
            result['confidence'] = 0.7
            result['should_fetch_images'] = False
            result['should_crawl_wiki'] = True
            return result
        
        if self._is_medication_search(query_lower):
            result['type'] = 'medication_search'
            result['confidence'] = 0.75
            result['should_fetch_images'] = True
            return result
        
        return result
    
    def _extract_medication(self, query: str) -> Optional[str]:
        """Extract medication name from query."""
        for pattern in MEDICATION_PATTERNS:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                if len(match) > 3 and match.lower() not in {'what', 'about', 'tell', 'give', 'this', 'that', 'have', 'need', 'want', 'medicine', 'drug', 'tablet'}:
                    return match.strip()
        return None
    
    def _extract_disease(self, query: str) -> Optional[str]:
        """Extract disease/condition name from query."""
        for keyword in DISEASE_KEYWORDS:
            if keyword in query:
                return keyword
        return None
    
    def _extract_symptoms(self, query: str) -> List[str]:
        """Extract symptoms from query."""
        found = []
        for keyword in SYMPTOM_KEYWORDS:
            if keyword in query:
                found.append(keyword)
        return found
    
    def _is_medication_search(self, query: str) -> bool:
        """Check if query is searching for medication."""
        search_indicators = ['medicine for', 'tablet for', 'drug for', 'treatment for', 'دوا', 'گولی']
        return any(ind in query for ind in search_indicators)
    
    def generate_db_query(self, classification: Dict) -> str:
        """Generate optimized database query based on classification."""
        if classification['extracted_medication']:
            return classification['extracted_medication']
        if classification['extracted_disease']:
            return classification['extracted_disease']
        if classification['extracted_symptoms']:
            return ' '.join(classification['extracted_symptoms'][:3])
        return ""
    
    def generate_wiki_subject(self, classification: Dict, original_query: str) -> Optional[str]:
        """Generate Wikipedia search subject."""
        if classification['extracted_disease']:
            return classification['extracted_disease']
        if classification['extracted_symptoms']:
            return classification['extracted_symptoms'][0]
        return None


def should_fetch_medication_image(medication_name: str, med_data: Dict) -> bool:
    """Determine if medication image should be fetched."""
    if not medication_name:
        return False
    
    name_lower = medication_name.lower()
    for blocked in BLOCKED_IMAGE_KEYWORDS:
        if blocked in name_lower:
            return False
    
    image_path = med_data.get('image', '')
    if image_path and len(image_path) > 5:
        return True
    
    return False


def validate_image_relevance(image_path: str, medication_name: str) -> bool:
    """Validate that an image is relevant to the medication."""
    if not image_path:
        return False
    
    path_lower = image_path.lower()
    
    blocked_extensions = ['.gif', '.svg', '.ico']
    if any(path_lower.endswith(ext) for ext in blocked_extensions):
        return False
    
    blocked_paths = ['anatomy', 'organ', 'body', 'disease', 'symptom', 'logo', 'icon', 'banner']
    if any(blocked in path_lower for blocked in blocked_paths):
        return False
    
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    if not any(path_lower.endswith(ext) for ext in valid_extensions):
        return False
    
    return True
