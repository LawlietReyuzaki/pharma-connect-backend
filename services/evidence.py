"""
Evidence Sub-Agent helpers (Phase 2).

Restricts web-search grounding to a credible medical-sources allow-list,
appends numbered citations, and produces the refuse message when no
credible source is found for a query.

The route handler in routes/chatbot_routes.py wires these helpers around
Gemini's Google-Search grounding call.
"""
import re
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse


# Credible-sources allow-list (spec section 9.1).
# Matching is "host endswith one of these or equals one of these".
CREDIBLE_DOMAINS = [
    # Peer-reviewed indexes and journals
    "ncbi.nlm.nih.gov",          # PubMed, PMC
    "nejm.org",                   # New England Journal of Medicine
    "bmj.com",                    # BMJ
    "thelancet.com",              # The Lancet
    "jamanetwork.com",            # JAMA
    "cochrane.org",
    "cochranelibrary.com",

    # Reference / point-of-care
    "uptodate.com",
    "medlineplus.gov",
    "msdmanuals.com",

    # Public health agencies
    "who.int",
    "cdc.gov",
    "nih.gov",
    "fda.gov",
    "ema.europa.eu",
    "nice.org.uk",

    # Patient-facing trusted
    "mayoclinic.org",
    "nhs.uk",
]


def _host_of(url: str) -> str:
    try:
        host = (urlparse(url).hostname or "").lower()
        # strip a leading "www." so the suffix match works
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def is_credible(url: str) -> bool:
    """Subdomain-aware membership check against CREDIBLE_DOMAINS."""
    host = _host_of(url)
    if not host:
        return False
    return any(host == d or host.endswith("." + d) for d in CREDIBLE_DOMAINS)


def filter_sources(sources: List[Dict]) -> List[Dict]:
    """Keep only sources whose URL is on the allow-list. Preserves order."""
    out = []
    seen = set()
    for s in sources or []:
        url = (s or {}).get("url") or ""
        if not url or url in seen:
            continue
        if is_credible(url):
            out.append(s)
            seen.add(url)
    return out


def refuse_message(lang: str = "en") -> str:
    if lang == "ur":
        return (
            "اس سوال کے لیے ہمیں کسی مستند طبی ذریعے سے معلومات نہیں ملیں۔ "
            "براہ کرم سوال کو مختلف الفاظ میں دہرائیں یا کسی مستند ڈاکٹر سے "
            "مشورہ کریں۔"
        )
    return (
        "I couldn't find this in any of our trusted medical sources "
        "(PubMed, WHO, CDC, NIH, NICE, Mayo Clinic, NEJM, BMJ, The Lancet, "
        "JAMA, MedlinePlus, NHS, FDA, EMA, Cochrane, UpToDate, MSD Manuals). "
        "Try rephrasing your question, or consult a qualified doctor for "
        "a clinical opinion."
    )


def inject_citations(text: str, sources: List[Dict], lang: str = "en") -> str:
    """
    Append a numbered Sources section to the message.

    The model's prose may already mention publication names; we add an
    explicit, clickable list at the bottom so the citation is auditable.
    """
    if not sources:
        return text

    header = "**Sources**" if lang == "en" else "**حوالہ جات**"
    lines = [f"\n\n---\n{header}"]
    for i, s in enumerate(sources, 1):
        title = (s.get("title") or s.get("url") or "Source").strip()
        url = s.get("url") or ""
        # markdown link; frontend already uses ReactMarkdown
        lines.append(f"{i}. [{title}]({url})")
    return text.rstrip() + "\n" + "\n".join(lines)


# Soft-instruction block injected into the Gemini prompt. Gemini does not
# enforce domain restriction natively for grounded search, so we (a) ask it
# in the system prompt, (b) hard-filter the returned chunks afterward.
SOURCE_INSTRUCTION_EN = (
    "EVIDENCE-MODE RULES (CRITICAL):\n"
    "1. Prefer information from peer-reviewed medical literature, public health "
    "agencies, and established clinical references: PubMed/PMC, WHO, CDC, NIH, "
    "FDA, EMA, NICE, NEJM, BMJ, The Lancet, JAMA, Cochrane, UpToDate, "
    "MedlinePlus, Mayo Clinic, NHS, MSD Manuals.\n"
    "2. Do NOT cite blogs, social media, forums, news aggregators, ad-supported "
    "health portals, or commercial pharmacy sites.\n"
    "3. If you cannot find information from the trusted sources above, say "
    "explicitly that no credible source was found. Do not pad with general AI "
    "knowledge.\n"
    "4. Keep the answer concise. End with a one-line note that the system will "
    "append a numbered citation list."
)
SOURCE_INSTRUCTION_UR = (
    "ثبوت موڈ کے قواعد (لازمی):\n"
    "1. صرف معتبر طبی ذرائع سے معلومات استعمال کریں: PubMed، WHO، CDC، NIH، "
    "FDA، NICE، NEJM، BMJ، The Lancet، JAMA، Cochrane، UpToDate، "
    "MedlinePlus، Mayo Clinic، NHS، MSD Manuals۔\n"
    "2. بلاگ، سوشل میڈیا، خبریں یا اشتہاری طبی ویب سائٹس کا حوالہ نہ دیں۔\n"
    "3. اگر مذکورہ ذرائع سے معلومات نہ ملیں تو واضح کہیں کہ کوئی معتبر ذریعہ "
    "نہیں ملا۔ عمومی AI علم سے بات نہ بنائیں۔\n"
    "4. جواب مختصر رکھیں؛ سسٹم نیچے حوالہ جات کی فہرست خود لگائے گا۔"
)


def source_instructions(lang: str) -> str:
    return SOURCE_INSTRUCTION_UR if lang == "ur" else SOURCE_INSTRUCTION_EN


def audit_log(request_id: str, raw_sources: List[Dict], kept_sources: List[Dict]):
    raw_hosts = [_host_of((s or {}).get("url") or "") for s in raw_sources or []]
    kept_hosts = [_host_of((s or {}).get("url") or "") for s in kept_sources or []]
    dropped = [h for h in raw_hosts if h and h not in kept_hosts]
    logging.info(
        f"[req={request_id}] EvidenceAgent raw={len(raw_hosts)} "
        f"kept={len(kept_hosts)} dropped_hosts={dropped[:10]}"
    )
