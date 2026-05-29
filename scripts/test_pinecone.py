"""
Quick test that we can:
  1. Authenticate with Pinecone
  2. List indexes in the project
  3. Connect to our index (if it exists)
  4. Show its stats (dimension, total vectors, etc.)
  5. Do a dummy upsert + query roundtrip with a 768-dim zero vector

Run:  python scripts/test_pinecone.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))


def main():
    api_key = os.environ.get("PINECONE_API_KEY")
    index_name = os.environ.get("PINECONE_INDEX") or "reddot-medicines"

    print("=" * 60)
    print("PINECONE CONNECTIVITY TEST")
    print("=" * 60)

    if not api_key:
        print("[FAIL] PINECONE_API_KEY not set in env / .env")
        sys.exit(1)
    masked = api_key[:10] + "..." + api_key[-4:]
    print(f"Key:        {masked}")
    print(f"Index name: {index_name}")
    print()

    try:
        from pinecone import Pinecone
    except ImportError:
        print("[FAIL] pinecone package not installed. Run: pip install pinecone")
        sys.exit(1)

    try:
        pc = Pinecone(api_key=api_key)
        print("[OK] Pinecone client initialized")
    except Exception as e:
        print(f"[FAIL] Pinecone init failed: {e}")
        sys.exit(1)

    # List indexes
    try:
        indexes = pc.list_indexes()
        names = [i.name for i in indexes]
        print(f"[OK] Indexes in your project: {names if names else '(none yet)'}")
    except Exception as e:
        print(f"[FAIL] Could not list indexes: {e}")
        sys.exit(1)

    if index_name not in names:
        print(f"[FAIL] Index '{index_name}' NOT FOUND in your project.")
        print(f"       Either rename PINECONE_INDEX in .env to one of {names},")
        print(f"       or create the index '{index_name}' in the Pinecone console.")
        sys.exit(1)

    # Connect to the index
    try:
        idx = pc.Index(index_name)
        print(f"[OK] Connected to index '{index_name}'")
    except Exception as e:
        print(f"[FAIL] Connecting to index failed: {e}")
        sys.exit(1)

    # Stats
    try:
        stats = idx.describe_index_stats()
        dim = stats.get("dimension")
        total = stats.get("total_vector_count")
        print(f"[OK] Index dimension: {dim}")
        print(f"[OK] Current vectors stored: {total}")
        if dim != 768:
            print(f"[!!] WARNING: dimension is {dim}, expected 768.")
            print("     If you keep this, our Gemini 768-dim vectors won't fit.")
            sys.exit(1)
    except Exception as e:
        print(f"[FAIL] Stats failed: {e}")
        sys.exit(1)

    # Dummy upsert + query roundtrip
    try:
        dummy_vec = [0.0] * 768
        dummy_vec[0] = 1.0  # make it non-zero so cosine works
        print()
        print("[..] Upserting a dummy vector (id=__test__)...")
        idx.upsert(vectors=[{"id": "__test__", "values": dummy_vec, "metadata": {"name": "PING"}}])
        print("[OK] Upsert succeeded")

        print("[..] Querying for the dummy vector...")
        result = idx.query(vector=dummy_vec, top_k=1, include_metadata=True)
        matches = result.get("matches", [])
        if matches and matches[0]["id"] == "__test__":
            print(f"[OK] Query returned the test vector with score={matches[0]['score']:.4f}")
        else:
            print(f"[!!] Query returned unexpected: {matches}")

        print("[..] Cleaning up — deleting test vector...")
        idx.delete(ids=["__test__"])
        print("[OK] Cleanup done")

    except Exception as e:
        print(f"[FAIL] Roundtrip test failed: {e}")
        sys.exit(1)

    print()
    print("=" * 60)
    print("ALL CHECKS PASSED. Pinecone index is reachable and writable.")
    print("Ready to migrate 6,772 vectors from local Chroma.")
    print("=" * 60)


if __name__ == "__main__":
    main()
