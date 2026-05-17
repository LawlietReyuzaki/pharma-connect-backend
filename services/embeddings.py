"""
Gemini text-embedding wrapper.
Uses the new google.genai SDK (same one used for web-search grounding).
"""
import os
import time
import logging
from typing import List

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-004")
EMBED_DIM = 768

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


def embed_one(text: str) -> List[float]:
    """Embed a single string. Returns a 768-dim vector."""
    client = _get_client()
    text = (text or "").strip()
    if not text:
        return [0.0] * EMBED_DIM
    result = client.models.embed_content(model=EMBED_MODEL, contents=text)
    return list(result.embeddings[0].values)


def embed_batch(texts: List[str], retries: int = 3, sleep: float = 1.5) -> List[List[float]]:
    """Embed a list of strings in one call. Retries on transient failures."""
    client = _get_client()
    cleaned = [(t or "").strip() or " " for t in texts]
    last_err = None
    for attempt in range(retries):
        try:
            result = client.models.embed_content(model=EMBED_MODEL, contents=cleaned)
            return [list(e.values) for e in result.embeddings]
        except Exception as e:
            last_err = e
            logging.warning(f"Embedding batch failed (attempt {attempt + 1}/{retries}): {e}")
            time.sleep(sleep * (attempt + 1))
    raise RuntimeError(f"Embedding batch failed after {retries} attempts: {last_err}")
