"""Plan A retrieval (Lane 4): semantic FAISS first, lexical fallback. Emits CT-02."""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from contracts.schemas import CT01Chunk, CT02EvidencePack, CT02Hit

ROOT = Path(__file__).resolve().parent.parent
CORPUS_PATH = ROOT / "data" / "processed" / "corpus.json"
INDEX_PATH = ROOT / "data" / "processed" / "embeddings.faiss"
IDS_PATH = ROOT / "data" / "processed" / "embedding_ids.json"

MODEL = "all-MiniLM-L6-v2"
SUFFICIENT_SCORE = 0.30  # calibrated on gold queries, see docs/PIVOT_LOG.md

_WORD = re.compile(r"[a-z0-9]+")
_STOP = frozenset(
    "a an the of is are was were be been to in on for with what when where which who how why "
    "it its this that these those as at by from or and do does did i you we they he she him her our your".split()
)


def _toks(s: str) -> list[str]:
    return [w for w in _WORD.findall(s.lower()) if w not in _STOP]


@lru_cache(maxsize=1)
def _corpus() -> list[CT01Chunk]:
    try:
        return [CT01Chunk(**c) for c in json.loads(CORPUS_PATH.read_text(encoding="utf-8"))]
    except Exception:
        return []  # corrupt/missing corpus fails closed downstream (insufficient)


@lru_cache(maxsize=1)
def _semantic():
    if not (INDEX_PATH.exists() and IDS_PATH.exists()):
        return None, None, None
    index = faiss.read_index(str(INDEX_PATH))
    ids = json.loads(IDS_PATH.read_text(encoding="utf-8"))
    return SentenceTransformer(MODEL), index, ids


def _lexical(query: str, top_k: int) -> list[tuple[CT01Chunk, float]]:
    chunks = _corpus()
    q = _toks(query)
    if not q:
        return []
    df: Counter[str] = Counter()
    tf_list: list[Counter[str]] = []
    for c in chunks:
        t = Counter(_toks(c.text))
        tf_list.append(t)
        for w in set(t):
            df[w] += 1
    n = len(chunks)
    scored = []
    for c, tf in zip(chunks, tf_list):
        s = sum((tf[w] / (tf[w] + 1.2)) * math.log(1 + n / (1 + df[w])) for w in q if w in tf)
        scored.append((c, round(s, 4)))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [(c, s) for c, s in scored[:top_k] if s > 0]


def retrieve(query: str, top_k: int = 5, query_id: str = "q") -> CT02EvidencePack:
    if not _corpus():
        return CT02EvidencePack(query_id=query_id, evidence_status="insufficient",
                                results=[], retrieval_method="lexical",
                                reason_code="corpus_unavailable")
    model, index, ids = _semantic()
    if model is not None:
        qv = np.asarray(model.encode([query], normalize_embeddings=True), dtype=np.float32)
        scores, idx = index.search(qv, top_k)
        chunks = _corpus()
        by_id = {c.chunk_id: c for c in chunks}
        hits = []
        for rank, (i, s) in enumerate(zip(idx[0], scores[0]), start=1):
            c = by_id[ids[int(i)]]
            hits.append(CT02Hit(chunk=c, score=round(float(s), 4), rank=rank))
        status = "sufficient" if hits and hits[0].score >= SUFFICIENT_SCORE else "insufficient"
        return CT02EvidencePack(
            query_id=query_id, evidence_status=status, results=hits,
            retrieval_method="semantic",
            reason_code=None if status == "sufficient" else "below_threshold",
        )
    lex = _lexical(query, top_k)
    hits = [CT02Hit(chunk=c, score=s, rank=r) for r, (c, s) in enumerate(lex, start=1)]
    return CT02EvidencePack(
        query_id=query_id,
        evidence_status="sufficient" if hits else "insufficient",
        results=hits, retrieval_method="lexical", reason_code="index_not_ready",
    )
