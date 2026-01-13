"""
Gemini LLM Client - Query Understanding & Medical Mapping
"""
import os
import json
import re
from typing import Dict, List, Any
import google.generativeai as genai


class GeminiClient:
    def __init__(self):
        self.api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        self._connected = False
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
                self.model = genai.GenerativeModel(model_name)
                self._connected = True
                print("Gemini API connected")
            except Exception as e:
                print(f"Gemini connection failed: {e}")
    
    def is_connected(self) -> bool:
        return self._connected
    
    async def extract_medical_keyword(self, query: str) -> Dict[str, Any]:
        """Extract clean medical subject from user query"""
        prompt = f"""You are a medical query parser. Extract the PRIMARY medical subject.

Query: "{query}"

Respond ONLY in JSON:
{{
    "extracted_keyword": "<single medical term>",
    "query_type": "<medication|disease|symptom|general>",
    "intent": "<lookup|explanation|treatment|side_effects>",
    "confidence": <0.0-1.0>
}}

Examples:
- "what are main symptoms of disease syphilis" -> {{"extracted_keyword": "syphilis", "query_type": "disease", "intent": "explanation", "confidence": 0.95}}
- "Panadol 500mg" -> {{"extracted_keyword": "panadol", "query_type": "medication", "intent": "lookup", "confidence": 0.98}}
- "medicine for fever" -> {{"extracted_keyword": "fever", "query_type": "symptom", "intent": "treatment", "confidence": 0.9}}
"""
        
        if not self._connected:
            return self._fallback_extraction(query)
        
        try:
            response = self.model.generate_content(prompt)
            json_match = re.search(r'\{[^}]+\}', response.text.strip(), re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return self._fallback_extraction(query)
        except Exception as e:
            print(f"Gemini error: {e}")
            return self._fallback_extraction(query)
    
    def extract_medical_keyword_sync(self, query: str) -> Dict[str, Any]:
        """Synchronous version for non-async contexts"""
        prompt = f"""You are a medical query parser. Extract the PRIMARY medical subject.

Query: "{query}"

Respond ONLY in JSON:
{{
    "extracted_keyword": "<single medical term>",
    "query_type": "<medication|disease|symptom|general>",
    "intent": "<lookup|explanation|treatment|side_effects>",
    "confidence": <0.0-1.0>
}}
"""
        
        if not self._connected:
            return self._fallback_extraction(query)
        
        try:
            response = self.model.generate_content(prompt)
            json_match = re.search(r'\{[^}]+\}', response.text.strip(), re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return self._fallback_extraction(query)
        except Exception as e:
            print(f"Gemini error: {e}")
            return self._fallback_extraction(query)
    
    async def map_disease_to_medications(self, disease: str) -> List[str]:
        """Map disease/symptom to medication ingredients"""
        prompt = f"""Map this condition to common medication INGREDIENTS (generic names, not brands).

Condition: "{disease}"

Rules:
1. List only generic ingredient names
2. Maximum 5 ingredients
3. Order by common usage

Respond ONLY as JSON array: ["ingredient1", "ingredient2", "ingredient3"]
"""
        
        if not self._connected:
            return self._fallback_disease_mapping(disease)
        
        try:
            response = self.model.generate_content(prompt)
            json_match = re.search(r'\[[^\]]+\]', response.text.strip())
            if json_match:
                return json.loads(json_match.group())
            return self._fallback_disease_mapping(disease)
        except:
            return self._fallback_disease_mapping(disease)
    
    def map_disease_to_medications_sync(self, disease: str) -> List[str]:
        """Synchronous version"""
        prompt = f"""Map this condition to common medication INGREDIENTS (generic names, not brands).

Condition: "{disease}"

Rules:
1. List only generic ingredient names
2. Maximum 5 ingredients
3. Order by common usage

Respond ONLY as JSON array: ["ingredient1", "ingredient2", "ingredient3"]
"""
        
        if not self._connected:
            return self._fallback_disease_mapping(disease)
        
        try:
            response = self.model.generate_content(prompt)
            json_match = re.search(r'\[[^\]]+\]', response.text.strip())
            if json_match:
                return json.loads(json_match.group())
            return self._fallback_disease_mapping(disease)
        except:
            return self._fallback_disease_mapping(disease)
    
    async def generate_wiki_query(self, keyword: str, query_type: str) -> str:
        """Generate safe Wikipedia search query - NO IMAGES"""
        forbidden = ['image', 'picture', 'photo', 'anatomy', 'diagram']
        
        if not self._connected:
            return f"{keyword} {query_type} medical information"
        
        try:
            prompt = f"""Generate a Wikipedia search query for medical info.
Keyword: "{keyword}", Type: "{query_type}"
NEVER include: images, pictures, anatomy, diagrams
Respond with ONLY the search query string."""
            
            response = self.model.generate_content(prompt)
            query = response.text.strip().strip('"\'')
            
            if any(term in query.lower() for term in forbidden):
                return f"{keyword} {query_type} medical information"
            return query
        except:
            return f"{keyword} {query_type} medical information"
    
    async def summarize_wiki_content(self, content: str, keyword: str) -> str:
        """Summarize Wikipedia content - medical focus only"""
        if not self._connected:
            return content[:1000] + "..." if len(content) > 1000 else content
        
        try:
            prompt = f"""Summarize this medical content about "{keyword}".
Focus ONLY on: indications, usage, side effects, symptoms, treatment.
Remove any image references. Max 500 words.

Content: {content[:4000]}"""
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except:
            return content[:1000]
    
    def _fallback_extraction(self, query: str) -> Dict[str, Any]:
        """Fallback when Gemini unavailable"""
        stop_words = {'what', 'are', 'is', 'the', 'main', 'symptoms', 'of', 'for', 
                      'disease', 'medicine', 'drug', 'tablet', 'capsule', 'how', 'can', 'i'}
        words = [w for w in query.lower().split() if w not in stop_words and len(w) > 2]
        
        query_type = "general"
        if any(w in query.lower() for w in ['symptom', 'disease', 'infection', 'condition']):
            query_type = "disease"
        elif any(w in query.lower() for w in ['mg', 'ml', 'tablet', 'capsule', 'dose']):
            query_type = "medication"
        elif any(w in query.lower() for w in ['pain', 'fever', 'cough', 'cold', 'headache']):
            query_type = "symptom"
        
        return {
            "extracted_keyword": words[0] if words else query.split()[0],
            "query_type": query_type,
            "intent": "lookup",
            "confidence": 0.6
        }
    
    def _fallback_disease_mapping(self, disease: str) -> List[str]:
        """Fallback disease to medication mapping"""
        mappings = {
            "fever": ["paracetamol", "ibuprofen"],
            "pain": ["paracetamol", "ibuprofen", "aspirin"],
            "headache": ["paracetamol", "ibuprofen"],
            "infection": ["amoxicillin", "azithromycin"],
            "cold": ["paracetamol", "phenylephrine"],
            "cough": ["dextromethorphan", "guaifenesin"],
            "allergy": ["cetirizine", "loratadine"],
            "inflammation": ["ibuprofen", "diclofenac"],
            "diabetes": ["metformin", "glibenclamide"],
            "hypertension": ["amlodipine", "losartan"],
            "asthma": ["salbutamol", "budesonide"],
        }
        
        for key, meds in mappings.items():
            if key in disease.lower():
                return meds
        return ["paracetamol"]
