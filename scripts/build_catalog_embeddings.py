"""
Build / refresh the catalog Chroma collection.

Reads from the SQLite/Postgres DB (medicines table) and embeds each medicine's
`clinical_use` paragraph + name + chemical. The vector store is then queried
by the RAG pipeline (services/catalog_agent.py) to fetch correct medicines for
a user query.

Usage:
  python scripts/build_catalog_embeddings.py            # incremental (skip existing)
  python scripts/build_catalog_embeddings.py --rebuild  # wipe and rebuild

Reads:  medicines table (clinical_use column)
Writes: data/catalog_chroma/  (gitignored)
"""
import os
import sys
import time
import argparse
import logging
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

from services.embeddings import embed_batch, EMBED_DIM  # noqa: E402

CHROMA_DIR = os.path.join(ROOT, "data", "catalog_chroma")
DB_PATH = os.path.join(ROOT, "instance", "red_dot_pharmacy.db")
COLLECTION_NAME = "medicines"
BATCH = 50

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("build_catalog_embeddings")


JUNK_CU_MARKERS = (
    "insufficient information",
    "consult a pharmacist for specific use",
    "consult a pharmacist.",
)


def _is_junk_cu(text: str) -> bool:
    if not text:
        return True
    t = text.lower().strip()
    return any(t.startswith(m) for m in JUNK_CU_MARKERS) or len(t) < 30


def _fetch_medicines(only_in_stock: bool = True) -> list:
    """Fetch all medicines from the local SQLite DB with clinical_use."""
    if not os.path.exists(DB_PATH):
        log.error(f"DB not found: {DB_PATH}")
        return []
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    q = "SELECT id, name, chemical, category, price, status, clinical_use FROM medicines"
    if only_in_stock:
        q += " WHERE status = 'in_stock' OR status IS NULL"
    cur.execute(q)
    rows = cur.fetchall()
    con.close()
    medicines = []
    skipped_junk = 0
    for r in rows:
        cu = r[6] or ""
        if _is_junk_cu(cu):
            skipped_junk += 1
            continue
        medicines.append({
            "id": r[0],
            "name": r[1] or "",
            "chemical": r[2] or "",
            "category": r[3] or "",
            "price": r[4] or 0,
            "status": r[5] or "in_stock",
            "clinical_use": cu,
        })
    log.info(f"Skipped {skipped_junk} rows with junk/empty clinical_use")
    return medicines


import re as _re

_NEG_RE = _re.compile(
    r"(?:^|\.\s+)\s*NOT\s+(?:used|recommended|indicated|for|prescribed)[^.]*\.",
    flags=_re.IGNORECASE,
)


def _strip_negations(text: str) -> str:
    """
    Strip 'NOT used for ...' sentences from clinical_use so embeddings don't
    contain anti-uses that would falsely match queries via the negated terms.
    The full text stays in the DB for the LLM ranker which understands negation.
    """
    if not text:
        return text
    cleaned = _NEG_RE.sub(". ", text)
    cleaned = _re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def medicine_to_embedding_text(m: dict) -> str:
    """
    Text that gets embedded for this medicine.
    Includes brand name + chemical (so brand-name queries still match).
    Then the POSITIVE part of clinical_use (NOT-FOR sentence stripped).
    """
    parts = [m.get("name", ""), m.get("chemical") or ""]
    cu = m.get("clinical_use") or ""
    if cu:
        parts.append(_strip_negations(cu))
    else:
        parts.append(m.get("category") or "")
    return " | ".join(p for p in parts if p)


def build_catalog(rebuild: bool = False, only_in_stock: bool = True) -> int:
    """
    Build / refresh the Chroma medicines collection from the DB.
    Returns: final medicine count in the collection.
    """
    medicines = _fetch_medicines(only_in_stock=only_in_stock)
    log.info(f"Loaded {len(medicines)} medicines from DB ({DB_PATH})")
    with_cu = sum(1 for m in medicines if m["clinical_use"])
    log.info(f"  with clinical_use:    {with_cu}")
    log.info(f"  without clinical_use: {len(medicines) - with_cu}")

    os.makedirs(CHROMA_DIR, exist_ok=True)

    import chromadb
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    if rebuild:
        try:
            client.delete_collection(COLLECTION_NAME)
            log.info("Wiped existing collection")
        except Exception:
            pass

    col = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    existing_ids = set(col.get(include=[])["ids"]) if col.count() else set()
    log.info(f"Collection currently has {len(existing_ids)} entries")

    todo = [m for m in medicines if str(m["id"]) not in existing_ids]
    log.info(f"To embed: {len(todo)}")

    if not todo:
        log.info("Nothing to do — collection up to date")
        return col.count()

    start = time.time()
    for i in range(0, len(todo), BATCH):
        batch = todo[i:i + BATCH]
        texts = [medicine_to_embedding_text(m) for m in batch]
        try:
            vectors = embed_batch(texts)
        except Exception as e:
            log.error(f"Batch {i}-{i + len(batch)} failed: {e}; skipping")
            continue

        col.add(
            ids=[str(m["id"]) for m in batch],
            embeddings=vectors,
            metadatas=[{
                "name": m.get("name", ""),
                "chemical": m.get("chemical") or "",
                "category": m.get("category") or "",
                "price": int(m.get("price") or 0),
                "status": m.get("status") or "in_stock",
            } for m in batch],
        )
        elapsed = time.time() - start
        done = i + len(batch)
        rate = done / elapsed if elapsed else 0
        eta = (len(todo) - done) / rate if rate else 0
        log.info(f"  {done}/{len(todo)} embedded ({rate:.1f}/s, eta {eta:.0f}s)")

    log.info(f"Done in {time.time() - start:.1f}s. Final count: {col.count()}")
    return col.count()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true", help="Wipe existing collection")
    parser.add_argument("--all", action="store_true", help="Include out-of-stock items too")
    args = parser.parse_args()
    build_catalog(rebuild=args.rebuild, only_in_stock=not args.all)


if __name__ == "__main__":
    main()
