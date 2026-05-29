"""
Gemini text-embedding wrapper.
Uses the new google.genai SDK (same one used for web-search grounding).
"""
import os
import time
import logging
from typing import List

EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
EMBED_DIM = 768  # gemini-embedding-001 default is 3072; we force 768 for storage compactness

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


def _embed_config(task_type: str = "RETRIEVAL_DOCUMENT"):
    from google.genai import types as genai_types
    return genai_types.EmbedContentConfig(
        output_dimensionality=EMBED_DIM,
        task_type=task_type,
    )


def embed_one(text: str, task_type: str = "RETRIEVAL_QUERY") -> List[float]:
    """
    Embed a single string. Default task_type is RETRIEVAL_QUERY because
    embed_one is mainly used at search time for user queries.
    Returns a 768-dim vector.
    """
    client = _get_client()
    text = (text or "").strip()
    if not text:
        return [0.0] * EMBED_DIM
    result = client.models.embed_content(
        model=EMBED_MODEL,
        contents=text,
        config=_embed_config(task_type),
    )
    return list(result.embeddings[0].values)


def embed_batch(texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT",
                retries: int = 3, sleep: float = 1.5) -> List[List[float]]:
    """
    Embed a list of strings in one call. Default task_type is RETRIEVAL_DOCUMENT
    because embed_batch is mainly used at index-build time for medicine docs.
    """
    client = _get_client()
    cleaned = [(t or "").strip() or " " for t in texts]
    last_err = None
    for attempt in range(retries):
        try:
            result = client.models.embed_content(
                model=EMBED_MODEL,
                contents=cleaned,
                config=_embed_config(task_type),
            )
            return [list(e.values) for e in result.embeddings]
        except Exception as e:
            last_err = e
            logging.warning(f"Embedding batch failed (attempt {attempt + 1}/{retries}): {e}")
            time.sleep(sleep * (attempt + 1))
    raise RuntimeError(f"Embedding batch failed after {retries} attempts: {last_err}")
