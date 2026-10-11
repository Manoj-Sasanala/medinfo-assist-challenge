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
from contracts.schemas import (
    CT04ChatRequest, CT05ChatResponse, CT05Citation, CT06SourceManifest,
)

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
MANIFEST = ROOT / "docs" / "MANIFEST.md"

app = FastAPI(title="MedInfo Assist Challenge (Plan A)")
if FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(FRONTEND / "index.html"))


def _manifest() -> list[dict]:
    # parsed from docs/MANIFEST.md is overkill; rebuild from CT-06 via build facts
    import hashlib
    out = []
    for f, sid in (("Eating_Diabetes_508.pdf", "eating-and-diabetes-nih-08-5043"),
                   ("DIA_Ch01.pdf", "dia-ch01-reference")):
        p = ROOT / "data" / "raw" / f
        if p.exists():
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            import pymupdf
            n = pymupdf.open(p).page_count
            out.append({"source_id": sid, "filename": f, "sha256": h,
                        "page_count": n, "extraction_status": "ok" if sid.startswith("eating") else "reference_only"})
    return out


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "retrieval": "semantic", "manifest": _manifest()}


@app.get("/api/sources")
def sources() -> dict:
    return {"sources": _manifest()}


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
    text = gen.generate(q, pack.results) or gen.extractive(pack.results)
    cites = [CT05Citation(document_title=h.chunk.document_title, pdf_page=h.chunk.pdf_page,
                           printed_page_label=h.chunk.printed_page_label,
                           chunk_id=h.chunk.chunk_id,
                           excerpt=h.chunk.text[:400]) for h in pack.results[:2]]
    return CT05ChatResponse(status="answered", answer=text, citations=cites).model_dump()
