"""
Orchestrator Agent (spec section 5.1).

Single entry point that classifies the user's intent and routes the
message to the appropriate sub-agent(s), then composes one unified
response. The frontend no longer needs to know which endpoint to call.

Intent classes (chosen to map to the 5 sub-agents shipped earlier):
  - catalog           in-stock recommendations / "what do you have for X"
  - clinical          differential diagnosis brainstorming
  - evidence          "what does the literature say about X"
  - substitute        "X is out of stock, what else?"
  - images            visually-identifiable conditions, rashes, lesions
  - emergency         red-flag short-circuit (no LLM)
  - small_talk        greeting / chit-chat -> Catalog with empty recommendations

The orchestrator does ONE Gemini structured-JSON call for classification,
then calls the corresponding sub-agent. Two LLM calls per turn worst case
(classifier + sub-agent), which is well within the latency budget.

A `mode` field on the request (patient | doctor | pharmacist) can be
provided by the frontend; otherwise it is resolved from the user's JWT
role (defaults to "patient").
"""
import os
import json
import logging
import time
from typing import Dict, Optional

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

INTENT_VALUES = ["catalog", "clinical", "evidence", "substitute", "images", "small_talk"]


class OrchestratorUnavailable(Exception):
    pass


_singleton: Optional["Orchestrator"] = None


def get_orchestrator() -> "Orchestrator":
    global _singleton
    if _singleton is None:
        _singleton = Orchestrator()
    return _singleton


class Orchestrator:
    def __init__(self):
        self._client = None
        self._ready = False
        self._init_error: Optional[str] = None
        self._initialize()

    def _initialize(self):
        try:
            from google import genai
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise RuntimeError("GEMINI_API_KEY not set")
            self._client = genai.Client(api_key=api_key)
            self._ready = True
            logging.info("Orchestrator ready")
        except Exception as e:
            self._init_error = str(e)
            logging.warning(f"Orchestrator unavailable: {e}")

    @property
    def is_ready(self) -> bool:
        return self._ready

    # ------------------------------------------------------------ main entry

    def handle(
        self,
        user_message: str,
        lang: str = "en",
        mode: str = "patient",
        user_role: str = "patient",
        pharmacy_name: str = "Red Dot Pharmacy",
        pharmacy_id: Optional[int] = None,
        request_id: str = "-",
        force_intent: Optional[str] = None,
    ) -> Dict:
        """
        Returns a unified response with keys:
          intent, message, medicines?, sources?, image_references?,
          needs_doctor?, red_flag?, cta?, requested?, exact_count?, class_count?
        """
        # 1. Emergency short-circuit (no LLM)
        from services.chatbot import needs_escalation, get_emergency_response
        if needs_escalation(user_message):
            cta_label = "Book a consultation" if lang == "en" else "ڈاکٹر سے رابطہ"
            return {
                "intent": "emergency",
                "message": get_emergency_response(lang),
                "needs_doctor": True,
                "red_flag": True,
                "cta": {"label": cta_label, "url": "/consultation"},
            }

        # 2. Classify intent (or take override)
        if force_intent in INTENT_VALUES:
            intent = force_intent
            classify_ms = 0
            sub_query = user_message
        else:
            t0 = time.time()
            intent, sub_query = self._classify(user_message, mode)
            classify_ms = int((time.time() - t0) * 1000)

        logging.info(f"[req={request_id}] Orchestrator intent={intent} mode={mode} classify_ms={classify_ms}")

        # 3. Dispatch
        try:
            if intent == "catalog" or intent == "small_talk":
                return self._call_catalog(user_message, lang, mode, pharmacy_name, request_id, intent)
            if intent == "clinical":
                return self._call_clinical(user_message, lang, user_role, request_id)
            if intent == "evidence":
                return self._call_evidence(sub_query or user_message, lang, request_id)
            if intent == "substitute":
                return self._call_substitute(sub_query or user_message, lang, pharmacy_name, request_id)
            if intent == "images":
                return self._call_images(sub_query or user_message, lang, request_id)
        except Exception as e:
            logging.exception(f"[req={request_id}] Orchestrator dispatch failed for intent={intent}: {e}")

        # Fallback: catalog with empty recommendations
        return self._call_catalog(user_message, lang, mode, pharmacy_name, request_id, "catalog")

    # -------------------------------------------------------- classification

    def _classify(self, user_message: str, mode: str):
        """
        Returns (intent: str, sub_query: str).
        sub_query is the cleaned query to pass to the sub-agent.
        """
        if not self._ready:
            return "catalog", user_message

        from google.genai import types as genai_types

        prompt = f"""Classify the user's message into ONE of these intents:

  - catalog       : asking what medicines we have for a symptom/condition, OR
                    asking about a specific medicine by name (price, availability)
  - clinical      : describing patient symptoms wanting differential diagnoses,
                    or asking "what could these symptoms mean"
  - evidence      : asking what the medical literature, guidelines, or credible
                    sources say about a topic ("what does WHO say", "latest
                    guidelines", "research on X")
  - substitute    : a specific medicine is out of stock / unavailable and the
                    user wants alternatives ("we're out of X, what else?",
                    "alternative to X")
  - images        : wants visual references — rash, lesion, X-ray, radiology,
                    skin condition pictures; phrases like "what does X look
                    like", "image of", "differentiate X from Y visually"
  - small_talk    : greeting, thanks, or non-medical chat

USER MODE: {mode}
USER MESSAGE: {user_message}

If the message has multiple intents, pick the PRIMARY one.

Also extract a cleaned 'sub_query' string suitable for passing to the
sub-agent. For evidence/images, strip filler words so the search is focused.
For catalog/clinical/substitute, the sub_query may equal the original message.

Respond ONLY with JSON:
{{
  "intent": "<one of: catalog, clinical, evidence, substitute, images, small_talk>",
  "sub_query": "<cleaned query>"
}}"""

        schema = {
            "type": "object",
            "properties": {
                "intent": {"type": "string"},
                "sub_query": {"type": "string"},
            },
            "required": ["intent", "sub_query"],
        }
        try:
            response = self._client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    max_output_tokens=200,
                    temperature=0.0,
                ),
            )
            data = json.loads((response.text or "").strip() or "{}")
            intent = (data.get("intent") or "").strip()
            if intent not in INTENT_VALUES:
                intent = "catalog"
            sub_query = (data.get("sub_query") or "").strip() or user_message
            return intent, sub_query
        except Exception as e:
            logging.warning(f"Intent classification failed, defaulting to catalog: {e}")
            return "catalog", user_message

    # ----------------------------------------------------------- dispatchers

    def _call_catalog(self, msg, lang, mode, pharmacy_name, request_id, intent):
        from services.catalog_agent import get_agent
        agent = get_agent()
        if not agent.is_ready:
            # Catalog Chroma index still warming up (or unavailable). Fall
            # through to the legacy Gemini path so we still respond — never
            # show a "service unavailable" message for normal chat turns.
            try:
                from services.chatbot import generate_response
                legacy = generate_response(
                    text=msg, lang=lang, session_id=request_id, mode=mode,
                )
                return {
                    "intent": intent,
                    "message": legacy.get("message", self._fallback_text(lang)),
                    "medicines": legacy.get("medicines", []),
                    "needs_doctor": legacy.get("needs_doctor", False),
                }
            except Exception as e:
                logging.exception(f"[req={request_id}] legacy fallback also failed: {e}")
                return {"intent": intent, "message": self._fallback_text(lang), "medicines": []}
        result = agent.recommend(
            user_message=msg, lang=lang, mode=mode,
            pharmacy_name=pharmacy_name, request_id=request_id,
        )
        return {
            "intent": intent,
            "message": result["message"],
            "medicines": result["medicines"],
        }

    def _call_clinical(self, msg, lang, user_role, request_id):
        from services.clinical_agent import get_agent
        agent = get_agent()
        if not agent.is_ready:
            return {"intent": "clinical", "message": self._fallback_text(lang), "needs_doctor": True}
        result = agent.reason(
            user_message=msg, lang=lang, user_role=user_role, request_id=request_id,
        )
        cta = None
        if result.get("red_flag") or result.get("needs_doctor"):
            cta = {
                "label": "Book a consultation" if lang == "en" else "ڈاکٹر سے ملاقات بک کریں",
                "url": "/consultation",
            }
        return {
            "intent": "clinical",
            "message": result["message"],
            "needs_doctor": result["needs_doctor"],
            "red_flag": result["red_flag"],
            "cta": cta,
        }

    def _call_evidence(self, msg, lang, request_id):
        from services.evidence_search import run_evidence_search
        return run_evidence_search(msg, lang, request_id)

    def _call_substitute(self, msg, lang, pharmacy_name, request_id):
        from services.substitution_agent import get_agent
        agent = get_agent()
        if not agent.is_ready:
            return {"intent": "substitute", "message": self._fallback_text(lang), "medicines": []}
        result = agent.find_alternatives(
            requested_medicine=msg, lang=lang,
            pharmacy_name=pharmacy_name, request_id=request_id,
        )
        return {
            "intent": "substitute",
            "message": result["message"],
            "medicines": result["medicines"],
            "requested": result.get("requested"),
            "exact_count": result.get("exact_count", 0),
            "class_count": result.get("class_count", 0),
        }

    def _call_images(self, msg, lang, request_id):
        from services.image_agent import get_agent
        agent = get_agent()
        if not agent.is_ready:
            return {"intent": "images", "message": self._fallback_text(lang), "image_references": []}
        result = agent.find_images(query=msg, lang=lang, request_id=request_id)
        return {
            "intent": "images",
            "message": result["message"],
            "image_references": result["image_references"],
        }

    @staticmethod
    def _fallback_text(lang: str) -> str:
        if lang == "ur":
            return "معذرت، ابھی سروس دستیاب نہیں۔ براہ کرم دوبارہ کوشش کریں۔"
        return "Sorry, this service is unavailable right now. Please try again."
