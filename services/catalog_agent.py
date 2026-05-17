"""
Catalog Sub-Agent — Phase 1 of the multi-agent rewrite.

Flow:
  1. Embed the user's message
  2. Vector-search the Chroma `medicines` collection for top-K candidates
  3. Inject candidates into a single Gemini call with structured-JSON output
  4. Validate returned ids against the candidate set
  5. Return { message, medicines, audit }

If Chroma or Gemini fails, raises CatalogAgentUnavailable so the caller can
fall back to the legacy keyword path.
"""
import os
import json
import logging
import time
from typing import Dict, List, Optional

CHROMA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "catalog_chroma",
)
COLLECTION_NAME = "medicines"
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
    def __init__(self, chroma_dir: str = CHROMA_DIR):
        self.chroma_dir = chroma_dir
        self._col = None
        self._client = None
        self._ready = False
        self._init_error: Optional[str] = None
        self._initialize()

    def _initialize(self):
        try:
            import chromadb
            from google import genai
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise RuntimeError("GEMINI_API_KEY not set")
            if not os.path.isdir(self.chroma_dir):
                raise RuntimeError(f"Chroma dir not found: {self.chroma_dir}")

            chroma_client = chromadb.PersistentClient(path=self.chroma_dir)
            self._col = chroma_client.get_collection(COLLECTION_NAME)
            if self._col.count() == 0:
                raise RuntimeError("Chroma collection is empty — run build_catalog_embeddings.py")

            self._client = genai.Client(api_key=api_key)
            self._ready = True
            logging.info(f"CatalogAgent ready — {self._col.count()} medicines indexed")
        except Exception as e:
            self._init_error = str(e)
            logging.warning(f"CatalogAgent unavailable: {e}")

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

        t0 = time.time()
        # 1. Embed query
        q_vec = embed_one(user_message)
        t_embed = time.time() - t0

        # 2. Vector search top-K
        t0 = time.time()
        hits = self._col.query(
            query_embeddings=[q_vec],
            n_results=TOP_K,
            include=["metadatas", "distances"],
        )
        t_search = time.time() - t0
        ids = hits["ids"][0] if hits.get("ids") else []
        metadatas = hits["metadatas"][0] if hits.get("metadatas") else []
        candidates = []
        for cid, md in zip(ids, metadatas):
            try:
                candidates.append({
                    "id": int(cid),
                    "name": md.get("name", ""),
                    "chemical": md.get("chemical", ""),
                    "category": md.get("category", ""),
                    "price": int(md.get("price") or 0),
                    "status": md.get("status", "in_stock"),
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
            "candidate_ids": [c["id"] for c in candidates],
            "recommended_ids": valid_ids,
            "embed_ms": int(t_embed * 1000),
            "search_ms": int(t_search * 1000),
            "llm_ms": int(t_llm * 1000),
            "mode": mode,
        }
        logging.info(
            f"[req={request_id}] CatalogAgent mode={mode} "
            f"cands={len(candidates)} rec={valid_ids} "
            f"embed_ms={audit['embed_ms']} search_ms={audit['search_ms']} llm_ms={audit['llm_ms']}"
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
