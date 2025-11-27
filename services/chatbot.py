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
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))

if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel(GEMINI_MODEL)
        logging.info(f"Gemini model initialized: {GEMINI_MODEL}")
    except Exception as e:
        logging.error(f"Failed to initialize Gemini client: {e}")
else:
    logging.warning("GOOGLE_API_KEY/GEMINI_API_KEY not set - chatbot will use offline mode")

MEDICAL_SYSTEM_PROMPT = """You are a Medical Support Assistant designed ONLY to provide:
- General medical information
- First-aid guidance
- Self-care tips
- Condition awareness
- Red-flag warnings
- Medication education (non-prescriptive)
- Help navigating patients to the right doctor or specialist
- Summaries of user symptoms (without diagnosing)

You MUST NOT:
- Diagnose any disease
- Prescribe any medication or dosage
- Replace a doctor
- Provide harmful, inaccurate or unsafe clinical advice
- Tell the user what exact treatment to take
- Provide emergency instructions beyond 'seek urgent medical help'

If user describes severe pain, chest pain, difficulty breathing, bleeding, fainting, stroke symptoms, severe infection, suicidal thoughts:
→ Immediately tell them to seek an ER or call emergency services (1122 in Pakistan).

TONE:
- Polite
- Supportive
- Never authoritative
- Provide helpful but safe general guidance only

If the patient asks about medicines:
- Provide only general info about what the medicine is commonly used for
- Never give dosage, frequency, or prescription advice
- Always remind them to consult a qualified doctor for medical decisions

If the user asks for diagnosis:
- Decline gently and offer general possibilities to consider
- Encourage them to visit a doctor for confirmation

If the user gives symptoms:
- Provide possible causes at a high level (non-diagnostic)
- Highlight red flags
- Suggest seeing a doctor if necessary

Always include at the end:
"This information is for general awareness only and not a medical diagnosis."

You work for Red Dot Pharmacy in Islamabad, Pakistan. Suggest they can book a consultation or visit the pharmacy for proper medical advice.

Keep responses concise (2-4 sentences) and easy to understand."""

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
    "⚠️ Important: This information is for general awareness only and not a medical diagnosis. "
    "In emergency situations, immediately call 1122 or visit the nearest hospital. "
    "Red Dot Pharmacy cares for your health."
)

DISCLAIMER_UR = (
    "⚠️ اہم: یہ معلومات صرف عمومی آگاہی کے لیے ہیں اور طبی تشخیص نہیں ہے۔ "
    "ہنگامی صورتحال میں فوراً 1122 پر کال کریں یا قریبی ہسپتال جائیں۔ "
    "Red Dot Pharmacy آپ کی صحت کی دیکھ بھال کرتا ہے۔"
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
    Generate chatbot response with medical guardrails
    
    Args:
        text: User message
        prefer_urdu: Deprecated - use lang instead
        session_id: Session identifier for logging
        lang: Language preference ("auto", "en", "ur")
    
    Returns: dict with message, flagged, needs_doctor, language, timestamp
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
    
    if needs_escalation(text):
        response_msg = get_emergency_response(detected_lang)
        return {
            'message': response_msg,
            'flagged': True,
            'needs_doctor': True,
            'suggested_medicines': [],
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
            
            full_prompt = f"{system_prompt}\n\nUser: {text}\n\nAssistant:"
            
            generation_config = {
                "temperature": GEMINI_TEMPERATURE,
                "max_output_tokens": 500,
            }
            
            response = gemini_model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            ai_message = response.text.strip() if response.text else ""
            
            if not ai_message:
                ai_message = get_offline_response(detected_lang)
            
            if DISCLAIMER_EN not in ai_message and DISCLAIMER_UR not in ai_message:
                disclaimer = DISCLAIMER_UR if detected_lang == "ur" else DISCLAIMER_EN
                ai_message = f"{ai_message}\n\n{disclaimer}"
            
            return {
                'message': ai_message,
                'flagged': False,
                'needs_doctor': False,
                'suggested_medicines': [],
                'language': detected_lang,
                'timestamp': timestamp,
                'session_id': session_id or str(uuid.uuid4())
            }
            
        except Exception as e:
            logging.error(f"Gemini API error: {e}")
    
    return {
        'message': get_offline_response(detected_lang),
        'flagged': False,
        'needs_doctor': True,
        'suggested_medicines': [],
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
