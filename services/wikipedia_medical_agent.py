"""
Enhanced Wikipedia Medical Information Agent
Intelligently extracts keywords, searches Wikipedia, and recommends medicines from catalog.
"""

import logging
import re
from typing import Optional, Dict, List, Tuple
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
    ANATOMY = "anatomy"
    UNKNOWN = "unknown"


@dataclass
class EnhancedMedicalQuery:
    """Enhanced query with extracted keywords and recommendations"""
    original_query: str
    topic_type: MedicalTopicType
    wiki_keywords: List[str]
    primary_keyword: str
    medicine_keywords: List[str]
    should_search_wikipedia: bool
    should_search_medicines: bool
    extraction_confidence: float
    reason: str


class KeywordExtractor:
    """Intelligent medical keyword extractor."""
    
    DISEASE_NAMES = [
        'diabetes', 'hypertension', 'asthma', 'pneumonia', 'malaria', 'typhoid',
        'dengue', 'hepatitis', 'tuberculosis', 'tb', 'cancer', 'arthritis',
        'migraine', 'epilepsy', 'parkinson', 'alzheimer', 'covid', 'flu',
        'influenza', 'bronchitis', 'sinusitis', 'gastritis', 'colitis',
        'syphilis', 'gonorrhea', 'chlamydia', 'herpes', 'hiv', 'aids',
        'measles', 'chickenpox', 'mumps', 'rubella', 'polio', 'tetanus',
        'cholera', 'dysentery', 'diarrhea', 'constipation', 'hemorrhoids',
        'psoriasis', 'eczema', 'dermatitis', 'acne', 'rosacea',
        'depression', 'anxiety', 'insomnia', 'schizophrenia', 'bipolar'
    ]
    
    SYMPTOM_KEYWORDS = [
        'fever', 'pain', 'headache', 'cough', 'cold', 'sore throat',
        'runny nose', 'nausea', 'vomiting', 'diarrhea', 'constipation',
        'fatigue', 'weakness', 'dizziness', 'rash', 'itching',
        'swelling', 'bleeding', 'numbness', 'tingling', 'breathlessness',
        'chest pain', 'back pain', 'stomach pain', 'joint pain',
        'muscle pain', 'toothache', 'earache', 'eye pain'
    ]
    
    MEDICINE_INDICATORS = [
        'medicine', 'drug', 'medication', 'treatment', 'cure', 'remedy',
        'tablet', 'capsule', 'syrup', 'injection', 'antibiotic', 'painkiller'
    ]
    
    QUESTION_PATTERNS = {
        'symptoms': [
            r'what (?:are|is) (?:the )?(?:main |common |primary )?symptoms? of (.+)',
            r'symptoms? (?:of|for) (.+)',
            r'signs? (?:of|for) (.+)',
            r'how (?:do i|can i) (?:know|tell) (?:if i have|i have) (.+)',
        ],
        'treatment': [
            r'(?:what|which) (?:medicine|drug|treatment) (?:for|to treat|helps with|cures?) (.+)',
            r'(?:how to|treatment for|cure for) (.+)',
            r'(?:medicine|drug) (?:for|to treat) (.+)',
            r'recommend (?:medicine|drug|treatment) for (.+)',
        ],
        'disease_info': [
            r'what is (.+)',
            r'tell me about (.+)',
            r'explain (.+)',
            r'information (?:about|on) (.+)',
            r'(?:about|regarding) (.+) (?:disease|condition)',
        ],
        'medication_info': [
            r'(?:what|tell me) (?:about|is) (.+) (?:medicine|drug|tablet|capsule)',
            r'information on (.+) (?:medicine|drug)',
            r'(.+) (?:medicine|drug|tablet) (?:uses?|for what)',
        ]
    }
    
    def extract(self, query: str) -> EnhancedMedicalQuery:
        """Extract intelligent keywords from user query."""
        query_clean = query.strip().lower()
        
        result = EnhancedMedicalQuery(
            original_query=query,
            topic_type=MedicalTopicType.UNKNOWN,
            wiki_keywords=[],
            primary_keyword="",
            medicine_keywords=[],
            should_search_wikipedia=False,
            should_search_medicines=False,
            extraction_confidence=0.0,
            reason=""
        )
        
        extracted = self._extract_by_patterns(query_clean)
        
        if extracted:
            result.topic_type = extracted['type']
            result.wiki_keywords = extracted['wiki_keywords']
            result.primary_keyword = extracted['primary']
            result.medicine_keywords = extracted['medicine_keywords']
            result.extraction_confidence = extracted['confidence']
            result.reason = extracted['reason']
        else:
            extracted = self._extract_entities(query_clean)
            result.wiki_keywords = extracted['diseases']
            result.medicine_keywords = extracted['symptoms'] + extracted['medicines']
            result.primary_keyword = extracted['diseases'][0] if extracted['diseases'] else ""
            result.extraction_confidence = 0.5
            result.reason = "Entity-based extraction"
        
        result.should_search_wikipedia = bool(result.primary_keyword)
        result.should_search_medicines = bool(result.medicine_keywords) or bool(result.primary_keyword)
        
        if 'symptom' in query_clean or 'sign' in query_clean:
            result.should_search_wikipedia = True
            result.should_search_medicines = True
        
        if any(word in query_clean for word in self.MEDICINE_INDICATORS):
            result.should_search_medicines = True
        
        logger.info(f"Extracted - Wiki: {result.primary_keyword}, "
                   f"Medicine: {result.medicine_keywords}, "
                   f"Confidence: {result.extraction_confidence:.2f}")
        
        return result
    
    def _extract_by_patterns(self, query: str) -> Optional[Dict]:
        """Extract using regex patterns"""
        for pattern in self.QUESTION_PATTERNS['symptoms']:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                disease = match.group(1).strip()
                disease_clean = self._clean_entity(disease)
                return {
                    'type': MedicalTopicType.DISEASE,
                    'wiki_keywords': [disease_clean],
                    'primary': disease_clean,
                    'medicine_keywords': [disease_clean],
                    'confidence': 0.9,
                    'reason': f"Symptom query about '{disease_clean}'"
                }
        
        for pattern in self.QUESTION_PATTERNS['treatment']:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                condition = match.group(1).strip()
                condition_clean = self._clean_entity(condition)
                return {
                    'type': MedicalTopicType.TREATMENT,
                    'wiki_keywords': [condition_clean],
                    'primary': condition_clean,
                    'medicine_keywords': [condition_clean],
                    'confidence': 0.85,
                    'reason': f"Treatment query for '{condition_clean}'"
                }
        
        for pattern in self.QUESTION_PATTERNS['disease_info']:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                disease = match.group(1).strip()
                disease_clean = self._clean_entity(disease)
                if self._is_disease(disease_clean):
                    return {
                        'type': MedicalTopicType.DISEASE,
                        'wiki_keywords': [disease_clean],
                        'primary': disease_clean,
                        'medicine_keywords': [disease_clean],
                        'confidence': 0.8,
                        'reason': f"Disease information query about '{disease_clean}'"
                    }
        
        for pattern in self.QUESTION_PATTERNS['medication_info']:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                medicine = match.group(1).strip()
                medicine_clean = self._clean_entity(medicine)
                return {
                    'type': MedicalTopicType.MEDICATION,
                    'wiki_keywords': [medicine_clean + " medication"],
                    'primary': medicine_clean + " medication",
                    'medicine_keywords': [medicine_clean],
                    'confidence': 0.85,
                    'reason': f"Medication query about '{medicine_clean}'"
                }
        
        return None
    
    def _extract_entities(self, query: str) -> Dict:
        """Extract diseases, symptoms, medicines from text"""
        diseases = []
        symptoms = []
        medicines = []
        
        for disease in self.DISEASE_NAMES:
            if disease in query:
                diseases.append(disease)
        
        for symptom in self.SYMPTOM_KEYWORDS:
            if symptom in query:
                symptoms.append(symptom)
        
        words = query.split()
        for i in range(len(words)):
            for j in range(i+1, min(i+4, len(words)+1)):
                phrase = ' '.join(words[i:j])
                if self._looks_like_medicine(phrase):
                    medicines.append(phrase)
        
        return {
            'diseases': diseases,
            'symptoms': symptoms,
            'medicines': medicines
        }
    
    def _clean_entity(self, entity: str) -> str:
        """Clean extracted entity"""
        stop_words = ['the', 'a', 'an', 'is', 'are', 'of', 'disease', 'condition']
        words = entity.split()
        cleaned_words = [w for w in words if w not in stop_words]
        cleaned = ' '.join(cleaned_words).strip()
        cleaned = re.sub(r'[?.!,;]+$', '', cleaned)
        return cleaned
    
    def _is_disease(self, term: str) -> bool:
        """Check if term is likely a disease"""
        term_lower = term.lower()
        if term_lower in self.DISEASE_NAMES:
            return True
        disease_suffixes = ['itis', 'osis', 'emia', 'pathy', 'oma', 'algia']
        if any(term_lower.endswith(suffix) for suffix in disease_suffixes):
            return True
        return False
    
    def _looks_like_medicine(self, term: str) -> bool:
        """Check if term looks like a medicine name"""
        medicine_patterns = [
            r'\w+(?:cin|zole|pril|olol|mycin|cillin)$',
            r'\b[A-Z][a-z]+[A-Z][a-z]+\b',
            r'\w+\s*\d+\s*mg',
        ]
        return any(re.search(pattern, term, re.IGNORECASE) for pattern in medicine_patterns)


class EnhancedWikipediaMedicalAgent:
    """
    Enhanced Wikipedia agent with intelligent keyword extraction.
    
    SYSTEM PROMPT FOR WIKIPEDIA SEARCH:
    - When searching for diseases, ALWAYS append "disease" or "medical condition" 
      to ensure Wikipedia API returns the MEDICAL article, not unrelated pages
    - Example: "typhoid" → "typhoid fever disease" (NOT "Typhoid Mary")
    - Example: "malaria" → "malaria disease infection"  
    - Example: "diabetes" → "diabetes mellitus medical"
    - For medications, append "medication" or "drug" for pharmaceutical results
    - NEVER return biographical, historical, or non-medical Wikipedia pages
    """
    
    KNOWN_DISEASES = [
        'typhoid', 'malaria', 'dengue', 'cholera', 'tuberculosis', 'pneumonia',
        'diabetes', 'hypertension', 'asthma', 'hepatitis', 'syphilis', 'gonorrhea',
        'covid', 'influenza', 'measles', 'chickenpox', 'polio', 'tetanus',
        'arthritis', 'epilepsy', 'migraine', 'bronchitis', 'gastritis', 'diarrhea'
    ]
    
    def __init__(self):
        self.extractor = KeywordExtractor()
        self.cache = {}
        self.fetch_count = 0
        self.cache_hits = 0
    
    def _make_medical_query(self, keyword: str, topic_type: MedicalTopicType) -> str:
        """
        Convert keyword to medical-specific Wikipedia search query.
        
        Ensures we get the DISEASE article, not unrelated pages.
        Example: "typhoid" → "typhoid fever disease" (NOT "Typhoid Mary")
        """
        keyword = keyword.lower().strip()
        
        if topic_type == MedicalTopicType.DISEASE or keyword in self.KNOWN_DISEASES:
            if 'fever' not in keyword and keyword in ['typhoid', 'dengue', 'yellow', 'scarlet']:
                keyword = f"{keyword} fever"
            return f"{keyword} disease medical condition"
        
        elif topic_type == MedicalTopicType.MEDICATION:
            return f"{keyword} medication drug pharmaceutical"
        
        elif topic_type == MedicalTopicType.SYMPTOM:
            return f"{keyword} symptom medical"
        
        elif topic_type == MedicalTopicType.TREATMENT:
            return f"{keyword} treatment therapy medical"
        
        else:
            return f"{keyword} medical health"
    
    def process_query(self, query: str) -> Dict:
        """Main method: Process query, extract keywords, fetch Wikipedia + medicines."""
        extracted = self.extractor.extract(query)
        
        result = {
            'extracted': extracted,
            'wikipedia': None,
            'medicines': [],
            'combined_context': ""
        }
        
        if extracted.should_search_wikipedia and extracted.primary_keyword:
            result['wikipedia'] = self._fetch_wikipedia(extracted.primary_keyword, extracted.topic_type)
        
        if extracted.should_search_medicines:
            keywords = extracted.medicine_keywords if extracted.medicine_keywords else [extracted.primary_keyword]
            result['medicines'] = self._search_medicine_catalog(keywords)
        
        result['combined_context'] = self._build_combined_context(
            extracted, result['wikipedia'], result['medicines']
        )
        
        logger.info(f"Processed query - Wiki: {bool(result['wikipedia'])}, "
                   f"Medicines: {len(result['medicines'])}")
        
        return result
    
    def fetch_medical_info(self, query: str) -> Optional[Dict]:
        """Backward compatible method for simple Wikipedia fetch."""
        extracted = self.extractor.extract(query)
        keyword = extracted.primary_keyword if extracted.primary_keyword else query
        return self._fetch_wikipedia(keyword)
    
    def build_medical_context(self, wiki_data: Optional[Dict]) -> str:
        """Build context from Wikipedia data."""
        if not wiki_data:
            return ""
        
        return f"""
[Wikipedia Medical Reference]
Topic: {wiki_data['title']}
(Searched with keyword: '{wiki_data.get('search_keyword', wiki_data['title'])}')

Summary:
{wiki_data['summary']}

Source: {wiki_data['page_url']}

MEDICAL DISCLAIMER:
This Wikipedia information is for EDUCATIONAL PURPOSES ONLY.
It is NOT a substitute for professional medical advice.
ALWAYS consult a qualified healthcare provider.
""".strip()
    
    def _fetch_wikipedia(self, keyword: str, topic_type: MedicalTopicType = None) -> Optional[Dict]:
        """
        Fetch from Wikipedia using extracted keyword with MEDICAL-SPECIFIC query.
        
        Converts "typhoid" → "typhoid fever disease" to get the disease article,
        NOT "Typhoid Mary" or other unrelated pages.
        """
        cache_key = keyword.lower()
        if cache_key in self.cache:
            self.cache_hits += 1
            logger.info(f"Cache hit: {keyword}")
            return self.cache[cache_key]
        
        try:
            from services.wikipedia_utils_safe import wiki_search_top_title, fetch_wiki_text_summary
            
            medical_query = self._make_medical_query(keyword, topic_type or MedicalTopicType.DISEASE)
            logger.info(f"Medical Wikipedia query: '{keyword}' → '{medical_query}'")
            
            title = wiki_search_top_title(medical_query)
            
            if not title:
                title = wiki_search_top_title(keyword)
            
            if not title:
                logger.info(f"No Wikipedia page for: {keyword}")
                return None
            
            if not self._is_medical_title(title):
                medical_query_alt = f"{keyword} disease"
                alt_title = wiki_search_top_title(medical_query_alt)
                if alt_title and self._is_medical_title(alt_title):
                    title = alt_title
            
            wiki_data = fetch_wiki_text_summary(title, max_sentences=6)
            
            if not wiki_data:
                return None
            
            quality_score = self._score_quality(wiki_data['summary'])
            
            result = {
                'title': wiki_data['title'],
                'summary': wiki_data['summary'],
                'page_url': wiki_data['page_url'],
                'search_keyword': keyword,
                'medical_query_used': medical_query,
                'quality_score': quality_score,
                'is_reliable': quality_score > 0.6,
                'word_count': wiki_data.get('word_count', 0)
            }
            
            self.cache[cache_key] = result
            self.fetch_count += 1
            
            logger.info(f"Wikipedia fetched: {title} (keyword: {keyword})")
            return result
            
        except Exception as e:
            logger.error(f"Wikipedia fetch error: {e}")
            return None
    
    def _is_medical_title(self, title: str) -> bool:
        """Check if Wikipedia title is a medical article (not biographical etc.)"""
        title_lower = title.lower()
        
        non_medical = ['mary', 'john', 'person', 'singer', 'actor', 'film', 'movie',
                       'novel', 'book', 'album', 'song', 'band', 'tv series']
        
        if any(term in title_lower for term in non_medical):
            return False
        
        medical_indicators = ['disease', 'disorder', 'syndrome', 'infection', 'fever',
                              'medication', 'drug', 'symptom', 'treatment', 'itis', 'osis']
        
        if any(term in title_lower for term in medical_indicators):
            return True
        
        return True
    
    def _search_medicine_catalog(self, keywords: List[str]) -> List[Dict]:
        """Search medicine catalog with extracted keywords"""
        try:
            from services.medicine_rag import search_medicines, search_medicines_for_condition
            
            all_medicines = []
            seen_ids = set()
            
            for keyword in keywords[:3]:
                if not keyword:
                    continue
                    
                medicines = search_medicines(keyword, limit=3)
                
                if not medicines:
                    medicines = search_medicines_for_condition(keyword, limit=3)
                
                for med in medicines:
                    if med['id'] not in seen_ids:
                        seen_ids.add(med['id'])
                        all_medicines.append(med)
                
                if len(all_medicines) >= 5:
                    break
            
            logger.info(f"Found {len(all_medicines)} medicines for keywords: {keywords}")
            return all_medicines[:5]
            
        except Exception as e:
            logger.error(f"Medicine catalog search error: {e}")
            return []
    
    def _build_combined_context(self, extracted: EnhancedMedicalQuery, 
                                wikipedia: Optional[Dict], 
                                medicines: List[Dict]) -> str:
        """Build combined context for AI"""
        parts = []
        
        parts.append(f"[INTELLIGENT QUERY ANALYSIS]")
        parts.append(f"Original Query: {extracted.original_query}")
        parts.append(f"Detected Topic: {extracted.topic_type.value}")
        parts.append(f"Extracted Keyword: {extracted.primary_keyword}")
        parts.append(f"Confidence: {extracted.extraction_confidence:.2f}")
        parts.append("")
        
        if wikipedia:
            parts.append(f"[WIKIPEDIA MEDICAL INFORMATION]")
            parts.append(f"Topic: {wikipedia['title']}")
            parts.append(f"(Searched with keyword: '{wikipedia['search_keyword']}')")
            parts.append(f"\nSummary:")
            parts.append(wikipedia['summary'])
            parts.append(f"\nSource: {wikipedia['page_url']}")
            parts.append("")
        
        if medicines:
            parts.append(f"[RECOMMENDED MEDICINES FROM RED DOT PHARMACY]")
            parts.append(f"Found {len(medicines)} relevant medicines:")
            parts.append("")
            
            for i, med in enumerate(medicines, 1):
                parts.append(f"{i}. {med['name']}")
                parts.append(f"   Price: Rs. {med['price']}")
                if med.get('ingredients'):
                    parts.append(f"   Ingredients: {med['ingredients']}")
                if med.get('description'):
                    parts.append(f"   Use: {med['description'][:100]}...")
                parts.append("")
        
        parts.append("[MEDICAL DISCLAIMER]")
        parts.append("This information is for EDUCATIONAL PURPOSES ONLY.")
        parts.append("It is NOT a substitute for professional medical advice.")
        parts.append("ALWAYS consult a qualified healthcare provider.")
        parts.append("Visit Red Dot Pharmacy or consult a licensed physician.")
        
        return "\n".join(parts)
    
    def _score_quality(self, text: str) -> float:
        """Score content quality"""
        if not text:
            return 0.0
        
        score = 0.5
        medical_terms = ['treatment', 'symptoms', 'diagnosis', 'therapy', 'disease']
        term_count = sum(1 for term in medical_terms if term in text.lower())
        score += min(term_count * 0.1, 0.3)
        
        if len(text.split()) > 50:
            score += 0.2
        
        return min(1.0, score)
    
    def get_stats(self) -> Dict:
        """Get agent statistics"""
        total = self.fetch_count + self.cache_hits
        cache_rate = (self.cache_hits / total * 100) if total > 0 else 0
        
        return {
            'total_fetches': self.fetch_count,
            'cache_hits': self.cache_hits,
            'cache_hit_rate': f"{cache_rate:.1f}%",
            'cached_pages': len(self.cache)
        }


_enhanced_agent = None

def get_enhanced_wiki_agent() -> EnhancedWikipediaMedicalAgent:
    """Get global enhanced agent"""
    global _enhanced_agent
    if _enhanced_agent is None:
        _enhanced_agent = EnhancedWikipediaMedicalAgent()
    return _enhanced_agent


def get_wiki_agent() -> EnhancedWikipediaMedicalAgent:
    """Backward compatible alias"""
    return get_enhanced_wiki_agent()


def process_medical_query(query: str) -> Dict:
    """Main entry point: Process query with intelligent extraction."""
    agent = get_enhanced_wiki_agent()
    return agent.process_query(query)


def extract_keywords_only(query: str) -> EnhancedMedicalQuery:
    """Just extract keywords without fetching data."""
    extractor = KeywordExtractor()
    return extractor.extract(query)


def fetch_medical_wikipedia(query: str) -> Optional[Dict]:
    """Backward compatible convenience function."""
    agent = get_enhanced_wiki_agent()
    return agent.fetch_medical_info(query)
