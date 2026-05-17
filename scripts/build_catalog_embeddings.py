"""
Build / refresh the catalog Chroma collection from medicines_export.json.

Usage:
  python scripts/build_catalog_embeddings.py            # incremental (skip existing)
  python scripts/build_catalog_embeddings.py --rebuild  # wipe and rebuild

Reads:  medicines_export.json (committed to repo)
Writes: data/catalog_chroma/  (gitignored — baked into Docker image)
"""
import os
import sys
import json
import time
import argparse
import logging

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from services.embeddings import embed_batch, EMBED_DIM  # noqa: E402

CHROMA_DIR = os.path.join(ROOT, "data", "catalog_chroma")
SOURCE_JSON = os.path.join(ROOT, "medicines_export.json")
COLLECTION_NAME = "medicines"
BATCH = 50

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("build_catalog_embeddings")


def medicine_to_text(m: dict) -> str:
    parts = [
        m.get("name", ""),
        m.get("chemical") or "",
        m.get("category") or "",
        (m.get("description") or "")[:500],
    ]
    return " | ".join(p for p in parts if p)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true", help="Wipe existing collection")
    parser.add_argument("--only-in-stock", action="store_true", default=True)
    args = parser.parse_args()

    if not os.path.exists(SOURCE_JSON):
        log.error(f"Source file not found: {SOURCE_JSON}")
        sys.exit(1)

    with open(SOURCE_JSON, "r", encoding="utf-8") as f:
        medicines = json.load(f)
    log.info(f"Loaded {len(medicines)} medicines from {SOURCE_JSON}")

    if args.only_in_stock:
        medicines = [m for m in medicines if (m.get("status") or "in_stock") == "in_stock"]
        log.info(f"Filtered to in-stock: {len(medicines)} remain")

    os.makedirs(CHROMA_DIR, exist_ok=True)

    import chromadb
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    if args.rebuild:
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
        return

    start = time.time()
    for i in range(0, len(todo), BATCH):
        batch = todo[i:i + BATCH]
        texts = [medicine_to_text(m) for m in batch]
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


if __name__ == "__main__":
    main()
