"""
Medicine RAG (Retrieval-Augmented Generation) Service
Retrieves medicine data from the database for the chatbot.
"""

import re
import logging
from typing import List, Dict, Optional

def search_medicines(query: str, limit: int = 5) -> List[Dict]:
    """
    Search medicines by name, ingredients, or description.
    Returns a list of matching medicine dictionaries.
    """
    try:
        from app import db
        from models import Medicine
        
        if not query or len(query.strip()) < 2:
            return []
        
        search_term = f"%{query.strip()}%"
        
        medicines = Medicine.query.filter(
            db.or_(
                Medicine.name.ilike(search_term),
                Medicine.chemical.ilike(search_term),
                Medicine.description.ilike(search_term),
                Medicine.category.ilike(search_term)
            )
        ).limit(limit).all()
        
        results = []
        for med in medicines:
            results.append({
                'id': med.id,
                'name': med.name,
                'price': med.price,
                'manufacturer': extract_manufacturer(med.description) if med.description else '',
                'ingredients': med.chemical or '',
                'form': med.category or '',
                'size': extract_size(med.description) if med.description else '',
                'prescription_required': False,
                'description': med.description or '',
                'image': med.image_path or '',
                'status': med.status or 'in_stock',
                'stock_quantity': med.stock_quantity or 0
            })
        
        return results
        
    except Exception as e:
        logging.error(f"Medicine search error: {e}")
        return []


def get_medicine_by_name(name: str) -> Optional[Dict]:
    """
    Get a specific medicine by exact or partial name match.
    """
    try:
        from app import db
        from models import Medicine
        
        medicine = Medicine.query.filter(
            Medicine.name.ilike(f"%{name}%")
        ).first()
        
        if not medicine:
            return None
        
        return {
            'id': medicine.id,
            'name': medicine.name,
            'price': medicine.price,
            'manufacturer': extract_manufacturer(medicine.description) if medicine.description else '',
            'ingredients': medicine.chemical or '',
            'form': medicine.category or '',
            'size': extract_size(medicine.description) if medicine.description else '',
            'prescription_required': False,
            'description': medicine.description or '',
            'image': medicine.image_path or '',
            'status': medicine.status or 'in_stock',
            'stock_quantity': medicine.stock_quantity or 0
        }
        
    except Exception as e:
        logging.error(f"Get medicine error: {e}")
        return None


def get_all_medicine_names() -> List[str]:
    """
    Get all medicine names for keyword matching.
    """
    try:
        from models import Medicine
        
        medicines = Medicine.query.with_entities(Medicine.name).all()
        return [m.name for m in medicines if m.name]
        
    except Exception as e:
        logging.error(f"Get medicine names error: {e}")
        return []


def extract_medicine_keywords(text: str) -> List[str]:
    """
    Extract potential medicine names or keywords from user text.
    Uses pattern matching and known medicine names.
    """
    keywords = []
    
    medicine_patterns = [
        r'\b(\w+(?:\s+\d+\s*(?:mg|ml|gm|g|mcg|iu))?(?:\s+(?:tablets?|capsules?|syrup|injection|drops?|suspension|cream|ointment|gel|solution))?)\b',
        r'\b(\w+(?:tab|cap|inj|syr|susp)s?)\b',
    ]
    
    for pattern in medicine_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        keywords.extend(matches)
    
    common_words = {'i', 'me', 'my', 'you', 'your', 'the', 'a', 'an', 'is', 'are', 'was', 'were', 
                    'what', 'which', 'who', 'how', 'when', 'where', 'why', 'can', 'could', 'should',
                    'would', 'do', 'does', 'did', 'have', 'has', 'had', 'for', 'to', 'of', 'in', 
                    'on', 'at', 'by', 'with', 'about', 'this', 'that', 'these', 'those', 'it',
                    'tell', 'show', 'give', 'get', 'find', 'need', 'want', 'like', 'use', 'take',
                    'medicine', 'drug', 'tablet', 'capsule', 'syrup', 'price', 'cost', 'buy'}
    
    keywords = [k.strip() for k in keywords if k.strip().lower() not in common_words and len(k.strip()) > 2]
    
    return list(set(keywords))


def find_medicines_in_text(text: str) -> List[Dict]:
    """
    Find all medicines mentioned in the text by matching against database.
    """
    try:
        all_names = get_all_medicine_names()
        found_medicines = []
        text_lower = text.lower()
        
        for name in all_names:
            name_parts = name.lower().split()
            if any(part in text_lower for part in name_parts if len(part) > 3):
                medicine = get_medicine_by_name(name)
                if medicine:
                    found_medicines.append(medicine)
        
        keywords = extract_medicine_keywords(text)
        for keyword in keywords:
            if len(keyword) > 3:
                matches = search_medicines(keyword, limit=2)
                for match in matches:
                    if match not in found_medicines:
                        found_medicines.append(match)
        
        return found_medicines[:5]
        
    except Exception as e:
        logging.error(f"Find medicines error: {e}")
        return []


def search_medicines_for_condition(condition: str, limit: int = 5) -> List[Dict]:
    """
    Search medicines that may help with a given condition/symptom.
    Searches in medicine descriptions.
    """
    try:
        from app import db
        from models import Medicine
        
        condition_keywords = condition.lower().split()
        
        search_terms = []
        for keyword in condition_keywords:
            if len(keyword) > 3:
                search_terms.append(f"%{keyword}%")
        
        if not search_terms:
            return []
        
        conditions = [Medicine.description.ilike(term) for term in search_terms]
        
        medicines = Medicine.query.filter(db.or_(*conditions)).limit(limit).all()
        
        results = []
        for med in medicines:
            results.append({
                'id': med.id,
                'name': med.name,
                'price': med.price,
                'manufacturer': extract_manufacturer(med.description) if med.description else '',
                'ingredients': med.chemical or '',
                'form': med.category or '',
                'size': extract_size(med.description) if med.description else '',
                'prescription_required': False,
                'description': med.description or '',
                'image': med.image_path or '',
                'status': med.status or 'in_stock',
                'stock_quantity': med.stock_quantity or 0
            })
        
        return results
        
    except Exception as e:
        logging.error(f"Condition search error: {e}")
        return []


def build_medicine_context(medicines: List[Dict]) -> str:
    """
    Build a context string from medicine data for the AI prompt.
    """
    if not medicines:
        return ""
    
    context_parts = ["[MEDICINE DATA FROM RED DOT PHARMACY DATABASE]"]
    
    for med in medicines:
        context_parts.append(f"\n--- Medicine: {med['name']} ---")
        context_parts.append(f"Price: Rs. {med['price']}")
        
        if med.get('manufacturer'):
            context_parts.append(f"Manufacturer: {med['manufacturer']}")
        
        if med.get('ingredients'):
            context_parts.append(f"Ingredients/Active Compound: {med['ingredients']}")
        
        if med.get('form'):
            context_parts.append(f"Form: {med['form']}")
        
        if med.get('size'):
            context_parts.append(f"Package Size: {med['size']}")
        
        if med.get('description'):
            desc = med['description'][:500] if len(med['description']) > 500 else med['description']
            context_parts.append(f"Description: {desc}")
        
        context_parts.append(f"Availability: {med.get('status', 'in_stock')}")
    
    context_parts.append("\n[END OF MEDICINE DATA]")
    context_parts.append("\nIMPORTANT: Use ONLY this medicine data in your response. Do not make up any medicine information.")
    
    return "\n".join(context_parts)


def format_medicine_response(medicines: List[Dict], lang: str = "en") -> List[Dict]:
    """
    Format medicines for display in chatbot response.
    Includes image paths for frontend display.
    """
    formatted = []
    
    for med in medicines:
        formatted.append({
            'id': med.get('id'),
            'name': med.get('name', ''),
            'price': med.get('price', 0),
            'form': med.get('form', ''),
            'ingredients': med.get('ingredients', ''),
            'image': med.get('image', ''),
            'status': med.get('status', 'in_stock'),
            'description_short': (med.get('description', '')[:150] + '...') if med.get('description') and len(med.get('description', '')) > 150 else med.get('description', '')
        })
    
    return formatted


def extract_manufacturer(description: str) -> str:
    """Extract manufacturer from description if mentioned."""
    if not description:
        return ''
    
    patterns = [
        r'Manufacturer:\s*([^\n]+)',
        r'Manufactured by:\s*([^\n]+)',
        r'By:\s*([^\n]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return ''


def extract_size(description: str) -> str:
    """Extract package size from description if mentioned."""
    if not description:
        return ''
    
    patterns = [
        r'Package Size:\s*([^\n]+)',
        r'Pack of\s*([^\n]+)',
        r'(\d+\s*(?:tablets?|capsules?|ml|mg|g))',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return ''
