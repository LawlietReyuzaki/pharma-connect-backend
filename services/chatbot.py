"""
Medical Assistant Chatbot Service
Provides safe, guard-railed medical information in English and Urdu.
Uses Google Gemini for AI responses with comprehensive safety features.
"""

import os
import re
import logging
import uuid
from datetime import datetime

gemini_model = None
genai = None
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
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
        logging.error(f"Failed to initialize Gemini client: {e}")
else:
    logging.warning("GOOGLE_API_KEY/GEMINI_API_KEY not set - chatbot will use offline mode")

MEDICAL_SYSTEM_PROMPT = """You are a Pharmacy Medical Assistant AI Agent for Red Dot Pharmacy.

Your role is to provide helpful, accurate, and safe information related to diseases and medicines available in the pharmacy system.

CORE RESPONSIBILITIES:
1. Assist users by providing general information about diseases.
2. Assist users by providing detailed information about medicines from our database.
3. Provide medicine-related details including:
   - Price
   - Brand / Manufacturer
   - Ingredients
   - Description
   - Form and size
   - Common diseases or conditions the medicine is used for
4. Help users inquire about diseases by explaining:
   - Common symptoms
   - Possible causes
   - General treatment approaches
5. Analyze patient-reported symptoms and suggest possible conditions or relevant medicines, but NEVER give a final or confirmed diagnosis.

MEDICAL SAFETY (MANDATORY):
- You are NOT a doctor or healthcare professional.
- You must NOT replace professional medical advice.
- When discussing symptoms, diseases, or diagnosis, ALWAYS include this disclaimer:
"⚠️ This information is for educational purposes only and is not a medical diagnosis. Please consult a qualified doctor or healthcare professional for proper evaluation, diagnosis, and treatment."

DATA USAGE RULES (CRITICAL - MUST FOLLOW):
- You can ONLY provide medicine information for medicines that exist in the Red Dot Pharmacy database.
- NEVER invent, fabricate, or suggest any medicine that is not in the provided database context.
- If a user asks about a medicine NOT in our database, say: "I don't have information about that medicine in our pharmacy database. Please ask about medicines available at Red Dot Pharmacy, or visit our shop to browse available products."
- Do NOT provide prices, brands, or details for medicines outside the database.
- When medicine data is provided in context, use ONLY that exact data - never add medicines that weren't found.
- If no medicines are found for a query, clearly state that no matching medicines were found in our database.
- You may provide general disease/health information, but for medicine recommendations, ONLY suggest medicines from our database.

COMMUNICATION STYLE:
- Professional and friendly
- Clear and easy to understand
- Calm and non-alarming
- Patient-focused and supportive

BOUNDARIES:
- Do NOT provide emergency medical instructions beyond "seek immediate help".
- Do NOT prescribe dosages beyond general usage information.
- Encourage users to consult a doctor when needed.

If user describes severe symptoms (chest pain, difficulty breathing, severe bleeding, stroke symptoms, suicidal thoughts):
→ Immediately tell them to seek an ER or call emergency services (1122 in Pakistan).

You work for Red Dot Pharmacy in Islamabad, Pakistan. Suggest they can book a consultation or visit the pharmacy for proper medical advice.

Keep responses clear and helpful (3-5 sentences). When medicines are found in the database, include their details in your response."""

MEDICAL_SYSTEM_PROMPT_URDU = MEDICAL_SYSTEM_PROMPT + """

IMPORTANT: You MUST respond in Urdu language using Urdu script (not Roman Urdu).
Use respectful language appropriate for Pakistani culture.
Keep medicine names in Urdu where possible, unless the user uses English names."""

RED_FLAGS_EN = [
    r"chest pain",
    r"heart attack",
    r"stroke",
    r"seizure",
    r"unconscious",
    r"severe bleeding",
    r"difficulty breathing",
    r"can'?t breathe",
    r"suicidal",
    r"suicide",
    r"kill myself",
    r"want to die",
    r"overdose",
    r"poisoning",
    r"severe pain",
    r"blood in stool",
    r"blood in urine",
    r"fainting",
    r"paralysis",
    r"severe infection",
    r"high fever.*days",
    r"allergic reaction",
    r"anaphylaxis",
]

RED_FLAGS_UR = [
    r"سینے میں درد",
    r"سانس.*میں دقت",
    r"سانس.*نہیں آ رہا",
    r"بیہوش",
    r"خون.*بہت زیادہ",
    r"دل کا دورہ",
    r"فالج",
    r"خودکشی",
    r"مرنا چاہتا",
    r"شدید درد",
    r"تیز بخار",
    r"الرجی",
    r"زہر",
]

RED_FLAGS = RED_FLAGS_EN + RED_FLAGS_UR

DISCLAIMER_EN = (
    "⚠️ This information is for educational purposes only and is not a medical diagnosis. "
    "Please consult a qualified doctor or healthcare professional for proper evaluation, diagnosis, and treatment. "
    "Red Dot Pharmacy - Your trusted healthcare partner."
)

DISCLAIMER_UR = (
    "⚠️ یہ معلومات صرف تعلیمی مقاصد کے لیے ہیں اور طبی تشخیص نہیں ہے۔ "
    "مناسب جانچ، تشخیص اور علاج کے لیے براہ کرم کسی مستند ڈاکٹر یا صحت کے پیشہ ور سے مشورہ کریں۔ "
    "Red Dot Pharmacy - آپ کا قابل اعتماد صحت کا ساتھی۔"
)

UNSAFE_PATTERNS = [
    r"give me.*prescription",
    r"prescribe.*for me",
    r"what.*dose.*should",
    r"how much.*should.*take",
    r"diagnose me",
    r"what disease.*do i have",
    r"tell me.*exactly.*treatment",
    r"نسخہ.*دیں",
    r"دوا.*کتنی.*لوں",
    r"تشخیص.*کریں",
]


def detect_language(text):
    """Auto-detect if text is primarily Urdu or English"""
    urdu_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    total_chars = len(text.replace(" ", ""))
    
    if total_chars == 0:
        return "en"
    
    urdu_ratio = urdu_chars / total_chars
    return "ur" if urdu_ratio > 0.3 else "en"


def needs_escalation(text):
    """Check if message contains medical red flags requiring immediate attention"""
    text_lower = text.lower()
    return any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in RED_FLAGS)


def is_unsafe_request(text):
    """Check if user is asking for diagnosis/prescription (which we can't provide)"""
    text_lower = text.lower()
    return any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in UNSAFE_PATTERNS)


def get_emergency_response(lang):
    """Get emergency response for red flag situations"""
    if lang == "ur":
        return (
            "🚨 آپ کی علامات سنگین ہو سکتی ہیں۔ براہ کرم فوراً:\n\n"
            "• 1122 پر کال کریں (ایمرجنسی)\n"
            "• قریبی ہسپتال جائیں\n"
            "• یا Red Dot Pharmacy میں آئیں تاکہ ہمارے ڈاکٹر سے مشورہ کر سکیں\n\n"
            f"{DISCLAIMER_UR}"
        )
    else:
        return (
            "🚨 Your symptoms may be serious. Please immediately:\n\n"
            "• Call 1122 (Emergency Services)\n"
            "• Visit the nearest hospital\n"
            "• Or come to Red Dot Pharmacy to consult with our doctors\n\n"
            f"{DISCLAIMER_EN}"
        )


def get_guardrail_response(lang):
    """Response when user asks for diagnosis/prescription"""
    if lang == "ur":
        return (
            "معذرت، میں تشخیص یا نسخہ نہیں دے سکتا کیونکہ یہ صرف ڈاکٹر کا کام ہے۔\n\n"
            "میں آپ کی مدد کر سکتا ہوں:\n"
            "• عمومی صحت کی معلومات\n"
            "• ابتدائی طبی امداد کی رہنمائی\n"
            "• علامات کا خلاصہ (بغیر تشخیص کے)\n\n"
            "براہ کرم Red Dot Pharmacy میں ڈاکٹر سے ملاقات کریں یا آن لائن مشاورت بک کریں۔\n\n"
            f"{DISCLAIMER_UR}"
        )
    else:
        return (
            "I'm sorry, I cannot provide a diagnosis or prescription as that's only a doctor's role.\n\n"
            "I can help you with:\n"
            "• General health information\n"
            "• First-aid guidance\n"
            "• Symptom summaries (without diagnosing)\n\n"
            "Please visit Red Dot Pharmacy to consult with a doctor or book an online consultation.\n\n"
            f"{DISCLAIMER_EN}"
        )


def generate_response(text, prefer_urdu=None, session_id=None, lang="auto"):
    """
    Generate chatbot response with medical guardrails and RAG-based medicine retrieval
    
    Args:
        text: User message
        prefer_urdu: Deprecated - use lang instead
        session_id: Session identifier for logging
        lang: Language preference ("auto", "en", "ur")
    
    Returns: dict with message, flagged, needs_doctor, language, timestamp, medicines
    """
    if lang == "auto":
        detected_lang = detect_language(text)
    elif lang in ["ur", "urdu"]:
        detected_lang = "ur"
    else:
        detected_lang = "en"
    
    if prefer_urdu is not None:
        detected_lang = "ur" if prefer_urdu else "en"
    
    timestamp = datetime.now().isoformat()
    
    retrieved_medicines = []
    medicine_context = ""
    retrieval_result = None
    
    try:
        from services.smart_rag_orchestrator import smart_retrieve, get_orchestrator
        from services.medicine_rag import format_medicine_response
        
        retrieval_result = smart_retrieve(text, detected_lang)
        retrieved_medicines = retrieval_result.get('medications', [])
        
        if retrieved_medicines or retrieval_result.get('wiki_context'):
            orchestrator = get_orchestrator()
            medicine_context = orchestrator.build_ai_context(retrieval_result)
            logging.info(f"Smart RAG: Retrieved {len(retrieved_medicines)} medicines, context: {retrieval_result.get('context_type')}")
    except Exception as rag_error:
        logging.warning(f"Smart RAG retrieval failed (non-blocking): {rag_error}")
        try:
            from services.medicine_rag import find_medicines_in_text, build_medicine_context, format_medicine_response
            retrieved_medicines = find_medicines_in_text(text)
            if retrieved_medicines:
                medicine_context = build_medicine_context(retrieved_medicines)
        except:
            pass
    
    if needs_escalation(text):
        response_msg = get_emergency_response(detected_lang)
        return {
            'message': response_msg,
            'flagged': True,
            'needs_doctor': True,
            'suggested_medicines': [],
            'medicines': format_medicine_response(retrieved_medicines, detected_lang) if retrieved_medicines else [],
            'language': detected_lang,
            'timestamp': timestamp,
            'session_id': session_id or str(uuid.uuid4())
        }
    
    if is_unsafe_request(text):
        response_msg = get_guardrail_response(detected_lang)
        return {
            'message': response_msg,
            'flagged': False,
            'needs_doctor': True,
            'suggested_medicines': [],
            'medicines': format_medicine_response(retrieved_medicines, detected_lang) if retrieved_medicines else [],
            'language': detected_lang,
            'timestamp': timestamp,
            'session_id': session_id or str(uuid.uuid4())
        }
    
    if gemini_model:
        try:
            if detected_lang == "ur":
                system_prompt = MEDICAL_SYSTEM_PROMPT_URDU
            else:
                system_prompt = MEDICAL_SYSTEM_PROMPT
            
            if medicine_context:
                system_prompt += f"\n\n{medicine_context}"
            
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
            
            try:
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content.parts:
                        ai_message = "".join(part.text for part in candidate.content.parts if hasattr(part, 'text'))
                        ai_message = ai_message.strip()
                    
                    if hasattr(candidate, 'finish_reason'):
                        finish_reason = candidate.finish_reason
                        if finish_reason == 2:
                            logging.warning("Response blocked by safety filters, using fallback")
                            ai_message = ""
                        elif finish_reason == 3:
                            logging.warning("Response recitation blocked, using fallback")
                            ai_message = ""
                
                if not ai_message and hasattr(response, 'text') and response.text:
                    ai_message = response.text.strip()
                    
            except Exception as parse_error:
                logging.error(f"Error parsing Gemini response: {parse_error}")
                ai_message = ""
            
            if not ai_message:
                ai_message = get_offline_response(detected_lang)
            
            if DISCLAIMER_EN not in ai_message and DISCLAIMER_UR not in ai_message:
                disclaimer = DISCLAIMER_UR if detected_lang == "ur" else DISCLAIMER_EN
                ai_message = f"{ai_message}\n\n{disclaimer}"
            
            formatted_medicines = []
            try:
                from services.medicine_rag import format_medicine_response
                formatted_medicines = format_medicine_response(retrieved_medicines, detected_lang) if retrieved_medicines else []
            except:
                pass
            
            return {
                'message': ai_message,
                'flagged': False,
                'needs_doctor': False,
                'suggested_medicines': [],
                'medicines': formatted_medicines,
                'language': detected_lang,
                'timestamp': timestamp,
                'session_id': session_id or str(uuid.uuid4())
            }
            
        except Exception as e:
            logging.error(f"Gemini API error: {e}")
    
    formatted_medicines = []
    try:
        from services.medicine_rag import format_medicine_response
        formatted_medicines = format_medicine_response(retrieved_medicines, detected_lang) if retrieved_medicines else []
    except:
        pass
    
    return {
        'message': get_offline_response(detected_lang),
        'flagged': False,
        'needs_doctor': True,
        'suggested_medicines': [],
        'medicines': formatted_medicines,
        'language': detected_lang,
        'timestamp': timestamp,
        'session_id': session_id or str(uuid.uuid4())
    }


def get_offline_response(lang):
    """Fallback response when AI is unavailable"""
    if lang == "ur":
        return (
            "شکریہ آپ کے سوال کا! Red Dot Pharmacy میں ہمارے پاس تجربہ کار ڈاکٹرز موجود ہیں۔\n\n"
            "بہتر رہنمائی کے لیے:\n"
            "• اپنی علامات تفصیل سے بتائیں\n"
            "• آن لائن ملاقات بک کریں\n"
            "• یا ہمارے فارمیسی آئیں\n\n"
            f"{DISCLAIMER_UR}"
        )
    else:
        return (
            "Thank you for your question! Red Dot Pharmacy has experienced doctors available.\n\n"
            "For better guidance:\n"
            "• Describe your symptoms in detail\n"
            "• Book an online consultation\n"
            "• Or visit our pharmacy\n\n"
            f"{DISCLAIMER_EN}"
        )


def log_chat_interaction(session_id, user_message, bot_response, user_id=None, 
                         flagged=False, language="en"):
    """Log chat interaction for analysis and improvement"""
    try:
        from app import db
        from models import ChatLog
        
        chat_log = ChatLog()
        chat_log.user_id = user_id
        chat_log.session_id = session_id
        chat_log.message = user_message
        chat_log.response = bot_response
        chat_log.language = language
        chat_log.flagged = flagged
        chat_log.created_at = datetime.utcnow()
        
        db.session.add(chat_log)
        db.session.commit()
        
        logging.info(f"Chat logged - Session: {session_id}, Lang: {language}, Flagged: {flagged}")
        
    except Exception as e:
        logging.error(f"Failed to log chat interaction: {e}")


def get_chat_history(session_id, limit=50):
    """Retrieve chat history for a session"""
    try:
        from models import ChatLog
        
        logs = ChatLog.query.filter_by(session_id=session_id)\
                            .order_by(ChatLog.created_at.asc())\
                            .limit(limit).all()
        
        history = []
        for log in logs:
            history.append({
                'user_message': log.message,
                'bot_response': log.response,
                'language': log.language,
                'flagged': log.flagged,
                'timestamp': log.created_at.isoformat() if log.created_at else None
            })
        
        return history
        
    except Exception as e:
        logging.error(f"Failed to get chat history: {e}")
        return []
