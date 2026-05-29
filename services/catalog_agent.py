"""
Catalog Sub-Agent — Phase 1 of the multi-agent rewrite.

Flow (RAG, no SQL keyword grep):
  1. Enhance the user's message via Gemini Flash (synonyms, drug class, generics)
  2. Embed the enhanced query (Gemini gemini-embedding-001, RETRIEVAL_QUERY)
  3. Vector-search Pinecone index `reddot-medicines` for top-K candidates
  4. Pull full medicine rows from the DB for the candidate IDs
  5. Send candidates to a Gemini LLM ranker with structured-JSON output
  6. Validate returned ids against the candidate set
  7. Return { message, medicines, audit }
"""
import os
import json
import logging
import time
from typing import Dict, List, Optional

PINECONE_INDEX = os.getenv("PINECONE_INDEX", "reddot-medicines")
TOP_K = 50
MAX_RECOMMENDED = 4
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


class CatalogAgentUnavailable(Exception):
    pass


_agent_singleton: Optional["CatalogAgent"] = None


def get_agent() -> "CatalogAgent":
    global _agent_singleton
    if _agent_singleton is None:
        _agent_singleton = CatalogAgent()
    return _agent_singleton


class CatalogAgent:
    def __init__(self, index_name: str = PINECONE_INDEX):
        self.index_name = index_name
        self._index = None
        self._client = None
        self._ready = False
        self._init_error: Optional[str] = None
        self._initialize()

    def _initialize(self):
        try:
            from google import genai
            from pinecone import Pinecone

            gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if not gemini_key:
                raise RuntimeError("GEMINI_API_KEY not set")
            pine_key = os.environ.get("PINECONE_API_KEY")
            if not pine_key:
                raise RuntimeError("PINECONE_API_KEY not set")

            self._client = genai.Client(api_key=gemini_key)

            pc = Pinecone(api_key=pine_key)
            names = [i.name for i in pc.list_indexes()]
            if self.index_name not in names:
                raise RuntimeError(
                    f"Pinecone index '{self.index_name}' missing. "
                    f"Available: {names}"
                )
            self._index = pc.Index(self.index_name)

            stats = self._index.describe_index_stats()
            count = stats.get("total_vector_count", 0)
            dim = stats.get("dimension", 0)
            if count == 0:
                raise RuntimeError(
                    f"Pinecone index '{self.index_name}' is empty. "
                    "Run scripts/migrate_chroma_to_pinecone.py first."
                )

            self._ready = True
            logging.info(f"CatalogAgent ready — Pinecone '{self.index_name}' has {count} vectors (dim={dim})")
        except Exception as e:
            self._init_error = str(e)
            logging.warning(f"CatalogAgent not ready yet: {e}")

    @property
    def is_ready(self) -> bool:
        return self._ready

    def recommend(
        self,
        user_message: str,
        lang: str = "en",
        mode: str = "patient",
        pharmacy_name: str = "Red Dot Pharmacy",
        request_id: str = "-",
    ) -> Dict:
        if not self._ready:
            raise CatalogAgentUnavailable(self._init_error or "agent not ready")

        from services.embeddings import embed_one
        from services.medicine_rag import format_medicine_response
        from services.query_rewriter import enhance_query

        # 1. Enhance the user query (expand with synonyms / drug classes / generics)
        t0 = time.time()
        enhanced = enhance_query(user_message)
        t_enhance = time.time() - t0

        # 2. Embed the ENHANCED query
        t0 = time.time()
        q_vec = embed_one(enhanced)
        t_embed = time.time() - t0

        # 3. Vector search top-K in Pinecone
        t0 = time.time()
        result = self._index.query(
            vector=q_vec,
            top_k=TOP_K,
            include_metadata=True,
        )
        t_search = time.time() - t0

        matches = result.get("matches", []) or []
        candidates = []
        for m in matches:
            try:
                md = m.get("metadata") or {}
                candidates.append({
                    "id": int(m["id"]),
                    "name": md.get("name", ""),
                    "chemical": md.get("chemical", ""),
                    "category": md.get("category", ""),
                    "price": int(md.get("price") or 0),
                    "status": md.get("status", "in_stock"),
                    "score": float(m.get("score") or 0.0),
                })
            except Exception:
                continue

        if not candidates:
            return {
                "message": self._no_results_message(lang),
                "medicines": [],
                "audit": {
                    "request_id": request_id,
                    "candidate_ids": [],
                    "recommended_ids": [],
                    "enhance_ms": int(t_enhance * 1000),
                    "embed_ms": int(t_embed * 1000),
                    "search_ms": int(t_search * 1000),
                    "llm_ms": 0,
                },
            }

        # 3. Build prompt
        prompt = self._build_prompt(user_message, candidates, lang, mode, pharmacy_name)

        # 4. Structured LLM call
        t0 = time.time()
        message, recommended_ids = self._call_llm(prompt, lang)
        t_llm = time.time() - t0

        # 5. Validate ids
        candidate_id_set = {c["id"] for c in candidates}
        valid_ids = []
        seen = set()
        for rid in recommended_ids[:MAX_RECOMMENDED]:
            if rid in candidate_id_set and rid not in seen:
                valid_ids.append(rid)
                seen.add(rid)

        # 6. Fetch full data for recommended ids only
        try:
            from app import db  # noqa
            from models import Medicine
            chosen = Medicine.query.filter(Medicine.id.in_(valid_ids)).all() if valid_ids else []
            medicines_for_response = [self._medicine_to_dict(m) for m in chosen]
            medicines_formatted = format_medicine_response(medicines_for_response, lang)
        except Exception as e:
            logging.warning(f"[req={request_id}] DB fetch for ids {valid_ids} failed: {e}")
            medicines_formatted = []

        audit = {
            "request_id": request_id,
            "enhanced_query": enhanced if enhanced != user_message else None,
            "candidate_ids": [c["id"] for c in candidates],
            "recommended_ids": valid_ids,
            "enhance_ms": int(t_enhance * 1000),
            "embed_ms": int(t_embed * 1000),
            "search_ms": int(t_search * 1000),
            "llm_ms": int(t_llm * 1000),
            "mode": mode,
        }
        logging.info(
            f"[req={request_id}] CatalogAgent mode={mode} "
            f"cands={len(candidates)} rec={valid_ids} "
            f"enhance_ms={audit['enhance_ms']} embed_ms={audit['embed_ms']} "
            f"search_ms={audit['search_ms']} llm_ms={audit['llm_ms']}"
        )

        return {
            "message": message,
            "medicines": medicines_formatted,
            "audit": audit,
        }

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _medicine_to_dict(m) -> dict:
        return {
            "id": m.id,
            "name": m.name,
            "price": m.price,
            "chemical": m.chemical or "",
            "ingredients": m.chemical or "",
            "description": m.description or "",
            "category": m.category or "",
            "form": m.category or "",
            "image": m.image_path or "",
            "status": m.status or "in_stock",
            "stock_quantity": m.stock_quantity or 0,
        }

    def _build_prompt(
        self,
        user_message: str,
        candidates: List[dict],
        lang: str,
        mode: str,
        pharmacy_name: str,
    ) -> str:
        role_block = self._role_block(mode, lang, pharmacy_name)
        candidate_lines = "\n".join(
            f"[ID {c['id']}] {c['name']} | {c['chemical'] or 'n/a'} | "
            f"{c['category'] or 'n/a'} | Rs.{c['price']} | {c['status']}"
            for c in candidates
        )
        lang_instruction = (
            "Respond in Urdu (Urdu script, not Roman Urdu) inside the 'message' field."
            if lang == "ur"
            else "Respond in English inside the 'message' field."
        )

        return f"""{role_block}

RESPONSE FORMAT (CRITICAL):
You MUST respond with ONLY a valid JSON object matching this exact schema:
{{
  "message": "<your reply text — markdown allowed>",
  "recommended_ids": [<list of integer IDs you actually recommend, in ranked order>]
}}

RECOMMENDATION RULES:
- recommended_ids MUST be chosen ONLY from the CATALOG CANDIDATES below.
- NEVER invent IDs. Never pick an ID that is not in the list below.
- Pick at most {MAX_RECOMMENDED} medicines that GENUINELY match the user's actual medical need.
- If no candidate truly fits the user's need (e.g. user asked about depression but only asthma drugs are in the list), return recommended_ids: [] and explain in the message that the pharmacy does not currently stock something appropriate.
- Skip candidates whose chemical / category is clinically unrelated to the user's query, even if their text matched.
- Skip out_of_stock items unless the user explicitly asks for them.
- For greetings, general chat, or clarifying-question turns: return recommended_ids: [] and respond conversationally.
- For symptoms that need a clinician (chest pain, suicidal ideation, severe bleeding, etc.): say so in the message and return recommended_ids: [] — the system will trigger emergency flow separately.
- {lang_instruction}

CATALOG CANDIDATES (top {len(candidates)} by semantic similarity to the user's query):
{candidate_lines}

USER QUERY: {user_message}

JSON RESPONSE:"""

    @staticmethod
    def _role_block(mode: str, lang: str, pharmacy_name: str) -> str:
        if mode == "pharmacist":
            return (
                f"You are a clinical pharmacist AI consultant for {pharmacy_name}. "
                "Provide clinical reference for pharmacy staff — drug classes, "
                "interactions, indications, and counseling points. Be precise and "
                "concise. You are NOT speaking to a patient."
            )
        return (
            f"You are a friendly Medical Consultant AI for {pharmacy_name}. "
            "You help patients understand their symptoms and recommend medicines "
            "from the pharmacy's stock. Keep replies short (3-6 sentences), warm, "
            "and direct. You can suggest possible conditions but never give a "
            "definitive diagnosis. For serious symptoms recommend seeing a doctor."
        )

    def _call_llm(self, prompt: str, lang: str):
        from google.genai import types as genai_types

        schema = {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "recommended_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                },
            },
            "required": ["message", "recommended_ids"],
        }

        config = genai_types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            max_output_tokens=1024,
            temperature=0.4,
        )

        response = self._client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=config,
        )

        raw = (response.text or "").strip()
        if not raw:
            raise CatalogAgentUnavailable("Empty LLM response")

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            logging.error(f"LLM returned non-JSON: {raw[:300]} | err={e}")
            raise CatalogAgentUnavailable(f"LLM JSON parse failed: {e}")

        message = (parsed.get("message") or "").strip()
        rec = parsed.get("recommended_ids") or []
        if not isinstance(rec, list):
            rec = []
        rec_ints = []
        for r in rec:
            try:
                rec_ints.append(int(r))
            except Exception:
                continue
        if not message:
            message = self._fallback_message(lang)
        return message, rec_ints

    @staticmethod
    def _no_results_message(lang: str) -> str:
        if lang == "ur":
            return (
                "معذرت، ابھی میں مناسب دوا تلاش نہیں کر سکا۔ براہ کرم تفصیل بتائیں "
                "یا فارمیسی پر تشریف لائیں۔"
            )
        return (
            "I'm not able to find an appropriate medicine right now. "
            "Could you share a bit more about your symptoms, or feel free to visit "
            "the pharmacy so our team can help directly."
        )

    @staticmethod
    def _fallback_message(lang: str) -> str:
        if lang == "ur":
            return "معذرت، میں اس وقت جواب نہیں دے سکا۔ دوبارہ کوشش کریں۔"
        return "Sorry, I couldn't generate a response. Please try again."
