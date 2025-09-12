# import faiss
# import json
# import numpy as np
# from sentence_transformers import SentenceTransformer

# # Paths must match Day 2 outputs
# INDEX_PATH = "knowledge_base_docs/faiss_index.bin"
# META_PATH = "knowledge_base_docs/index_meta.json"

# class RAGHelper:
#     def __init__(self):
#         self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
#         self.index = faiss.read_index(INDEX_PATH)
#         with open(META_PATH, encoding="utf-8") as f:
#             self.meta = json.load(f)

#     def search(self, query, k=3):
#         q_emb = self.model.encode([query]).astype("float32")
#         D, I = self.index.search(q_emb, k)
#         results = [self.meta[idx] for idx in I[0]]
#         return results


# # backend/rag_utils.py
# import faiss
# import json
# import numpy as np
# from sentence_transformers import SentenceTransformer
# from pathlib import Path
# from typing import List, Dict

# # Paths (match your Day 2 output)
# INDEX_PATH = Path("knowledge_base_docs/faiss_index.bin")
# META_PATH = Path("knowledge_base_docs/index_meta.json")

# class RAGHelper:
#     def __init__(self, index_path=INDEX_PATH, meta_path=META_PATH, model_name="sentence-transformers/all-MiniLM-L6-v2"):
#         if not index_path.exists() or not meta_path.exists():
#             raise FileNotFoundError(f"FAISS index or metadata not found at {index_path} / {meta_path}")

#         # load HF sentence-transformer
#         self.embed_model = SentenceTransformer(model_name)
#         # load faiss index
#         self.index = faiss.read_index(str(index_path))
#         # load metadata list [{"doc":..., "chunk":...}, ...]
#         with open(meta_path, "r", encoding="utf-8") as fh:
#             self.meta = json.load(fh)

#     def search(self, question: str, top_k: int = 3) -> List[Dict]:
#         """Return list of top_k results with {doc, chunk, text, rank, score}."""
#         q_emb = self.embed_model.encode([question]).astype("float32")
#         D, I = self.index.search(q_emb, top_k)
#         results = []
#         for rank, idx in enumerate(I[0]):
#             if idx < 0 or idx >= len(self.meta):
#                 continue
#             item = self.meta[idx]
#             results.append({
#                 "rank": rank + 1,
#                 "score": float(D[0][rank]),
#                 "doc": item.get("doc"),
#                 # some metadata used 'chunk' key for text
#                 "text": item.get("chunk", item.get("text", "")),
#                 "meta_idx": idx
#             })
#         return results

# # Export a convenience function that will lazily load the helper
# _rag_singleton = None
# def get_rag_helper():
#     global _rag_singleton
#     if _rag_singleton is None:
#         _rag_singleton = RAGHelper()
#     return _rag_singleton

# def retrieve_docs(question: str, top_k: int = 3):
#     return get_rag_helper().search(question, top_k=top_k)


# backend/rag_utils.py
import os
import faiss
import json
import numpy as np
import requests
from sentence_transformers import SentenceTransformer
from pathlib import Path
from typing import List, Dict

# Paths (match your Day 2 output)
INDEX_PATH = Path("knowledge_base_docs/faiss_index.bin")
META_PATH = Path("knowledge_base_docs/index_meta.json")

# 🔗 Set your Colab MedGemma public URL (replace ngrok link when you restart Colab)
#MEDGEMMA_URL = "MEDGEMMA_URL"

MEDGEMMA_URL = os.getenv("MEDGEMMA_URL", "https://54ee1dfbce90.ngrok-free.app/v1/medgemma/infer")


class RAGHelper:
    def __init__(self, index_path=INDEX_PATH, meta_path=META_PATH, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        if not index_path.exists() or not meta_path.exists():
            raise FileNotFoundError(f"FAISS index or metadata not found at {index_path} / {meta_path}")

        # load HF sentence-transformer
        self.embed_model = SentenceTransformer(model_name)
        # load faiss index
        self.index = faiss.read_index(str(index_path))
        # load metadata list [{"doc":..., "chunk":...}, ...]
        with open(meta_path, "r", encoding="utf-8") as fh:
            self.meta = json.load(fh)

    def search(self, question: str, top_k: int = 3) -> List[Dict]:
        """Return list of top_k results with {doc, chunk, text, rank, score}."""
        q_emb = self.embed_model.encode([question]).astype("float32")
        D, I = self.index.search(q_emb, top_k)
        results = []
        for rank, idx in enumerate(I[0]):
            if idx < 0 or idx >= len(self.meta):
                continue
            item = self.meta[idx]
            results.append({
                "rank": rank + 1,
                "score": float(D[0][rank]),
                "doc": item.get("doc"),
                # some metadata used 'chunk' key for text
                "text": item.get("chunk", item.get("text", "")),
                "meta_idx": idx
            })
        return results


# Singleton loader
_rag_singleton = None
def get_rag_helper():
    global _rag_singleton
    if _rag_singleton is None:
        _rag_singleton = RAGHelper()
    return _rag_singleton


def retrieve_docs(question: str, top_k: int = 3):
    return get_rag_helper().search(question, top_k=top_k)


# -------------------------------
# NEW: Wrapper to call MedGemma Colab API
# -------------------------------
def ask_medgemma(question: str, retrieved: List[Dict], system_prompt: str = "You are a helpful medical assistant."):
    """Send query + retrieved context to MedGemma Colab API."""
    # Join top-k docs into context
    context = "\n".join([r["text"] for r in retrieved])

    payload = {
        "question": question,
        "context": context,
        "system_prompt": system_prompt
    }

    try:
        resp = requests.post(MEDGEMMA_URL, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return {
            "answer": data.get("answer", "No answer returned"),
            "used_context": context,
            "raw": data
        }
    except Exception as e:
        return {"error": str(e), "answer": "MedGemma request failed."}
