"""
Image Retrieval Sub-Agent — Phase 5.

For queries about visually identifiable conditions (rashes, lesions,
radiology findings, eye conditions, etc.) the agent returns structured
"image references" — links into credible medical image repositories.

Pragmatic v1: we DO NOT scrape or rehost images. We return curated source
page links so the user lands on a licensed image viewer at the upstream
site. The allow-list restricts these to medically-credible repositories.

Implementation:
  - Reuses Gemini google.genai SDK + GoogleSearch grounding (same SDK
    pattern already used for Phases 2 Evidence and 1 Catalog calls).
  - Asks the LLM to identify 2-4 distinguishable conditions and return
    structured image references per condition.
  - Hard-filters returned URLs against IMAGE_DOMAINS allow-list.
  - If no allow-listed URL survives, returns an explicit "no image source
    available" message per FR-9 (never fabricate).
"""
import os
import re
import json
import logging
import time
from typing import Dict, List, Optional
from urllib.parse import urlparse, urljoin

try:
    import urllib.request as _urllib_request  # stdlib — no extra dependency
except Exception:
    _urllib_request = None

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.4"))

# Medical-image allow-list (Phase 5 / spec section 9.2).
# Matching is "host endswith one of these or equals one of these".
IMAGE_DOMAINS = [
    "dermnetnz.org",            # dermatology
    "radiopaedia.org",           # radiology
    "phil.cdc.gov",              # CDC Public Health Image Library
    "cdc.gov",                   # CDC general (image-rich pages)
    "ncbi.nlm.nih.gov",          # PMC figures
    "who.int",                   # WHO image library
    "nih.gov",                   # NIH visual references
    "msdmanuals.com",            # MSD manuals - figures embedded
    "mayoclinic.org",
    "medlineplus.gov",
    "nhs.uk",
    "aao.org",                   # American Academy of Ophthalmology
    "eyewiki.aao.org",           # AAO EyeWiki
]


class ImageAgentUnavailable(Exception):
    pass


_agent_singleton: Optional["ImageAgent"] = None


def get_agent() -> "ImageAgent":
    global _agent_singleton
    if _agent_singleton is None:
        _agent_singleton = ImageAgent()
    return _agent_singleton


def _host_of(url: str) -> str:
    try:
        host = (urlparse(url).hostname or "").lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def is_image_credible(url: str) -> bool:
    host = _host_of(url)
    if not host:
        return False
    return any(host == d or host.endswith("." + d) for d in IMAGE_DOMAINS)


class ImageAgent:
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
            logging.info("ImageAgent ready")
        except Exception as e:
            self._init_error = str(e)
            logging.warning(f"ImageAgent unavailable: {e}")

    @property
    def is_ready(self) -> bool:
        return self._ready

    def find_images(
        self,
        query: str,
        lang: str = "en",
        request_id: str = "-",
    ) -> Dict:
        if not self._ready:
            raise ImageAgentUnavailable(self._init_error or "agent not ready")

        from google.genai import types as genai_types

        domain_list = ", ".join(IMAGE_DOMAINS)
        lang_block = (
            "Respond in Urdu in the 'message' field. Captions remain in English."
            if lang == "ur" else
            "Respond in English."
        )

        prompt = f"""You are a medical reference assistant. The user is trying to visually
distinguish between or look up a condition.

USER QUERY: {query}

Tasks:
1. Identify 2-4 visually distinguishable medical conditions implied by the query.
2. For each, find a reference page on one of these CREDIBLE MEDICAL IMAGE SOURCES:
   {domain_list}
3. Each reference must have a real URL on one of those domains. NEVER fabricate URLs.
4. If you cannot find a credible source for a condition, omit that condition.

RESPONSE FORMAT (CRITICAL):
Return ONLY a valid JSON object:
{{
  "message": "<short prose: which conditions you considered and what to look for visually>",
  "image_references": [
    {{
      "condition": "Condition Name",
      "distinguishing_features": "1-2 sentences on the visual signature",
      "source_title": "page title",
      "source_url": "https://...",
      "source_domain": "dermnetnz.org"
    }},
    ...
  ]
}}

RULES:
- Every source_url MUST come from the allow-list above.
- Never invent URLs. If unsure, omit.
- 2-4 references total is the target.
- {lang_block}
"""

        t0 = time.time()
        try:
            response = self._client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    tools=[genai_types.Tool(google_search=genai_types.GoogleSearch())],
                    max_output_tokens=1500,
                    temperature=GEMINI_TEMPERATURE,
                ),
            )
        except Exception as e:
            logging.error(f"[req={request_id}] ImageAgent generate_content failed: {e}")
            raise ImageAgentUnavailable(f"LLM call failed: {e}")
        t_llm = time.time() - t0

        raw = (response.text or "").strip()
        if not raw:
            raise ImageAgentUnavailable("Empty LLM response")

        # Gemini sometimes wraps JSON in markdown code fence when the search tool is enabled;
        # strip it defensively.
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
            if raw.endswith("```"):
                raw = raw[:-3].strip()

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            logging.error(f"ImageAgent JSON parse failed: {raw[:300]} | err={e}")
            raise ImageAgentUnavailable(f"JSON parse failed: {e}")

        message = (parsed.get("message") or "").strip()
        raw_refs = parsed.get("image_references") or []

        # Hard-filter against allow-list. Drop anything not credible.
        kept_refs: List[Dict] = []
        dropped: List[str] = []
        seen_urls = set()
        for ref in raw_refs:
            if not isinstance(ref, dict):
                continue
            url = (ref.get("source_url") or "").strip()
            if not url or url in seen_urls:
                continue
            if not is_image_credible(url):
                dropped.append(url)
                continue
            seen_urls.add(url)
            kept_refs.append({
                "condition": (ref.get("condition") or "").strip(),
                "distinguishing_features": (ref.get("distinguishing_features") or "").strip(),
                "source_title": (ref.get("source_title") or "").strip(),
                "source_url": url,
                "source_domain": _host_of(url),
            })

        audit = {
            "request_id": request_id,
            "raw_count": len(raw_refs),
            "kept_count": len(kept_refs),
            "dropped_urls": dropped[:5],
            "llm_ms": int(t_llm * 1000),
        }
        logging.info(
            f"[req={request_id}] ImageAgent kept={len(kept_refs)} dropped={len(dropped)} llm_ms={audit['llm_ms']}"
        )

        if not kept_refs:
            return {
                "message": self._refuse_message(lang),
                "image_references": [],
                "audit": audit,
            }

        if not message:
            message = (
                "Reference pages on visually distinguishing the conditions below."
                if lang == "en" else
                "متعلقہ بصری حالتوں کے لیے مستند طبی ذرائع نیچے دیے گئے ہیں۔"
            )

        # Try to enrich each ref with an actual image_url via og:image fetch.
        kept_refs = kept_refs[:4]
        for r in kept_refs:
            img = _fetch_og_image(r["source_url"])
            if img and is_image_credible(img):
                r["image_url"] = img
            elif img:
                # Same-host image is OK even if the absolute URL doesn't match
                # the allow-list (e.g. CDN subdomain). Use only if same registrable host root.
                src_host = _host_of(r["source_url"])
                img_host = _host_of(img)
                if src_host and img_host and (img_host == src_host or img_host.endswith("." + src_host) or src_host.endswith("." + img_host)):
                    r["image_url"] = img

        return {
            "message": message,
            "image_references": kept_refs,
            "audit": audit,
        }

    # (helper functions below module-level)

    @staticmethod
    def _refuse_message(lang: str) -> str:
        if lang == "ur":
            return (
                "اس سوال کے لیے ہمیں مستند طبی تصویری ذریعے سے کوئی صفحہ نہیں ملا۔ "
                "براہ کرم سوال کو دوبارہ مختلف الفاظ میں دہرائیں یا کسی ڈاکٹر سے رجوع کریں۔"
            )
        return (
            "I couldn't find a credible medical image reference for that query in our "
            "approved sources (DermNet NZ, Radiopaedia, CDC PHIL, MSD Manuals, "
            "Mayo Clinic, NHS, etc.). Try rephrasing the query or consult a "
            "specialist for visual confirmation."
        )


# ────────────────────────────── og:image fetcher ─────────────────────────────

_OG_IMAGE_RE = re.compile(
    r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_OG_IMAGE_RE_ALT = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
    re.IGNORECASE,
)
_TWITTER_IMAGE_RE = re.compile(
    r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)


def _fetch_og_image(page_url: str, timeout: float = 4.0) -> Optional[str]:
    """
    Best-effort extraction of the Open Graph image (or twitter:image) from a
    source page. Returns absolute URL, or None on any failure. Uses stdlib
    urllib only — no new dependency.
    """
    if not _urllib_request or not page_url:
        return None
    try:
        req = _urllib_request.Request(
            page_url,
            headers={
                "User-Agent": "Mozilla/5.0 (pharma-connect image agent)",
                "Accept": "text/html",
            },
        )
        with _urllib_request.urlopen(req, timeout=timeout) as resp:
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if "html" not in ctype:
                return None
            # Read at most 256 KB — og tags appear in <head> early on the page.
            html_bytes = resp.read(256 * 1024)
        try:
            html = html_bytes.decode("utf-8", errors="ignore")
        except Exception:
            html = html_bytes.decode("latin-1", errors="ignore")
        for pat in (_OG_IMAGE_RE, _OG_IMAGE_RE_ALT, _TWITTER_IMAGE_RE):
            m = pat.search(html)
            if m:
                img = m.group(1).strip()
                if not img:
                    continue
                # Normalise relative URLs
                if img.startswith("//"):
                    img = "https:" + img
                elif img.startswith("/"):
                    img = urljoin(page_url, img)
                return img
        return None
    except Exception as e:
        logging.debug(f"_fetch_og_image failed for {page_url}: {e}")
        return None
