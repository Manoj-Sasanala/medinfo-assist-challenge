"""Plan A embeddings build: all-MiniLM-L6-v2 -> normalized -> FAISS IndexFlatIP."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "processed" / "corpus.json"
OUT_INDEX = ROOT / "data" / "processed" / "embeddings.faiss"
OUT_IDS = ROOT / "data" / "processed" / "embedding_ids.json"
MODEL = "all-MiniLM-L6-v2"


def main() -> int:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    texts = [c["text"] for c in corpus]
    model = SentenceTransformer(MODEL)
    vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    vecs = np.asarray(vecs, dtype=np.float32)
    index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(vecs)
    faiss.write_index(index, str(OUT_INDEX))
    OUT_IDS.write_text(json.dumps([c["chunk_id"] for c in corpus]), encoding="utf-8")
    print(f"OK model={MODEL} dim={vecs.shape[1]} vectors={index.ntotal}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
