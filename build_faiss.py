# build_faiss.py
import os
import json
import faiss
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

# ---------------------------
# Config (adjusted to your paths)
# ---------------------------
BASEDIR = Path("knowledge_base_docs/documents")
TEXTDIR = BASEDIR / "texts"
INDEX_PATH = Path("knowledge_base_docs/faiss_index.bin")
META_PATH = Path("knowledge_base_docs/index_meta.json")

# ---------------------------
# Helpers
# ---------------------------
def chunk_text(text, size=500, overlap=50):
    words = text.split()
    for i in range(0, len(words), size - overlap):
        yield " ".join(words[i:i+size])

# ---------------------------
# Step 1. Load embedding model
# ---------------------------
print("Loading embedding model...")
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# ---------------------------
# Step 2. Load documents
# ---------------------------
print(f"Loading documents from {TEXTDIR}")
docs = []
for f in TEXTDIR.glob("*.txt"):
    with open(f, encoding="utf-8") as fh:
        docs.append((f.stem, fh.read()))

# ---------------------------
# Step 3. Chunk documents
# ---------------------------
print("Chunking documents...")
chunks = []
for doc_id, text in docs:
    for ch in chunk_text(text):
        chunks.append((doc_id, ch))

print(f"Total chunks: {len(chunks)}")

# ---------------------------
# Step 4. Embed and build FAISS index
# ---------------------------
print("Encoding embeddings...")
embeddings = model.encode([ch for _, ch in chunks])
embeddings = np.array(embeddings).astype("float32")

dim = embeddings.shape[1]
index = faiss.IndexFlatL2(dim)
index.add(embeddings)

# ---------------------------
# Step 5. Save index + metadata
# ---------------------------
faiss.write_index(index, str(INDEX_PATH))
with open(META_PATH, "w", encoding="utf-8") as f:
    json.dump([{"doc": d, "chunk": c} for (d, c) in chunks], f, indent=2)

print(f"Index saved to {INDEX_PATH}")
print(f"Metadata saved to {META_PATH}")

# ---------------------------
# Step 6. Quick test
# ---------------------------
query = "What are the symptoms of dengue?"
q_emb = model.encode([query]).astype("float32")
D, I = index.search(q_emb, k=3)

meta = json.load(open(META_PATH, encoding="utf-8"))
print("\nQuery:", query)
for rank, idx in enumerate(I[0]):
    print(f"Result {rank+1}: {meta[idx]['chunk'][:200]}...\n")
