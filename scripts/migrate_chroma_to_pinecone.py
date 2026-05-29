"""
Migrate every vector from local Chroma to Pinecone.

Reads:  data/catalog_chroma/  (built earlier by build_catalog_embeddings.py)
Writes: PINECONE_INDEX (set in .env)

Pulls each vector with its metadata (name, chemical, category, price, status)
and upserts to Pinecone in batches of 100.

Run:   python scripts/migrate_chroma_to_pinecone.py
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

try:
    from tqdm import tqdm
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tqdm"])
    from tqdm import tqdm

CHROMA_DIR = os.path.join(ROOT, "data", "catalog_chroma")
INDEX_NAME = os.environ.get("PINECONE_INDEX", "reddot-medicines")
BATCH = 100


def main():
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        print("PINECONE_API_KEY not set in .env"); sys.exit(1)

    import chromadb
    from pinecone import Pinecone

    # 1. Open local Chroma
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    col = chroma_client.get_collection("medicines")
    total = col.count()
    print(f"Local Chroma: {total} vectors found.")

    if total == 0:
        print("Chroma is empty. Run build_catalog_embeddings.py first."); sys.exit(1)

    # Pull EVERYTHING out of Chroma
    print("Pulling vectors + metadata from Chroma...")
    payload = col.get(include=["embeddings", "metadatas"])
    ids = payload["ids"]
    vectors = payload["embeddings"]
    metadatas = payload["metadatas"]
    print(f"Pulled {len(ids)} records.")

    # 2. Connect to Pinecone
    pc = Pinecone(api_key=api_key)
    if INDEX_NAME not in [i.name for i in pc.list_indexes()]:
        print(f"Index '{INDEX_NAME}' not found in your Pinecone project."); sys.exit(1)
    idx = pc.Index(INDEX_NAME)
    print(f"Connected to Pinecone index '{INDEX_NAME}'.")

    # 3. Upsert in batches
    pbar = tqdm(total=len(ids), desc="upsert", unit="vec", ncols=100)
    written = 0
    for i in range(0, len(ids), BATCH):
        batch_ids = ids[i:i+BATCH]
        batch_vecs = vectors[i:i+BATCH]
        batch_mds = metadatas[i:i+BATCH]

        records = []
        for vid, vec, md in zip(batch_ids, batch_vecs, batch_mds):
            # Pinecone metadata values cannot be None — strip Nones.
            clean_md = {k: v for k, v in (md or {}).items() if v is not None}
            records.append({
                "id": str(vid),
                "values": list(vec),
                "metadata": clean_md,
            })

        try:
            idx.upsert(vectors=records)
            written += len(records)
        except Exception as e:
            print(f"\nBatch {i}-{i+len(batch_ids)} failed: {e}")
            time.sleep(2)
            continue
        pbar.update(len(records))
        pbar.set_postfix_str(f"ids {batch_ids[0]}..{batch_ids[-1]}")
    pbar.close()

    # 4. Verify
    time.sleep(2)  # give Pinecone a moment to update stats
    stats = idx.describe_index_stats()
    pine_count = stats.get("total_vector_count", 0)
    print()
    print("=" * 60)
    print(f"Pinecone now has {pine_count} vectors (we sent {written})")
    if pine_count >= written:
        print("MIGRATION SUCCESSFUL.")
    else:
        print(f"Mismatch — Pinecone reports {pine_count}, we sent {written}. May need a moment to update.")
    print("=" * 60)


if __name__ == "__main__":
    main()
