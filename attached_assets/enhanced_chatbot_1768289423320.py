"""
Enhanced Medical Chatbot with Smart RAG Integration
Replaces direct RAG calls with intelligent orchestration layer.
"""

import os
import logging
import uuid
from datetime import datetime
from smart_rag_orchestrator import smart_retrieve, get_orchestrator

# Import existing chatbot functions
from services.chatbot import (
    detect_language,
    needs_escalation,
    is_unsafe_request,
    get_emergency_response,
    get_guardrail_response,
    get_offline_response,
    MEDICAL_SYSTEM_PROMPT,
    MEDICAL_SYSTEM_PROMPT_URDU,
    DISCLAIMER_EN,
    DISCLAIMER_UR
)

# Gemini setup (from original chatbot.py)
gemini_model = None
genai = None
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))

if GEMINI_API_KEY:
    try:
        import google.generativeai as genai_module
        genai = genai_module
        genai.configure(api_key=GEMINI_API_KEY)
        
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        gemini_model = genai.GenerativeModel(
            GEMINI_MODEL,
            safety_settings=safety_settings
        )
        logging.info(f"Gemini model initialized: {GEMINI_MODEL}")
    except Exception as e:
        logging.error(f"Failed to initialize Gemini: {e}")


def generate_smart_response(text, prefer_urdu=None, session_id=None, lang="auto"):
    """
    Enhanced response generation with smart RAG orchestration.
    
    Key improvements:
    - Query classification before retrieval
    - Database-first approach
    - Image validation and filtering
    - No irrelevant Wikipedia content
    """
    
    # Detect language
    if lang == "auto":
        detected_lang = detect_language(text)
    elif lang in ["ur", "urdu"]:
        detected_lang = "ur"
    else:
        detected_lang = "en"
    
    if prefer_urdu is not None:
        detected_lang = "ur" if prefer_urdu else "en"
    
    timestamp = datetime.now().isoformat()
    session_id = session_id or str(uuid.uuid4())
    
    # Safety checks (unchanged)
    if needs_escalation(text):
        return {
            'message': get_emergency_response(detected_lang),
            'flagged': True,
            'needs_doctor': True,
            'suggested_medicines': [],
            'medicines': [],
            'language': detected_lang,
            'timestamp': timestamp,
            'session_id': session_id
        }
    
    if is_unsafe_request(text):
        return {
            'message': get_guardrail_response(detected_lang),
            'flagged': False,
            'needs_doctor': True,
            'suggested_medicines': [],
            'medicines': [],
            'language': detected_lang,
            'timestamp': timestamp,
            'session_id': session_id
        }
    
    # === NEW: Smart RAG Orchestration ===
    try:
        orchestrator = get_orchestrator()
        retrieval = smart_retrieve(text, detected_lang)
        
        logging.info(f"Smart retrieval: {retrieval['context_type']}, "
                    f"{len(retrieval['medications'])} meds, "
                    f"{len(retrieval['images'])} images")
        
    except Exception as rag_error:
        logging.error(f"Smart RAG failed: {rag_error}")
        retrieval = {
            'medications': [],
            'wiki_context': None,
            'images': [],
            'context_type': 'none',
            'should_show_images': False
        }
    
    # Generate AI response
    if gemini_model:
        try:
            # Select system prompt
            system_prompt = MEDICAL_SYSTEM_PROMPT_URDU if detected_lang == "ur" else MEDICAL_SYSTEM_PROMPT
            
            # Build context from smart retrieval
            ai_context = orchestrator.build_ai_context(retrieval) if retrieval['context_type'] != 'none' else ""
            
            if ai_context:
                system_prompt += f"\n\n{ai_context}"
            
            full_prompt = f"{system_prompt}\n\nUser: {text}\n\nAssistant:"
            
            generation_config = {
                "temperature": GEMINI_TEMPERATURE,
                "max_output_tokens": 500,
            }
            
            response = gemini_model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            ai_message = ""
            
            # Parse response (unchanged)
            try:
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content.parts:
                        ai_message = "".join(
                            part.text for part in candidate.content.parts 
                            if hasattr(part, 'text')
                        ).strip()
                    
                    if hasattr(candidate, 'finish_reason'):
                        finish_reason = candidate.finish_reason
                        if finish_reason in [2, 3]:  # Blocked
                            logging.warning("Response blocked by safety filters")
                            ai_message = ""
                
                if not ai_message and hasattr(response, 'text') and response.text:
                    ai_message = response.text.strip()
                    
            except Exception as parse_error:
                logging.error(f"Parse error: {parse_error}")
                ai_message = ""
            
            # Fallback if empty
            if not ai_message:
                ai_message = get_offline_response(detected_lang)
            
            # Add disclaimer if missing
            if DISCLAIMER_EN not in ai_message and DISCLAIMER_UR not in ai_message:
                disclaimer = DISCLAIMER_UR if detected_lang == "ur" else DISCLAIMER_EN
                ai_message = f"{ai_message}\n\n{disclaimer}"
            
            # Format medicine response
            formatted_medicines = []
            if retrieval['medications']:
                formatted_medicines = _format_medicine_display(
                    retrieval['medications'],
                    retrieval['images'],
                    detected_lang
                )
            
            return {
                'message': ai_message,
                'flagged': False,
                'needs_doctor': False,
                'suggested_medicines': [],
                'medicines': formatted_medicines,
                'images': retrieval['images'] if retrieval['should_show_images'] else [],
                'language': detected_lang,
                'timestamp': timestamp,
                'session_id': session_id,
                'context_source': retrieval['context_type']
            }
            
        except Exception as e:
            logging.error(f"Gemini error: {e}")
    
    # Offline fallback
    formatted_medicines = []
    if retrieval['medications']:
        formatted_medicines = _format_medicine_display(
            retrieval['medications'],
            retrieval['images'],
            detected_lang
        )
    
    return {
        'message': get_offline_response(detected_lang),
        'flagged': False,
        'needs_doctor': True,
        'suggested_medicines': [],
        'medicines': formatted_medicines,
        'language': detected_lang,
        'timestamp': timestamp,
        'session_id': session_id
    }


def _format_medicine_display(medications: List, images: List, lang: str) -> List[Dict]:
    """
    Format medications for display with validated images only.
    """
    formatted = []
    
    for med in medications:
        # Find matching validated image
        matching_image = next(
            (img for img in images if img['medication_id'] == med.get('id')),
            None
        )
        
        image_url = matching_image['url'] if matching_image else '/static/images/default-medicine.png'
        
        formatted.append({
            'type': 'medicine',
            'id': med.get('id'),
            'name': med.get('name', ''),
            'price': med.get('price', 0),
            'manufacturer': med.get('manufacturer', ''),
            'form': med.get('form', ''),
            'ingredients': med.get('ingredients', ''),
            'image_url': image_url,
            'status': med.get('status', 'in_stock'),
            'description': med.get('description', ''),
            'description_short': (
                med.get('description', '')[:150] + '...'
                if med.get('description') and len(med.get('description', '')) > 150
                else med.get('description', '')
            ),
            'image_source': 'database'  # Always from DB
        })
    
    return formatted


# Drop-in replacement for existing generate_response
def generate_response(text, prefer_urdu=None, session_id=None, lang="auto"):
    """
    Backward-compatible wrapper for existing code.
    Routes to smart response generation.
    """
    return generate_smart_response(text, prefer_urdu, session_id, lang)
