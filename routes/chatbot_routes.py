from flask import Blueprint, request, jsonify, send_file
from services.chatbot import generate_response, log_chat_interaction, detect_language, get_chat_history as get_history
from services.wikipedia_utils import collect_wikipedia_resources, build_wiki_context
import speech_recognition as sr
import uuid
import logging
import os
import re
import time
from datetime import datetime
from gtts import gTTS
import io
from werkzeug.utils import secure_filename

bp = Blueprint("chatbot", __name__)

# Only fetch Wikipedia for the display panel when the query is about a
# specific disease or condition (not for greetings, medicine prices, etc.)
_DISEASE_TERMS = {
    "diabetes","hypertension","asthma","pneumonia","malaria","typhoid","dengue",
    "hepatitis","tuberculosis","cancer","arthritis","migraine","epilepsy","covid",
    "influenza","bronchitis","sinusitis","gastritis","eczema","psoriasis",
    "depression","anxiety","parkinson","alzheimer","cholesterol","thyroid",
}

def _needs_wiki_panel(text: str) -> bool:
    """Return True only for specific disease/condition queries — for wiki panel display only."""
    t = text.lower()
    return any(term in t for term in _DISEASE_TERMS)


@bp.route("/medical-chat", methods=["POST"])
def medical_chat():
    """
    POST /medical-chat - Medical assistant chatbot with safety guardrails + Wikipedia integration
    
    Request body:
    {
        "message": "user text here",
        "lang": "auto"   // auto-detect Urdu/English, or "en"/"ur"
    }
    
    Response:
    {
        "success": true,
        "message": "AI response",
        "language": "detected language",
        "flagged": false,
        "needs_doctor": false,
        "timestamp": "ISO timestamp",
        "session_id": "uuid",
        "disclaimer": "safety notice",
        "wiki": { ... Wikipedia data with images and attribution ... }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
        
        message = data.get("message", "").strip()
        if not message:
            return jsonify({
                "success": False,
                "error": "Message is required"
            }), 400

        # Support both "lang" and "language" parameters
        lang = data.get("lang") or data.get("language") or "auto"
        session_id = data.get("session_id", str(uuid.uuid4()))
        user_id = data.get("user_id")
        pharmacy_id = data.get("pharmacy_id")
        include_wiki = data.get("include_wiki", True)

        detected_lang = detect_language(message) if lang == "auto" else lang

        # Step 1: Get AI response — pure Gemini + DB medicines, no Wikipedia involved
        response_data = generate_response(
            text=message,
            session_id=session_id,
            lang=lang,
            pharmacy_id=pharmacy_id
        )

        # Step 2: Wikipedia display panel — only for specific disease queries,
        # completely separate from AI response, display-only in the frontend
        wiki_data = None
        if include_wiki and _needs_wiki_panel(message):
            try:
                words = re.findall(r'\b[a-zA-Z]{4,}\b', message)
                search_query = " ".join(words[:3]) if words else message[:40]
                wiki_data = collect_wikipedia_resources(search_query)
                if not (wiki_data and wiki_data.get("success")):
                    wiki_data = None
            except Exception as wiki_error:
                logging.warning(f"Wikipedia panel fetch failed: {wiki_error}")
                wiki_data = None
        
        log_chat_interaction(
            session_id=session_id,
            user_message=message,
            bot_response=response_data['message'],
            user_id=user_id,
            flagged=response_data.get('flagged', False),
            language=response_data.get('language', detected_lang),
            pharmacy_id=pharmacy_id
        )

        disclaimer = (
            "This AI does not provide medical diagnosis. Consult a doctor for accurate guidance."
            if detected_lang == "en" else
            "یہ AI طبی تشخیص فراہم نہیں کرتا۔ درست رہنمائی کے لیے ڈاکٹر سے مشورہ کریں۔"
        )
        
        response_json = {
            "success": True,
            "message": response_data['message'],
            "language": response_data.get('language', detected_lang),
            "flagged": response_data.get('flagged', False),
            "needs_doctor": response_data.get('needs_doctor', False),
            "timestamp": response_data.get('timestamp', datetime.now().isoformat()),
            "session_id": session_id,
            "disclaimer": disclaimer
        }
        
        if response_data.get('medicines'):
            response_json["medicines"] = response_data['medicines']
        
        if wiki_data and wiki_data.get("success"):
            response_json["wiki"] = {
                "title": wiki_data.get("title"),
                "page_url": wiki_data.get("page_url"),
                "summary": wiki_data.get("summary", "")[:2500] if wiki_data.get("summary") else "",
                "images": wiki_data.get("images", [])[:4]
            }
        
        return jsonify(response_json)
        
    except Exception as e:
        logging.error(f"Medical chat error: {e}")
        return jsonify({
            "success": False,
            "error": "Sorry, I'm having trouble right now. Please try again later."
        }), 500

@bp.route("/pharmacist-consult", methods=["POST"])
def pharmacist_consult():
    """
    POST /api/chat/pharmacist-consult
    Pharmacist consultation mode — clinical reference for pharmacy staff.
    Uses the comprehensive pharmacist knowledge base system prompt.

    Body: { "message": "...", "lang": "auto"|"en"|"ur", "session_id": "..." }
    Response: same shape as /medical-chat
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        message = data.get("message", "").strip()
        if not message:
            return jsonify({"success": False, "error": "Message is required"}), 400

        lang = data.get("lang") or data.get("language") or "auto"
        session_id = data.get("session_id", str(uuid.uuid4()))
        user_id = data.get("user_id")
        pharmacy_id = data.get("pharmacy_id")

        detected_lang = detect_language(message) if lang == "auto" else lang

        response_data = generate_response(
            text=message,
            session_id=session_id,
            lang=lang,
            pharmacy_id=pharmacy_id,
            mode="pharmacist",
        )

        log_chat_interaction(
            session_id=session_id,
            user_message=message,
            bot_response=response_data["message"],
            user_id=user_id,
            flagged=response_data.get("flagged", False),
            language=response_data.get("language", detected_lang),
            pharmacy_id=pharmacy_id,
        )

        response_json = {
            "success": True,
            "message": response_data["message"],
            "language": response_data.get("language", detected_lang),
            "flagged": response_data.get("flagged", False),
            "needs_doctor": response_data.get("needs_doctor", False),
            "timestamp": response_data.get("timestamp", datetime.now().isoformat()),
            "session_id": session_id,
            "mode": "pharmacist",
        }

        if response_data.get("medicines"):
            response_json["medicines"] = response_data["medicines"]

        return jsonify(response_json)

    except Exception as e:
        logging.error(f"Pharmacist consult error: {e}")
        return jsonify({"success": False, "error": "Pharmacist consultation unavailable. Please try again."}), 500


@bp.route("/agent", methods=["POST"])
def agent():
    """
    POST /api/chat/agent — Orchestrator entry point (spec section 5.1).

    Single endpoint the frontend can call for every chat turn. The
    orchestrator classifies intent, dispatches to the correct sub-agent
    (Catalog / Clinical / Evidence / Substitution / Images), and returns
    a unified response.

    Body: { "message": "...", "lang": "auto"|"en"|"ur",
            "session_id": "...", "user_id": <int>, "pharmacy_id": <int>,
            "mode": "patient"|"pharmacist"   (optional override),
            "force_intent": "catalog"|"clinical"|"evidence"|"substitute"|"images"
                            (optional) }
    Reply: unified envelope; see services/orchestrator_agent.handle() docstring.
    """
    try:
        from services.chatbot import detect_language
        from services.orchestrator_agent import get_orchestrator, OrchestratorUnavailable

        try:
            from flask import g
            request_id = getattr(g, "request_id", "-")
        except Exception:
            request_id = "-"

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        message = (data.get("message") or "").strip()
        if not message:
            return jsonify({"success": False, "error": "'message' is required"}), 400

        lang = data.get("lang") or data.get("language") or "auto"
        session_id = data.get("session_id", str(uuid.uuid4()))
        user_id = data.get("user_id")
        pharmacy_id = data.get("pharmacy_id")
        mode = (data.get("mode") or "patient").lower()
        force_intent = data.get("force_intent")
        detected_lang = detect_language(message) if lang == "auto" else lang

        # Resolve pharmacy name + user role
        pharmacy_name = "Red Dot Pharmacy"
        if pharmacy_id:
            try:
                from models import Pharmacy
                ph = Pharmacy.query.get(pharmacy_id)
                if ph:
                    pharmacy_name = ph.name
            except Exception:
                pass

        user_role = "patient"
        try:
            from services.auth import get_current_user
            user = get_current_user()
            if user and getattr(user, "role", None):
                user_role = user.role
        except Exception:
            pass

        try:
            orch = get_orchestrator()
            if not orch.is_ready:
                raise OrchestratorUnavailable("orchestrator not ready")
            result = orch.handle(
                user_message=message,
                lang=detected_lang,
                mode=mode,
                user_role=user_role,
                pharmacy_name=pharmacy_name,
                pharmacy_id=pharmacy_id,
                request_id=request_id,
                force_intent=force_intent,
            )
        except OrchestratorUnavailable as e:
            logging.warning(f"[req={request_id}] Orchestrator unavailable, falling back to medical-chat: {e}")
            from services.chatbot import generate_response
            legacy = generate_response(
                text=message, lang=detected_lang, pharmacy_id=pharmacy_id,
                session_id=session_id, mode=mode,
            )
            result = {
                "intent": "catalog",
                "message": legacy.get("message"),
                "medicines": legacy.get("medicines", []),
                "needs_doctor": legacy.get("needs_doctor", False),
            }

        log_chat_interaction(
            session_id=session_id,
            user_message=message,
            bot_response=result.get("message", ""),
            user_id=user_id,
            flagged=bool(result.get("red_flag")),
            language=detected_lang,
            pharmacy_id=pharmacy_id,
        )

        return jsonify({
            "success": True,
            "session_id": session_id,
            "language": detected_lang,
            "intent": result.get("intent", "catalog"),
            "message": result.get("message", ""),
            "medicines": result.get("medicines", []),
            "sources": result.get("sources", []),
            "image_references": result.get("image_references", []),
            "needs_doctor": result.get("needs_doctor", False),
            "red_flag": result.get("red_flag", False),
            "cta": result.get("cta"),
            "requested": result.get("requested"),
            "exact_count": result.get("exact_count", 0),
            "class_count": result.get("class_count", 0),
        })

    except Exception as e:
        logging.exception(f"Orchestrator error: {e}")
        return jsonify({"success": False, "error": "Chat agent unavailable. Please try again."}), 500


@bp.route("/correct-transcript", methods=["POST"])
def correct_transcript():
    """
    POST /api/chat/correct-transcript — Phase 6 STT post-correction.

    Takes a raw speech-to-text transcript (English or Urdu) and returns a
    medical-vocabulary-corrected version. Intended to be called by the
    frontend between mic capture and chat submit, so drug names and
    clinical terms aren't garbled by a general-purpose recogniser.

    Body:  { "transcript": "panda doll for fever",
             "lang": "auto"|"en"|"ur" }
    Reply: { "success": true,
             "transcript": "<original>",
             "corrected": "Panadol for fever",
             "changes": [{"original": "panda doll", "corrected": "Panadol"}] }
    """
    try:
        from services.chatbot import detect_language
        from services.transcript_corrector import get_corrector, TranscriptCorrectorUnavailable

        try:
            from flask import g
            request_id = getattr(g, "request_id", "-")
        except Exception:
            request_id = "-"

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        transcript = (data.get("transcript") or data.get("text") or "").strip()
        if not transcript:
            return jsonify({"success": False, "error": "'transcript' is required"}), 400

        lang = data.get("lang") or data.get("language") or "auto"
        detected_lang = detect_language(transcript) if lang == "auto" else lang

        try:
            corrector = get_corrector()
            if not corrector.is_ready:
                raise TranscriptCorrectorUnavailable("corrector not ready")
            result = corrector.correct(transcript=transcript, lang=detected_lang, request_id=request_id)
        except TranscriptCorrectorUnavailable as e:
            logging.warning(f"[req={request_id}] TranscriptCorrector unavailable: {e}")
            # Soft-fail: return the original so the frontend can still submit something.
            return jsonify({
                "success": True,
                "transcript": transcript,
                "corrected": transcript,
                "changes": [],
                "language": detected_lang,
                "corrector_available": False,
            })

        return jsonify({
            "success": True,
            "transcript": transcript,
            "corrected": result["corrected"],
            "changes": result["changes"],
            "language": detected_lang,
            "corrector_available": True,
        })

    except Exception as e:
        logging.exception(f"Transcript correction error: {e}")
        return jsonify({"success": False, "error": "Transcript correction unavailable."}), 500


@bp.route("/images", methods=["POST"])
def images():
    """
    POST /api/chat/images — Phase 5 Image Retrieval Sub-Agent.

    Returns 2–4 reference page links from a credible medical-image allow-list
    (DermNet NZ, Radiopaedia, CDC PHIL, MSD Manuals, Mayo, NHS, AAO, etc.)
    for queries about visually-identifiable conditions.

    Body:  { "query": "rash that could be dengue or chicken pox",
             "lang": "auto"|"en"|"ur", "session_id": "..." }
    Reply: { "success": true, "message": "...",
             "image_references": [{condition, distinguishing_features,
                                   source_title, source_url, source_domain}],
             "session_id": "..." }
    """
    try:
        from services.chatbot import detect_language
        from services.image_agent import get_agent, ImageAgentUnavailable

        try:
            from flask import g
            request_id = getattr(g, "request_id", "-")
        except Exception:
            request_id = "-"

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        query = (data.get("query") or data.get("message") or "").strip()
        if not query:
            return jsonify({"success": False, "error": "'query' is required"}), 400

        lang = data.get("lang") or data.get("language") or "auto"
        session_id = data.get("session_id", str(uuid.uuid4()))
        user_id = data.get("user_id")
        detected_lang = detect_language(query) if lang == "auto" else lang

        try:
            agent = get_agent()
            if not agent.is_ready:
                raise ImageAgentUnavailable("agent not ready")
            result = agent.find_images(query=query, lang=detected_lang, request_id=request_id)
        except ImageAgentUnavailable as e:
            logging.warning(f"[req={request_id}] ImageAgent unavailable: {e}")
            return jsonify({
                "success": False,
                "error": "Image reference service unavailable. Please try again.",
            }), 503

        log_chat_interaction(
            session_id=session_id,
            user_message=f"[IMAGES] {query}",
            bot_response=result["message"],
            user_id=user_id,
            flagged=False,
            language=detected_lang,
        )

        return jsonify({
            "success": True,
            "message": result["message"],
            "image_references": result["image_references"],
            "language": detected_lang,
            "session_id": session_id,
        })

    except Exception as e:
        logging.exception(f"Image retrieval error: {e}")
        return jsonify({"success": False, "error": "Image retrieval unavailable. Please try again."}), 500


@bp.route("/substitute", methods=["POST"])
def substitute():
    """
    POST /api/chat/substitute — Phase 4 Substitution Sub-Agent.

    Given a requested medication (typically out of stock), returns
    therapeutic alternatives from in-stock SKUs:
      - exact_equivalents  (same active ingredient)
      - class_alternatives (same class, requires prescriber approval)

    Body:  { "requested": "Augmentin 625mg" | "Panadol",
             "lang": "auto"|"en"|"ur",
             "pharmacy_id": <int|null>,
             "session_id": "..." }
    Reply: { "success": true, "message": "<markdown>",
             "medicines": [{...with substitution_type}],
             "requested": {name, chemical, in_catalog, in_stock},
             "exact_count": N, "class_count": M,
             "session_id": "..." }
    """
    try:
        from services.chatbot import detect_language
        from services.substitution_agent import get_agent, SubstitutionAgentUnavailable

        try:
            from flask import g
            request_id = getattr(g, "request_id", "-")
        except Exception:
            request_id = "-"

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        requested = (data.get("requested") or data.get("message") or "").strip()
        if not requested:
            return jsonify({"success": False, "error": "'requested' (medication name) is required"}), 400

        lang = data.get("lang") or data.get("language") or "auto"
        session_id = data.get("session_id", str(uuid.uuid4()))
        user_id = data.get("user_id")
        pharmacy_id = data.get("pharmacy_id")
        detected_lang = detect_language(requested) if lang == "auto" else lang

        pharmacy_name = "Red Dot Pharmacy"
        if pharmacy_id:
            try:
                from models import Pharmacy
                ph = Pharmacy.query.get(pharmacy_id)
                if ph:
                    pharmacy_name = ph.name
            except Exception:
                pass

        try:
            agent = get_agent()
            if not agent.is_ready:
                raise SubstitutionAgentUnavailable("agent not ready")
            result = agent.find_alternatives(
                requested_medicine=requested,
                lang=detected_lang,
                pharmacy_name=pharmacy_name,
                request_id=request_id,
            )
        except SubstitutionAgentUnavailable as e:
            logging.warning(f"[req={request_id}] SubstitutionAgent unavailable: {e}")
            return jsonify({
                "success": False,
                "error": "Substitution service unavailable. Please try again.",
            }), 503

        log_chat_interaction(
            session_id=session_id,
            user_message=f"[SUBSTITUTE] {requested}",
            bot_response=result["message"],
            user_id=user_id,
            flagged=False,
            language=detected_lang,
            pharmacy_id=pharmacy_id,
        )

        return jsonify({
            "success": True,
            "message": result["message"],
            "medicines": result["medicines"],
            "requested": result["requested"],
            "exact_count": result["exact_count"],
            "class_count": result["class_count"],
            "language": detected_lang,
            "session_id": session_id,
        })

    except Exception as e:
        logging.exception(f"Substitution error: {e}")
        return jsonify({"success": False, "error": "Substitution unavailable. Please try again."}), 500


@bp.route("/clinical-reasoning", methods=["POST"])
def clinical_reasoning():
    """
    POST /api/chat/clinical-reasoning — Phase 3 Clinical Reasoning Sub-Agent.

    Generates a ranked differential diagnosis with discriminating features,
    confirmatory workup, and red-flag warnings. Adapts depth to user role
    (doctor: 3–7 ranked differentials; patient: 2–3 plain-language causes).

    Body:  { "message": "...", "lang": "auto"|"en"|"ur", "session_id": "...",
             "user_id": <int> }
    Reply: { "success": true, "message": "<markdown>", "needs_doctor": bool,
             "red_flag": bool, "session_id": "..." }
    """
    try:
        from services.chatbot import detect_language, needs_escalation, get_emergency_response
        from services.clinical_agent import get_agent, ClinicalAgentUnavailable

        try:
            from flask import g
            request_id = getattr(g, "request_id", "-")
        except Exception:
            request_id = "-"

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        message = data.get("message", "").strip()
        if not message:
            return jsonify({"success": False, "error": "Message is required"}), 400

        lang = data.get("lang") or data.get("language") or "auto"
        session_id = data.get("session_id", str(uuid.uuid4()))
        user_id = data.get("user_id")
        detected_lang = detect_language(message) if lang == "auto" else lang

        # Resolve user role from JWT if present; default to "patient".
        user_role = "patient"
        try:
            from services.auth import get_current_user
            user = get_current_user()
            if user and getattr(user, "role", None):
                user_role = user.role
        except Exception:
            pass

        # Emergency phrases — short-circuit before the LLM call.
        if needs_escalation(message):
            emergency_text = get_emergency_response(detected_lang)
            log_chat_interaction(
                session_id=session_id, user_message=message,
                bot_response=emergency_text, user_id=user_id,
                flagged=True, language=detected_lang,
            )
            return jsonify({
                "success": True,
                "message": emergency_text,
                "needs_doctor": True,
                "red_flag": True,
                "language": detected_lang,
                "session_id": session_id,
            })

        try:
            agent = get_agent()
            if not agent.is_ready:
                raise ClinicalAgentUnavailable("agent not ready")
            result = agent.reason(
                user_message=message,
                lang=detected_lang,
                user_role=user_role,
                request_id=request_id,
            )
        except ClinicalAgentUnavailable as e:
            logging.warning(f"[req={request_id}] ClinicalAgent unavailable: {e}")
            return jsonify({
                "success": False,
                "error": "Clinical reasoning service unavailable. Please try again.",
            }), 503

        log_chat_interaction(
            session_id=session_id, user_message=message,
            bot_response=result["message"], user_id=user_id,
            flagged=result["red_flag"], language=detected_lang,
        )

        return jsonify({
            "success": True,
            "message": result["message"],
            "needs_doctor": result["needs_doctor"],
            "red_flag": result["red_flag"],
            "language": detected_lang,
            "session_id": session_id,
        })

    except Exception as e:
        logging.exception(f"Clinical reasoning error: {e}")
        return jsonify({"success": False, "error": "Clinical reasoning unavailable. Please try again."}), 500


@bp.route("/web-search", methods=["POST"])
def web_search_chat():
    """
    POST /api/chat/web-search — Phase 2 Evidence Sub-Agent.

    Uses Gemini google.genai SDK with Google Search grounding, then enforces
    a credible-medical-sources allow-list. If no allow-listed source is
    returned, refuses with a clear "no credible source" message rather than
    falling back to ungrounded AI knowledge.

    Body:  { "message": "...", "lang": "en"|"ur", "session_id": "..." }
    Reply: { "success": true, "message": "<answer + Sources block>",
             "grounded": true, "sources": [{title, url}], "evidence_only": true }
    """
    try:
        from services.chatbot import detect_language, needs_escalation, get_emergency_response
        from services.evidence_search import run_evidence_search

        try:
            from flask import g
            request_id = getattr(g, "request_id", "-")
        except Exception:
            request_id = "-"

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        message = data.get("message", "").strip()
        if not message:
            return jsonify({"success": False, "error": "Message is required"}), 400

        lang = data.get("lang") or data.get("language") or "auto"
        session_id = data.get("session_id", str(uuid.uuid4()))
        user_id = data.get("user_id")
        detected_lang = detect_language(message) if lang == "auto" else lang

        # Emergency check first
        if needs_escalation(message):
            return jsonify({
                "success": True,
                "message": get_emergency_response(detected_lang),
                "grounded": False,
                "sources": [],
                "session_id": session_id,
            })

        result = run_evidence_search(message, detected_lang, request_id)

        log_chat_interaction(
            session_id=session_id,
            user_message=message,
            bot_response=result["message"],
            user_id=user_id,
            flagged=False,
            language=detected_lang,
        )

        return jsonify({
            "success": True,
            "message": result["message"],
            "language": detected_lang,
            "grounded": result.get("grounded", False),
            "sources": result.get("sources", []),
            "evidence_only": result.get("evidence_only", True),
            "session_id": session_id,
        })

    except Exception as e:
        logging.exception(f"Web search chat error: {e}")
        return jsonify({"success": False, "error": "Web search unavailable. Please try again."}), 500


# TTS Configuration
TTS_API_KEY = "8f1e5568-0d81-477a-a023-259fff2346d0"
TTS_BASE_URL = "https://aivoov.com/api/v8"
URDU_VOICE_ID = "86cad650-a467-486c-bc86-15d1615084e0"

@bp.route("/", methods=["POST"])
def chat():
    """Main chatbot endpoint with Wikipedia integration"""
    try:
        print("Chat endpoint called")
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        message = data.get("message", "").strip()
        if not message:
            return jsonify({"error": "Message is required"}), 400

        session_id = data.get("session_id", str(uuid.uuid4()))
        # Support both "language" and "prefer_urdu" parameters
        prefer_urdu = data.get("language") == "ur" or data.get("prefer_urdu")
        user_id = data.get("user_id")
        include_wiki = data.get("include_wiki", True)
        
        wiki_data = None
        wiki_context = ""
        
        if include_wiki:
            try:
                search_query = extract_medical_keywords(message)
                wiki_data = collect_wikipedia_resources(search_query)
                if wiki_data and wiki_data.get("success"):
                    wiki_context = build_wiki_context(wiki_data)
            except Exception as wiki_error:
                logging.warning(f"Wikipedia fetch failed: {wiki_error}")
        
        enhanced_message = f"{message}\n\n{wiki_context}" if wiki_context else message
        
        response_data = generate_response(
            text=enhanced_message,
            prefer_urdu=prefer_urdu,
            session_id=session_id
        )
        
        log_chat_interaction(
            session_id=session_id,
            user_message=message,
            bot_response=response_data['message'],
            user_id=user_id,
            flagged=response_data['flagged']
        )
        
        response_json = {
            "success": True,
            "session_id": session_id,
            "message": response_data['message'],
            "flagged": response_data['flagged'],
            "needs_doctor": response_data['needs_doctor'],
            "suggested_medicines": response_data['suggested_medicines']
        }
        
        if response_data.get('medicines'):
            response_json["medicines"] = response_data['medicines']
        
        if wiki_data and wiki_data.get("success"):
            response_json["wiki"] = {
                "title": wiki_data.get("title"),
                "page_url": wiki_data.get("page_url"),
                "summary": wiki_data.get("summary", "")[:300] if wiki_data.get("summary") else "",
                "images": wiki_data.get("images", [])[:4]
            }
        
        return jsonify(response_json)
        
    except Exception as e:
        logging.error(f"Chatbot error: {e}")
        return jsonify({
            "error": "Sorry, I'm having trouble right now. Please try again later.",
            "success": False
        }), 500

@bp.route("/voice", methods=["POST"])
def voice_chat():
    """Voice-enabled chat endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Handle voice input (transcript from client-side Speech Recognition)
        transcript = data.get("transcript", "").strip()
        if not transcript:
            return jsonify({"error": "No transcript provided"}), 400
        
        session_id = data.get("session_id", str(uuid.uuid4()))
        prefer_urdu = data.get("prefer_urdu", True)
        user_id = data.get("user_id")
        
        # Generate response using the same chatbot logic
        response_data = generate_response(
            text=transcript,
            prefer_urdu=prefer_urdu,
            session_id=session_id
        )
        
        # Log the voice interaction
        log_chat_interaction(
            session_id=session_id,
            user_message=f"[VOICE] {transcript}",
            bot_response=response_data['message'],
            user_id=user_id,
            flagged=response_data['flagged']
        )
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "transcript": transcript,
            "message": response_data['message'],
            "flagged": response_data['flagged'],
            "needs_doctor": response_data['needs_doctor'],
            "suggested_medicines": response_data['suggested_medicines'],
            "voice_enabled": True
        })
        
    except Exception as e:
        logging.error(f"Voice chat error: {e}")
        return jsonify({
            "error": "Voice chat is temporarily unavailable. Please try text chat.",
            "success": False
        }), 500

@bp.route("/history/<session_id>", methods=["GET"])
def get_chat_history(session_id):
    """Get chat history for a session"""
    try:
        from models import ChatLog
        
        # Get chat logs for this session
        logs = ChatLog.query.filter_by(session_id=session_id).order_by(ChatLog.created_at).all()
        
        history = []
        for log in logs:
            history.append({
                "message": log.message,
                "response": log.response,
                "timestamp": log.created_at.isoformat(),
                "flagged": log.flagged
            })
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "history": history
        })
        
    except Exception as e:
        logging.error(f"Chat history error: {e}")
        return jsonify({
            "error": "Failed to retrieve chat history",
            "success": False
        }), 500

@bp.route("/sessions", methods=["GET"])
def get_user_sessions():
    """Get chat sessions for authenticated user"""
    try:
        from services.auth import get_current_user
        from models import ChatLog
        
        user = get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        
        # Get unique sessions for this user
        sessions = ChatLog.query.filter_by(user_id=user.id)\
                               .with_entities(ChatLog.session_id, ChatLog.created_at)\
                               .distinct(ChatLog.session_id)\
                               .order_by(ChatLog.created_at.desc())\
                               .limit(10).all()
        
        session_list = []
        for session in sessions:
            # Get first message of each session for preview
            first_log = ChatLog.query.filter_by(
                user_id=user.id, 
                session_id=session.session_id
            ).first()
            
            session_list.append({
                "session_id": session.session_id,
                "created_at": session.created_at.isoformat(),
                "preview": (first_log.message[:50] + "...") if (first_log and first_log.message and len(first_log.message) > 50) else (first_log.message if first_log and first_log.message else "No preview available")
            })
        
        return jsonify({
            "success": True,
            "sessions": session_list
        })
        
    except Exception as e:
        logging.error(f"User sessions error: {e}")
        return jsonify({
            "error": "Failed to retrieve chat sessions",
            "success": False
        }), 500

def transcribe_audio_common(audio_file, language_code):
    """
    Common function to transcribe audio files
    Handles WebM, OGG, and other formats by converting to WAV
    Enhanced for better Urdu recognition
    """
    import tempfile
    from pydub import AudioSegment
    
    upload_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    
    content_type = audio_file.content_type or 'audio/webm'
    logging.info(f"Received audio with content-type: {content_type}")
    
    if 'webm' in content_type:
        ext = '.webm'
    elif 'ogg' in content_type:
        ext = '.ogg'
    elif 'mp4' in content_type or 'mpeg' in content_type:
        ext = '.mp4'
    else:
        ext = '.webm'
    
    temp_input = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    
    try:
        audio_file.save(temp_input.name)
        logging.info(f"Saved audio to: {temp_input.name}")
        
        sound = AudioSegment.from_file(temp_input.name)
        
        is_urdu = language_code.startswith('ur')
        if is_urdu:
            sound = sound + 3
            sound = sound.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            sound = sound.normalize()
        else:
            sound = sound.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        
        sound.export(temp_wav.name, format='wav')
        logging.info(f"Converted to WAV: {temp_wav.name}, duration: {len(sound)}ms")
        
        if len(sound) < 500:
            logging.warning(f"Audio too short: {len(sound)}ms")
            return {"success": False, "error": "Recording too short. Please speak for at least 1 second."}
        
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        
        with sr.AudioFile(temp_wav.name) as source:
            if len(sound) > 1000:
                recognizer.adjust_for_ambient_noise(source, duration=0.1)
            audio = recognizer.record(source)
        
        language_attempts = [language_code]
        if is_urdu:
            if language_code == "ur-PK":
                language_attempts.append("ur")
            else:
                language_attempts.append("ur-PK")
        
        last_error = None
        for lang in language_attempts:
            try:
                text = recognizer.recognize_google(audio, language=lang)
                logging.info(f"Transcribed text ({lang}): {text}")
                return {"success": True, "transcript": text}
            except sr.UnknownValueError as e:
                logging.warning(f"Speech recognition failed for {lang}")
                last_error = e
                continue
            except sr.RequestError as e:
                logging.error(f"Speech recognition service error for {lang}: {e}")
                last_error = e
                break
        
        if isinstance(last_error, sr.UnknownValueError):
            return {"success": False, "error": "Could not understand the audio. Please speak clearly and try again."}
        else:
            return {"success": False, "error": f"Speech recognition service error: {str(last_error)}"}
        
    except sr.RequestError as e:
        logging.error(f"Speech recognition service error: {e}")
        return {"success": False, "error": f"Speech recognition service error: {str(e)}"}
        
    except Exception as e:
        logging.error(f"Audio processing error: {e}")
        return {"success": False, "error": f"Audio processing error: {str(e)}"}
        
    finally:
        try:
            os.unlink(temp_input.name)
        except:
            pass
        try:
            os.unlink(temp_wav.name)
        except:
            pass


@bp.route("/transcribe-urdu", methods=["POST"])
def transcribe_urdu_audio():
    """
    Endpoint to transcribe Urdu speech from an audio file
    Accepts: multipart/form-data with 'audio' file
    Returns: JSON with transcribed text or error message
    """
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided", "success": False}), 400
        
        audio_file = request.files['audio']
        result = transcribe_audio_common(audio_file, "ur-PK")
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logging.error(f"Urdu transcription error: {e}")
        return jsonify({
            "success": False,
            "error": "An error occurred during audio processing"
        }), 500


@bp.route("/transcribe-english", methods=["POST"])
def transcribe_english_audio():
    """
    Endpoint to transcribe English speech from an audio file
    Accepts: multipart/form-data with 'audio' file
    Returns: JSON with transcribed text or error message
    """
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided", "success": False}), 400
        
        audio_file = request.files['audio']
        result = transcribe_audio_common(audio_file, "en-US")
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logging.error(f"English transcription error: {e}")
        return jsonify({
            "success": False,
            "error": "An error occurred during audio processing"
        }), 500


@bp.route("/translate", methods=["POST"])
def translate_text():
    """
    Endpoint to translate text between English and Urdu
    Accepts: JSON with 'text' and 'target_lang' (en or ur)
    Returns: JSON with translated text
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided", "success": False}), 400
        
        text = data.get("text", "").strip()
        target_lang = data.get("target_lang", "ur")  # Default translate to Urdu
        
        if not text:
            return jsonify({"error": "Text is required", "success": False}), 400
        
        # Use Gemini for translation
        import google.generativeai as genai
        
        api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            return jsonify({"error": "Translation service not configured", "success": False}), 500
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        if target_lang == 'ur':
            prompt = f"Translate the following English text to Urdu. Only provide the translation, no explanations:\n\n{text}"
        else:
            prompt = f"Translate the following Urdu text to English. Only provide the translation, no explanations:\n\n{text}"
        
        response = model.generate_content(prompt)
        translated = response.text.strip()
        
        return jsonify({
            "success": True,
            "original": text,
            "translated": translated,
            "target_lang": target_lang
        })
        
    except Exception as e:
        logging.error(f"Translation error: {e}")
        return jsonify({
            "error": "Translation failed",
            "success": False
        }), 500


@bp.route("/speak-english", methods=["POST"])
def speak_english():
    """
    Endpoint to convert English text to speech
    Accepts: JSON with 'text' field containing English text
    Returns: Audio file
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        text = data.get("text", "").strip()
        if not text:
            return jsonify({"error": "Text is required"}), 400
        
        # Generate speech using gTTS
        tts = gTTS(text=text, lang='en')
        
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        return send_file(
            audio_buffer,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name=f"speech_{int(time.time())}.mp3"
        )

    except Exception as e:
        logging.error(f"English TTS error: {e}")
        return jsonify({
            "error": "Failed to process text-to-speech request",
            "success": False
        }), 500


@bp.route("/speak-urdu", methods=["POST"])
def speak_urdu():
    """
    Endpoint to convert Urdu text to speech
    Accepts: JSON with 'text' field containing Urdu text
    Returns: JSON with audio file URL or error message
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        text = data.get("text", "").strip()
        if not text:
            return jsonify({"error": "Text is required"}), 400
        
        # Generate speech using gTTS
        tts = gTTS(text=text, lang='ur')
        
        # Create a file-like buffer to store the audio
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)  # Rewind the buffer to the beginning
        
        # Return the audio file directly from memory
        return send_file(
            audio_buffer,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name=f"speech_{int(time.time())}.mp3"
        )

    except Exception as e:
        logging.error(f"TTS error: {e}")
        return jsonify({
            "error": "Failed to process text-to-speech request",
            "success": False
        }), 500