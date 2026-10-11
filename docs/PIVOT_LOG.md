# Plan A / Plan B record (Lane 4)

Plan A attempted FIRST, per 07 proof checkpoints. No pivot on retrieval.

## Generation model retirement (found 2026-10-11 — disclosure)

`gemini-2.5-flash` returns **404 retired**. Consequence: every `answered`
response served before this date was the **extractive fallback**, never Gemini
prose. The fallback worked exactly as designed (no crash, no ungrounded text),
but all earlier claims of "Gemini generation" were wrong — the serving path was
never verified end to end.
Fix: default model is now `gemini-3.8-flash` (verified HTTP 200), overridable
via `GEMINI_MODEL`; any provider failure (retirement, 503 overload, quota)
returns None and serves the extractive quote. Lesson recorded in
docs/ACCEPTANCE.md R-02/R-10: verify the serving path, not just the code path.

## Plan A: semantic (all-MiniLM-L6-v2, 384-dim, FAISS IndexFlatIP)

Install: `pymupdf pypdf faiss-cpu sentence-transformers` — all OK on Python 3.13.
Index: `python scripts/build_embeddings.py` → 54 vectors from extracted corpus.

Gold proof (2026-10-11, threshold SUFFICIENT_SCORE=0.30):

| query | method | status | top chunk | score |
|---|---|---|---|---|
| What should blood glucose be before meals? | semantic | sufficient | eating-p08-c01 (expected) | 0.6911 |
| How do I treat low blood glucose below 70? | semantic | sufficient | eating-p13-c01 | 0.6007 |
| How much is a serving of starch? | semantic | sufficient | eating-p20-c01 | 0.7019 |
| What is the capital of France? | semantic | insufficient | eating-p45-c01 | 0.1366 |

Answerable queries score 0.60–0.69, off-topic 0.14. Clean separation.
Decision: STAY ON PLAN A.

## Plan B: lexical TF-IDF (kept as degraded fallback only)

Used only with `reason_code=index_not_ready` when the FAISS index is absent.
Never preferred while Plan A passes. Both satisfy CT-02 (method recorded).
