# ── RAG (inactive — uncomment to enable) ──────────────────────────────────────
# Requires: chromadb>=1.5.5, sentence-transformers>=5.3.0
# Add to pyproject.toml dependencies before use.
#
# import chromadb
# from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
# CHROMA_DIR = r"C:\Users\stelg\Documents\Rostock_Projekte\FBI\Revit_RAG\chroma_db"
# _embedding  = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
# _chroma     = chromadb.PersistentClient(path=CHROMA_DIR)
# _collection = _chroma.get_collection(name="revit_api", embedding_function=_embedding)
#
# @mcp.tool()
# def search_revit_api(query: str, n: int = 3) -> str:
#     """Search the local Revit API documentation index for classes and methods."""
#     results = _collection.query(query_texts=[query], n_results=n)
#     return "\n\n".join(results["documents"][0])


# ── Entry point ────────────────────────────────────────────────────────────────