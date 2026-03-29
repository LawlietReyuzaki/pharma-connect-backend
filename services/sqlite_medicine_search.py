"""
SQLite-Optimized Medicine Search Functions
Provides database-agnostic search functions compatible with both SQLite and PostgreSQL
Enhanced with better query patterns and fallback strategies
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


# Levenshtein Distance for spell checking
def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


class MedicineSearchService:
    """Enhanced medicine search service with SQLite optimization"""
    
    @staticmethod
    def search_by_name(query: str, limit: int = 5) -> List[Dict]:
        """
        Search medicines by name with fuzzy matching
        Works with both SQLite and PostgreSQL
        """
        try:
            from app import db
            from models import Medicine
            
            if not query or len(query.strip()) < 2:
                return []
            
            search_term = f"%{query.strip()}%"
            
            # Use ilike for case-insensitive search (works on both SQLite via flask-sqlalchemy and PostgreSQL)
            medicines = Medicine.query.filter(
                Medicine.name.ilike(search_term)
            ).limit(limit).all()
            
            return MedicineSearchService._format_results(medicines)
            
        except Exception as e:
            logger.error(f"Name search error: {e}")
            return []
    
    @staticmethod
    def search_by_chemical(query: str, limit: int = 5) -> List[Dict]:
        """
        Search medicines by active ingredient/chemical
        """
        try:
            from app import db
            from models import Medicine
            
            if not query or len(query.strip()) < 2:
                return []
            
            search_term = f"%{query.strip()}%"
            
            medicines = Medicine.query.filter(
                Medicine.chemical.ilike(search_term)
            ).limit(limit).all()
            
            return MedicineSearchService._format_results(medicines)
            
        except Exception as e:
            logger.error(f"Chemical search error: {e}")
            return []
    
    @staticmethod
    def search_by_category(category: str, limit: int = 5) -> List[Dict]:
        """
        Search medicines by category
        """
        try:
            from app import db
            from models import Medicine
            
            if not category or len(category.strip()) < 2:
                return []
            
            search_term = f"%{category.strip()}%"
            
            medicines = Medicine.query.filter(
                Medicine.category.ilike(search_term)
            ).limit(limit).all()
            
            return MedicineSearchService._format_results(medicines)
            
        except Exception as e:
            logger.error(f"Category search error: {e}")
            return []
    
    @staticmethod
    def search_by_description(query: str, limit: int = 5) -> List[Dict]:
        """
        Search medicines by description content
        """
        try:
            from app import db
            from models import Medicine
            
            if not query or len(query.strip()) < 2:
                return []
            
            search_term = f"%{query.strip()}%"
            
            medicines = Medicine.query.filter(
                Medicine.description.ilike(search_term)
            ).limit(limit).all()
            
            return MedicineSearchService._format_results(medicines)
            
        except Exception as e:
            logger.error(f"Description search error: {e}")
            return []
    
    @staticmethod
    def multi_field_search(query: str, limit: int = 5) -> List[Dict]:
        """
        Search across multiple fields: name, chemical, description, category
        Returns combined results with deduplication
        """
        try:
            from app import db
            from models import Medicine

            if not query or len(query.strip()) < 2:
                return []

            search_term = f"%{query.strip()}%"

            # Use OR to search across all fields
            medicines = Medicine.query.filter(
                db.or_(
                    Medicine.name.ilike(search_term),
                    Medicine.chemical.ilike(search_term),
                    Medicine.description.ilike(search_term),
                    Medicine.category.ilike(search_term)
                )
            ).limit(limit).all()

            return MedicineSearchService._format_results(medicines)

        except Exception as e:
            logger.error(f"Multi-field search error: {e}")
            return []

    @staticmethod
    def fuzzy_search(query: str, limit: int = 5, max_distance: int = 2) -> List[Dict]:
        """
        Search for medicines with spelling tolerance (Levenshtein distance)
        Handles incorrect spellings up to max_distance edits
        """
        try:
            from models import Medicine

            if not query or len(query.strip()) < 2:
                return []

            query_normalized = query.strip().lower()
            all_medicines = Medicine.query.all()

            # Calculate distance for each medicine name
            scored_medicines: List[Tuple[Medicine, int]] = []

            for medicine in all_medicines:
                med_name_lower = medicine.name.lower()
                distance = levenshtein_distance(query_normalized, med_name_lower)

                # Also check for partial matches (prefix)
                if med_name_lower.startswith(query_normalized):
                    distance = 0  # Perfect prefix match

                if distance <= max_distance:
                    scored_medicines.append((medicine, distance))

            # Sort by distance and return top results
            scored_medicines.sort(key=lambda x: x[1])
            results = [med for med, _ in scored_medicines[:limit]]

            return MedicineSearchService._format_results(results)

        except Exception as e:
            logger.error(f"Fuzzy search error: {e}")
            return []

    @staticmethod
    def partial_search(prefix: str, limit: int = 10) -> List[Dict]:
        """
        Search for medicines starting with the given prefix (half search)
        Used for autocomplete and as-you-type searching
        """
        try:
            from models import Medicine

            if not prefix or len(prefix.strip()) < 1:
                return []

            prefix_normalized = prefix.strip().lower()

            # Get all medicines and filter by prefix
            all_medicines = Medicine.query.all()
            matching_medicines = [
                med for med in all_medicines
                if med.name.lower().startswith(prefix_normalized)
            ]

            # Sort by name relevance
            matching_medicines.sort(key=lambda x: (x.name.lower() != prefix_normalized, len(x.name)))

            return MedicineSearchService._format_results(matching_medicines[:limit])

        except Exception as e:
            logger.error(f"Partial search error: {e}")
            return []

    @staticmethod
    def smart_search(query: str, limit: int = 5) -> List[Dict]:
        """
        Intelligent search that combines partial matching and fuzzy matching
        First tries partial/prefix match, then falls back to fuzzy search
        """
        try:
            from models import Medicine

            if not query or len(query.strip()) < 2:
                return []

            query_normalized = query.strip().lower()

            # Get all medicines for combined search
            all_medicines = Medicine.query.all()
            results_with_score: List[Tuple[Medicine, float]] = []

            for medicine in all_medicines:
                med_name_lower = medicine.name.lower()
                score = 0.0

                # Prefer exact matches or prefix matches (highest score)
                if med_name_lower == query_normalized:
                    score = 1000.0
                elif med_name_lower.startswith(query_normalized):
                    score = 500.0 + (len(query_normalized) / len(med_name_lower))
                # Check for substring (word boundary)
                elif query_normalized in med_name_lower:
                    score = 100.0
                # Fuzzy match
                else:
                    distance = levenshtein_distance(query_normalized, med_name_lower)
                    if distance <= 2:
                        score = max(0, 50.0 - (distance * 10))

                if score > 0:
                    results_with_score.append((medicine, score))

            # Sort by score (descending)
            results_with_score.sort(key=lambda x: x[1], reverse=True)
            results = [med for med, _ in results_with_score[:limit]]

            return MedicineSearchService._format_results(results)

        except Exception as e:
            logger.error(f"Smart search error: {e}")
            return []
    
    @staticmethod
    def get_by_exact_name(name: str) -> Optional[Dict]:
        """
        Get medicine by exact name match (case-insensitive)
        """
        try:
            from models import Medicine
            
            if not name:
                return None
            
            medicine = Medicine.query.filter(
                Medicine.name.ilike(name)
            ).first()
            
            if not medicine:
                return None
            
            return MedicineSearchService._format_single(medicine)
            
        except Exception as e:
            logger.error(f"Exact name search error: {e}")
            return None
    
    @staticmethod
    def search_in_stock(query: str, limit: int = 5) -> List[Dict]:
        """
        Search only in-stock medicines
        """
        try:
            from app import db
            from models import Medicine
            
            if not query or len(query.strip()) < 2:
                return []
            
            search_term = f"%{query.strip()}%"
            
            medicines = Medicine.query.filter(
                db.and_(
                    Medicine.status == 'in_stock',
                    db.or_(
                        Medicine.name.ilike(search_term),
                        Medicine.chemical.ilike(search_term),
                        Medicine.description.ilike(search_term)
                    )
                )
            ).limit(limit).all()
            
            return MedicineSearchService._format_results(medicines)
            
        except Exception as e:
            logger.error(f"In-stock search error: {e}")
            return []
    
    @staticmethod
    def get_all_medicines(limit: int = None, offset: int = 0) -> List[Dict]:
        """
        Get all medicines with pagination
        """
        try:
            from models import Medicine
            
            query = Medicine.query.order_by(Medicine.name)
            
            if limit:
                query = query.limit(limit).offset(offset)
            
            medicines = query.all()
            return MedicineSearchService._format_results(medicines)
            
        except Exception as e:
            logger.error(f"Get all medicines error: {e}")
            return []
    
    @staticmethod
    def get_medicines_by_price_range(min_price: int = 0, max_price: int = 100000, 
                                     limit: int = 5) -> List[Dict]:
        """
        Get medicines within a price range
        """
        try:
            from app import db
            from models import Medicine
            
            medicines = Medicine.query.filter(
                db.and_(
                    Medicine.price >= min_price,
                    Medicine.price <= max_price
                )
            ).limit(limit).all()
            
            return MedicineSearchService._format_results(medicines)
            
        except Exception as e:
            logger.error(f"Price range search error: {e}")
            return []
    
    @staticmethod
    def autocomplete(prefix: str, limit: int = 10) -> List[str]:
        """
        Get autocomplete suggestions for medicine names
        """
        try:
            from models import Medicine
            
            if not prefix or len(prefix.strip()) < 1:
                return []
            
            search_term = f"{prefix.strip()}%"
            
            medicines = Medicine.query.filter(
                Medicine.name.ilike(search_term)
            ).with_entities(Medicine.name).limit(limit).all()
            
            return [m.name for m in medicines if m.name]
            
        except Exception as e:
            logger.error(f"Autocomplete error: {e}")
            return []
    
    @staticmethod
    def _format_single(medicine) -> Dict:
        """Format a single medicine object"""
        image_path = medicine.image_path or ''
        
        # Build image URL
        if image_path:
            if image_path.startswith('/'):
                image_url = image_path
            else:
                image_url = f"/static/uploads/medicines/{image_path}"
        else:
            image_url = '/static/images/default-medicine.png'
        
        return {
            'id': medicine.id,
            'name': medicine.name,
            'price': medicine.price,
            'chemical': medicine.chemical or '',
            'ingredients': medicine.chemical or '',
            'description': medicine.description or '',
            'category': medicine.category or '',
            'form': medicine.category or '',
            'status': medicine.status or 'in_stock',
            'stock_quantity': medicine.stock_quantity or 0,
            'image': image_path,
            'image_url': image_url,
            'manufacturer': MedicineSearchService._extract_manufacturer(medicine.description),
            'size': MedicineSearchService._extract_size(medicine.description),
            'prescription_required': False,
            'created_at': medicine.created_at.isoformat() if medicine.created_at else None,
            'updated_at': medicine.updated_at.isoformat() if medicine.updated_at else None,
        }
    
    @staticmethod
    def _format_results(medicines) -> List[Dict]:
        """Format a list of medicine objects"""
        return [MedicineSearchService._format_single(med) for med in medicines]
    
    @staticmethod
    def _extract_manufacturer(description: str) -> str:
        """Extract manufacturer from description"""
        if not description:
            return ''
        
        patterns = [
            r'Manufacturer:\s*([^\n.]+)',
            r'Manufactured by:\s*([^\n.]+)',
            r'By:\s*([^\n.]+)',
            r'(?:produced|made)\s+by:\s*([^\n.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ''
    
    @staticmethod
    def _extract_size(description: str) -> str:
        """Extract package size from description"""
        if not description:
            return ''
        
        patterns = [
            r'(?:Pack|Package|Size|Qty|Quantity)\s*(?:of|:)?\s*([^\n.]+?)(?:\n|$)',
            r'(\d+\s*(?:tablets?|capsules?|ml|mg|gm|g|pieces|pcs))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                result = match.group(1).strip()
                if result:
                    return result
        
        return ''


# Backward compatibility functions for existing code

def search_medicines(query: str, limit: int = 5) -> List[Dict]:
    """
    Legacy function - uses smart search (combines partial + fuzzy matching)
    Handles spelling mistakes and partial searches
    """
    return MedicineSearchService.smart_search(query, limit)


def get_medicine_by_name(name: str) -> Optional[Dict]:
    """Legacy function"""
    return MedicineSearchService.get_by_exact_name(name)


def search_medicines_for_condition(condition: str, limit: int = 5) -> List[Dict]:
    """Legacy function - searches description for condition keywords"""
    return MedicineSearchService.search_by_description(condition, limit)


def get_all_medicine_names() -> List[str]:
    """Legacy function - get all medicine names"""
    try:
        return MedicineSearchService.autocomplete('', limit=10000)
    except Exception as e:
        logger.error(f"Get medicine names error: {e}")
        return []


def find_medicines_in_text(text: str) -> List[Dict]:
    """
    Find medicines mentioned in text using keyword extraction
    """
    try:
        found_medicines = []
        seen_ids = set()
        
        # Extract keywords from text
        keywords = extract_medicine_keywords(text)
        
        # Also try individual words
        words = text.split()
        for word in words:
            if len(word) > 3 and word.lower() not in {
                'what', 'about', 'tell', 'give', 'information', 'this', 'that', 
                'have', 'need', 'want', 'can', 'could', 'should', 'would'
            }:
                if word not in keywords:
                    keywords.append(word)
        
        # Search for each keyword
        for keyword in keywords[:8]:
            if len(keyword) > 2:
                matches = search_medicines(keyword, limit=3)
                for match in matches:
                    if match['id'] not in seen_ids:
                        seen_ids.add(match['id'])
                        found_medicines.append(match)
                        if len(found_medicines) >= 5:
                            return found_medicines
        
        return found_medicines[:5]
        
    except Exception as e:
        logger.error(f"Find medicines error: {e}")
        return []


def extract_medicine_keywords(text: str) -> List[str]:
    """Extract medicine name patterns from text"""
    keywords = []
    
    patterns = [
        r'\b(\w+(?:\s+\d+\s*(?:mg|ml|gm|g|mcg|iu))?(?:\s+(?:tablets?|capsules?|syrup|injection|drops?|suspension|cream|ointment|gel|solution))?)\b',
        r'\b(\w+(?:tab|cap|inj|syr|susp)s?)\b',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        keywords.extend(matches)
    
    common_words = {
        'i', 'me', 'my', 'you', 'your', 'the', 'a', 'an', 'is', 'are', 'was', 'were',
        'what', 'which', 'who', 'how', 'when', 'where', 'why', 'can', 'could', 'should',
        'would', 'do', 'does', 'did', 'have', 'has', 'had', 'for', 'to', 'of', 'in',
        'on', 'at', 'by', 'with', 'about', 'this', 'that', 'these', 'those', 'it',
        'tell', 'show', 'give', 'get', 'find', 'need', 'want', 'like', 'use', 'take',
        'medicine', 'drug', 'tablet', 'capsule', 'syrup', 'price', 'cost', 'buy'
    }
    
    keywords = [
        k.strip() for k in keywords
        if k.strip().lower() not in common_words and len(k.strip()) > 2
    ]
    
    return list(set(keywords))


def build_medicine_context(medicines: List[Dict]) -> str:
    """Build context string from medicines for AI prompt"""
    if not medicines:
        return ""
    
    context_parts = ["[MEDICINE DATA FROM RED DOT PHARMACY DATABASE]"]
    
    for med in medicines:
        context_parts.append(f"\n--- Medicine: {med['name']} ---")
        context_parts.append(f"Price: Rs. {med['price']}")
        context_parts.append(f"Image URL: {med['image_url']}")
        
        if med.get('manufacturer'):
            context_parts.append(f"Manufacturer: {med['manufacturer']}")
        
        if med.get('ingredients'):
            context_parts.append(f"Ingredients/Active Compound: {med['ingredients']}")
        
        if med.get('form'):
            context_parts.append(f"Form: {med['form']}")
        
        if med.get('size'):
            context_parts.append(f"Package Size: {med['size']}")
        
        if med.get('description'):
            desc = med['description'][:500]
            context_parts.append(f"Description: {desc}")
        
        context_parts.append(f"Availability: {med.get('status', 'in_stock')}")
    
    context_parts.append("\n[END OF MEDICINE DATA]")
    context_parts.append("\nIMPORTANT: Use ONLY this medicine data in your response. Include the Image URL when mentioning medicines.")
    
    return "\n".join(context_parts)


def format_medicine_response(medicines: List[Dict], lang: str = "en") -> List[Dict]:
    """Format medicines for chatbot response"""
    formatted = []
    
    for med in medicines:
        formatted.append({
            'type': 'medicine',
            'id': med.get('id'),
            'name': med.get('name', ''),
            'price': med.get('price', 0),
            'manufacturer': med.get('manufacturer', ''),
            'form': med.get('form', ''),
            'ingredients': med.get('ingredients', ''),
            'image_url': med.get('image_url', '/static/images/default-medicine.png'),
            'status': med.get('status', 'in_stock'),
            'description': med.get('description', ''),
            'description_short': (med.get('description', '')[:150] + '...') if len(med.get('description', '')) > 150 else med.get('description', '')
        })
    
    return formatted
