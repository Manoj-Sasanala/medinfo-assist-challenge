"""Robustness: fallback paths, fail-closed safety, schema validity."""
import json
import os
from pathlib import Path

from backend import generate as gen
from backend import retrieve as ret
from backend.safety import decide
from contracts.schemas import CT01Chunk

ROOT = Path(__file__).resolve().parent.parent


def test_all_chunks_validate_ct01():
    corpus = json.loads((ROOT / "data" / "processed" / "corpus.json").read_text(encoding="utf-8"))
    for c in corpus:
        CT01Chunk(**c)


def test_lexical_fallback_when_index_missing(monkeypatch):
    monkeypatch.setattr(ret, "INDEX_PATH", ROOT / "data" / "processed" / "no-such-index.faiss")
    ret._semantic.cache_clear()
    try:
        pack = ret.retrieve("What should blood glucose be before meals?", top_k=3)
    finally:
        ret._semantic.cache_clear()
    assert pack.retrieval_method == "lexical"
    assert pack.reason_code == "index_not_ready"


def test_safety_fails_closed(monkeypatch):
    assert decide(None).decision == "safety_redirect"
    assert decide("").decision == "safety_redirect"


def test_generate_none_without_key(monkeypatch):
    from contracts.schemas import CT02Hit
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert gen.generate("q?", []) is None
    chunk = CT01Chunk(chunk_id="c1", source_id="s", document_title="T",
                      filename="f.pdf", pdf_page=8, text="x" * 500)
    out = gen.extractive([CT02Hit(chunk=chunk, score=0.9, rank=1)])
    assert "page 8" in out and isinstance(out, str)


def test_corrupt_corpus_fails_closed(monkeypatch, tmp_path):
    bad = tmp_path / "corpus.json"
    bad.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(ret, "CORPUS_PATH", bad)
    ret._corpus.cache_clear()
    try:
        pack = ret.retrieve("What should blood glucose be before meals?")
    finally:
        ret._corpus.cache_clear()
    assert pack.evidence_status == "insufficient"
    assert pack.reason_code == "corpus_unavailable"


def test_grounding_validator_on_live_answers():
    from fastapi.testclient import TestClient
    from backend.api import app
    from backend import validate as val
    t = TestClient(app)
    for q in [
        "What should blood glucose be before meals?",
        "How much is a serving of starch?",
        "How do I treat low blood glucose below 70?",
    ]:
        j = t.post("/api/chat", json={"question": q}).json()
        assert j["status"] == "answered", q
        pack = ret.retrieve(q, top_k=2)
        assert val.grounded(j["answer"], pack.results), q
        assert val.coverage(j["answer"], pack.results) >= val.MIN_COVERAGE
