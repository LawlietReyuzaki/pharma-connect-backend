"""
Clinical Reasoning Sub-Agent — Phase 3.

Produces a ranked differential diagnosis (3-7 candidates for doctors,
2-3 plausible causes for patients) with discriminating features,
confirmatory workup, and red-flag warnings.

Always emits the decision-support disclaimer. Emergency-trigger phrases
are handled by needs_escalation() before this agent is invoked.
"""
import os
import json
import logging
import time
from typing import Dict, Optional

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.4"))

DISCLAIMER_DOCTOR_EN = (
    "*Decision support only — not a diagnosis. Final clinical decisions "
    "must be made by a qualified physician based on full history, examination, "
    "and investigations.*"
)
DISCLAIMER_PATIENT_EN = (
    "*This is general health information, not a diagnosis. Please consult a "
    "doctor for proper evaluation — you can book a consultation on this "
    "platform.*"
)
DISCLAIMER_DOCTOR_UR = (
    "*یہ صرف کلینیکل سپورٹ ہے — تشخیص نہیں۔ حتمی فیصلہ مکمل تاریخ، معائنہ اور "
    "ٹیسٹس کے بعد ڈاکٹر ہی کرے گا۔*"
)
DISCLAIMER_PATIENT_UR = (
    "*یہ عمومی صحت کی معلومات ہیں، تشخیص نہیں۔ مکمل جانچ کے لیے ڈاکٹر سے "
    "مشورہ کریں — اس پلیٹ فارم پر اپائنٹمنٹ بک کر سکتے ہیں۔*"
)


class ClinicalAgentUnavailable(Exception):
    pass


_agent_singleton: Optional["ClinicalAgent"] = None


def get_agent() -> "ClinicalAgent":
    global _agent_singleton
    if _agent_singleton is None:
        _agent_singleton = ClinicalAgent()
    return _agent_singleton


class ClinicalAgent:
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
            logging.info("ClinicalAgent ready")
        except Exception as e:
            self._init_error = str(e)
            logging.warning(f"ClinicalAgent unavailable: {e}")

    @property
    def is_ready(self) -> bool:
        return self._ready

    def reason(
        self,
        user_message: str,
        lang: str = "en",
        user_role: str = "patient",
        request_id: str = "-",
    ) -> Dict:
        """
        Returns:
          {
            "message": "<markdown-formatted differential + disclaimer>",
            "needs_doctor": bool,
            "red_flag": bool,
            "audit": {...}
          }
        """
        if not self._ready:
            raise ClinicalAgentUnavailable(self._init_error or "agent not ready")

        is_clinician = user_role in ("doctor", "admin", "pharmacy_admin")
        prompt = self._build_prompt(user_message, lang, is_clinician)

        t0 = time.time()
        message, needs_doctor, red_flag = self._call_llm(prompt, lang, is_clinician)
        t_llm = time.time() - t0

        # Ensure disclaimer is present.
        disclaimer = self._disclaimer(lang, is_clinician)
        if disclaimer not in message:
            message = f"{message}\n\n---\n{disclaimer}"

        audit = {
            "request_id": request_id,
            "user_role": user_role,
            "is_clinician": is_clinician,
            "red_flag": red_flag,
            "needs_doctor": needs_doctor,
            "llm_ms": int(t_llm * 1000),
        }
        logging.info(
            f"[req={request_id}] ClinicalAgent role={user_role} "
            f"red_flag={red_flag} needs_doctor={needs_doctor} llm_ms={audit['llm_ms']}"
        )
        return {
            "message": message,
            "needs_doctor": needs_doctor,
            "red_flag": red_flag,
            "audit": audit,
        }

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _disclaimer(lang: str, is_clinician: bool) -> str:
        if lang == "ur":
            return DISCLAIMER_DOCTOR_UR if is_clinician else DISCLAIMER_PATIENT_UR
        return DISCLAIMER_DOCTOR_EN if is_clinician else DISCLAIMER_PATIENT_EN

    @staticmethod
    def _build_prompt(user_message: str, lang: str, is_clinician: bool) -> str:
        lang_block = (
            "Respond in Urdu (Urdu script, not Roman Urdu) in the 'message' field."
            if lang == "ur"
            else "Respond in English in the 'message' field."
        )

        if is_clinician:
            role_block = (
                "You are a Clinical Reasoning AI assisting a licensed physician. "
                "The user is a doctor brainstorming a differential diagnosis. "
                "Be specific, use medical vocabulary, and structure the output for "
                "rapid clinical scanning."
            )
            format_rules = (
                "Structure the 'message' as markdown with this format:\n\n"
                "### Working differential (decision support — not a diagnosis)\n\n"
                "For EACH of 3–7 candidate conditions, in descending order of "
                "likelihood given the input:\n\n"
                "**N. Condition Name** *(likelihood: high|moderate|low)*\n"
                "- **Discriminating features to look for**: <bullet/list>\n"
                "- **Suggested workup**: <bullet/list of investigations>\n"
                "- **Red flags**: <bullet/list of features that warrant urgent referral>\n\n"
                "End with a short '### Suggested next steps' section "
                "(2–4 bullet points) — history, exam, or investigation priorities."
            )
            count_rule = "Return 3 to 7 differentials."
        else:
            role_block = (
                "You are a Health Assistant talking to a patient. The user is "
                "describing how they feel. Avoid alarming language. Avoid raw "
                "probabilities. Always recommend seeing a doctor for proper "
                "evaluation."
            )
            format_rules = (
                "Structure the 'message' as friendly markdown:\n\n"
                "### What this might be\n\n"
                "List 2–3 plausible everyday causes in plain language. For each:\n\n"
                "**Possible cause**: short non-alarming explanation.\n"
                "- **What might help right now**: simple self-care (rest, hydration, OTC if appropriate)\n"
                "- **When to see a doctor**: the threshold — symptoms persisting >X days, fever, etc.\n\n"
                "End with a short '### See a doctor sooner if...' section listing "
                "red-flag symptoms in plain language."
            )
            count_rule = "Return at most 3 possible causes in plain language."

        return f"""{role_block}

{format_rules}
{count_rule}

RESPONSE FORMAT (CRITICAL):
You MUST respond with ONLY a valid JSON object:
{{
  "message": "<markdown text following the structure above>",
  "needs_doctor": <true if clinical review is recommended, else false>,
  "red_flag": <true if any red-flag feature is present in the symptoms, else false>
}}

RULES:
- Never give a definitive diagnosis. Always frame as decision-support.
- If symptoms include chest pain, sudden severe headache, loss of consciousness, focal neuro deficit, suicidal ideation, severe bleeding, anaphylaxis-like features, suspected stroke, or pregnancy-related red flags: set red_flag=true and put a prominent urgent-care warning at the TOP of the message.
- {lang_block}

USER INPUT:
{user_message}

JSON RESPONSE:"""

    def _call_llm(self, prompt: str, lang: str, is_clinician: bool):
        from google.genai import types as genai_types

        schema = {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "needs_doctor": {"type": "boolean"},
                "red_flag": {"type": "boolean"},
            },
            "required": ["message", "needs_doctor", "red_flag"],
        }

        config = genai_types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            max_output_tokens=1500,
            temperature=GEMINI_TEMPERATURE,
        )

        response = self._client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=config,
        )

        raw = (response.text or "").strip()
        if not raw:
            raise ClinicalAgentUnavailable("Empty LLM response")

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            logging.error(f"ClinicalAgent JSON parse failed: {raw[:300]} | err={e}")
            raise ClinicalAgentUnavailable(f"JSON parse failed: {e}")

        message = (parsed.get("message") or "").strip()
        needs_doctor = bool(parsed.get("needs_doctor", False))
        red_flag = bool(parsed.get("red_flag", False))

        if not message:
            message = self._fallback_message(lang, is_clinician)
            needs_doctor = True

        return message, needs_doctor, red_flag

    @staticmethod
    def _fallback_message(lang: str, is_clinician: bool) -> str:
        if lang == "ur":
            return (
                "معذرت، میں ابھی تفصیلی تفریقی تشخیص نہیں دے سکا۔ "
                "براہ کرم تفصیل دوبارہ بتائیں یا ڈاکٹر سے ملاقات کا اپائنٹمنٹ بک کریں۔"
            )
        return (
            "I couldn't produce a detailed differential right now. "
            "Could you share a bit more (onset, duration, severity, associated "
            "symptoms)? Or book a consultation with a clinician for full evaluation."
        )
