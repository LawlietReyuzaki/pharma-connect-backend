"""
Evidence search flow — runs a Gemini google_search-grounded call and produces
a unified response with credible-source filtering and PROPER inline [N]
citations injected via grounding_supports segment indices.

Extracted from routes/chatbot_routes.py::web_search_chat so the Orchestrator
can call it as a sub-agent without going through HTTP.
"""
import os
import logging
from typing import Dict, List

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.5"))


def run_evidence_search(user_message: str, lang: str = "en", request_id: str = "-") -> Dict:
    """
    Returns:
      {
        "intent": "evidence",
        "message": "<answer with inline [1], [2], ... + Sources block>",
        "sources": [{title, url}],
        "grounded": bool,
        "evidence_only": True,
      }
    """
    from services.chatbot import (
        MEDICAL_CONSULTANT_PROMPT_EN, MEDICAL_CONSULTANT_PROMPT_UR,
        DISCLAIMER_EN, DISCLAIMER_UR,
    )
    from services.evidence import (
        filter_sources, refuse_message, source_instructions, audit_log,
        is_credible,
    )

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return {
            "intent": "evidence",
            "message": refuse_message(lang),
            "sources": [],
            "grounded": False,
            "evidence_only": True,
        }

    from google import genai as new_genai
    from google.genai import types as genai_types

    client = new_genai.Client(api_key=api_key)
    consultant_prompt = MEDICAL_CONSULTANT_PROMPT_UR if lang == "ur" else MEDICAL_CONSULTANT_PROMPT_EN
    full_prompt = (
        f"{consultant_prompt}\n\n"
        f"{source_instructions(lang)}\n\n"
        f"User: {user_message}\n\nAssistant:"
    )

    ai_message = ""
    raw_sources: List[Dict] = []
    grounding_supports = []
    grounded = False

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt,
            config=genai_types.GenerateContentConfig(
                tools=[genai_types.Tool(google_search=genai_types.GoogleSearch())],
                max_output_tokens=1024,
                temperature=GEMINI_TEMPERATURE,
            ),
        )

        ai_message = (response.text or "").strip()

        if response.candidates and response.candidates[0].grounding_metadata:
            grounded = True
            gm = response.candidates[0].grounding_metadata
            for chunk in (gm.grounding_chunks or []):
                if chunk.web:
                    raw_sources.append({
                        "title": getattr(chunk.web, "title", "") or "",
                        "url": getattr(chunk.web, "uri", "") or "",
                    })
            for sup in (gm.grounding_supports or []) or []:
                seg = getattr(sup, "segment", None)
                idxs = getattr(sup, "grounding_chunk_indices", None) or []
                if seg is not None:
                    grounding_supports.append({
                        "start": getattr(seg, "start_index", None),
                        "end": getattr(seg, "end_index", None),
                        "chunk_indices": list(idxs),
                    })
    except Exception as e:
        logging.exception(f"[req={request_id}] Evidence search Gemini call failed: {e}")
        ai_message = ""

    # Filter sources by allow-list. Build remap from original chunk index -> new 1-based citation number.
    kept_sources: List[Dict] = []
    remap = {}
    seen_urls = set()
    for orig_idx, src in enumerate(raw_sources):
        url = (src.get("url") or "").strip()
        if not url or url in seen_urls:
            continue
        if not is_credible(url):
            continue
        seen_urls.add(url)
        remap[orig_idx] = len(kept_sources) + 1   # 1-based
        kept_sources.append(src)

    audit_log(request_id, raw_sources, kept_sources)

    if not kept_sources:
        return {
            "intent": "evidence",
            "message": refuse_message(lang),
            "sources": [],
            "grounded": False,
            "evidence_only": True,
        }

    if not ai_message:
        ai_message = (
            "Credible sources are listed below."
            if lang == "en" else
            "متعلقہ مستند ذرائع نیچے دیے گئے ہیں۔"
        )

    # Inject inline [N] citations using segment end_indices.
    ai_message = _inject_inline_citations(ai_message, grounding_supports, remap)

    # Append the Sources block at the bottom (markdown).
    ai_message = _append_sources_block(ai_message, kept_sources, lang)

    disclaimer = DISCLAIMER_UR if lang == "ur" else DISCLAIMER_EN
    if DISCLAIMER_EN not in ai_message and DISCLAIMER_UR not in ai_message:
        ai_message = f"{ai_message}\n\n{disclaimer}"

    return {
        "intent": "evidence",
        "message": ai_message,
        "sources": kept_sources[:5],
        "grounded": grounded,
        "evidence_only": True,
    }


def _inject_inline_citations(text: str, supports: List[Dict], remap: Dict[int, int]) -> str:
    """
    For each grounding_support, insert citation markers like "[1]" or "[1,2]"
    at the support's end_index in the text. Indices are character offsets in
    the original Gemini response.

    Supports are processed in reverse end-index order so insertions don't
    shift the positions of earlier ones.
    """
    if not text or not supports or not remap:
        return text

    # Build a list of (end_index, [new citation numbers]) entries
    insertions = []
    for sup in supports:
        end = sup.get("end")
        if end is None:
            continue
        new_nums = []
        for ci in sup.get("chunk_indices") or []:
            mapped = remap.get(ci)
            if mapped is not None and mapped not in new_nums:
                new_nums.append(mapped)
        if not new_nums:
            continue
        insertions.append((end, new_nums))

    # Sort by end_index ascending, then merge consecutive insertions at the same offset.
    insertions.sort(key=lambda x: x[0])
    merged = []
    for end, nums in insertions:
        if merged and merged[-1][0] == end:
            for n in nums:
                if n not in merged[-1][1]:
                    merged[-1][1].append(n)
        else:
            merged.append((end, list(nums)))

    # Apply in reverse so earlier offsets remain valid.
    out = text
    for end, nums in reversed(merged):
        end = max(0, min(end, len(out)))
        marker = " " + ",".join(f"[{n}]" for n in sorted(nums))
        out = out[:end] + marker + out[end:]
    return out


def _append_sources_block(text: str, sources: List[Dict], lang: str) -> str:
    if not sources:
        return text
    header = "**Sources**" if lang == "en" else "**حوالہ جات**"
    lines = [f"\n\n---\n{header}"]
    for i, s in enumerate(sources, 1):
        title = (s.get("title") or s.get("url") or "Source").strip()
        url = s.get("url") or ""
        lines.append(f"{i}. [{title}]({url})")
    return text.rstrip() + "\n" + "\n".join(lines)
