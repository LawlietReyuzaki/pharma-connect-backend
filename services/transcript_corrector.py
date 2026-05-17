"""
Phase 6 — STT post-correction for medical vocabulary.

The current STT pipeline (browser webkitSpeechRecognition + server-side
Google STT) is general-purpose and often mistranscribes drug names,
chemical compounds, and clinical jargon. Instead of swapping the
recogniser, we add a cheap LLM correction pass on the transcript.

Single Gemini call with structured JSON output. ~200 tokens per
correction. No grounding, no search — pure text rewrite under tight
constraints ('only fix terms; preserve the user's meaning verbatim').

Usable from:
  - The new /api/chat/correct-transcript endpoint (frontend opt-in)
  - As a pre-processor inside any chat route that wants STT cleanup
"""
import os
import json
import logging
import time
from typing import Dict, Optional

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


class TranscriptCorrectorUnavailable(Exception):
    pass


_singleton: Optional["TranscriptCorrector"] = None


def get_corrector() -> "TranscriptCorrector":
    global _singleton
    if _singleton is None:
        _singleton = TranscriptCorrector()
    return _singleton


class TranscriptCorrector:
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
            logging.info("TranscriptCorrector ready")
        except Exception as e:
            self._init_error = str(e)
            logging.warning(f"TranscriptCorrector unavailable: {e}")

    @property
    def is_ready(self) -> bool:
        return self._ready

    def correct(self, transcript: str, lang: str = "en", request_id: str = "-") -> Dict:
        if not self._ready:
            raise TranscriptCorrectorUnavailable(self._init_error or "corrector not ready")
        transcript = (transcript or "").strip()
        if not transcript:
            return {"corrected": "", "changes": [], "audit": {"request_id": request_id, "skipped": True}}

        from google.genai import types as genai_types

        lang_block = (
            "The transcript is Urdu. Keep the Urdu script intact. "
            "Only normalise medical/drug terms that are mis-spelled or transliterated incorrectly."
            if lang == "ur" else
            "The transcript is English."
        )

        prompt = f"""You are a strict medical-transcript editor. The text below comes from a
speech-to-text engine and may contain mis-heard medical terms (drug names,
chemicals, conditions, dosages).

YOUR JOB:
1. Fix ONLY mis-transcribed medical/drug/clinical terms.
   Examples:
     "panda doll" -> "Panadol"
     "iboo proof in" -> "Ibuprofen"
     "amox seclude" -> "Amoxiclav"
     "para set a mall" -> "paracetamol"
     "iron deef" -> "iron deficiency"
2. Preserve the user's meaning verbatim. Do NOT rephrase, summarise, expand,
   or add information.
3. Preserve casing/punctuation that is not part of a medical term.
4. If unsure whether a word is a medical term, leave it unchanged.
5. Never add disclaimers, advice, or extra sentences.

{lang_block}

RESPONSE FORMAT (CRITICAL):
Return ONLY a JSON object:
{{
  "corrected": "<the fully corrected transcript>",
  "changes": [
    {{ "original": "<original token or phrase>", "corrected": "<replacement>" }},
    ...
  ]
}}

If no changes are needed, return the original transcript as 'corrected' and
'changes': [].

ORIGINAL TRANSCRIPT:
{transcript}

JSON RESPONSE:"""

        schema = {
            "type": "object",
            "properties": {
                "corrected": {"type": "string"},
                "changes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "original": {"type": "string"},
                            "corrected": {"type": "string"},
                        },
                        "required": ["original", "corrected"],
                    },
                },
            },
            "required": ["corrected", "changes"],
        }

        t0 = time.time()
        try:
            response = self._client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    max_output_tokens=600,
                    temperature=0.0,  # deterministic correction
                ),
            )
        except Exception as e:
            logging.error(f"[req={request_id}] TranscriptCorrector LLM call failed: {e}")
            raise TranscriptCorrectorUnavailable(f"LLM call failed: {e}")
        t_llm = time.time() - t0

        raw = (response.text or "").strip()
        if not raw:
            return {"corrected": transcript, "changes": [], "audit": {"request_id": request_id, "empty": True}}

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            logging.error(f"[req={request_id}] TranscriptCorrector JSON parse failed: {raw[:300]} | err={e}")
            # Soft-fail: return original rather than blow up the caller.
            return {"corrected": transcript, "changes": [], "audit": {"request_id": request_id, "parse_error": str(e)}}

        corrected = (parsed.get("corrected") or transcript).strip()
        changes_raw = parsed.get("changes") or []
        # Sanitize changes — drop entries that don't have both fields.
        changes = []
        for c in changes_raw:
            if isinstance(c, dict):
                orig = (c.get("original") or "").strip()
                corr = (c.get("corrected") or "").strip()
                if orig and corr and orig != corr:
                    changes.append({"original": orig, "corrected": corr})

        audit = {
            "request_id": request_id,
            "input_len": len(transcript),
            "output_len": len(corrected),
            "change_count": len(changes),
            "llm_ms": int(t_llm * 1000),
        }
        logging.info(
            f"[req={request_id}] TranscriptCorrector changes={len(changes)} llm_ms={audit['llm_ms']}"
        )
        return {"corrected": corrected, "changes": changes, "audit": audit}
