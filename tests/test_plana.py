"""Plan A golden tests: extraction integrity, semantic proof, CT statuses, citations."""
import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api import app
from backend.retrieve import retrieve

client = TestClient(app)
ROOT = Path(__file__).resolve().parent.parent


def test_extraction_integrity():
    corpus = json.loads((ROOT / "data" / "processed" / "corpus.json").read_text(encoding="utf-8"))
    assert len(corpus) >= 40, "expected full-guide extraction, not fixtures"
    pages = {c["pdf_page"] for c in corpus}
    assert min(pages) >= 1 and max(pages) <= 52
    assert all(c["source_id"] == "eating-and-diabetes-nih-08-5043" for c in corpus)
    assert all(c["text"].strip() for c in corpus)


def test_plan_a_gold_proof():
    pack = retrieve("What should blood glucose be before meals?", top_k=3)
    assert pack.retrieval_method == "semantic"
    assert pack.evidence_status == "sufficient"
    assert pack.results[0].chunk.chunk_id == "eating-p08-c01"
    assert pack.results[0].score >= 0.30


def test_offtopic_insufficient():
    pack = retrieve("What is the capital of France?", top_k=3)
    assert pack.retrieval_method == "semantic"
    assert pack.evidence_status == "insufficient"


def test_chat_statuses():
    ok = client.post("/api/chat", json={"question": "How much is a serving of starch?"}).json()
    assert ok["status"] == "answered" and len(ok["citations"]) >= 1
    assert all(c["pdf_page"] >= 1 for c in ok["citations"])
    no = client.post("/api/chat", json={"question": "What is the capital of France?"}).json()
    assert no["status"] == "insufficient_evidence" and no["citations"] == []
    dx = client.post("/api/chat", json={"question": "Do I have diabetes? What dose?"}).json()
    assert dx["status"] == "safety_redirect" and dx["citations"] == []
    for j in (ok, no, dx):
        assert "medical advice" in j["disclaimer"]


def test_citations_resolve():
    ids = {c["chunk_id"] for c in json.loads((ROOT / "data" / "processed" / "corpus.json").read_text(encoding="utf-8"))}
    j = client.post("/api/chat", json={"question": "What should blood glucose be before meals?"}).json()
    for c in j["citations"]:
        assert c["chunk_id"] in ids
