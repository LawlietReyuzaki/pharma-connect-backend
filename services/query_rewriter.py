"""
Medical query rewriter for RAG retrieval.

Before embedding a user query for vector search, we expand it with:
  - Generic drug names (e.g. "viagra" → "sildenafil")
  - Drug class (e.g. "blood pressure" → "antihypertensive, ARB, ACE inhibitor")
  - Related conditions / synonyms
  - Common patient-language → clinical-language mapping

This dramatically improves recall because the medicine documents are written
in clinical language while users type colloquially or by brand name.

Implementation: a single fast Gemini Flash call with structured JSON output.
Falls back to the original query if the rewriter fails.
"""
import os
import json
import logging
import re
from typing import Optional

GEMINI_MODEL = os.getenv("GEMINI_REWRITER_MODEL", "gemini-2.0-flash")

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY / GOOGLE_API_KEY not set")
    from google import genai
    _client = genai.Client(api_key=api_key)
    return _client


REWRITE_PROMPT = """\
You expand a user's medical query into a richer retrieval query so vector \
search over a medicine catalogue can find the right products.

Given the user message, output a single line of comma-separated medical \
terms that would appear in the clinical description of relevant medicines. \
Include:
- Generic active ingredients (e.g. "viagra" -> "sildenafil")
- Drug class names (e.g. "blood pressure" -> "antihypertensive, ARB, ACE inhibitor, beta-blocker, calcium channel blocker")
- Clinical synonyms (e.g. "stomach pain" -> "gastric pain, dyspepsia, gastritis, GERD, acid reflux")
- Related conditions (e.g. "headache" -> "migraine, tension headache, analgesic, NSAID")

STRICT RULES:
- DO NOT invent or guess generic names for brand names you don't recognise. \
If the user typed an unfamiliar product / brand name, KEEP it as-is — do not \
map it to a similar-sounding but unrelated generic.
- For widely-known brands ONLY (viagra/sildenafil, cialis/tadalafil, panadol/paracetamol, \
brufen/ibuprofen, ventolin/salbutamol), do map to the generic.
- Otherwise stick to clinical synonyms of whatever the user described.
- Keep it tight: 5-15 terms, comma-separated, no explanation, no quotes, no JSON.

If the user message is not medical (greetings, chit-chat), output it unchanged.

USER MESSAGE: {query}

EXPANDED RETRIEVAL TERMS:"""


# Lightweight regex shortcut: don't bother calling Gemini for greetings
_GREETING_RE = re.compile(r"^(hi|hello|hey|salam|assalam|good\s*(morning|evening|night|afternoon)|thanks|thank you|bye|goodbye)\b", re.IGNORECASE)


def enhance_query(user_query: str) -> str:
    """
    Return an expanded query string suitable for embedding. Falls back to
    the original on any failure so callers never need a try/except.
    """
    q = (user_query or "").strip()
    if not q:
        return q
    if len(q) > 600 or _GREETING_RE.match(q):
        return q

    try:
        client = _get_client()
        from google.genai import types as genai_types
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=REWRITE_PROMPT.format(query=q),
            config=genai_types.GenerateContentConfig(
                max_output_tokens=200,
                temperature=0.1,
            ),
        )
        expanded = (response.text or "").strip()
        # Strip any quoting or accidental JSON
        expanded = expanded.strip('"').strip("'").strip()
        if not expanded:
            return q
        # Combine: original + expansion. The original phrasing still
        # carries the patient context (e.g. "I have a 3-year-old with...").
        return f"{q} | {expanded}"
    except Exception as e:
        logging.warning(f"Query rewriter failed, falling back to raw query: {e}")
        return q
