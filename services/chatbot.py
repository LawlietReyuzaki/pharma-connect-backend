"""
Medical Consultant Chatbot Service — Red Dot Pharmacy
Gemini-powered medical assistant with pharmacy DB integration.
"""

import os
import re
import logging
import uuid
from datetime import datetime

# ─── Gemini init ────────────────────────────────────────────────────────────
gemini_model = None
genai = None
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))

if GEMINI_API_KEY:
    try:
        import google.generativeai as genai_module
        genai = genai_module
        genai.configure(api_key=GEMINI_API_KEY)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT",        "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH",       "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        gemini_model = genai.GenerativeModel(GEMINI_MODEL, safety_settings=safety_settings)
        logging.info(f"Gemini ready: {GEMINI_MODEL}")
    except Exception as e:
        logging.error(f"Gemini init failed: {e}")
else:
    logging.warning("No GEMINI_API_KEY — chatbot offline")

# ─── System prompts ──────────────────────────────────────────────────────────
MEDICAL_CONSULTANT_PROMPT_EN = """You are a knowledgeable and caring Medical Consultant AI working for Red Dot Pharmacy in Islamabad, Pakistan.

YOUR ROLE:
You act like a real pharmacist + medical advisor. When a user describes symptoms or asks about a condition, you:
1. Briefly explain the condition in simple, clear language
2. Recommend suitable medicines FROM the pharmacy database provided to you
3. Give practical advice (rest, hydration, diet, when to see a doctor)
4. Be warm, direct, and helpful — not robotic

MEDICINE RULES (CRITICAL):
- ONLY recommend medicines that appear in the [PHARMACY DATABASE] section below
- If medicines are provided, always mention their name and price (e.g. "Panadol Extra — PKR 45")
- If NO medicines are in the database context, say so clearly and suggest visiting the pharmacy
- NEVER invent, guess, or hallucinate medicine names or prices
- If user asks about a specific medicine not in the database, say it's not in our current stock

RESPONSE STYLE:
- Conversational and human — not a bullet-point report
- Keep it concise: 3-6 sentences is ideal
- Lead with the most useful information first
- For serious symptoms: mention seeing a doctor but still help with what you know
- For simple queries (greetings, general questions): respond naturally without forcing medical info

BOUNDARIES:
- You can suggest POSSIBLE conditions based on symptoms, but NEVER give a definitive diagnosis
- Do NOT prescribe exact dosages — give general guidance only
- For emergencies (chest pain, stroke, severe bleeding, can't breathe): tell them to call 1122 immediately

LOCATION: Red Dot Pharmacy, Shop #69 Ground Floor Silver City Plaza, G11 Markaz, Islamabad
EMERGENCY: 1122 | Consultation booking: available on our website"""

MEDICAL_CONSULTANT_PROMPT_UR = """آپ Red Dot Pharmacy اسلام آباد کے لیے ایک ماہر اور مہربان طبی مشیر AI ہیں۔

آپ کا کردار:
آپ ایک اصل فارماسسٹ اور طبی مشیر کی طرح کام کریں۔ جب صارف علامات بیان کرے یا کسی بیماری کے بارے میں پوچھے، آپ:
1. بیماری کو آسان الفاظ میں مختصراً بیان کریں
2. فارمیسی ڈیٹا بیس سے مناسب دوائیں تجویز کریں
3. عملی مشورہ دیں (آرام، پانی، خوراک، ڈاکٹر سے کب ملیں)
4. گرم، واضح اور مددگار انداز میں بات کریں

دوائی کے اصول (ضروری):
- صرف وہی دوائیں تجویز کریں جو نیچے [فارمیسی ڈیٹا بیس] میں موجود ہوں
- اگر دوائیں موجود ہیں تو نام اور قیمت ضرور بتائیں
- اگر ڈیٹا بیس میں دوائی نہیں تو واضح کہیں اور فارمیسی آنے کی تجویز دیں
- کبھی بھی دوائی کا نام یا قیمت خود سے نہ بنائیں

جواب کا انداز:
- اردو میں جواب دیں (رومن اردو نہیں، اردو رسم الخط)
- مختصر اور کام کی بات: 3-6 جملے کافی ہیں
- سنجیدہ علامات میں ڈاکٹر سے ملنے کا مشورہ دیں

حدود:
- ممکنہ بیماری بتا سکتے ہیں لیکن حتمی تشخیص نہیں دے سکتے
- ایمرجنسی میں (سینے میں درد، فالج، شدید خون): فوری 1122 کال کرنے کو کہیں

مقام: Red Dot Pharmacy، شاپ 69، سلور سٹی پلازہ، G11 مرکز، اسلام آباد"""

# ─── Disclaimers ─────────────────────────────────────────────────────────────
DISCLAIMER_EN = (
    "\n\n⚠️ *This is general health information, not a medical diagnosis. "
    "For proper evaluation and treatment, please consult a qualified doctor. "
    "Red Dot Pharmacy — your trusted healthcare partner.*"
)
DISCLAIMER_UR = (
    "\n\n⚠️ *یہ عمومی صحت کی معلومات ہیں، طبی تشخیص نہیں۔ "
    "مناسب علاج کے لیے کسی مستند ڈاکٹر سے مشورہ کریں۔ "
    "Red Dot Pharmacy — آپ کا قابل اعتماد صحت کا ساتھی۔*"
)

# ─── Safety patterns ──────────────────────────────────────────────────────────
_EMERGENCY_PATTERNS = [
    r"chest pain", r"heart attack", r"stroke", r"seizure", r"unconscious",
    r"severe bleeding", r"can'?t breathe", r"difficulty breathing",
    r"suicidal", r"suicide", r"kill myself", r"want to die",
    r"overdose", r"poisoning", r"anaphylaxis", r"paralysis",
    r"سینے میں درد", r"دل کا دورہ", r"فالج", r"خودکشی",
    r"سانس نہیں", r"مرنا چاہتا", r"زہر",
]

# ─── Language detection ───────────────────────────────────────────────────────
def detect_language(text: str) -> str:
    urdu_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    total = len(text.replace(" ", ""))
    if total == 0:
        return "en"
    return "ur" if (urdu_chars / total) > 0.3 else "en"


def needs_escalation(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t, re.IGNORECASE) for p in _EMERGENCY_PATTERNS)


def get_emergency_response(lang: str) -> str:
    if lang == "ur":
        return (
            "🚨 **آپ کی علامات سنگین ہو سکتی ہیں۔ فوری اقدام کریں:**\n\n"
            "• **1122** پر ابھی کال کریں (ایمرجنسی سروس)\n"
            "• قریبی ہسپتال جائیں\n"
            "• خود گاڑی نہ چلائیں، کسی کو ساتھ لیں\n\n"
            "Red Dot Pharmacy میں ڈاکٹر سے آن لائن مشاورت بھی بک کر سکتے ہیں۔"
        )
    return (
        "🚨 **Your symptoms may be serious. Take immediate action:**\n\n"
        "• Call **1122** right now (Emergency Services)\n"
        "• Go to the nearest hospital\n"
        "• Do not drive yourself — take someone with you\n\n"
        "You can also book an online doctor consultation at Red Dot Pharmacy."
    )


# ─── Medicine lookup ──────────────────────────────────────────────────────────
_PURE_GREETINGS = re.compile(
    r"^(hi|hello|hey|salam|assalam|how are you|good morning|good evening|"
    r"good afternoon|thanks|thank you|ok|okay|bye|goodbye|آداب|سلام|شکریہ)\W*$",
    re.IGNORECASE
)

def _should_search_medicines(text: str) -> bool:
    """
    Return True if the message likely needs a pharmacy DB search.
    Skip ONLY for pure greetings/small-talk. Search for everything else.
    """
    stripped = text.strip()
    # Skip pure greetings — no need to hit the DB
    if _PURE_GREETINGS.match(stripped):
        return False
    # For anything else (symptoms, medicine names, conditions, questions) → search
    return True


def _fetch_medicines_for_query(text: str) -> list:
    """
    Search the pharmacy DB for medicines relevant to the user's query.
    Returns a list of medicine dicts. Max 5 results.
    """
    try:
        from services.medicine_rag import search_medicines, search_medicines_for_condition

        stop = {
            "the","a","an","is","are","was","were","what","which","who","how",
            "when","where","why","can","could","should","would","do","does",
            "did","have","has","had","for","to","of","in","on","at","by",
            "with","about","this","that","these","those","it","me","my","i",
            "you","your","and","or","but","not","help","tell","give","need",
            "want","please","hello","hi","hey","thanks","thank","also","some",
        }

        # Extract meaningful words from the user's message
        raw_words = re.findall(r'\b[a-zA-Z\u0600-\u06FF]{3,}\b', text)
        keywords = list(dict.fromkeys(
            w for w in raw_words if w.lower() not in stop
        ))[:6]

        seen_ids = set()
        results = []

        # 1. Search by keyword (medicine name / condition name)
        for kw in keywords:
            for med in search_medicines(kw, limit=3):
                if med["id"] not in seen_ids:
                    seen_ids.add(med["id"])
                    results.append(med)
            if len(results) >= 5:
                break

        # 2. If still under 3, try condition/description search with top 2 keywords
        if len(results) < 3:
            for kw in keywords[:2]:
                for med in search_medicines_for_condition(kw, limit=3):
                    if med["id"] not in seen_ids:
                        seen_ids.add(med["id"])
                        results.append(med)
                if len(results) >= 5:
                    break

        return results[:5]

    except Exception as e:
        logging.warning(f"Medicine DB search failed: {e}")
        return []


def _build_medicine_context(medicines: list) -> str:
    """Format medicines from DB into a clean prompt context block."""
    if not medicines:
        return ""
    lines = ["[PHARMACY DATABASE — use ONLY these medicines in your response]"]
    for m in medicines:
        lines.append(f"\n• {m['name']} — PKR {m['price']}")
        if m.get("chemical"):
            lines.append(f"  Active ingredient: {m['chemical']}")
        if m.get("category"):
            lines.append(f"  Category: {m['category']}")
        if m.get("description"):
            lines.append(f"  Use: {m['description'][:120]}")
        lines.append(f"  Stock: {'Available' if m.get('status') == 'in_stock' else 'Out of stock'}")
    lines.append("\n[END DATABASE — do NOT suggest medicines outside this list]")
    return "\n".join(lines)


# ─── Main response function ───────────────────────────────────────────────────
def generate_response(text: str, prefer_urdu=None, session_id=None, lang="auto", pharmacy_id=None, mode="patient") -> dict:
    """
    Generate a medical consultant response using Gemini + pharmacy DB.

    Flow:
      1. Detect language
      2. Emergency check → immediate response (no Gemini call)
      3. Search pharmacy DB if query is medical
      4. Build prompt: consultant system prompt + DB medicines + user message
      5. Call Gemini → clean response
      6. Return response dict
    """
    # 1. Language
    if lang in ("ur", "urdu"):
        detected_lang = "ur"
    elif lang == "auto":
        detected_lang = detect_language(text)
    else:
        detected_lang = "en"
    if prefer_urdu is not None:
        detected_lang = "ur" if prefer_urdu else "en"

    timestamp = datetime.now().isoformat()
    sid = session_id or str(uuid.uuid4())

    # 2. Emergency check — skip Gemini, respond immediately
    if needs_escalation(text):
        return {
            "message": get_emergency_response(detected_lang),
            "flagged": True,
            "needs_doctor": True,
            "medicines": [],
            "suggested_medicines": [],
            "language": detected_lang,
            "timestamp": timestamp,
            "session_id": sid,
        }

    # 3. Resolve pharmacy name (used by both new and legacy paths)
    pharmacy_name = "Red Dot Pharmacy"
    if pharmacy_id:
        try:
            from models import Pharmacy
            pharmacy = Pharmacy.query.get(pharmacy_id)
            if pharmacy:
                pharmacy_name = pharmacy.name
        except Exception:
            pass

    # 4. PRIMARY PATH: Catalog Sub-Agent (embeddings + structured JSON)
    use_legacy = os.getenv("USE_LEGACY_MEDICINE_SEARCH", "").strip() == "1"
    request_id = "-"
    try:
        from flask import g
        request_id = getattr(g, "request_id", "-")
    except Exception:
        pass

    if not use_legacy:
        try:
            from services.catalog_agent import get_agent, CatalogAgentUnavailable
            agent = get_agent()
            if agent.is_ready:
                result = agent.recommend(
                    user_message=text,
                    lang=detected_lang,
                    mode=mode,
                    pharmacy_name=pharmacy_name,
                    request_id=request_id,
                )
                return {
                    "message": result["message"],
                    "flagged": False,
                    "needs_doctor": False,
                    "medicines": result["medicines"],
                    "suggested_medicines": [],
                    "language": detected_lang,
                    "timestamp": timestamp,
                    "session_id": sid,
                }
        except CatalogAgentUnavailable as e:
            logging.warning(f"[req={request_id}] CatalogAgent unavailable, falling back to legacy: {e}")
        except Exception as e:
            logging.exception(f"[req={request_id}] CatalogAgent error, falling back to legacy: {e}")

    # 5. LEGACY FALLBACK PATH (kept for resilience — keyword search + free-text Gemini)
    medicines = []
    medicine_context = ""
    if _should_search_medicines(text):
        medicines = _fetch_medicines_for_query(text)
        if medicines:
            medicine_context = _build_medicine_context(medicines)

    formatted_medicines = []
    try:
        from services.medicine_rag import format_medicine_response
        formatted_medicines = format_medicine_response(medicines, detected_lang) if medicines else []
    except Exception:
        pass

    if not gemini_model:
        return {
            "message": _offline_response(detected_lang),
            "flagged": False,
            "needs_doctor": True,
            "medicines": formatted_medicines,
            "suggested_medicines": [],
            "language": detected_lang,
            "timestamp": timestamp,
            "session_id": sid,
        }

    if mode == "pharmacist":
        from services.pharmacist_knowledge import (
            PHARMACIST_SYSTEM_PROMPT_EN, PHARMACIST_SYSTEM_PROMPT_UR
        )
        system_prompt = (
            PHARMACIST_SYSTEM_PROMPT_UR if detected_lang == "ur"
            else PHARMACIST_SYSTEM_PROMPT_EN
        )
    else:
        system_prompt = (
            MEDICAL_CONSULTANT_PROMPT_UR if detected_lang == "ur"
            else MEDICAL_CONSULTANT_PROMPT_EN
        )

    if pharmacy_name != "Red Dot Pharmacy":
        system_prompt = system_prompt.replace("Red Dot Pharmacy", pharmacy_name)

    if medicine_context:
        system_prompt = f"{system_prompt}\n\n{medicine_context}"

    full_prompt = f"{system_prompt}\n\nUser: {text}\n\nAssistant:"

    gen_config = {
        "temperature": GEMINI_TEMPERATURE,
        "max_output_tokens": 800,
    }

    ai_message = ""
    try:
        response = gemini_model.generate_content(full_prompt, generation_config=gen_config)
        if hasattr(response, "text") and response.text:
            ai_message = response.text.strip()
        elif response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "content") and candidate.content.parts:
                ai_message = "".join(
                    p.text for p in candidate.content.parts if hasattr(p, "text")
                ).strip()
    except Exception as e:
        logging.error(f"Gemini call failed: {e}")

    if not ai_message:
        ai_message = _offline_response(detected_lang)

    return {
        "message": ai_message,
        "flagged": False,
        "needs_doctor": False,
        "medicines": formatted_medicines,
        "suggested_medicines": [],
        "language": detected_lang,
        "timestamp": timestamp,
        "session_id": sid,
    }


# ─── Offline fallback ─────────────────────────────────────────────────────────
def _offline_response(lang: str) -> str:
    if lang == "ur":
        return (
            "معذرت، ابھی AI سروس دستیاب نہیں ہے۔\n\n"
            "براہ کرم:\n"
            "• تھوڑی دیر بعد دوبارہ کوشش کریں\n"
            "• یا Red Dot Pharmacy پر کال کریں: 051-5111222\n"
            "• یا آن لائن ڈاکٹر مشاورت بک کریں"
        )
    return (
        "Sorry, the AI service is temporarily unavailable.\n\n"
        "Please:\n"
        "• Try again in a moment\n"
        "• Call Red Dot Pharmacy: 051-5111222\n"
        "• Or book an online doctor consultation"
    )


# ─── Logging ──────────────────────────────────────────────────────────────────
def log_chat_interaction(session_id, user_message, bot_response,
                         user_id=None, flagged=False, language="en",
                         pharmacy_id=None):
    try:
        from app import db
        from models import ChatLog
        log = ChatLog()
        log.user_id = user_id
        log.session_id = session_id
        log.message = user_message
        log.response = bot_response
        log.language = language
        log.flagged = flagged
        log.pharmacy_id = pharmacy_id
        log.created_at = datetime.utcnow()
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        logging.error(f"Chat log failed: {e}")


def get_chat_history(session_id, limit=50):
    try:
        from models import ChatLog
        logs = (ChatLog.query
                .filter_by(session_id=session_id)
                .order_by(ChatLog.created_at.asc())
                .limit(limit).all())
        return [
            {
                "user_message": l.message,
                "bot_response": l.response,
                "language": l.language,
                "flagged": l.flagged,
                "timestamp": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ]
    except Exception as e:
        logging.error(f"Chat history failed: {e}")
        return []
