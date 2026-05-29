"""
Interactive RAG test running against PINECONE (cloud vector store).

Same flow as scripts/test_rag.py but the vector search hits Pinecone
instead of local Chroma. This proves the production path works.

Flow:
  1. Embed the user query (Gemini gemini-embedding-001, RETRIEVAL_QUERY)
  2. Optionally expand the query (Gemini Flash) when --enhance is set
  3. Pinecone.query(top_k=K)
  4. Print the top matches

Usage:
  python scripts/test_rag_pinecone.py                          # interactive
  python scripts/test_rag_pinecone.py "I have depression"      # single query
  python scripts/test_rag_pinecone.py "fever" --top 10 --enhance
"""
import os
import sys
import argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT, ".env"))


def _setup():
    from services.embeddings import embed_one
    from pinecone import Pinecone

    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        print("PINECONE_API_KEY not set in .env"); sys.exit(1)
    index_name = os.environ.get("PINECONE_INDEX", "reddot-medicines")
    pc = Pinecone(api_key=api_key)
    if index_name not in [i.name for i in pc.list_indexes()]:
        print(f"Index '{index_name}' missing in Pinecone project."); sys.exit(1)
    idx = pc.Index(index_name)
    return embed_one, idx, index_name


def run_query(query: str, top_k: int, embed_one, idx,
              enhance: bool = False):
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

    qvec = embed_one(search_query)  # task_type=RETRIEVAL_QUERY

    result = idx.query(
        vector=qvec,
        top_k=top_k,
        include_metadata=True,
    )

    matches = result.get("matches", [])
    if not matches:
        print("  (no matches)")
        return

    print(f"  TOP {len(matches)} from Pinecone (cosine score, higher = better):")
    print()
    for rank, m in enumerate(matches, start=1):
        md = m.get("metadata") or {}
        print(f"  {rank:>2}. [score {m['score']:.3f}]  {md.get('name', '?')}")
        print(f"        chemical: {md.get('chemical') or 'n/a'}")
        print(f"        Rs.{md.get('price', 0)}   status: {md.get('status', '?')}   id: {m['id']}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Interactive RAG test against Pinecone")
    parser.add_argument("query", nargs="*", help="Medical query (omit for interactive)")
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--enhance", action="store_true",
                        help="Expand the query via Gemini Flash before embedding")
    args = parser.parse_args()

    embed_one, idx, index_name = _setup()
    stats = idx.describe_index_stats()
    print(f"Pinecone index: '{index_name}'")
    print(f"  dimension:   {stats.get('dimension')}")
    print(f"  vectors in:  {stats.get('total_vector_count')}")
    print(f"  embedding:   gemini-embedding-001 (RETRIEVAL_QUERY for queries)")

    if args.query:
        run_query(" ".join(args.query), args.top, embed_one, idx, enhance=args.enhance)
        return

    print("\nEnter a medical query. Type 'q' to quit.")
    while True:
        try:
            q = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print(); break
        if not q:
            continue
        if q.lower() in ("q", "quit", "exit"):
            break
        try:
            run_query(q, args.top, embed_one, idx, enhance=args.enhance)
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")
    print("bye")


if __name__ == "__main__":
    main()
