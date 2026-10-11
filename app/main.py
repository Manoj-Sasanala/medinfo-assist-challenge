"""MedInfo Assist MVP API."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .corpus import ALLOWLIST, load_chunks
from .generate import extractive, generate
from .retrieve import search
from .safety import DISCLAIMER, is_diagnosis_or_dose, redirect_answer
from .schemas import ChatRequest, ChatResponse, Citation

app = FastAPI(title="MedInfo Assist Challenge (single-PDF MVP)")

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(WEB_DIR / "index.html"))


@app.get("/api/health")
def health() -> dict:
    chunks = load_chunks()
    return {
        "status": "ok",
        "sources": sorted(ALLOWLIST),
        "chunks": len(chunks),
        "llm": "gemini-2.5-flash",
    }


@app.post("/api/search")
def api_search(body: ChatRequest) -> dict:
    return {"results": [e.model_dump() for e in search(body.question)]}


@app.post("/api/chat")
def api_chat(body: ChatRequest) -> dict:
    q = body.question.strip()
    if not q:
        return ChatResponse(
            answer="Please ask a question about the supplied guide.", abstained=True
        ).model_dump()
    if is_diagnosis_or_dose(q):
        return ChatResponse(
            answer=redirect_answer(), safety_redirect=True
        ).model_dump()
    evidence = search(q, top_k=3)
    if not evidence:
        return ChatResponse(
            answer="Not found in the supplied guide — I don't have a supported answer.",
            abstained=True,
        ).model_dump()
    text = generate(q, evidence) or extractive(q, evidence)
    cites = [
        Citation(
            document_title=e.document_title,
            filename=e.filename,
            pdf_page=e.pdf_page,
            chunk_id=e.chunk_id,
            excerpt=e.excerpt,
        )
        for e in evidence[:2]
    ]
    return ChatResponse(answer=text, citations=cites).model_dump()
