"""
Interactive RAG test.

Ask a medical query (symptom, condition, or drug name) and the script will:
  1. Embed the query with task_type=RETRIEVAL_QUERY (gemini-embedding-001)
  2. Search the Chroma `medicines` collection (built from clinical_use text)
  3. Print the top-K matching medicines

This is the same retrieval path the chatbot uses (services/catalog_agent.py).
If the top results look correct, the RAG pipeline is fetching the right
medications and the chatbot will too.

Usage:
  python scripts/test_rag.py                      # interactive
  python scripts/test_rag.py "I have depression"  # single query
  python scripts/test_rag.py "fever" --top 10     # with custom K
"""
import os
import sys
import sqlite3
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))

CHROMA_DIR = os.path.join(ROOT, "data", "catalog_chroma")
DB_PATH = os.path.join(ROOT, "instance", "red_dot_pharmacy.db")
COLLECTION_NAME = "medicines"


def _setup():
    from services.embeddings import embed_one
    import chromadb
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    col = client.get_collection(COLLECTION_NAME)
    con = sqlite3.connect(DB_PATH)
    return embed_one, col, con


def _fetch_clinical_use(con, med_id: int) -> str:
    cur = con.cursor()
    cur.execute("SELECT clinical_use FROM medicines WHERE id = ?", (med_id,))
    row = cur.fetchone()
    return (row[0] if row else "") or ""


def run_query(query: str, top_k: int, embed_one, col, con,
              show_cu: bool = False, enhance: bool = False):
    print()
    print("=" * 78)
    print(f"USER QUERY:  {query!r}")
    print("=" * 78)

    search_query = query
    if enhance:
        from services.query_rewriter import enhance_query
        search_query = enhance_query(query)
        if search_query != query:
            print(f"EXPANDED  :  {search_query!r}")
            print("-" * 78)

    qvec = embed_one(search_query)  # RETRIEVAL_QUERY by default

    hits = col.query(
        query_embeddings=[qvec],
        n_results=top_k,
        include=["metadatas", "distances"],
    )

    ids = hits["ids"][0]
    mds = hits["metadatas"][0]
    dists = hits["distances"][0]

    if not ids:
        print("  (no results)")
        return

    print(f"  TOP {len(ids)} CANDIDATES (cosine similarity, higher = better match):")
    print()
    for rank, (cid, md, dist) in enumerate(zip(ids, mds, dists), start=1):
        score = 1 - dist
        name = md.get("name", "?")
        chemical = md.get("chemical", "") or "n/a"
        price = md.get("price", 0)
        status = md.get("status", "?")
        print(f"  {rank:>2}. [score {score:.3f}]  {name}")
        print(f"        chemical: {chemical}")
        print(f"        Rs.{price}   status: {status}   id: {cid}")
        if show_cu:
            cu = _fetch_clinical_use(con, int(cid))
            print(f"        clinical_use: {cu[:200]}{'...' if len(cu) > 200 else ''}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Interactive RAG retrieval test")
    parser.add_argument("query", nargs="*", help="Medical query (omit for interactive mode)")
    parser.add_argument("--top", type=int, default=5, help="How many results to show (default 5)")
    parser.add_argument("--show-cu", action="store_true",
                        help="Also print each medicine's clinical_use text")
    parser.add_argument("--enhance", action="store_true",
                        help="Expand the query with synonyms/drug-class via Gemini Flash before embedding")
    args = parser.parse_args()

    embed_one, col, con = _setup()
    count = col.count()
    print(f"Chroma index loaded: {count} medicines indexed.")
    print(f"Embedding model: gemini-embedding-001 (task_type=RETRIEVAL_QUERY for queries).")

    if args.query:
        q = " ".join(args.query)
        run_query(q, args.top, embed_one, col, con, show_cu=args.show_cu, enhance=args.enhance)
        con.close()
        return

    # Interactive
    print("Enter a medical query. Type 'q' to quit.")
    while True:
        try:
            q = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q:
            continue
        if q.lower() in ("q", "quit", "exit"):
            break
        try:
            run_query(q, args.top, embed_one, col, con, show_cu=args.show_cu, enhance=args.enhance)
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")

    con.close()
    print("bye")


if __name__ == "__main__":
    main()
