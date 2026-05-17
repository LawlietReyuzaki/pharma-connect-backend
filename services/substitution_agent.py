"""
Substitution Sub-Agent — Phase 4.

When a requested medication is out of stock (or not stocked at all), this
agent returns therapeutic alternatives from in-stock SKUs:

  - exact_equivalents     same active ingredient (and ideally same strength)
  - class_alternatives    different molecule but same drug class
                          (LABELLED "requires prescriber approval")

Retrieval pipeline:
  1. Look up the requested drug in the catalog by fuzzy name match.
     If found, take its `chemical` field as the ground truth.
     If not found, ask Gemini for the active ingredient (knowledge-only,
     not grounded — used only as a search seed).
  2. SQL search: in-stock medicines where chemical contains the requested
     active ingredient → exact equivalents (always safe).
  3. Vector search via CatalogAgent on the requested drug + "alternative"
     to find class-alternative candidates.
  4. Single Gemini structured-JSON call that classifies the candidates
     into the two buckets and produces a pharmacist-friendly summary.
"""
import os
import json
import logging
import time
import re
from typing import Dict, List, Optional

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.3"))


class SubstitutionAgentUnavailable(Exception):
    pass


_agent_singleton: Optional["SubstitutionAgent"] = None


def get_agent() -> "SubstitutionAgent":
    global _agent_singleton
    if _agent_singleton is None:
        _agent_singleton = SubstitutionAgent()
    return _agent_singleton


class SubstitutionAgent:
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
            logging.info("SubstitutionAgent ready")
        except Exception as e:
            self._init_error = str(e)
            logging.warning(f"SubstitutionAgent unavailable: {e}")

    @property
    def is_ready(self) -> bool:
        return self._ready

    # ------------------------------------------------------------ public entry

    def find_alternatives(
        self,
        requested_medicine: str,
        lang: str = "en",
        pharmacy_name: str = "Red Dot Pharmacy",
        request_id: str = "-",
    ) -> Dict:
        if not self._ready:
            raise SubstitutionAgentUnavailable(self._init_error or "agent not ready")

        # 1. Resolve the requested medicine's active ingredient.
        requested_record, requested_chemical = self._resolve_requested(requested_medicine)

        # 2. Exact-equivalent candidates via SQL chemical-LIKE.
        sql_candidates = self._chemical_sql_candidates(requested_chemical, exclude_id=(requested_record.id if requested_record else None))

        # 3. Class-alternative candidates via the existing Chroma vector index.
        vector_candidates = self._vector_candidates(
            query=f"{requested_medicine} alternative substitute therapeutic class",
            exclude_ids={c["id"] for c in sql_candidates},
        )

        all_candidates = sql_candidates + vector_candidates
        if not all_candidates:
            return self._no_alternative_response(requested_medicine, lang, request_id)

        # 4. LLM classification call.
        t0 = time.time()
        parsed = self._call_llm(
            requested_medicine=requested_medicine,
            requested_chemical=requested_chemical,
            candidates=all_candidates,
            lang=lang,
            pharmacy_name=pharmacy_name,
        )
        t_llm = time.time() - t0

        exact_ids = self._sanitize_ids(parsed.get("exact_equivalents", []), all_candidates)
        class_ids = self._sanitize_ids(parsed.get("class_alternatives", []), all_candidates)
        # If LLM put the same id in both lists, exact wins.
        class_ids = [i for i in class_ids if i not in set(exact_ids)]

        # 5. Hydrate to full medicine rows.
        exact_meds = self._hydrate(exact_ids, substitution_type="exact")
        class_meds = self._hydrate(class_ids, substitution_type="class_alternative")
        merged = exact_meds + class_meds

        message = parsed.get("message") or self._fallback_message(requested_medicine, lang)

        audit = {
            "request_id": request_id,
            "requested": requested_medicine,
            "requested_chemical": requested_chemical,
            "sql_candidates": [c["id"] for c in sql_candidates],
            "vector_candidates": [c["id"] for c in vector_candidates],
            "exact_ids": exact_ids,
            "class_ids": class_ids,
            "llm_ms": int(t_llm * 1000),
        }
        logging.info(
            f"[req={request_id}] SubstitutionAgent req='{requested_medicine}' "
            f"chemical='{requested_chemical}' exact={exact_ids} class={class_ids} llm_ms={audit['llm_ms']}"
        )

        return {
            "message": message,
            "medicines": merged,
            "requested": {
                "name": requested_medicine,
                "chemical": requested_chemical or "",
                "in_catalog": requested_record is not None,
                "in_stock": bool(requested_record and (requested_record.status or "in_stock") == "in_stock"),
            },
            "exact_count": len(exact_meds),
            "class_count": len(class_meds),
            "audit": audit,
        }

    # ----------------------------------------------------------------- helpers

    def _resolve_requested(self, requested_medicine: str):
        """
        Returns (Medicine|None, chemical_string).
        Strategy:
          a) try exact-name ilike
          b) try chemical-substring ilike
          c) fall back to asking Gemini for the active ingredient
        """
        try:
            from models import Medicine
            stripped = re.sub(r"\b(\d+\s*(mg|ml|mcg|g|iu))\b", "", requested_medicine, flags=re.I).strip()
            stripped = stripped or requested_medicine

            med = (Medicine.query
                   .filter(Medicine.name.ilike(f"%{stripped}%"))
                   .order_by(Medicine.id.asc())
                   .first())
            if med:
                return med, (med.chemical or stripped)

            med = (Medicine.query
                   .filter(Medicine.chemical.ilike(f"%{stripped}%"))
                   .order_by(Medicine.id.asc())
                   .first())
            if med:
                return med, (med.chemical or stripped)
        except Exception as e:
            logging.warning(f"_resolve_requested DB lookup failed: {e}")

        # Knowledge fallback — Gemini suggests the active ingredient.
        chem = self._ask_chemical(requested_medicine)
        return None, (chem or requested_medicine)

    def _ask_chemical(self, drug_name: str) -> Optional[str]:
        try:
            from google.genai import types as genai_types
            schema = {
                "type": "object",
                "properties": {"active_ingredient": {"type": "string"}},
                "required": ["active_ingredient"],
            }
            prompt = (
                "What is the primary active ingredient (chemical / generic name) of the medicine "
                f"'{drug_name}'? Reply with ONLY a JSON object: "
                '{"active_ingredient": "<single generic name, no brand>"}. '
                "If you do not know with confidence, return an empty string."
            )
            response = self._client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    max_output_tokens=80,
                    temperature=0.1,
                ),
            )
            data = json.loads(response.text or "{}")
            chem = (data.get("active_ingredient") or "").strip()
            return chem or None
        except Exception as e:
            logging.warning(f"_ask_chemical failed for '{drug_name}': {e}")
            return None

    def _chemical_sql_candidates(self, chemical: Optional[str], exclude_id: Optional[int] = None) -> List[dict]:
        if not chemical:
            return []
        try:
            from models import Medicine
            # take the first whitespace-separated token to broaden the LIKE (e.g. "Paracetamol 500mg" -> "Paracetamol")
            head = chemical.split(",")[0].split()[0]
            q = (Medicine.query
                 .filter(Medicine.chemical.ilike(f"%{head}%"))
                 .filter(Medicine.status == "in_stock"))
            if exclude_id:
                q = q.filter(Medicine.id != exclude_id)
            rows = q.limit(20).all()
            return [self._row_to_candidate(r) for r in rows]
        except Exception as e:
            logging.warning(f"_chemical_sql_candidates failed: {e}")
            return []

    def _vector_candidates(self, query: str, exclude_ids: set) -> List[dict]:
        try:
            from services.catalog_agent import get_agent as _get_catalog_agent
            catalog = _get_catalog_agent()
            if not catalog.is_ready:
                return []
            # Reuse the Chroma collection directly.
            from services.embeddings import embed_one
            q_vec = embed_one(query)
            hits = catalog._col.query(  # noqa: protected access — same module family
                query_embeddings=[q_vec],
                n_results=30,
                include=["metadatas"],
            )
            ids = hits["ids"][0] if hits.get("ids") else []
            metadatas = hits["metadatas"][0] if hits.get("metadatas") else []
            out = []
            for cid, md in zip(ids, metadatas):
                try:
                    iid = int(cid)
                    if iid in exclude_ids:
                        continue
                    if (md.get("status") or "in_stock") != "in_stock":
                        continue
                    out.append({
                        "id": iid,
                        "name": md.get("name", ""),
                        "chemical": md.get("chemical", ""),
                        "category": md.get("category", ""),
                        "price": int(md.get("price") or 0),
                        "status": md.get("status", "in_stock"),
                    })
                except Exception:
                    continue
            return out[:20]
        except Exception as e:
            logging.warning(f"_vector_candidates failed: {e}")
            return []

    @staticmethod
    def _row_to_candidate(r) -> dict:
        return {
            "id": r.id,
            "name": r.name,
            "chemical": r.chemical or "",
            "category": r.category or "",
            "price": r.price or 0,
            "status": r.status or "in_stock",
        }

    def _call_llm(
        self,
        requested_medicine: str,
        requested_chemical: Optional[str],
        candidates: List[dict],
        lang: str,
        pharmacy_name: str,
    ):
        from google.genai import types as genai_types

        lang_instruction = (
            "Respond in Urdu (Urdu script) inside the 'message' field."
            if lang == "ur" else
            "Respond in English inside the 'message' field."
        )
        candidate_lines = "\n".join(
            f"[ID {c['id']}] {c['name']} | {c['chemical'] or 'n/a'} | "
            f"{c['category'] or 'n/a'} | Rs.{c['price']} | {c['status']}"
            for c in candidates
        )

        schema = {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "exact_equivalents": {"type": "array", "items": {"type": "integer"}},
                "class_alternatives": {"type": "array", "items": {"type": "integer"}},
            },
            "required": ["message", "exact_equivalents", "class_alternatives"],
        }

        prompt = f"""You are a clinical pharmacist substitution AI at {pharmacy_name}.

REQUESTED MEDICATION (out of stock or being verified):
  Name: {requested_medicine}
  Active ingredient (best guess): {requested_chemical or 'unknown'}

CANDIDATE IN-STOCK MEDICINES FROM OUR PHARMACY:
{candidate_lines}

CLASSIFY each candidate ID into ONE of:
  - exact_equivalents     : same active ingredient as the requested drug
                            (different brand / size is OK; flag big strength
                            differences in the message).
  - class_alternatives    : DIFFERENT molecule but same drug class
                            (e.g. Paracetamol -> Ibuprofen for fever).
                            Class alternatives require prescriber approval.

If a candidate fits neither bucket, omit it.
Output exact_equivalents in ranked order (best match first).
Output class_alternatives in ranked order.

In 'message' (markdown allowed):
  - 1-2 sentences identifying the active ingredient of the requested drug.
  - If exact_equivalents is non-empty: list them by name & price.
  - If only class_alternatives exist: state clearly that no exact equivalent
    is in stock and that class alternatives require prescriber approval before
    substitution.
  - If both lists are empty: say no acceptable substitute is in stock and
    suggest visiting the pharmacy or consulting a doctor.

{lang_instruction}

JSON RESPONSE:"""

        response = self._client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                max_output_tokens=1200,
                temperature=GEMINI_TEMPERATURE,
            ),
        )
        raw = (response.text or "").strip()
        if not raw:
            raise SubstitutionAgentUnavailable("Empty LLM response")
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            logging.error(f"SubstitutionAgent JSON parse failed: {raw[:300]} | err={e}")
            raise SubstitutionAgentUnavailable(f"JSON parse failed: {e}")

    @staticmethod
    def _sanitize_ids(ids, candidates: List[dict]) -> List[int]:
        valid = {c["id"] for c in candidates}
        out: List[int] = []
        seen = set()
        for i in ids or []:
            try:
                iid = int(i)
            except Exception:
                continue
            if iid in valid and iid not in seen:
                out.append(iid)
                seen.add(iid)
        return out

    def _hydrate(self, ids: List[int], substitution_type: str) -> List[dict]:
        if not ids:
            return []
        try:
            from models import Medicine
            from services.medicine_rag import format_medicine_response
            rows = Medicine.query.filter(Medicine.id.in_(ids)).all()
            # preserve ranked order
            by_id = {r.id: r for r in rows}
            ordered = [by_id[i] for i in ids if i in by_id]
            raw_dicts = [{
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
            } for m in ordered]
            formatted = format_medicine_response(raw_dicts, "en")
            for med in formatted:
                med["substitution_type"] = substitution_type
                if substitution_type == "class_alternative":
                    med["requires_prescriber_approval"] = True
            return formatted
        except Exception as e:
            logging.warning(f"_hydrate failed for ids {ids}: {e}")
            return []

    def _no_alternative_response(self, requested: str, lang: str, request_id: str) -> Dict:
        msg = self._fallback_message(requested, lang, hard_none=True)
        logging.info(f"[req={request_id}] SubstitutionAgent no candidates for '{requested}'")
        return {
            "message": msg,
            "medicines": [],
            "requested": {"name": requested, "chemical": "", "in_catalog": False, "in_stock": False},
            "exact_count": 0,
            "class_count": 0,
            "audit": {"request_id": request_id, "requested": requested, "no_candidates": True},
        }

    @staticmethod
    def _fallback_message(requested: str, lang: str, hard_none: bool = False) -> str:
        if lang == "ur":
            if hard_none:
                return (
                    f"معذرت، '{requested}' کا کوئی متبادل ابھی ہمارے سٹاک میں موجود نہیں۔ "
                    "براہ کرم فارمیسی تشریف لائیں یا ڈاکٹر سے مشورہ کریں۔"
                )
            return f"'{requested}' کے ممکنہ متبادل کی فہرست نیچے دی گئی ہے۔"
        if hard_none:
            return (
                f"We don't currently have a suitable substitute for **{requested}** in stock. "
                "Please visit the pharmacy in person or consult a doctor for an alternative."
            )
        return f"Possible substitutes for **{requested}** are listed below."
