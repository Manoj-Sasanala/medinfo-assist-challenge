"""Lane 2 Backend/API (Plan A): CT-04 in, CT-03xCT-02 routing, CT-05 out."""
from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend import generate as gen
from backend import retrieve as ret
from backend import safety as pol
from backend import validate as val
from contracts.schemas import (
    CT04ChatRequest, CT05ChatResponse, CT05Citation, CT06SourceManifest,
)

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
MANIFEST_JSON = ROOT / "data" / "processed" / "manifest.json"
CORPUS_JSON = ROOT / "data" / "processed" / "corpus.json"
INDEX_PATH = ROOT / "data" / "processed" / "embeddings.faiss"

app = FastAPI(title="MedInfo Assist Challenge (Plan A)")
if FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(FRONTEND / "index.html"))


def _readiness() -> dict:
    """CT-06 readiness from committed derived artifacts (works without raw PDFs)."""
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8")) if MANIFEST_JSON.exists() else []
    corpus = json.loads(CORPUS_JSON.read_text(encoding="utf-8")) if CORPUS_JSON.exists() else []
    indexed = {c.get("source_id") for c in corpus}
    sources = []
    for m in manifest:
        raw = ROOT / "data" / "raw" / m["filename"]
        sources.append({**m, "raw_present": raw.exists(),
                        "chunks_indexed": sum(1 for c in corpus if c.get("source_id") == m["source_id"])})
    ready = bool(corpus) and ret.semantic_ready() and any(s["chunks_indexed"] > 0 for s in sources)
    sem = ret.semantic_ready()
    rt = ret.runtime_status()
    return {
        "status": "ok" if ready else "not_ready",
        "retrieval": "semantic" if sem else "lexical_fallback",
        "chunks": len(corpus),
        "index_present": INDEX_PATH.exists(),
        "sources": sources,
        # Degraded-state visibility: file-level readiness above cannot see
        # request-time failures, so runtime fallbacks and validator mode are
        # reported explicitly. Per-response fallback is in CT-02 reason_code.
        "degraded": {
            "semantic_fallbacks": rt["semantic_fallbacks"],
            "last_semantic_error": rt["last_semantic_error"],
            "nli_available": val.nli_available(),
            "validator": val.validator_mode(),
        },
    }


@app.get("/api/health")
def health() -> dict:
    return _readiness()


@app.get("/api/sources")
def sources() -> dict:
    r = _readiness()
    return {"sources": r["sources"], "status": r["status"]}


@app.post("/api/search")
def api_search(body: CT04ChatRequest) -> dict:
    return ret.retrieve(body.question.strip(), query_id=str(uuid4())[:8]).model_dump()


@app.post("/api/chat")
def api_chat(body: CT04ChatRequest) -> dict:
    q = (body.question or "").strip()
    if not q:
        return CT05ChatResponse(status="system_error",
                                answer="Empty question. Please ask about the supplied guides.").model_dump()
    dec = pol.decide(q)
    if dec.decision in ("safety_redirect", "emergency_redirect"):
        return CT05ChatResponse(status="safety_redirect",
                                answer=dec.user_message or "I can't help with that.").model_dump()
    pack = ret.retrieve(q, query_id=str(uuid4())[:8])
    if pack.evidence_status != "sufficient" or not pack.results:
        return CT05ChatResponse(
            status="insufficient_evidence",
            answer="The supplied guides do not provide enough information to answer that reliably.").model_dump()
    text = gen.generate(q, pack.results)
    cited = pack.results[:2]  # exactly what the UI shows; grounding is checked against these
    if text is None or not val.grounded(text, cited):
        # Extractive fallback is served WITHOUT re-validation: it is a verbatim
        # quote by construction, so it cannot add claims (its "From T (page N):"
        # framing is provenance, not a claim — see test_nli_rejects_extra_claim).
        text = gen.extractive(pack.results)  # ungrounded prose is never served
    cites = [CT05Citation(document_title=h.chunk.document_title, pdf_page=h.chunk.pdf_page,
                           printed_page_label=h.chunk.printed_page_label,
                           chunk_id=h.chunk.chunk_id,
                           excerpt=h.chunk.text[:400]) for h in pack.results[:2]]
    return CT05ChatResponse(status="answered", answer=text, citations=cites).model_dump()
