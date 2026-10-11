"""Lexical retrieval baseline (Plan B-proof; no install risk). BM25-lite via TF-IDF overlap."""
from __future__ import annotations

import math
import re
from collections import Counter

from .corpus import load_chunks
from .schemas import EvidenceItem

_WORD = re.compile(r"[a-z0-9]+")

_STOP = frozenset(
    "a an the of is are was were be been to in on for with what when where which who how why "
    "it its this that these those as at by from or and do does did i you we they he she me my your our their his her our".split()
)


def _tokens(s: str) -> list[str]:
    return [w for w in _WORD.findall(s.lower()) if w not in _STOP]


def search(query: str, top_k: int = 5) -> list[EvidenceItem]:
    chunks = load_chunks()
    q = _tokens(query)
    if not q:
        return []
    df: Counter[str] = Counter()
    doc_tf: list[Counter[str]] = []
    for c in chunks:
        t = Counter(_tokens(c.text + " " + (c.section_title or "")))
        doc_tf.append(t)
        for w in set(t):
            df[w] += 1
    n = len(chunks)
    out: list[EvidenceItem] = []
    for c, tf in zip(chunks, doc_tf):
        score = 0.0
        for w in q:
            if w not in tf:
                continue
            idf = math.log(1 + n / (1 + df[w]))
            score += (tf[w] / (tf[w] + 1.2)) * idf
        # small boost for question-relevant sections
        if any(k in c.text.lower() for k in q):
            score *= 1.0
        excerpt = c.text if len(c.text) <= 400 else c.text[:397] + "..."
        out.append(
            EvidenceItem(
                chunk_id=c.chunk_id,
                source_id=c.source_id,
                document_title=c.document_title,
                filename=c.filename,
                pdf_page=c.pdf_page,
                excerpt=excerpt,
                score=round(score, 4),
            )
        )
    out.sort(key=lambda e: e.score, reverse=True)
    return [e for e in out[:top_k] if e.score > 0]
